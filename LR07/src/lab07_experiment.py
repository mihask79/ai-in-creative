"""Variant 1: measured training, checkpointed results, and latent-size diagnostics."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
import hashlib
import importlib.metadata
import json
import platform
import sys
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
import lab07_lib as L

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts'
TZ = timezone(timedelta(hours=3))


def now():
    return datetime.now(TZ).isoformat(timespec='seconds')


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def log(message):
    line = f'{now()} {message}'
    print(line, flush=True)
    with (ROOT / 'reports/training_log.txt').open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def preregister():
    path = ROOT / 'configs/preregistration.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    a, b = L.settings(L.FACTORS[0])
    pre = dict(recorded_at=now(), variant=1, kind='disc', factor='latent_8_to_2',
               hypothesis='Сжатие латентного вектора с 8 до 2 чисел снизит PSNR на тесте более чем на 1 дБ. '
               'Изменение разрыва train-test останется в пределах 0,1 дБ; изменение времени - в пределах 20%. '
               'Основная предполагаемая причина потери качества - недостаточное узкое место для трёх факторов сцены.',
               A=a, B=b, seeds=list(L.SEEDS), data_seed=7,
               tolerances=dict(psnr=1.0, gap=0.1, seconds_relative=0.2),
               tolerance_rationale=dict(psnr='Изменение MSE примерно в 1,26 раза считаем практически заметным.',
                   gap='Сдвиг разрыва менее 0,1 дБ считаем малым.', seconds='Меньше 20% времени не считаем существенным.'),
               diagnostic_d=[1,2,3,4,8], diagnostic_seeds=[101,102,103],
               params_rule='Точное изменение ёмкости; практический допуск не задаётся.',
               environment_adaptation='Локальный Windows, CPU float32, 4 потока; Colab T4 не используется. '
                   'Данные, архитектура, шаг Adam, batch и 20 эпох сохранены.')
    write_json(path, pre)
    return pre


def summarize(records, pre):
    rows = []
    for metric in ('psnr', 'gap', 'params', 'seconds'):
        a = np.array([r[metric] for r in records if r['mode']=='A'])
        b = np.array([r[metric] for r in records if r['mode']=='B'])
        av, bv, s = float(a.mean()), float(b.mean()), float(a.std(ddof=1))
        delta = bv-av
        tol = pre['tolerances'].get(metric)
        if metric == 'seconds':
            tol = av*pre['tolerances']['seconds_relative']
        outside = None if tol is None else abs(delta)>tol
        if metric == 'params':
            classification = 'снижение числа параметров'
        elif not outside:
            classification = 'нейтрально'
        else:
            improved = delta>0 if metric=='psnr' else delta<0
            classification = 'улучшение' if improved else 'ухудшение'
        rows.append(dict(metric=metric,A=av,s=s,B=bv,delta=delta,
                         ratio=abs(delta)/s if s>0 else None,
                         criterion_2s=abs(delta)>2*s,threshold=tol,
                         outside_tolerance=outside,classification=classification))
    return rows


def image_sheet(reconstructions, original):
    tiles = [original.cpu().numpy().transpose(0,2,3,1)] + reconstructions
    grid = np.concatenate([np.concatenate(list(row),axis=1) for row in tiles],axis=0)
    sheet = Image.fromarray((np.clip(grid,0,1)*255).round().astype('uint8')).resize((1024,384),Image.Resampling.NEAREST)
    sheet.save(ART/'comparison.png')
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    labeled = Image.new('RGB',(1220,434),'white')
    draw = ImageDraw.Draw(labeled)
    for i,name in enumerate(['Оригинал','A: d = 8','B: d = 2']):
        labeled.paste(sheet.crop((0,i*128,1024,(i+1)*128)),(180,40+i*128))
        draw.text((12,90+i*128),name,font=font,fill='#172938')
    draw.text((180,8),'Первые 8 тестовых сцен; seed обучения 101',font=font,fill='#172938')
    labeled.save(ART/'comparison_labeled.png')


def run_all():
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    pre = preregister()
    assert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]] == ['d']
    env = dict(recorded_at=now(),platform=platform.platform(),python=sys.version,
               executable=sys.executable,device=L.DEVICE,dtype='float32',threads=4,
               deterministic_algorithms=True,
               packages={p:importlib.metadata.version(p) for p in ['torch','numpy','Pillow','nbformat','nbclient']},
               library_sha256=hashlib.sha256((ROOT/'src/lab07_lib.py').read_bytes()).hexdigest())
    write_json(ROOT/'reports/environment.json',env)
    Xtr,Xte,Ftr,Fte = L.dataset('disc')
    baseline = L.psnr_images(Xtr.mean(0,keepdim=True).expand_as(Xte),Xte)
    np.savez_compressed(ART/'dataset_identity.npz',train_factors=Ftr.cpu().numpy(),test_factors=Fte.cpu().numpy())
    data_hash = hashlib.sha256(Xtr.cpu().numpy().tobytes()+Xte.cpu().numpy().tobytes()).hexdigest()
    records=[]; diagnostics=[]; recons=[]
    log('Гипотеза и допуски записаны ДО обучения: '+pre['recorded_at'])
    log(f'Среда {env["packages"]["torch"]}; {L.DEVICE}; средняя картинка PSNR={baseline:.6f}')
    log('Прогрев: полный режим A, seed 0; не входит в статистику')
    L.run('disc',pre['A'],0)
    for seed in L.SEEDS:
        for mode in ('A','B'):
            cfg=pre[mode]
            started=now()
            log(f'Начало {mode}, seed={seed}, d={cfg["d"]}, 20 эпох')
            metrics,model=L.run('disc',cfg,seed)
            checkpoint=ART/f'{mode}_{seed}_weights.npz'
            np.savez_compressed(checkpoint,**{k:v.detach().cpu().numpy() for k,v in model.state_dict().items()})
            record=dict(mode=mode,seed=seed,d=cfg['d'],started_at=started,completed_at=now(),
                        checkpoint=str(checkpoint.relative_to(ROOT)).replace('\\','/'),**metrics)
            records.append(record)
            if seed==101:
                recons.append(L.reconstruct(model,Xte[:8]).cpu().numpy().transpose(0,2,3,1))
            log(f'Готово {mode}, seed={seed}: PSNR={metrics["psnr"]:.6f}; gap={metrics["gap"]:.6f}; время={metrics["seconds"]:.2f} с')
            write_json(ART/'measurements_checkpoint.json',records)
            del model
    image_sheet(recons,Xte[:8])
    for d in pre['diagnostic_d']:
        vals=[]
        for seed in pre['diagnostic_seeds']:
            cached=next((r for r in records if r['d']==d and r['seed']==seed),None)
            if cached:
                vals.append(cached['psnr'])
            else:
                log(f'Диагностика d={d}, seed={seed}, 20 эпох')
                metrics,model=L.run('disc',dict(L.BASE,d=d),seed)
                vals.append(metrics['psnr'])
                del model
                log(f'Диагностика d={d}, seed={seed}: PSNR={vals[-1]:.6f}')
        diagnostics.append(dict(d=d,seeds=pre['diagnostic_seeds'],values=vals,mean=float(np.mean(vals)),s=float(np.std(vals,ddof=1))))
        write_json(ART/'diagnostics_checkpoint.json',diagnostics)
    result=dict(variant=1,completed_at=now(),preregistration=pre,environment=env,
                dataset=dict(train=4096,test=1024,shape=[3,32,32],seed=7,sha256=data_hash),
                baseline_psnr=baseline,measurements=records,summary=summarize(records,pre),diagnostics=diagnostics)
    write_json(ART/'results.json',result)
    passport=dict(student='Скрыпник Михаил Дмитриевич',group='МИК11',variant=1,
                  task='Построение автокодировщика: диск, d 8 -> 2',
                  preregistration=pre,environment=env,dataset=result['dataset'],
                  training=dict(optimizer='Adam',lr=0.002,batch=128,epochs=20,steps=640),
                  baseline_psnr=baseline,command='python src/build_notebook.py',
                  source='Библиотека восстановлена из приложения А PDF: исправлены только переносы строк.',
                  rights='Синтетические сцены; внешних изображений и весов нет. Отдельная лицензия на библиотеку в методичке не указана.',
                  limitations=['Windows CPU вместо Colab T4','Один фиксированный train/test split','Пять seed','Синтетические сцены','2s - эвристика, не формальный тест'])
    write_json(ART/'passport.json',passport)
    with (ART/'metrics_by_seed.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    with (ART/'summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(result['summary'][0]));w.writeheader();w.writerows(result['summary'])
    log('Все 19 измеряемых обучений завершены: 10 основных + 9 дополнительных; 6 диагностических точек переиспользуют основную серию.')
    return result


if __name__=='__main__':
    run_all()
