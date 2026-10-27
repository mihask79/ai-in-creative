"""Independent validation of all deliverable measurements, images, and notebook."""
from pathlib import Path
import csv
from datetime import datetime
import hashlib
import json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def main():
    r=json.loads((ROOT/'artifacts/results.json').read_text(encoding='utf-8'))
    pre=json.loads((ROOT/'configs/preregistration.json').read_text(encoding='utf-8'))
    assert r['preregistration']==pre
    assert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]]==['steps']
    assert {(m['mode'],m['seed']) for m in r['measurements']}=={(m,s) for m in ['A','B'] for s in range(101,106)}
    images={}
    for m in r['measurements']:
        path=ROOT/m['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==m['sha256']
        assert datetime.fromisoformat(pre['recorded_at'])<datetime.fromisoformat(m['started_at'])
        with Image.open(path) as im:
            assert im.size==(512,512) and im.mode=='RGB'
            images[m['mode'],m['seed']]=im.copy()
            rgb=np.asarray(im,dtype=np.float64)/255
        y=.299*rgb[...,0]+.587*rgb[...,1]+.114*rgb[...,2]
        assert np.isclose(y.std(),m['contrast'],atol=1e-12,rtol=0)
        windows=np.lib.stride_tricks.sliding_window_view(np.pad(y,1,mode='symmetric'),(3,3))
        kernel=np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
        gx=np.einsum('ijkl,kl->ij',windows,kernel)
        gy=np.einsum('ijkl,kl->ij',windows,kernel.T)
        assert np.isclose(np.hypot(gx,gy).mean()/8,m['edge'],atol=1e-12,rtol=0)
        assert 0<m['clip']<100 and m['seconds']>0 and not m['cfg_active']
        manifest=json.loads(path.with_name('manifest.json').read_text(encoding='utf-8'))
        assert manifest['sha256']==m['sha256'] and manifest['steps']==(1 if m['mode']=='A' else 4)
    for row in r['summary']:
        k=row['metric']
        a=np.array([m[k] for m in r['measurements'] if m['mode']=='A'])
        b=np.array([m[k] for m in r['measurements'] if m['mode']=='B'])
        d=b.mean()-a.mean(); sd=a.std(ddof=1)
        for key,value in [('A',a.mean()),('B',b.mean()),('s',sd),('delta',d),('ratio',abs(d)/sd)]:
            assert np.isclose(row[key],value,atol=1e-12,rtol=0)
        assert row['criterion_2s']==bool(abs(d)>2*sd)
        tolerance=pre['tolerance'][k]
        threshold=tolerance['value']*(abs(a.mean()) if tolerance['kind']=='relative' else 1)
        assert np.isclose(row['threshold'],threshold)
        assert row['outside_tolerance']==bool(abs(d)>threshold)
    csv_rows=list(csv.DictReader((ROOT/'artifacts/metrics_by_seed.csv').open(encoding='utf-8-sig')))
    assert len(csv_rows)==10
    for cr,jr in zip(csv_rows,r['measurements']):
        assert cr['sha256']==jr['sha256']
        for k in ['clip','edge','contrast','seconds']: assert float(cr[k])==jr[k]
    with Image.open(ROOT/'artifacts/comparison.png') as sheet:
        assert sheet.size==(768,384)
        for i,mode in enumerate(['A','B']):
            assert np.array_equal(np.asarray(sheet.crop((384*i,0,384*(i+1),384))),
                np.asarray(images[mode,101].resize((384,384))))
    base=(ROOT/'artifacts/A_101/result.png').read_bytes()
    for key,e in r['guidance_check'].items():
        raw=(ROOT/e['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==e['sha256']
        assert (raw==base)==e['same_sha256']
        with Image.open(ROOT/e['path']) as im:
            mse=np.mean((np.asarray(im,dtype=np.float64)-np.asarray(images['A',101],dtype=np.float64))**2)
        assert mse==e['mse']
    assert r['guidance_check']['1.0']['same_sha256'] and not r['guidance_check']['1.0']['cfg_active']
    assert r['guidance_check']['3.0']['cfg_active'] and not r['guidance_check']['3.0']['same_sha256']
    nb=json.loads((ROOT/'LR06.ipynb').read_text(encoding='utf-8'))
    cells=[c for c in nb['cells'] if c['cell_type']=='code']
    assert cells and all(c['execution_count'] is not None for c in cells)
    assert all(o['output_type']!='error' for c in cells for o in c['outputs'])
    assert any(o['output_type']=='display_data' and 'image/png' in o.get('data',{}) for c in cells for o in c['outputs'])
    print('PASS: 10 images, manifests, preregistration, independent summary, CSV, comparison, guidance and executed notebook')

if __name__=='__main__': main()
