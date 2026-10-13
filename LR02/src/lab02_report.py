"""Build the variant 1 report from the current audit and model card."""
from pathlib import Path
import csv
from docx import Document
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]

def main():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Inches(.7)
    sec.left_margin = sec.right_margin = Inches(.8)
    doc.styles['Normal'].font.name = 'Times New Roman'
    doc.styles['Normal'].font.size = Pt(11)
    for name in ['Title', 'Heading 1', 'Heading 2']:
        doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    doc.add_paragraph('Карточка модели лицензии и риски', style='Title')
    doc.add_paragraph('Лабораторная работа 2 · Вариант 1\nДисциплина: Искусственный интеллект в креативных технологиях\nСтудент: Скрыпник Михаил Дмитриевич · Группа: МИК11\nДата выполнения: 13.10.2026')
    doc.add_heading('1 Цель и сценарий', level=1)
    doc.add_paragraph('Проверить пригодность набора для коммерческой афиши фестиваля: печать, продажа билетов, публикация и создание производных. ShareAlike не допускается. Аудит выявил четыре ошибки и три предупреждения. Четыре объекта исключены из допустимого состава, один ожидает подтверждения даты; семь оставшихся записей условно допустимы в рамках учебных правил.')
    doc.add_paragraph('До запуска ожидались конфликты NC у item01, item04, item08, item10, конфликты SA у item01 и item04 и отсутствующая дата item09. Ожидания записаны в reports/lab_journal.txt. Критерий успеха — решение по каждой находке, заполненные карточки и проверка рисков PASS.')
    doc.add_heading('2 Методика и воспроизведение', level=1)
    doc.add_paragraph('Использован Python 3.12.14 и стандартная библиотека для аудита. Для сборки DOCX применяется python-docx. Манифест синтетический: реальные произведения не загружались. Учебные правила из методички проверяют поля записей, а не подлинность лицензии. Команды выполняются из папки LR02.')
    for command in [
        'python src/lab02_make_variant.py --variant 1 --out artifacts',
        'python src/lab02_audit.py --manifest artifacts/manifest.csv --policy artifacts/policy.json --out reports',
        'python src/lab02_model_card.py --passport artifacts/passport_lr01.json --out reports/model_card.md',
        'python src/lab02_risks.py --csv artifacts/risk_register.csv --out reports/risk_ranking.md',
    ]:
        p=doc.add_paragraph(command); p.runs[0].font.size=Pt(9)
    doc.add_heading('3 Находки и решения', level=1)
    with (ROOT/'reports/audit_findings.csv').open(encoding='utf-8-sig', newline='') as f:
        findings=list(csv.DictReader(f))
    for item in dict.fromkeys(r['item_id'] for r in findings):
        subset=[r for r in findings if r['item_id']==item]
        doc.add_heading(item+' — '+', '.join(r['rule'] for r in subset), level=2)
        doc.add_paragraph('; '.join(r['description'] for r in subset)+'.')
        doc.add_paragraph(subset[0]['decision'])
    doc.add_paragraph('Решения принимаются по объектам: исключение item01 и item04 снимает обе находки по каждому. Сценарий не допускает коммерческое использование NC и передачу производных на условиях SA. Отдельное разрешение правообладателя должно охватывать все конфликтующие условия.')
    doc.add_heading('4 Паспорт набора данных', level=1)
    add_markdown(doc, ROOT/'reports/data_card.md')
    doc.add_heading('5 Карточка модели', level=1)
    add_markdown(doc, ROOT/'reports/model_card.md')
    doc.add_heading('6 Реестр рисков', level=1)
    with (ROOT/'artifacts/risk_register.csv').open(encoding='utf-8-sig',newline='') as f:
        risks=list(csv.DictReader(f))
    for risk in sorted(risks,key=lambda r:int(r['likelihood'])*int(r['impact']),reverse=True):
        score=int(risk['likelihood'])*int(risk['impact'])
        doc.add_heading(f"{risk['risk_id']} {risk['category']}",level=2)
        doc.add_paragraph(f"Вероятность {risk['likelihood']}, ущерб {risk['impact']}, приоритет {score}. {risk['description']}.")
        doc.add_paragraph(f"Мера: {risk['mitigation']}. Ответственный: {risk['owner']}. Триггер: {risk['trigger']}.")
    doc.add_paragraph('Проверка: RESULT: PASS. Шесть рисков в шести категориях; обязательные Intellectual Property и Information Integrity присутствуют. Оценка P×I задаёт учебный приоритет и не является вероятностью ущерба.')
    doc.add_heading('7 Ошибка диагностика и границы вывода', level=1)
    doc.add_paragraph('В отдельной проверке намеренно задана категория Copyright, оценка 7 и пустой ответственный. Валидатор отклоняет такой реестр. Исправление: Intellectual Property, целочисленная оценка 1–5 и заполненный ответственный; рабочий реестр проходит проверку. Протокол записан в reports/validation.txt.')
    doc.add_paragraph('Инженерное решение — исключить конфликтующие записи, хранить атрибуцию и вести карантин. Юридический вопрос — достаточно ли конкретного разрешения для печати, публикации и производных и как квалифицируется переработка; он требует проверки реальных документов. Этическое решение — не вводить зрителя в заблуждение об авторах и программе фестиваля. Организационное решение — назначить куратора и редактора, запретить выпуск до закрытия находок.')
    doc.add_paragraph('Контрольные вопросы. При переходе к некоммерческому сценарию R3 может исчезнуть, но условия SA и требование подтверждения происхождения сохраняются. Отсутствие ошибки в автоматическом аудите не подтверждает права: скрипт видит только записанные поля. По объекту с NC-SA нужно либо исключение, либо разрешение, снимающее оба конфликта.')
    doc.add_heading('8 Вывод и материалы',level=1)
    doc.add_paragraph('Для текущей политики исходный набор не готов к использованию. Решения по всем семи находкам записаны; карточка генератора использует фактические результаты варианта 1 из LR01-01. Ограничения: синтетические записи, упрощённые правила и неизвестные лицензия кода и ответственный за его сопровождение. Полный комплект: assignment/, src/, artifacts/, reports/ и README.md.')
    path=ROOT/'reports/ЛР02_Отчет_вариант_1.docx'
    doc.save(path)
    print(path)

def add_markdown(doc, path):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('# '): continue
        if line.startswith('## '): doc.add_heading(line[3:],level=2)
        elif line.strip(): doc.add_paragraph(line)

if __name__=='__main__': main()
