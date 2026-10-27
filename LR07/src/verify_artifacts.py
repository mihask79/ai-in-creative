"""Validate protocol, recorded values, notebook outputs, checkpoints, and comparison pixels."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import numpy as np
import torch
import nbformat
from PIL import Image
import lab07_lib as L
from lab07_experiment import summarize

ROOT=Path(__file__).resolve().parents[1]


def verify():
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    r=json.loads((ROOT/'artifacts/results.json').read_text(encoding='utf-8'))
    pre=r['preregistration']
    assert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]]==['d']
    assert pre['A']['d']==8 and pre['B']['d']==2
    assert len(r['measurements'])==10
    assert {(x['mode'],x['seed']) for x in r['measurements']}=={(m,s) for m in ['A','B'] for s in range(101,106)}
    assert r['summary']==summarize(r['measurements'],pre)
    Xtr,Xte,_,_=L.dataset('disc')
    assert hashlib.sha256(Xtr.cpu().numpy().tobytes()+Xte.cpu().numpy().tobytes()).hexdigest()==r['dataset']['sha256']
    assert abs(L.psnr_images(Xtr.mean(0,keepdim=True).expand_as(Xte),Xte)-r['baseline_psnr'])<1e-6
    tiles=[Xte[:8].cpu().numpy().transpose(0,2,3,1)]
    for row in r['measurements']:
        assert datetime.fromisoformat(pre['recorded_at'])<datetime.fromisoformat(row['started_at'])
        assert datetime.fromisoformat(row['started_at'])<=datetime.fromisoformat(row['completed_at'])
        model=L.build('conv',row['d'])
        with np.load(ROOT/row['checkpoint'],allow_pickle=False) as data:
            model.load_state_dict({k:torch.from_numpy(data[k]).to(L.DEVICE) for k in data.files})
        pred=L.reconstruct(model,Xte)
        psnr=L.psnr_images(pred,Xte)
        gap=L.psnr_images(L.reconstruct(model,Xtr[:1024]),Xtr[:1024])-psnr
        assert abs(psnr-row['psnr'])<1e-6 and abs(gap-row['gap'])<1e-6
        assert L.n_params(model)/1000==row['params'] and row['seconds']>0
        if row['seed']==101:tiles.append(pred[:8].cpu().numpy().transpose(0,2,3,1))
        print('PASS:',row['mode'],row['seed'],'PSNR, gap, parameters, timestamps, checkpoint')
    grid=np.concatenate([np.concatenate(list(t),axis=1) for t in tiles],axis=0)
    expected=Image.fromarray((np.clip(grid,0,1)*255).round().astype('uint8')).resize((1024,384),Image.Resampling.NEAREST)
    assert np.array_equal(np.array(expected),np.array(Image.open(ROOT/'artifacts/comparison.png')))
    print('PASS: comparison.png exactly matches originals and saved A/B models for seed 101')
    assert [d['d'] for d in r['diagnostics']]==[1,2,3,4,8]
    for d in r['diagnostics']:
        assert d['seeds']==[101,102,103] and len(d['values'])==3
        assert float(np.mean(d['values']))==d['mean']
        assert float(np.std(d['values'],ddof=1))==d['s']
    nb=nbformat.read(ROOT/'LR07.ipynb',as_version=4)
    code=[c for c in nb.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in code)
    assert not any(o.output_type=='error' for c in code for o in c.outputs)
    assert any('result=run_all()' in c.source and any('Все 19' in o.get('text','') for o in c.outputs) for c in code)
    assert any(o.output_type=='display_data' and 'image/png' in o.get('data',{}) for c in code for o in c.outputs)
    assert (ROOT/'lab07_lib.py').read_bytes()==(ROOT/'src/lab07_lib.py').read_bytes()
    print('PASS: full training notebook executed; outputs, image and diagnostic summaries are present')
    print('RESULT: PASS')


if __name__=='__main__':verify()
