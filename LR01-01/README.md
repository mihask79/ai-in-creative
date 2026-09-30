# Лабораторная работа № 1: воспроизводимость AI-эксперимента

Содержимое подготовлено для варианта 7: бумажная текстура (cell 4, 3 октавы, persistence 0,60), фактор — размер изображения ×1,5 (96 → 144).

Запуск из этой папки в Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip freeze
.venv\Scripts\python.exe src\seed_demo.py
.venv\Scripts\python.exe src\seed_demo.py --seed 101
.venv\Scripts\python.exe src\lab01_experiment.py --variant 7 --out artifacts
```

Генератор и эксперимент используют только стандартную библиотеку. `artifacts/results.json` содержит конфигурацию, контрольные суммы массивов и PNG, воспроизводимость, метрики и сведения о среде. Изображения для сравнения — `artifacts/baseline_seed101.png` и `artifacts/factor_seed101.png`. Паспорт и отчёт собраны в DOCX; журнал шагов — `reports/lab_journal.txt`.

Часть Б по Engee требует указания преподавателя и фактической работы в пользовательской среде; она отмечена как невыполненная, чтобы не подменять наблюдения вымышленными данными.
