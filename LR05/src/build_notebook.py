"""Create and execute the deliverable notebook with real cell outputs."""
from pathlib import Path
import os
import sys
import threading
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager

root = Path(__file__).resolve().parents[1]
os.environ["JUPYTER_RUNTIME_DIR"] = str(root / ".cache" / "jupyter")
os.environ["IPYTHONDIR"] = str(root / ".cache" / "ipython")
nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = dict(display_name="Python 3 (ЛР05)", language="python", name="python3")
nb.cells = [
    nbf.v4.new_markdown_cell("# Лабораторная работа 5\n## Запуск открытой модели text-to-image\n"
        "**Вариант 1. Скрыпник Михаил Дмитриевич, МИК11.**\n\n"
        "Бриф: афиша фестиваля робототехники. Условие: повтор в том же сеансе. Seed 1001. "
        "Фактическая среда: локальный Python / Windows / CPU float32.\n\n"
        "Гипотеза: свежий CPU Generator с одним seed даст побитово одинаковые изображения. "
        "Допуск задан до запуска: одинаковые пиксели - identical; PSNR >= 40 дБ - close; иначе different. "
        "Отдельно проверяется ошибка общего Generator и исправление."),
    nbf.v4.new_code_cell("from pathlib import Path\nimport sys\nROOT = Path.cwd()\n"
        "if not (ROOT / 'src').exists():\n    raise RuntimeError('Откройте блокнот из папки LR05')\n"
        "sys.path.insert(0, str(ROOT / 'src'))\n"
        "from lab05_experiment import main\nresults = main()"),
    nbf.v4.new_markdown_cell("## Полученные изображения\nA и B - независимые повторы со свежими генераторами. "
        "error_B - второй вызов с общим генератором; fixed - повтор после исправления."),
    nbf.v4.new_code_cell("from IPython.display import display\nfrom PIL import Image\n"
        "for name in ['run_A', 'run_B', 'error_A', 'error_B', 'fixed']:\n"
        "    print(name, results['manifests'][name]['sha256'])\n"
        "    display(Image.open(ROOT / 'artifacts' / name / 'result.png'))"),
    nbf.v4.new_markdown_cell("## Независимая проверка файлов и метрик"),
    nbf.v4.new_code_cell("import json, hashlib\nimport lab05_lib as L\n"
        "for name in ['run_A', 'run_B', 'error_A', 'error_B', 'fixed']:\n"
        "    folder = ROOT / 'artifacts' / name\n"
        "    m = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))\n"
        "    assert hashlib.sha256((folder / 'result.png').read_bytes()).hexdigest() == m['sha256']\n"
        "    with Image.open(folder / 'result.png') as im:\n"
        "        assert im.size == (512, 512) and im.mode == 'RGB'\n"
        "for key, names in {'repeat':('run_A','run_B'), 'shared_generator':('error_A','error_B'),\n"
        "                   'repaired_vs_reference':('run_A','fixed')}.items():\n"
        "    a, b = [Image.open(ROOT / 'artifacts' / n / 'result.png') for n in names]\n"
        "    assert L.compare(a,b) == results[key]\n"
        "    print(key, json.dumps(results[key], ensure_ascii=False))\n"
        "print('PASS: SHA-256, размеры и метрики пересчитаны по сохранённым PNG')"),
    nbf.v4.new_markdown_cell("## Интерпретация\n"
        "Вывод по измерениям приведён в отчёте и artifacts/results.json. Общий Generator хранит состояние: "
        "после первого вызова оно сдвигается. Исправление - новый Generator().manual_seed(1001) для каждого запуска. "
        "Проверка ограничена одним сеансом и CPU float32; перенос на другие устройства и новый сеанс не проверены.\n\n"
        "Источники: [модель](https://huggingface.co/stabilityai/sd-turbo/tree/b261bac6fd2cf515557d5d0707481eafa0485ec2), "
        "[лицензия](https://huggingface.co/stabilityai/sd-turbo/blob/b261bac6fd2cf515557d5d0707481eafa0485ec2/LICENSE.md), "
        "[воспроизводимость](https://huggingface.co/docs/diffusers/using-diffusers/reusing_seeds). "
        "Использование учебное некоммерческое. Powered by Stability AI.")]
target = root / "LR05.ipynb"
nbf.write(nb, target)
km = KernelManager(kernel_name="python3")
km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
client = NotebookClient(nb, km=km, timeout=3600, resources={"metadata":{"path":str(root)}})
stopped = threading.Event()
def checkpoint():
    while not stopped.wait(10):
        try:
            nbf.write(nb, target)
        except Exception:
            pass  # Final synchronous write below is authoritative.
thread = threading.Thread(target=checkpoint, daemon=True)
thread.start()
try:
    client.execute()
finally:
    stopped.set()
    thread.join()
    nbf.write(nb, target)
print("Executed notebook saved:", target, flush=True)
