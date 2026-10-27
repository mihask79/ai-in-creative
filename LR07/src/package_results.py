"""Build portable submission archive with checksums, excluding runtime caches."""
from pathlib import Path
import hashlib
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/LR07_variant_1.zip'
files=sorted(p for p in ROOT.rglob('*') if p.is_file()
             and not any(x in p.relative_to(ROOT).parts for x in ['.cache','.venv','__pycache__'])
             and p!=OUT and p.name!='SHA256SUMS.txt' and not p.name.endswith('_checkpoint.json'))
checks=ROOT/'artifacts/SHA256SUMS.txt'
checks.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files),encoding='utf-8')
with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files+[checks]:z.write(p,Path('LR07')/p.relative_to(ROOT))
with zipfile.ZipFile(OUT) as z:assert z.testzip() is None
print('Archive:',OUT,'files:',len(files)+1,'bytes:',OUT.stat().st_size)
