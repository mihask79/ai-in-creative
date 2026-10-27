"""Independent recomputation from every saved checkpoint and structural checks."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import sys
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import lab07_lib as L
import lab08_lib as V
from lab08_experiment import summarize, diagnostics


def verify():
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    r=json.loads((ROOT/'artifacts/results.json').read_text(encoding='utf-8'))
    lines=[]
    def out(s):print(s,flush=True);lines.append(s)
    assert [k for k in r['preregistration']['A'] if r['preregistration']['A'][k]!=r['preregistration']['B'][k]]==['beta']
    tensors=L.dataset('disc')
    assert hashlib.sha256(b''.join(t.cpu().numpy().tobytes() for t in tensors)).hexdigest()==r['dataset']['sha256']
    assert summarize(r['measurements'],r['preregistration'])==r['summary']
    assert {x['seed'] for x in r['measurements'] if x['mode']=='A'}==set(range(101,106))
    assert {x['seed'] for x in r['measurements'] if x['mode']=='B'}==set(range(101,106))
    for rec in r['measurements']+[r['ae']]+r['no_warmup']:
        assert datetime.fromisoformat(r['preregistration']['recorded_at'])<datetime.fromisoformat(rec['started_at'])
        file=ROOT/rec['checkpoint']
        assert hashlib.sha256(file.read_bytes()).hexdigest()==rec['checkpoint_sha256']
        model=V.ConvVAE(8).to(L.DEVICE)
        with np.load(file,allow_pickle=False) as z:model.load_state_dict({k:torch.from_numpy(z[k]).to(L.DEVICE) for k in z.files})
        measured=V.metrics(model,'disc','lin',1.0,rec['seed'])
        for k,v in measured.items():assert abs(v-rec['metrics'][k])<1e-6,(rec['mode'],rec['seed'],k)
        diag=diagnostics(model,rec['beta'])
        assert diag==rec['diagnostics']
        assert all(np.isfinite(v) for v in measured.values())
        out(f"PASS {rec['mode']} seed={rec['seed']}: 4 metrics and 8-axis diagnostics recomputed from checkpoint")
    baseline=L.psnr_images(tensors[0].mean(0,keepdim=True).expand_as(tensors[1]),tensors[1])
    assert abs(baseline-r['baseline_psnr'])<1e-6
    out('PASS: data hash, preregistration timing, one changed factor, five seeds, summary, baseline, 16 checkpoints')
    (ROOT/'reports/verification_log.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return True


if __name__=='__main__':verify()
