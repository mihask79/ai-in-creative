"""Generate real measurements; partial artifacts are checkpointed after every call."""
import os
os.environ.setdefault('HF_HUB_DISABLE_XET','1')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
from datetime import datetime, timezone, timedelta
import importlib.metadata as md
import json
from pathlib import Path
import platform
import time
import numpy as np
import torch
from PIL import Image
import lab06_lib as L

ROOT = L.ROOT
ART = ROOT/'artifacts'
def now(): return datetime.now(timezone(timedelta(hours=3))).isoformat()
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def generate_series():
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    ART.mkdir(exist_ok=True)
    pre = dict(recorded_at=now(),variant=1,student='Скрыпник Михаил Дмитриевич',group='МИК11',
        factor='num_inference_steps: 1 -> 4',seeds=L.SEEDS,prompt=L.PROMPT,
        A=dict(steps=1,guidance=0.0,size=512),B=dict(steps=4,guidance=0.0,size=512),
        hypothesis='Четыре шага повысят энергию границ и время; CLIP останется в пределах ±1,0. Контраст может возрасти.',
        tolerance=dict(clip=dict(kind='absolute',value=1.0),edge=dict(kind='relative',value=0.10),
                       contrast=dict(kind='relative',value=0.10),seconds=dict(kind='relative',value=0.20)),
        direction='CLIP, edge, contrast: рост показателя; seconds: уменьшение. Рост edge и contrast не доказывает качество.',
        payoff_rule='4 шага оправданы для черновиков, только если CLIP вырастет более чем на 1,0, время вырастет не более чем на 20%, а главный объект останется узнаваемым.',
        error_hypothesis='При guidance 1.0 CFG не включится; PNG совпадёт с guidance 0.0.',
        model=L.MODEL_ID,revision=L.REVISION,clip_model=L.CLIP_ID,clip_revision=L.CLIP_REVISION,
        environment_deviation='Локальный CPU float32 вместо Colab T4 float16; оба режима на одинаковой среде.')
    assert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]]==['steps']
    save(ROOT/'configs/preregistration.json',pre)
    env=dict(platform=platform.platform(),python=platform.python_version(),cpu=platform.processor(),
        device='cpu',dtype='float32',weight_variant='fp16',threads=torch.get_num_threads(),
        cuda_available=torch.cuda.is_available(),deterministic_algorithms=True,attention='PyTorch SDPA; slicing disabled',
        packages={k:md.version(k) for k in ['torch','diffusers','transformers','numpy','Pillow','accelerate','safetensors']})
    save(ROOT/'reports/environment.json',env)
    print('Гипотеза и допуски записаны ДО запуска:',pre['recorded_at'],flush=True)
    print(json.dumps(pre,ensure_ascii=False,indent=2),flush=True)
    t=time.perf_counter(); pipe=L.load_pipe(); load=time.perf_counter()-t
    print(f'Модель загружена: {load:.2f} с; CPU, 4 потока, float32',flush=True)
    warm=[]
    for steps in [1,4]:
        t=time.perf_counter(); L.generate(pipe,0,steps=steps); dt=time.perf_counter()-t
        warm.append(dict(steps=steps,seconds=dt)); print(f'Прогрев {steps}: {dt:.2f} с',flush=True)
    rows=[]
    for seed in L.SEEDS:
        for mode,steps in [('A',1),('B',4)]:
            started=now(); t=time.perf_counter(); img=L.generate(pipe,seed,steps=steps); dt=time.perf_counter()-t
            folder=ART/f'{mode}_{seed}'; folder.mkdir(exist_ok=True)
            raw=L.png_bytes(img); (folder/'result.png').write_bytes(raw)
            row=dict(mode=mode,seed=seed,steps=steps,guidance=0.0,size=512,seconds=dt,
                edge=L.edge_energy(img),contrast=L.contrast(img),sha256=L.sha(raw),
                path=f'artifacts/{mode}_{seed}/result.png',started_at=started,finished_at=now(),
                cfg_active=bool(pipe.do_classifier_free_guidance))
            save(folder/'manifest.json',{**row,**env, 'model':L.MODEL_ID,'revision':L.REVISION,'prompt':L.PROMPT})
            rows.append(row); save(ART/'generation_checkpoint.json',dict(preregistration=pre,environment=env,
                load_seconds=load,warmup=warm,measurements=rows))
            print(f'{mode} seed={seed} steps={steps} time={dt:.2f}s edge={row["edge"]:.6f} contrast={row["contrast"]:.6f}',flush=True)
    base=Image.open(ART/'A_101/result.png').convert('RGB')
    errors={}
    for guidance in [1.0,3.0]:
        t=time.perf_counter(); img=L.generate(pipe,101,guidance=guidance); dt=time.perf_counter()-t
        raw=L.png_bytes(img); path=ART/f'guidance_{int(guidance)}.png'; path.write_bytes(raw)
        mse=float(np.mean((np.asarray(img,dtype=np.float64)-np.asarray(base,dtype=np.float64))**2))
        errors[str(guidance)]=dict(guidance=guidance,cfg_active=bool(pipe.do_classifier_free_guidance),
            seconds=dt,sha256=L.sha(raw),same_sha256=L.sha(raw)==L.sha((ART/'A_101/result.png').read_bytes()),
            pixel_equal=bool(np.array_equal(np.asarray(img),np.asarray(base))),mse=mse,
            psnr_db='Infinity' if mse==0 else 10*np.log10(255**2/mse),path=f'artifacts/{path.name}')
        print('Проверка guidance:',json.dumps(errors[str(guidance)],ensure_ascii=False),flush=True)
    save(ART/'guidance_check.json',errors)
    sheet=Image.new('RGB',(768,384))
    for i,mode in enumerate(['A','B']):
        with Image.open(ART/f'{mode}_101/result.png') as im: sheet.paste(im.resize((384,384)),(384*i,0))
    sheet.save(ART/'comparison.png')
    print('Серия изображений и проверка guidance завершены.',flush=True)

