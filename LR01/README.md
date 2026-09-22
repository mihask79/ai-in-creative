# ЛР №1. Запуск открытой модели text-to-image

**Вариант 3** — концепт постера научной выставки.  
Изменяемый фактор: ограничение `no text` и чистая композиция.

## 📓 [LR01.ipynb](LR01.ipynb) — работа целиком

Ноутбук содержит код, фактические выходы его выполнения и отчёт. GitHub
рендерит его прямо в браузере: видны команда, результат проверки и изображение.

| | |
| --- | --- |
| Модель | `stabilityai/sd-turbo`, ревизия `b261bac6fd2cf515557d5d0707481eafa0485ec2` |
| Параметры | seed `30032026`, steps `1`, guidance `0.0`, 512 × 512 |
| Среда сохранённого прогона | Windows, CPU, `float32`, 1 поток |
| Результат | два запуска, SHA-256 совпали побитово; псевдотекста нет |

## Как повторить

**Вариант А — Google Colab:** открыть
[colab.research.google.com](https://colab.research.google.com) → File → Open
notebook → GitHub → вставить URL репозитория → выбрать `LR01/LR01.ipynb` →
Runtime → Run all.

**Вариант Б — локально (Windows PowerShell):**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch jupyter
jupyter notebook LR01.ipynb
```

Первый запуск скачивает закреплённый снимок модели. CPU допустим, но медленнее GPU.

## Что где лежит

| Путь | Содержимое |
| --- | --- |
| [LR01.ipynb](LR01.ipynb) | код, сохранённые выходы и отчёт |
| [artifacts/](artifacts) | `run_001`, `run_002`: `result.png` + `manifest.json` |
| [reports/](reports) | `environment.txt`, `sha256_comparison.json` |
| [configs/](configs) | `run_config.json` — параметры одним файлом |
| [assignment/](assignment) | методические указания и лицензия модели |

Каталоги `configs/`, `artifacts/` и `reports/` создаются самим ноутбуком.
Кэш весов и виртуальное окружение в репозиторий не попадают.
