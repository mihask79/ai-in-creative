"""Build a nine-section model card from the LR1 passport JSON."""
import argparse
from pathlib import Path
from lab02_common import read_json

SECTIONS=['Model Details','Intended Use','Factors','Metrics','Evaluation Data','Training Data','Quantitative Analyses','Ethical Considerations','Caveats and Recommendations']
def main():
    p=argparse.ArgumentParser(); p.add_argument('--passport',required=True); p.add_argument('--out',required=True); a=p.parse_args()
    data=read_json(a.passport); out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    text=['# Карточка учебной модели · вариант 7','', 'Объект: процедурный генератор бумажной текстуры из ЛР 1. Это не обученная нейросетевая модель; веса отсутствуют.','']
    for title in SECTIONS:
        text += [f'## {title}','',str(data.get(title,'Требует дополнения по паспорту ЛР 1.')),'']
    out.write_text('\n'.join(text),encoding='utf-8'); print(out)
if __name__=='__main__': main()
