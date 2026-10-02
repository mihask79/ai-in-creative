"""Rule-based educational audit of a manifest against a usage policy."""
import argparse
from pathlib import Path
from lab02_common import read_csv, read_json, write_csv

def findings(rows, policy):
    out=[]
    for r in rows:
        i=r['item_id']; lic=r.get('license_spdx','').strip()
        def add(rule,level,description): out.append({'rule':rule,'level':level,'item_id':i,'description':description,'decision':''})
        if not lic: add('R1','error','Лицензия не указана')
        elif lic not in {'CC0-1.0','CC-BY-4.0','CC-BY-SA-4.0','CC-BY-NC-4.0','CC-BY-NC-SA-4.0','CC-BY-ND-4.0','CC-BY-NC-ND-4.0','MIT','Apache-2.0'}:
            add('R2','error',f'Лицензия не распознана учебным перечнем: {lic}')
        if policy.get('commercial_use') and '-NC-' in f'-{lic}-': add('R3','error',f'{lic}: NonCommercial несовместимо с коммерческим использованием')
        if policy.get('create_derivatives') and '-ND-' in f'-{lic}-': add('R4','error',f'{lic}: NoDerivatives несовместимо с созданием производных')
        if policy.get('create_derivatives') and '-SA-' in f'-{lic}-' and not policy.get('allow_sharealike_derivatives'):
            add('R5','warning',f'{lic}: необходимо передавать производные на тех же условиях, что не допускает политика')
        if r.get('personal_data','').lower()=='true' and not r.get('consent_doc','').strip(): add('R6','error','Персональные данные без ссылки на документ-согласие')
        if r.get('personal_data','').lower()=='true' and r.get('consent_doc','').strip() and policy.get('publish_or_share_dataset'): add('R7','warning','Согласие есть, но при публикации нужно проверить его охват и срок')
        if not r.get('source','').strip() or not r.get('date_obtained','').strip(): add('R8','warning','Не указан источник или дата получения')
        if r.get('duplicate_of'): add('R9','warning',f"Дубликат контрольной суммы: {r['duplicate_of']}")
        if not r.get('rights_holder','').strip(): add('R10','warning','Не указан правообладатель')
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--manifest',required=True); p.add_argument('--policy',required=True); p.add_argument('--out',required=True); a=p.parse_args()
    rows=read_csv(a.manifest); pol=read_json(a.policy); result=findings(rows,pol); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    decisions={'item01':'Исключить или запросить отдельное коммерческое разрешение: NC конфликтует с монетизацией; SA можно соблюдать.',
      'item04':'Исключить или запросить отдельное коммерческое разрешение: NC конфликтует с монетизацией; SA можно соблюдать.',
      'item08':'Исключить или получить коммерческое разрешение до использования.',
      'item10':'Исключить или получить коммерческое разрешение до использования.',
      'item09':'Карантин до подтверждения даты получения и источника; не восстанавливать дату догадкой.'}
    for f in result: f['decision']=decisions.get(f['item_id'],'Уточнить у поставщика; до проверки не использовать.')
    write_csv(out/'audit_findings.csv',['rule','level','item_id','description','decision'],result)
    errors=sum(x['level']=='error' for x in result); warnings=sum(x['level']=='warning' for x in result)
    lines=['АУДИТ ЛР 2 · ВАРИАНТ 7','',f"Сценарий: {pol['scenario']}",f'Объектов: {len(rows)}',f'Ошибок: {errors}; предупреждений: {warnings}','', 'Решения по объектам:']
    for item,decision in decisions.items(): lines.append(f'- {item}: {decision}')
    lines += ['', 'Итог: исключить четыре NC-объекта или получить отдельные разрешения. item09 не использовать до подтверждения происхождения.',
      'Ограничение: автоматическая проверка оценивает только поля манифеста и не подтверждает лицензию у первоисточника; не является юридической консультацией.']
    (out/'audit_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Ошибок: {errors}; предупреждений: {warnings}; отчёт: {out / "audit_report.md"}')
if __name__=='__main__': main()
