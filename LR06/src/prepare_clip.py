"""Download pinned CLIP files and verify weight LFS SHA-256; no credentials."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REV = '3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268'
MODEL = 'openai/clip-vit-base-patch32'
OUT = ROOT/'.cache/clip'
OUT.mkdir(parents=True, exist_ok=True)

def read(url, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=90) as r:
        return r.read(), r.status, dict(r.headers)

data, _, _ = read(f'https://huggingface.co/api/models/{MODEL}/revision/{REV}?blobs=true')
metadata = json.loads(data)
assert metadata['sha']==REV
(ROOT/'configs/clip_repository_metadata.json').write_bytes(data)
names = ['config.json','preprocessor_config.json','tokenizer_config.json','special_tokens_map.json',
         'vocab.json','merges.txt','pytorch_model.bin','README.md']
records = []
for name in names:
    item = next(i for i in metadata['siblings'] if i['rfilename']==name)
    target = OUT/name
    url = f'https://huggingface.co/{MODEL}/resolve/{REV}/{name}'
    lfs = item.get('lfs')
    if lfs:
        size, expected = lfs['size'], lfs['sha256']
        if not (target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==expected):
            parts = ROOT/'.cache/clip_parts'
            parts.mkdir(exist_ok=True)
            chunk = 8*1024*1024
            def get(i):
                start, end = i*chunk, min(size,(i+1)*chunk)-1
                p = parts/f'{i:04d}.part'
                if p.exists() and p.stat().st_size==end-start+1:
                    return p
                for attempt in range(5):
                    try:
                        body, status, headers = read(url+f'?download=true&part={i}&attempt={attempt}',
                            {'Range':f'bytes={start}-{end}'})
                        assert status==206 and len(body)==end-start+1
                        assert headers.get('Content-Range',headers.get('content-range'))==f'bytes {start}-{end}/{size}'
                        p.write_bytes(body)
                        return p
                    except Exception:
                        if attempt==4: raise
                        time.sleep(1)
            indices = list(range((size+chunk-1)//chunk))
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                paths=[]
                for n,p in enumerate(pool.map(get,indices),1):
                    paths.append(p)
                    if n%10==0: print(f'CLIP {n}/{len(indices)} chunks', flush=True)
            temp=target.with_suffix('.partial')
            with temp.open('wb') as f:
                for p in paths: f.write(p.read_bytes())
            assert hashlib.sha256(temp.read_bytes()).hexdigest()==expected
            os.replace(temp,target)
    else:
        body, _, _ = read(url)
        target.write_bytes(body)
    records.append(dict(file=name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    print('Verified',name,target.stat().st_size,flush=True)
license_body,_,_=read('https://raw.githubusercontent.com/openai/CLIP/a1d071733d7111c9c014f024669f959182114e33/LICENSE')
(ROOT/'assignment/CLIP_LICENSE.txt').write_bytes(license_body)
(ROOT/'assignment/clip_model_card.md').write_bytes((OUT/'README.md').read_bytes())
(ROOT/'configs/clip_weight_verification.json').write_text(json.dumps(dict(model=MODEL,revision=REV,files=records),indent=2)+'\n',encoding='utf-8')
print('CLIP download complete',flush=True)
