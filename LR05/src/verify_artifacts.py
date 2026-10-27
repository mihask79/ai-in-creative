"""Independent saved-file validation; requires no torch or model weights."""
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image

root=Path(__file__).resolve().parents[1]
art=root/"artifacts"
r=json.loads((art/"results.json").read_text(encoding="utf-8"))
pre=json.loads((root/"configs"/"preregistration.json").read_text(encoding="utf-8"))
names=["run_A","run_B","error_A","error_B","fixed"]
arrays={}
hashes={}
for name in names:
    folder=art/name
    m=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    hashes[name]=hashlib.sha256((folder/"result.png").read_bytes()).hexdigest()
    assert hashes[name]==m["sha256"]==r["manifests"][name]["sha256"]
    assert datetime.fromisoformat(pre["recorded_at"]) < datetime.fromisoformat(m["created_at"])
    assert m["seed"]==1001 and m["revision"]==pre["revision"] and m["size"]==512
    with Image.open(folder/"result.png") as im:
        assert im.size==(512,512) and im.mode=="RGB"
        arrays[name]=np.asarray(im,dtype=np.float64)
for key,(a,b) in {
    "repeat":("run_A","run_B"), "shared_generator":("error_A","error_B"),
    "first_shared_vs_reference":("run_A","error_A"),
    "repaired_vs_reference":("run_A","fixed")}.items():
    delta=arrays[a]-arrays[b]
    mse=float(np.mean(delta**2))
    c=r[key]
    assert c["sha_a"]==hashes[a] and c["sha_b"]==hashes[b]
    assert c["sha_equal"]==(hashes[a]==hashes[b])
    assert c["pixel_equal"]==bool(np.array_equal(arrays[a],arrays[b]))
    assert c["mse"]==mse and c["max_diff"]==int(np.max(np.abs(delta)))
    if mse==0:
        assert c["psnr_db"]=="Infinity" and c["verdict"]=="identical"
    else:
        psnr=10*math.log10(255.0**2/mse)
        assert math.isclose(psnr,c["psnr_db"],abs_tol=1e-10)
        assert c["verdict"]==("close" if psnr>=40 else "different")
    print(key,": PASS;",c["verdict"],"PSNR",c["psnr_db"])
ea=r["manifests"]["error_A"]; eb=r["manifests"]["error_B"]
assert ea["generator_state_before_sha256"]!=ea["generator_state_after_sha256"]
assert ea["generator_state_after_sha256"]==eb["generator_state_before_sha256"]
nb=json.loads((root/"LR05.ipynb").read_text(encoding="utf-8"))
cells=[c for c in nb["cells"] if c["cell_type"]=="code"]
assert all(c["execution_count"] is not None for c in cells)
assert not any(o["output_type"]=="error" for c in cells for o in c.get("outputs",[]))
assert sum("image/png" in o.get("data",{}) for c in cells for o in c.get("outputs",[]))==5
print("PASS: все файлы, гипотеза до запуска, метрики, состояния Generator и выводы блокнота проверены")
