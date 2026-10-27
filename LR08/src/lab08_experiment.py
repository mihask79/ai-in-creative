"""Measured variant 1, original teaching-library algorithms, CPU execution."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
import hashlib
import importlib.metadata
import json
import platform
import sys
import time
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import lab07_lib as L
import lab08_lib as V
ART = ROOT / 'artifacts'
METRICS = ['recon', 'interp', 'sample', 'r2']


def now():
    return datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds')


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def log(message):
    line = now() + ' ' + str(message)
    print(line, flush=True)
    with (ROOT / 'reports/training_log.txt').open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def preregister():
    path = ROOT / 'configs/preregistration.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    a, b = V.settings(V.FACTORS[0])
    obj = dict(recorded_at=now(), variant=1, kind='disc', factor='beta_1_to_8', A=a, B=b,
        seeds=list(L.SEEDS), data_seed=7, pair_seed=11, sample_seed='1000 + training_seed',
        hypothesis='Увеличение beta с 1 до 8 ухудшит реконструкцию более чем на 1 дБ и уменьшит число активных осей. '
                   'Предполагается улучшение интерполяции и качества сэмплов более чем на 1 дБ; '
                   'изменение R2 предполагается в пределах 0,05. Эти предположения могут не подтвердиться.',
        tolerances=dict(recon=1.0, interp=1.0, sample=1.0, r2=0.05),
        tolerance_rationale='1 дБ соответствует изменению MSE примерно в 1,26 раза; 0,05 R2 - пять процентных пунктов '
                            'объяснённой дисперсии. Учебные пороги практической величины, не критерий проверки гипотез.',
        active_axis_rule='mean_test KL_j > 0.05 nat; mu.std uses ddof=1',
        diagnostics='AE beta=0 seed101; no warmup beta=1 seeds101..105; warmup main A reused',
        environment_adaptation='Windows CPU float32, 4 threads; Engee/Julia not used; algorithms and training budget preserved')
    save_json(path, obj)
    return obj


def summarize(records, pre):
    rows = []
    for metric in METRICS:
        a = np.array([r['metrics'][metric] for r in records if r['mode']=='A'])
        b = np.array([r['metrics'][metric] for r in records if r['mode']=='B'])
        av, bv, s = float(a.mean()), float(b.mean()), float(a.std(ddof=1))
        delta = bv-av
        outside = abs(delta)>pre['tolerances'][metric]
        rows.append(dict(metric=metric, A=av, s=s, B=bv, delta=delta,
            ratio=abs(delta)/s if s>0 else None, criterion_2s=abs(delta)>2*s,
            tolerance=pre['tolerances'][metric], classification=(('улучшение' if delta>0 else 'ухудшение') if outside else 'нейтрально'),
            outside_tolerance=outside))
    return rows


@torch.no_grad()
def diagnostics(model, beta):
    x = L.dataset('disc')[1]
    mu, lv = model.encode_dist(x)
    kl = (-0.5*(1+lv-mu**2-lv.exp())).mean(0)
    return dict(mu_std=mu.std(0).cpu().tolist(), mu_mean=mu.mean(0).cpu().tolist(),
                kl_axis=kl.cpu().tolist(), active_axes=int((kl>0.05).sum()) if beta>0 else None,
                ae_kl_note='For beta=0, lv head is untrained; KL and active count are not interpreted.' if beta==0 else None)


def train_record(mode, beta, seed, warmup=10):
    x = L.dataset('disc')[0]
    started = now()
    log(f'START {mode} beta={beta:g} seed={seed} warmup={warmup:g} epochs=30')
    torch.manual_seed(seed)
    t0 = time.perf_counter()
    model = V.train_vae(V.ConvVAE(8).to(L.DEVICE), x, beta, 30, seed=seed, warmup=warmup)
    seconds = time.perf_counter()-t0
    metrics = V.metrics(model, 'disc', 'lin', 1.0, seed)
    diag = diagnostics(model, beta)
    checkpoint = f'artifacts/checkpoints/{mode}_seed_{seed}.npz'
    np.savez_compressed(ROOT/checkpoint, **{k:v.detach().cpu().numpy() for k,v in model.state_dict().items()})
    record = dict(mode=mode, beta=beta, seed=seed, warmup=warmup, started_at=started, finished_at=now(),
                  seconds=seconds, metrics=metrics, diagnostics=diag, checkpoint=checkpoint,
                  checkpoint_sha256=hashlib.sha256((ROOT/checkpoint).read_bytes()).hexdigest())
    save_json(ART/f'{mode}_seed_{seed}.json', record)
    log(f'END {mode} seed={seed}: '+', '.join(f'{k}={v:.6f}' for k,v in metrics.items())+
        f'; active={diag["active_axes"]}; seconds={seconds:.3f}')
    log('mu_std='+str([round(v,4) for v in diag['mu_std']])+'; KL_axis='+str([round(v,4) for v in diag['kl_axis']]))
    return record, model


def tile_row(tensor):
    a = tensor.detach().cpu().numpy().transpose(0,2,3,1)
    return np.concatenate(list(a),axis=1)


def save_grid(rows, path, scale=4):
    data = np.concatenate([tile_row(r) for r in rows],axis=0)
    im = Image.fromarray((np.clip(data,0,1)*255).round().astype('uint8'))
    im = im.resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST)
    im.save(path)
    return im


@torch.no_grad()
def comparisons(models):
    ae, a, b = models['AE'], models['A'], models['B']
    x, f = L.dataset('disc')[1], L.dataset('disc')[3]
    g = torch.Generator(device='cpu').manual_seed(5)
    z = torch.randn((8,8),generator=g).to(L.DEVICE)
    t = torch.linspace(0,1,8,device=L.DEVICE).unsqueeze(1)
    paths = []
    for model in [a,b]:
        za, zb = model.encode(x[0:1]), model.encode(x[2:3])
        paths.append(model.decode((1-t)*za+t*zb))
    samples = [m.decode(z) for m in [ae,a,b]]
    save_grid([samples[0], samples[1], *paths], ART/'comparison.png')
    factors = ((1-t)*f[0:1]+t*f[2:3]).cpu().numpy()
    truth = torch.tensor(np.stack([L.render('disc',fi) for fi in factors]))
    full = save_grid([*samples,truth,*paths], ART/'comparison_extended.png')
    labeled = Image.new('RGB',(1320,6*128+100),'white')
    labeled.paste(full,(282,60))
    draw = ImageDraw.Draw(labeled)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    draw.text((15,15),'Seed обучения 101; сэмплы: seed 5; интерполяция: тестовые сцены 0 → 2',font=font,fill='#183047')
    for i,label in enumerate(['Сэмплы AE, beta=0','Сэмплы A, beta=1','Сэмплы B, beta=8','Истинный путь факторов','Интерполяция A, beta=1','Интерполяция B, beta=8']):
        draw.text((10,110+128*i),label,font=font,fill='#183047')
    for i in range(8):draw.text((304+128*i,834),f't={i/7:.2f}',font=font,fill='#183047')
    labeled.save(ART/'comparison_labeled.png')
    save_grid([x[:8],a.decode(a.encode(x[:8])),b.decode(b.encode(x[:8]))],ART/'reconstructions.png')
    # Pair selection is fixed in the method, without searching for attractive examples.
    save_json(ART/'comparison_manifest.json',dict(training_seed=101,sample_seed=5,test_indices=[0,2],
        interpolation_t=[i/7 for i in range(8)],endpoint_factors=f[[0,2]].cpu().tolist(),
        rows=['AE samples','A samples','B samples','true factor path','A interpolation','B interpolation']))


def console_image():
    lines = (ROOT/'reports/training_log.txt').read_text(encoding='utf-8').splitlines()
    # Faithful image of selected actual stdout lines, not a simulated app screenshot.
    selected = ['ЛР08 / вариант 1 / фрагмент фактического журнала', 'Полный вывод: reports/training_log.txt', '']
    selected += [line for line in lines if 'SUMMARY' in line or 'BASELINE' in line or 'AE CHECK' in line or 'WARMUP CHECK' in line or 'COMPLETE' in line]
    import textwrap
    rows = [part for line in selected for part in (textwrap.wrap(line,width=115) or [''])]
    im=Image.new('RGB',(1540,42+len(rows)*25),'#122030')
    draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',20)
    for i,line in enumerate(rows):draw.text((22,18+i*25),line,font=font,fill='#dfebf4')
    im.save(ART/'console_output.png')


def run_all():
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    pre = preregister()
    assert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]]==['beta']
    (ROOT/'reports/training_log.txt').write_text('',encoding='utf-8')
    log('PREREGISTRATION '+json.dumps(pre,ensure_ascii=False))
    env=dict(recorded_at=now(),platform=platform.platform(),python=sys.version,executable=sys.executable,
             device=L.DEVICE,threads=torch.get_num_threads(),dtype='float32',deterministic_algorithms=True,
             packages={k:importlib.metadata.version(k) for k in ['torch','numpy','Pillow','nbformat','nbclient']},
             libraries={k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest() for k in ['lab07_lib.py','lab08_lib.py']})
    save_json(ROOT/'reports/environment.json',env)
    log('ENVIRONMENT '+json.dumps(env,ensure_ascii=False))
    xtr,xte,ftr,fte=L.dataset('disc')
    dataset=dict(n_train=len(xtr),n_test=len(xte),shape=list(xtr.shape[1:]),data_seed=7,
                 sha256=hashlib.sha256(b''.join(t.cpu().numpy().tobytes() for t in [xtr,xte,ftr,fte])).hexdigest())
    baseline=L.psnr_images(xtr.mean(0,keepdim=True).expand_as(xte),xte)
    log(f'BASELINE mean training image, test PSNR={baseline:.6f}')
    records=[];models={}
    for seed in L.SEEDS:
        for mode,beta in [('A',1.0),('B',8.0)]:
            rec,model=train_record(mode,beta,seed)
            records.append(rec)
            V._MODELS[('disc',8,beta,30,seed)]=model
            if seed==101:models[mode]=model
    # This uses the original summary function over the already measured models.
    original_summary=V.variant_summary(1)
    summary=summarize(records,pre)
    for row,original in zip(summary,original_summary['rows']):
        assert np.allclose([row[k] for k in ['A','s','B','delta','ratio']],original[1:6],rtol=0,atol=1e-9)
        log('SUMMARY '+json.dumps(row,ensure_ascii=False))
    ae,models['AE']=train_record('AE',0.0,101)
    log('AE CHECK seed101: '+str(ae['metrics']))
    no_warmup=[]
    for seed in L.SEEDS:
        rec,_=train_record('NO_WARMUP',1.0,seed,1e-9)
        no_warmup.append(rec)
    log('WARMUP CHECK no_warmup recon='+str([round(r['metrics']['recon'],4) for r in no_warmup]))
    log('WARMUP CHECK main A recon='+str([round(r['metrics']['recon'],4) for r in records if r['mode']=='A']))
    comparisons(models)
    result=dict(variant=1,preregistration=pre,environment=env,dataset=dataset,baseline_psnr=baseline,
                measurements=records,summary=summary,ae=ae,no_warmup=no_warmup,completed_at=now())
    save_json(ART/'results.json',result)
    for name,rows in [('metrics_by_seed',[dict(mode=r['mode'],seed=r['seed'],beta=r['beta'],seconds=r['seconds'],**r['metrics'],active_axes=r['diagnostics']['active_axes']) for r in records]),('summary',summary)]:
        with (ART/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    diagrows=[]
    for r in records+[ae]+no_warmup:
        for j in range(8):diagrows.append(dict(mode=r['mode'],seed=r['seed'],axis=j+1,
            mu_std=r['diagnostics']['mu_std'][j],kl=r['diagnostics']['kl_axis'][j],
            active=r['diagnostics']['kl_axis'][j]>0.05 if r['beta']>0 else 'not_applicable'))
    with (ART/'axis_diagnostics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(diagrows[0]));w.writeheader();w.writerows(diagrows)
    save_json(ART/'passport.json',dict(author='Скрыпник Михаил Дмитриевич',group='МИК11',
        course='Искусственный интеллект в креативных технологиях',laboratory=8,variant=1,
        preregistration=pre,environment=env,dataset=dataset,baseline_psnr=baseline,
        training='ConvVAE 8; Adam lr=0.002; batch=128; 30 epochs = 960 steps; warmup=10',
        metrics='1024 reconstruction scenes; 200 pairs x 3 points; 256 nearest-test sample PSNR; linear factor R2',
        provenance='Synthetic data; source teaching PDF in assignment; libraries extracted/copied locally',
        license='No separate code license stated in the PDF; prepared for educational submission',
        individual_contribution='Experiment setup, execution, analysis and report automated with AI assistance; oral defense not performed',
        execution_command='python src/build_notebook.py',completed_at=now()))
    log('COMPLETE: 10 main models + 1 AE + 5 no-warmup; measured, checkpointed, figures saved')
    console_image()
    return result


if __name__=='__main__':run_all()
