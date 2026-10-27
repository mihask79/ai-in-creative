"""Export measured tables and execution journal, then package deliverables."""
from pathlib import Path
import csv
import hashlib
import json
import zipfile

root=Path(__file__).resolve().parents[1]
art=root/"artifacts"
r=json.loads((art/"results.json").read_text(encoding="utf-8"))
with (art/"comparison.csv").open("w",encoding="utf-8-sig",newline="") as stream:
    writer=csv.writer(stream,delimiter=";")
    writer.writerow(["comparison","sha_equal","pixel_equal","max_diff","mse","psnr_db","verdict"])
    for key in ["repeat","shared_generator","first_shared_vs_reference","repaired_vs_reference"]:
        c=r[key]
        writer.writerow([key]+[c[x] for x in ["sha_equal","pixel_equal","max_diff","mse","psnr_db","verdict"]])
nb=json.loads((root/"LR05.ipynb").read_text(encoding="utf-8"))
journal=[]
for cell in nb["cells"]:
    if cell["cell_type"]!="code":
        continue
    journal.append(f"CELL {cell['execution_count']}\n"+"".join(cell["source"]))
    for output in cell.get("outputs",[]):
        if "text" in output:
            journal.append("".join(output["text"]))
        elif "text/plain" in output.get("data",{}):
            journal.append("".join(output["data"]["text/plain"]))
(root/"reports"/"execution_log.txt").write_text("\n\n".join(journal),encoding="utf-8")
files=[]
for folder in ["src","assignment","configs","reports","artifacts"]:
    files += [p for p in (root/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts
              and p.suffix!=".zip" and p.name!="SHA256SUMS.txt"]
files += [root/n for n in ["README.md","LR05.ipynb","requirements.txt","requirements-lock.txt"]]
checksums="".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+p.relative_to(root).as_posix()+"\n" for p in sorted(files))
(art/"SHA256SUMS.txt").write_text(checksums,encoding="utf-8")
archive=art/"LR05_variant_1.zip"
with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as out:
    for p in files+[art/"SHA256SUMS.txt"]:
        out.write(p,Path("LR05")/p.relative_to(root))
with zipfile.ZipFile(archive) as check:
    assert check.testzip() is None
    assert not any("/.venv/" in name or "/.cache/" in name for name in check.namelist())
print(archive, archive.stat().st_size, "bytes;", len(files)+1,"files; ZIP verified")
