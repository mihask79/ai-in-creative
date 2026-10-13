"""Generate the self-contained synthetic dataset and policy for variant 1."""
import argparse
from pathlib import Path
from lab02_common import write_csv, write_json

def make(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    # These are synthetic teaching records. The NonCommercial defect profile
    # mirrors the method guide's demonstration records; no real works are used.
    licenses=['CC-BY-NC-SA-4.0','CC0-1.0','CC-BY-4.0','CC-BY-NC-SA-4.0',
              'CC0-1.0','CC-BY-4.0','CC-BY-4.0','CC-BY-NC-4.0',
              'CC-BY-4.0','CC-BY-NC-4.0','CC-BY-4.0','CC0-1.0']
    rows=[]
    for n,lic in enumerate(licenses,1):
        item=f'item{n:02d}'
        rows.append({'item_id':item,'asset_type':'synthetic_image','source':f'https://example.org/lab02/{item}',
          'date_obtained':'' if item=='item09' else '2026-10-02','license_spdx':lic,
          'rights_holder':f'Synthetic Holder {n:02d}','personal_data':'false',
          'consent_doc':'','sha256_synthetic':f'synthetic-{n:02d}','note':'synthetic teaching record'})
    write_csv(out/'manifest.csv',list(rows[0]),rows)
    write_json(out/'policy.json',{'variant':1,'scenario':'афиша фестиваля; печать, продажа билетов и публикация',
      'commercial_use':True,'publish_or_share_dataset':True,'create_derivatives':True,
      'allow_sharealike_derivatives':False,'personal_data_allowed':False,
      'note':'Учебная политика. Используются только синтетические записи; автоматическая проверка не является юридическим заключением.'})
    print(f'Созданы {len(rows)} синтетических записей: {out}')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--variant',type=int,required=True); p.add_argument('--out',required=True); a=p.parse_args()
    if a.variant!=1: raise SystemExit('Этот комплект реализует вариант 1.')
    make(a.out)
