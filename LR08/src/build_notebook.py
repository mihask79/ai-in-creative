"""Build and really execute the laboratory notebook, including training."""
from pathlib import Path
import os
import sys
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT=Path(__file__).resolve().parents[1]
for folder in ['.cache/jupyter','.cache/ipython']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'.cache/jupyter')
os.environ['IPYTHONDIR']=str(ROOT/'.cache/ipython')
nb=nbf.v4.new_notebook()
nb.metadata.kernelspec=dict(name='python3',display_name='Python 3 (ЛР08)',language='python')
nb.cells=[
nbf.v4.new_markdown_cell('# Лабораторная работа №8. Генерация и интерполяция в латентном пространстве\n'
 '**Вариант 1. Скрыпник Михаил Дмитриевич, МИК11.**\n\n'
 'Набор «диск»; единственный фактор основной серии β: 1 → 8. d=8, 30 эпох, seed 101–105. '
 'Windows CPU float32, 4 потока. Engee не использовалась. Ниже выполняются реальные обучения; результаты демонстрации не подставляются.'),
nbf.v4.new_code_cell("from pathlib import Path\nimport sys,json\nROOT=Path.cwd()\nassert (ROOT/'src/lab08_experiment.py').exists(), 'Откройте блокнот из папки LR08'\nsys.path.insert(0,str(ROOT/'src'))\nfrom lab08_experiment import preregister,run_all\npre=preregister()\nprint(json.dumps(pre,ensure_ascii=False,indent=2))\nassert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]]==['beta']"),
nbf.v4.new_markdown_cell('## Методика\n4096 обучающих и 1024 тестовых сцен, seed данных 7. '
 'Реконструкция оценивается по D(μ), интерполяция по 200 фиксированным парам при t=0.25,0.5,0.75. '
 '256 сэмплов из N(0,I), seed=1000+seed обучения. R² — линейная регрессия факторов по μ с проверкой на тесте. '
 'Допуски записаны выше до обучения: 1 дБ и 0.05 R². Критерий 2s — учебная эвристика, а не формальный тест.'),
nbf.v4.new_code_cell("# Полное обучение основной серии и диагностики. Может занять 10–20 минут.\nresult=run_all()\nfor row in result['summary']:print(json.dumps(row,ensure_ascii=False))"),
nbf.v4.new_markdown_cell('## Проверка сохранённых весов\nПовторный расчёт четырёх метрик и диагностики для всех 16 сохранённых моделей. Выполняется отдельным модулем.'),
nbf.v4.new_code_cell("from verify_artifacts import verify\nverify()"),
nbf.v4.new_markdown_cell('## Визуальные результаты\nСэмплы AE/A/B, истинный путь в пространстве факторов, интерполяция A/B. Пара 0 → 2, seed 101, восемь точек пути. Выбор пары фиксирован методичкой.'),
nbf.v4.new_code_cell("from PIL import Image\nfrom IPython.display import display\ndisplay(Image.open(ROOT/'artifacts/comparison_labeled.png'))\nprint('Реконструкции: оригинал / A / B')\ndisplay(Image.open(ROOT/'artifacts/reconstructions.png'))"),
nbf.v4.new_markdown_cell('## Диагностика и чувствительность к допускам\nОсь активна при среднем KL_j > 0.05 нат. Для AE logvar не обучается: число активных осей по KL не интерпретируется.'),
nbf.v4.new_code_cell("for mode in ['A','B']:\n    for r in result['measurements']:\n        if r['mode']==mode:print(mode,r['seed'],'active=',r['diagnostics']['active_axes'],'mu_std=',r['diagnostics']['mu_std'])\nfor r in result['summary']:\n    print(r['metric'],r['classification'],'2s=',r['criterion_2s'],'outside=',{k:abs(r['delta'])>k*r['tolerance'] for k in [0.5,1,2]})\nprint('AE seed101:',result['ae']['metrics'])\nprint('Без разогрева:',[(r['seed'],r['metrics']['recon'],r['diagnostics']['active_axes']) for r in result['no_warmup']])"),
nbf.v4.new_markdown_cell('## Вывод и ограничения\nЧисленный и визуальный анализ, сравнение с демонстрацией и ответы на 10 вопросов приведены в отчёте. '
 'Сэмплы оцениваются по близости к тесту, разнообразие этим не доказано. Активность осей зависит от порога; '
 'R² не доказывает независимость осей. Обобщение на реальные изображения, другие архитектуры и Engee не проверено. '
 'Полный паспорт — artifacts/passport.json; фактический журнал — reports/training_log.txt.')]
target=ROOT/'LR08.ipynb'
nbf.write(nb,target)
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
client=NotebookClient(nb,km=km,timeout=7200,startup_timeout=60,resources={'metadata':{'path':str(ROOT)}})
print('Notebook execution started',flush=True)
try:client.execute()
finally:nbf.write(nb,target)
print('Executed:',target,flush=True)
