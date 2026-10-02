"""Create a CSV risk-register template or validate and rank a filled register."""
import argparse
from pathlib import Path
from lab02_common import NIST_GROUPS, write_csv, read_csv

FIELDS=['risk_id','category','likelihood','impact','description','mitigation','owner','trigger']
def main():
    p=argparse.ArgumentParser(); p.add_argument('--template'); p.add_argument('--csv'); p.add_argument('--out',required=True); a=p.parse_args()
    if a.template:
        write_csv(a.template,FIELDS,[]); print(f'Шаблон: {a.template}'); return
    if not a.csv: p.error('Укажите --csv или --template')
    rows=read_csv(a.csv); errors=[]
    for i,r in enumerate(rows,1):
        for f in FIELDS:
            if not r.get(f,'').strip(): errors.append(f'{r.get("risk_id",i)}: не заполнено поле {f}')
        if r.get('category') not in NIST_GROUPS: errors.append(f'{r.get("risk_id",i)}: категория вне перечня NIST AI 600-1')
        for f in ('likelihood','impact'):
            try: v=int(r[f]); assert 1<=v<=5
            except Exception: errors.append(f'{r.get("risk_id",i)}: {f} должен быть целым от 1 до 5')
    groups={r.get('category') for r in rows};
    if len(rows)<5: errors.append(f'рисков {len(rows)}, требуется не менее 5')
    if len(groups)<4: errors.append(f'разных категорий {len(groups)}, требуется не менее 4')
    ranked=[]
    for r in rows:
        try: score=int(r['likelihood'])*int(r['impact'])
        except Exception: score=0
        ranked.append((score,r))
    ranked.sort(key=lambda x:x[0],reverse=True)
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    report=['РАНЖИРОВАНИЕ РИСКОВ · ВАРИАНТ 7','']+[f"{score}: {r.get('risk_id')} · {r.get('category')} · {r.get('description')}" for score,r in ranked]
    report+=['',f'RESULT: {"FAIL ("+str(len(errors))+")" if errors else "PASS"}']+([f'FAIL: {e}' for e in errors] if errors else [])
    out.write_text('\n'.join(report)+'\n',encoding='utf-8'); print(report[-1])
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