def score_series():
    torch.set_num_threads(4)
    checkpoint=json.loads((ART/'generation_checkpoint.json').read_text(encoding='utf-8'))
    print('Загрузка закреплённой CLIP ViT-B/32...',flush=True)
    clip=L.load_clip()
    rows=checkpoint['measurements']
    for row in rows:
        with Image.open(ROOT/row['path']) as im: row['clip']=L.clip_sim(clip,im)
        print(f'{row["mode"]} seed={row["seed"]}: CLIP={row["clip"]:.6f}',flush=True)
    summary=L.summarize(rows,checkpoint['preregistration'])
    result={**checkpoint,'finished_at':now(),'measurements':rows,'summary':summary,
            'guidance_check':json.loads((ART/'guidance_check.json').read_text(encoding='utf-8'))}
    save(ART/'results.json',result)
    import csv
    with (ART/'metrics_by_seed.csv').open('w',encoding='utf-8-sig',newline='') as f:
        keys=['mode','seed','steps','clip','edge','contrast','seconds','sha256']
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    with (ART/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
    for row in summary: print(json.dumps(row,ensure_ascii=False),flush=True)
    save(ART/'passport.json',dict(student=checkpoint['preregistration']['student'],group='МИК11',variant=1,
        date='2026-10-27',actual_environment=checkpoint['environment'],parameters=checkpoint['preregistration'],
        source='Приложение А ЛР06: адаптация CPU, NumPy Sobel; библиотека ЛР05 расширена параметрами.',
        validity='Одна модель, один бриф, 5 seed, локальный CPU. Новый сеанс и GPU не проверены.',
        notebook='LR06.ipynb',results='artifacts/results.json'))
    return result

if __name__=='__main__':
    import sys
    if '--score-only' in sys.argv: score_series()
    else: generate_series()
