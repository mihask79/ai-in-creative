# Лабораторная работа № 1: воспроизводимость AI-эксперимента

Содержимое подготовлено для варианта 1: облачное небо для фона афиши (cell 32, 4 октавы, persistence 0,50), фактор — размер изображения ×1,5 (96 → 144).

Запуск из этой папки в Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip freeze
.venv\Scripts\python.exe src\seed_demo.py
.venv\Scripts\python.exe src\seed_demo.py --seed 101
.venv\Scripts\python.exe src\lab01_experiment.py --variant 1 --out artifacts
```

Генератор и эксперимент используют только стандартную библиотеку. `artifacts/results.json` содержит конфигурацию, контрольные суммы массивов и PNG, воспроизводимость, метрики и сведения о среде. Изображения для сравнения — `artifacts/baseline_seed101.png` и `artifacts/factor_seed101.png`. Паспорт и отчёт собраны в DOCX; журнал шагов — `reports/lab_journal.txt`.

Часть Б по Engee требует указания преподавателя и фактической работы в пользовательской среде; она отмечена как невыполненная, чтобы не подменять наблюдения вымышленными данными.

## Отчёт и архив

Отчёт: [ЛР01_Отчет_и_паспорт.docx](reports/ЛР01_Отчет_и_паспорт.docx). Архив: [lr01_variant01_artifacts.zip](artifacts/lr01_variant01_artifacts.zip). Сборка отчёта: `python build_report.py` (требует python-docx).

Базовый хеш совпал с демонстрацией методички. Факторные метрики отличаются; сохранены фактические расчёты, а не числа из примера. Ни одна метрика не превысила порог 2.

## Задание

Исходная методичка сохранена в `assignment/`. Работа выполнена по варианту 1.
