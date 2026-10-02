# Лабораторная работа 2 — вариант 7

Рабочая папка для воспроизводимого учебного аудита лицензий и рисков при подготовке монетизируемых обложек подкастов.

## Структура

- `src/` — генератор синтетического манифеста, аудит, карточка модели и проверка рисков.
- `artifacts/` — манифест, политика, входной реестр рисков и паспорт-пересказ результатов ЛР 1.
- `reports/` — результаты запуска и итоговый DOCX.

## Запуск

Из этой папки, Python 3.10 или новее:

```powershell
python src/lab02_make_variant.py --variant 7 --out artifacts
python src/lab02_audit.py --manifest artifacts/manifest.csv --policy artifacts/policy.json --out reports
python src/lab02_model_card.py --passport artifacts/passport_lr01.json --out reports/model_card.md
python src/lab02_risks.py --csv artifacts/risk_register.csv --out reports/risk_ranking.md
```

Все записи манифеста — синтетические учебные данные на домене example.org. Записи воспроизводят профиль варианта 7 по демонстрационному примеру методички; они не являются реальными лицензированными изображениями.

Скрипты реализуют упрощённую учебную модель и не подтверждают права по первоисточникам, не оценивают юридическую квалификацию результата и не заменяют юриста.
