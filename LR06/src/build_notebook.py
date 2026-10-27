"""Execute an auditable analysis notebook over the real generated artifacts."""
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
nb.metadata.kernelspec=dict(name='python3',display_name='Python 3 (ЛР06)',language='python')
nb.cells=[
nbf.v4.new_markdown_cell('# Лабораторная работа 6. Вариант 1\n'
    '**Скрыпник Михаил Дмитриевич, МИК11.**\n\n'
    'Бриф: афиша фестиваля робототехники. Единственный фактор: 1 → 4 шага. Seed: 101–105.\n\n'
    'Фактическая среда: Windows, CPU float32, 4 потока. Это адаптация задания; Colab T4 и float16 не использовались.\n\n'
    'Генерация выполнена скриптом `src/lab06_experiment.py`; исходный журнал сохранён в `reports/generation_log.txt`. '
    'Этот блокнот выполнен для повторного расчёта и проверки результатов. '
    'Ячейка с RUN_FULL_EXPERIMENT=True позволяет заново выполнить генерацию и оценку; это занимает длительное время и перезаписывает артефакты.'),
nbf.v4.new_code_cell("from pathlib import Path\nimport sys, json, hashlib\nROOT=Path.cwd()\nassert (ROOT/'src/lab06_experiment.py').exists(), 'Откройте блокнот из LR06'\nsys.path.insert(0,str(ROOT/'src'))\nimport lab06_lib as L\npre=json.loads((ROOT/'configs/preregistration.json').read_text(encoding='utf-8'))\nprint(json.dumps(pre,ensure_ascii=False,indent=2))\nassert [k for k in pre['A'] if pre['A'][k]!=pre['B'][k]]==['steps']"),
nbf.v4.new_markdown_cell('## Код выполнения и сохранённый журнал\nГипотеза и допуски записаны до загрузки модели. Прогрев seed 0 не входит в измеряемую серию.'),
nbf.v4.new_code_cell("from lab06_experiment import generate_series, score_series\nRUN_FULL_EXPERIMENT=False\nif RUN_FULL_EXPERIMENT:\n    generate_series()\n    results=score_series()\nelse:\n    results=json.loads((ROOT/'artifacts/results.json').read_text(encoding='utf-8'))\n    print('Повторная генерация отключена; ниже исходный журнал фактического запуска:')\n    log=(ROOT/'reports/generation_log.txt').read_text(encoding='utf-8',errors='replace')\n    print('\\n'.join(line for line in log.splitlines() if any(s in line for s in ['ДО запуска','Модель загружена','Прогрев','seed=','Проверка guidance','завершены'])))"),
nbf.v4.new_markdown_cell('## Независимая проверка PNG и метрик\nСходство CLIP вновь вычисляется по сохранённым изображениям относительно неизменного английского брифа. Энергия границ: Собель с нормировкой 1/8 и отражением на границе; контраст: стандартное отклонение яркости.'),
nbf.v4.new_code_cell("import numpy as np, torch\nfrom PIL import Image\nfrom datetime import datetime\ntorch.set_num_threads(4)\nclip=L.load_clip()\nfor row in results['measurements']:\n    path=ROOT/row['path']\n    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']\n    assert datetime.fromisoformat(pre['recorded_at'])<datetime.fromisoformat(row['started_at'])\n    with Image.open(path) as im:\n        assert im.size==(512,512) and im.mode=='RGB'\n        assert np.isclose(L.edge_energy(im),row['edge'],rtol=0,atol=1e-12)\n        assert np.isclose(L.contrast(im),row['contrast'],rtol=0,atol=1e-12)\n        assert np.isclose(L.clip_sim(clip,im),row['clip'],rtol=0,atol=1e-5)\n    print(row['mode'],row['seed'],'CLIP=',round(row['clip'],4),'edge=',round(row['edge'],6),'contrast=',round(row['contrast'],6),'time=',round(row['seconds'],2))\nprint('PASS: все 10 PNG, SHA-256, CLIP, Собель, контраст и время записи гипотезы проверены')"),
nbf.v4.new_markdown_cell('## Средние, выборочное s, Δ и |Δ|/s\nКритерий 2s является учебной эвристикой разброса по seed, а не тестом с заданным p-уровнем.'),
nbf.v4.new_code_cell("rows=L.summarize(results['measurements'],pre)\nassert rows==results['summary']\nfor r in rows:\n    print(f\"{r['metric']:9s} A={r['A']:.6f} s={r['s']:.6f} B={r['B']:.6f} delta={r['delta']:+.6f} ratio={r['ratio']:.3f} 2s={r['criterion_2s']} допуск={r['classification']}\")\nprint('Критерий 2s и практический допуск расходятся для:',[r['metric'] for r in rows if r['criterion_2s']!=r['outside_tolerance']])"),
nbf.v4.new_markdown_cell('## Сравнительный лист, seed 101\nСлева A, 1 шаг; справа B, 4 шага. Для всех пяти пар изображения сохранены без уменьшения в artifacts.'),
nbf.v4.new_code_cell("from IPython.display import display\ndisplay(Image.open(ROOT/'artifacts/comparison.png'))\nfor seed in L.SEEDS:\n    pair=Image.new('RGB',(512,256))\n    for i,mode in enumerate(['A','B']):\n        with Image.open(ROOT/f'artifacts/{mode}_{seed}/result.png') as im:\n            pair.paste(im.resize((256,256)),(256*i,0))\n    print('seed',seed,'A | B')\n    display(pair)"),
nbf.v4.new_markdown_cell('## Ошибка: ожидание CFG при guidance_scale=1.0\nПроверяем сохранённые изображения: 0 и 1 дают одинаковые PNG; значение 3 используется как диагностика за пределами рекомендованного режима.'),
nbf.v4.new_code_cell("base=ROOT/'artifacts/A_101/result.png'\nfor key, r in results['guidance_check'].items():\n    raw=(ROOT/r['path']).read_bytes()\n    assert hashlib.sha256(raw).hexdigest()==r['sha256']\n    assert (raw==base.read_bytes())==r['same_sha256']\n    print(key,json.dumps(r,ensure_ascii=False))\nassert results['guidance_check']['1.0']['same_sha256']\nassert results['guidance_check']['1.0']['cfg_active'] is False\nassert results['guidance_check']['3.0']['cfg_active'] is True\nprint('PASS: диагностическая проверка guidance')"),
nbf.v4.new_markdown_cell('## Допуск и вывод\nРост энергии границ и контраста классифицируется как рост соответствующего показателя; это не доказательство улучшения изображения. Окупаемость оценивается по правилу, записанному до запуска.'),
nbf.v4.new_code_cell("for metric,factors in [('clip',[0.5,1,2]),('edge',[0.5,1,2]),('contrast',[0.5,1,2]),('seconds',[0.5,1,2])]:\n    r=next(r for r in rows if r['metric']==metric)\n    print(metric, {f:abs(r['delta'])>r['threshold']*f for f in factors})\nprint('Визуальная оценка:')\nprint((ROOT/'artifacts/visual_review.json').read_text(encoding='utf-8'))\nprint('Полный вывод и ответы для защиты находятся в PDF-отчёте.')"),
nbf.v4.new_markdown_cell('## Источники и лицензии\n'
    '[SD-Turbo, закреплённая ревизия](https://huggingface.co/stabilityai/sd-turbo/tree/b261bac6fd2cf515557d5d0707481eafa0485ec2), '
    '[CLIP, закреплённая ревизия](https://huggingface.co/openai/clip-vit-base-patch32/tree/3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268). '
    'Методичка, карточки и лицензии сохранены в assignment. Использование учебное некоммерческое. Powered by Stability AI.')]
target=ROOT/'LR06.ipynb'
nbf.write(nb,target)
print('Notebook created; starting local kernel...',flush=True)
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
client=NotebookClient(nb,km=km,timeout=7200,startup_timeout=60,resources={'metadata':{'path':str(ROOT)}})
try: client.execute()
finally: nbf.write(nb,target)
print('Executed notebook:',target)
