"""Create and execute the notebook, including the actual full training experiment."""
from pathlib import Path
import os
import sys
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT=Path(__file__).resolve().parents[1]
os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'.cache/jupyter')
os.environ['IPYTHONDIR']=str(ROOT/'.cache/ipython')
nb=nbf.v4.new_notebook()
nb.metadata.kernelspec=dict(name='python3',display_name='Python 3 (ЛР07)',language='python')
nb.cells=[
nbf.v4.new_markdown_cell('# Лабораторная работа №7. Построение автокодировщика\n'
    '**Вариант 1. Скрыпник Михаил Дмитриевич, МИК11.**\n\n'
    'Набор disc; единственный фактор: d = 8 → 2. Seed 101–105. '
    'Локальный Windows, CPU float32, 4 потока. Все обучения ниже действительно выполняются; '
    'числа из демонстрации методички не подставляются. Для повторного запуска откройте блокнот из LR07 с установленными зависимостями.'),
nbf.v4.new_code_cell('%%writefile lab07_lib.py\n'+(ROOT/'src/lab07_lib.py').read_text(encoding='utf-8')),
nbf.v4.new_code_cell("from pathlib import Path\nimport sys,json,hashlib\nimport numpy as np,torch\nROOT=Path.cwd()\nassert (ROOT/'src/lab07_experiment.py').exists(), 'Откройте блокнот из LR07'\nsys.path.insert(0,str(ROOT/'src'))\nimport lab07_lib as L\nfrom lab07_experiment import preregister,run_all,summarize\ntorch.set_num_threads(4)\ntorch.use_deterministic_algorithms(True)\npre=preregister()\nprint(json.dumps(pre,ensure_ascii=False,indent=2))\nassert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]]==['d']"),
nbf.v4.new_markdown_cell('## Основной эксперимент и диагностика\n4096 обучающих и 1024 тестовых сцены, seed данных 7. '
    'Adam, lr=0.002, batch=128, 20 эпох = 640 обновлений. '
    'Один прогрев, затем A/B для seed 101–105. Диагностика d=1,2,3,4,8 по seed 101–103; '
    'результаты d=2 и d=8 используются из основной серии.'),
nbf.v4.new_code_cell("# Это ячейка фактического обучения, а не загрузка заранее заданных чисел.\nresult=run_all()\nprint('Таблица результатов:')\nfor r in result['summary']:\n    print(json.dumps(r,ensure_ascii=False))"),
nbf.v4.new_markdown_cell('## Независимая проверка сохранённых весов\nПовторная реконструкция всех 1024 тестовых сцен и 1024 обучающих сцен для каждой из 10 моделей. PSNR усредняется по изображениям.'),
nbf.v4.new_code_cell("from datetime import datetime\nXtr,Xte,_,_=L.dataset('disc')\nassert hashlib.sha256(Xtr.cpu().numpy().tobytes()+Xte.cpu().numpy().tobytes()).hexdigest()==result['dataset']['sha256']\nfor r in result['measurements']:\n    assert datetime.fromisoformat(pre['recorded_at'])<datetime.fromisoformat(r['started_at'])\n    model=L.build('conv',r['d'])\n    with np.load(ROOT/r['checkpoint'],allow_pickle=False) as data:\n        model.load_state_dict({k:torch.from_numpy(data[k]).to(L.DEVICE) for k in data.files})\n    psnr=L.psnr_images(L.reconstruct(model,Xte),Xte)\n    gap=L.psnr_images(L.reconstruct(model,Xtr[:1024]),Xtr[:1024])-psnr\n    assert abs(psnr-r['psnr'])<1e-6 and abs(gap-r['gap'])<1e-6\n    assert L.n_params(model)/1000==r['params']\n    print(r['mode'],r['seed'],'PSNR',round(psnr,6),'gap',round(gap,6),'PASS')\nassert summarize(result['measurements'],pre)==result['summary']\nbaseline=L.psnr_images(Xtr.mean(0,keepdim=True).expand_as(Xte),Xte)\nassert abs(baseline-result['baseline_psnr'])<1e-6\nprint('PASS: 10 моделей, все метрики и средняя картинка:',baseline)"),
nbf.v4.new_markdown_cell('## Лист сравнения\nСтроки: оригинал, A (d=8), B (d=2). Первые восемь сцен из тестовой выборки; seed 101.'),
nbf.v4.new_code_cell("from IPython.display import display\nfrom PIL import Image\ndisplay(Image.open(ROOT/'artifacts/comparison_labeled.png'))"),
nbf.v4.new_markdown_cell('## Проверка узкого места и практических допусков\nКритерий |Δ|>2s - учебная эвристика, где s - выборочное стандартное отклонение A. '
    'Он не является формальным статистическим тестом. Для параметров s=0: отношение не определено, изменение детерминировано.'),
nbf.v4.new_code_cell("for r in result['diagnostics']:\n    print('d =',r['d'],'PSNR mean =',round(r['mean'],6),'s =',round(r['s'],6),'values =',r['values'])\nfor r in result['summary']:\n    print(r['metric'],r['classification'],'2s =',r['criterion_2s'],'за допуском =',r['outside_tolerance'])\nfor r in result['summary']:\n    if r['threshold'] is not None:\n        print('Чувствительность',r['metric'],{k:abs(r['delta'])>k*r['threshold'] for k in [0.5,1,2]})\nfor mode in ['A','B']:\n    p=next(r[mode] for r in result['summary'] if r['metric']=='psnr')\n    print(mode,'выигрыш над средней картинкой, дБ:',p-result['baseline_psnr'])"),
nbf.v4.new_markdown_cell('## Вывод и ограничения\nЧисленный вывод, визуальная оценка и ответы на 10 контрольных вопросов находятся в PDF-отчёте. '
    'Сцена имеет три непрерывных фактора (x, y, радиус); недостаток узкого места проверяется по серии и диагностике. '
    'Обобщение на фотографии не проверено. Время относится к CPU и включает создание модели, оптимизатора и обучение, как в функции L.run; '
    'генерация данных, оценка, сохранение весов и изображений не входят. Методичка сохранена в assignment/.')]
target=ROOT/'LR07.ipynb'
nbf.write(nb,target)
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
client=NotebookClient(nb,km=km,timeout=7200,startup_timeout=60,resources={'metadata':{'path':str(ROOT)}})
print('Notebook execution started',flush=True)
try:
    client.execute()
finally:
    nbf.write(nb,target)
print('Executed:',target,flush=True)
