"""Build a Russian PDF report from measured artifacts; no invented results."""
from pathlib import Path
import json
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
OUT = ROOT / "reports" / "ЛР05_Отчет_вариант_1.pdf"

def main():
    r = json.loads((ART / "results.json").read_text(encoding="utf-8"))
    p = json.loads((ART / "passport.json").read_text(encoding="utf-8"))
    m = r["manifests"]["run_A"]
    pre = r["preregistration"]
    err = r["shared_generator"]
    fonts = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("Arial", str(fonts / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("ArialBold", str(fonts / "arialbd.ttf")))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="ArialBold", italic="Arial", boldItalic="ArialBold")
    st = getSampleStyleSheet()
    st.add(ParagraphStyle(name="BodyRU", fontName="Arial", fontSize=10.5, leading=15, spaceAfter=8))
    st.add(ParagraphStyle(name="SmallRU", fontName="Arial", fontSize=8.6, leading=12, spaceAfter=5))
    st.add(ParagraphStyle(name="HeadRU", fontName="ArialBold", fontSize=15, leading=19, spaceAfter=13))
    st.add(ParagraphStyle(name="TitleRU", fontName="ArialBold", fontSize=22, leading=29, alignment=TA_CENTER, spaceAfter=18))
    st.add(ParagraphStyle(name="CenterRU", parent=st["BodyRU"], alignment=TA_CENTER))
    st.add(ParagraphStyle(name="CodeRU", fontName="Arial", fontSize=8.5, leading=12, spaceAfter=8))
    story = []
    def para(text, style="BodyRU"):
        return Paragraph(text, st[style])
    def add(text, style="BodyRU"):
        story.append(para(text,style))
    def head(text):
        add(text,"HeadRU")
    def page():
        story.append(PageBreak())
    def table(headers, rows, widths):
        data = [[para(escape(str(v)), "SmallRU") for v in headers]]
        data += [[para(escape(str(v)), "SmallRU") for v in row] for row in rows]
        t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E5EAF0")),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#D9D9D9")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        story.extend([t,Spacer(1,10)])
    def pair(left, right, labels):
        t=Table([[Image(str(ART/left/"result.png"),width=210,height=210),
                  Image(str(ART/right/"result.png"),width=210,height=210)],
                 [para(labels[0],"CenterRU"),para(labels[1],"CenterRU")]],colWidths=[237,237])
        t.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.extend([t,Spacer(1,10)])
    def value_psnr(v):
        return "+∞" if v == "Infinity" else f"{v:.4f}"

    # Page 1
    story.append(Spacer(1,48))
    add("Донской государственный технический университет", "CenterRU")
    story.append(Spacer(1,38))
    add("Лабораторная работа 5", "TitleRU")
    add("Запуск открытой модели<br/>text-to-image", "TitleRU")
    add("Вариант 1", "CenterRU")
    story.append(Spacer(1,32))
    add("Дисциплина: Искусственный интеллект в креативных технологиях")
    add("Выполнил: Скрыпник Михаил Дмитриевич<br/>Группа: МИК11")
    add("Дата выполнения: 27 октября 2026 года")
    story.append(Spacer(1,30))
    head("Результат эксперимента")
    repeat=r["repeat"]
    add(f"Два запуска SD-Turbo со свежим CPU-генератором и seed 1001 дали вердикт "
        f"<b>{repeat['verdict']}</b>: совпадение пикселей - {'да' if repeat['pixel_equal'] else 'нет'}, "
        f"максимальная разность - {repeat['max_diff']}, PSNR - {value_psnr(repeat['psnr_db'])} дБ. "
        f"При общем генераторе PSNR составил {value_psnr(err['psnr_db'])} дБ. "
        "Проверка относится к одному локальному сеансу Python на CPU.")
    add("Учебное некоммерческое использование. Powered by Stability AI.","SmallRU")

    # Page 2
    page(); head("1 Цель и постановка задачи")
    add("Цель - запустить открытую модель по закреплённой ревизии, сохранить изображение и манифест, "
        "а затем проверить воспроизводимость по байтам файла, пикселям и PSNR.")
    add("Вариант 1 задаёт бриф «афиша фестиваля робототехники» и условие «повтор запуска в том же сеансе». "
        "Основной объект - силуэт механической руки; палитра - глубокий синий и янтарный. Seed = 1000 + 1 = 1001.")
    add("<b>Гипотеза до запуска.</b> При неизменных параметрах модели и свежем CPU Generator с seed 1001 "
        "результаты A и B совпадут побитово. Общий Generator при повторном использовании даст другой шум.")
    add(f"Гипотеза и допуск записаны до загрузки модели: {escape(pre['recorded_at'])}. "
        "Запись сохранена в configs/preregistration.json.")
    table(["Класс", "Критерий"],[["identical", "Полное совпадение пикселей; дополнительно проверяется SHA-256 PNG"],
        ["close", "Пиксели отличаются, PSNR не ниже 40 дБ"],["different", "PSNR ниже 40 дБ"]],[95,379])
    head("2 Данные и лицензия")
    add("Входные данные - один синтетический текстовый запрос из приложения А методички:")
    add(escape(pre["prompt"]),"SmallRU")
    add("В запросе нет реальных лиц, названий производителей, логотипов или закрытых материалов. "
        "Изображение служит концептом афиши и не описывает реальное устройство.")
    add("Для закреплённой ревизии сохранён файл LICENSE.md с Stability AI Community License от 5 июля 2024 года. "
        "Работа имеет учебную некоммерческую цель. Коммерческое применение требует отдельной проверки условий, "
        "регистрации и порога выручки; доступность весов сама по себе не означает свободную лицензию. "
        "Также действуют ограничения использования из карточки модели и AUP.")

    # Page 3
    page(); head("3 Среда и параметры")
    add("Фактическое выполнение: локальный Python под Windows, CPU float32. Engee и Google Colab не использовались. "
        "Отличие от демонстрации методички - CPU вместо Tesla T4 и float32 вместо float16. "
        "Все сравниваемые запуски выполнены в одной среде.")
    table(["Параметр", "Значение"],[
        ["Модель",pre["model_id"]],["Ревизия",pre["revision"]],
        ["Seed / шаги / guidance", "1001 / 1 / 0.0"],["Размер и режим", "512 × 512, RGB"],
        ["Весовой снимок / вычисления", "fp16 / float32"],["Генератор / вычислитель", "CPU / CPU"],
        ["Потоки PyTorch",m["torch_num_threads"]],["Детерминированные алгоритмы",m["deterministic_algorithms"]],
        ["Python",m["python"]],["Платформа",m["platform"]]], [160,314])
    table(["Библиотека", "Версия"],list(m["packages"].items()),[190,284])
    add(f"Загрузка модели: {m['load_seconds']:.2f} с; прогрев: {m['warmup_seconds']:.2f} с; "
        f"генерация A после прогрева: {m['generation_seconds']:.2f} с. "
        "Времена отражают этот запуск и не входят в критерий совпадения.","SmallRU")

    # Page 4
    page(); head("4 Ход работы")
    add("1. До запуска сохранены гипотеза, допуск 40 дБ и фиксированные параметры. "
        "Загружен снимок модели с полной ревизией; веса fp16 приведены к float32 для CPU. "
        "Выполнен прогрев с отдельным seed 1.")
    add("2. Получено изображение A, сохранены result.png и manifest.json. "
        "Затем с новым генератором и тем же seed 1001 получено изображение B.")
    add("3. Сравнены байты PNG и SHA-256, декодированные RGB-пиксели, максимум абсолютной разности, MSE и PSNR. "
        "MSE вычислялась по всем 512 × 512 × 3 значениям каналов в float64, что исключает переполнение uint8. "
        "PSNR равен 10 log10(255² / MSE); при нулевой MSE используется +∞.")
    add("4. Для проверки ошибки создан один Generator с seed 1001 и передан в два вызова подряд. "
        "После этого выполнен исправленный повтор со свежим Generator. Состояния общего генератора "
        "до и после каждого вызова записаны в манифесты в виде SHA-256.")
    head("Фрагменты выполненного кода")
    code = [
        'g = torch.Generator(device="cpu").manual_seed(1001)',
        'image = pipe(prompt=PROMPT, generator=g,',
        '    num_inference_steps=1, guidance_scale=0.0,',
        '    height=512, width=512).images[0]',
        '',
        '# Ошибка: один объект, два вызова',
        'g = torch.Generator(device="cpu").manual_seed(1001)',
        'e1 = generate(pipe, generator=g)',
        'e2 = generate(pipe, generator=g)',
        '',
        '# Исправление: generate создаёт новый Generator',
        'fixed = generate(pipe, seed=1001)',
    ]
    add('<br/>'.join(escape(x).replace(' ','&#160;') for x in code),"CodeRU")
    add("Полный код: src/lab05_lib.py и src/lab05_experiment.py. "
        "Блокнот LR05.ipynb содержит фактический вывод выполнения и изображения. "
        "Функции приложения А адаптированы для локального CPU и сохранения результатов каждого вызова.")

    # Page 5
    page(); head("5 Результат повторного запуска")
    pair("run_A","run_B",["A - свежий генератор, seed 1001","B - новый генератор, seed 1001"])
    rows=[]
    for label,key in [("Повтор A и B","repeat"),("Общий генератор","shared_generator"),("Исправление и A","repaired_vs_reference")]:
        c=r[key]
        rows.append([label, "да" if c["sha_equal"] else "нет", "да" if c["pixel_equal"] else "нет",c["max_diff"],value_psnr(c["psnr_db"]),c["verdict"]])
    table(["Сравнение","SHA-256 равны","Пиксели равны","Макс. Δ","PSNR дБ","Вердикт"],rows,[118,65,65,55,70,101])
    add(f"MSE повторов A и B: {repeat['mse']:.6f}. "
        f"SHA-256 A: {m['sha256']}","SmallRU")
    add(f"SHA-256 B: {r['manifests']['run_B']['sha256']}","SmallRU")
    add("Визуальная оценка приведена после просмотра сохранённых PNG. "
        "Численное совпадение проверяет воспроизводимость; соответствие брифу оценивается отдельно.")
    visual = json.loads((ART / "visual_review.json").read_text(encoding="utf-8"))
    add(escape(visual["repeat_pair_review"]))

    # Page 6
    page(); head("6 Ошибка общего генератора и исправление")
    pair("error_A","error_B",["Первый вызов общего Generator","Второй вызов того же Generator"])
    add(f"Первый вызов общего генератора совпал с A: {r['first_shared_vs_reference']['pixel_equal']}. "
        f"Между первым и вторым вызовом: MSE = {err['mse']:.4f}, "
        f"максимальная разность = {err['max_diff']}, PSNR = {value_psnr(err['psnr_db'])} дБ, "
        f"вердикт - {err['verdict']}.")
    add(f"SHA-256 первого вызова: {r['manifests']['error_A']['sha256']}<br/>"
        f"SHA-256 второго вызова: {r['manifests']['error_B']['sha256']}","SmallRU")
    add(escape(visual["error_pair_review"]),"SmallRU")
    add("Причина: Generator хранит состояние. Первый вызов расходует случайные числа; второй продолжает "
        "последовательность, хотя начальный seed при создании объекта был тем же. "
        "Seed объекта не означает автоматический сброс перед каждым вызовом модели.")
    ea=r["manifests"]["error_A"]; eb=r["manifests"]["error_B"]
    add(f"Проверка состояния: конец первого вызова равен началу второго - "
        f"{ea['generator_state_after_sha256']==eb['generator_state_before_sha256']}; "
        f"начало и конец первого вызова различаются - "
        f"{ea['generator_state_before_sha256']!=ea['generator_state_after_sha256']}.")
    add(f"Исправление - создавать Generator заново внутри функции запуска. "
        f"После исправления пиксели совпали с A: {r['repaired_vs_reference']['pixel_equal']}; "
        f"PSNR = {value_psnr(r['repaired_vs_reference']['psnr_db'])} дБ. "
        "Это подтверждает связь наблюдаемого расхождения с состоянием генератора.")

    # Page 7
    page(); head("7 Паспорт эксперимента и вывод")
    table(["Поле", "Содержание"],[
        ["Автор и дата", "Скрыпник Михаил Дмитриевич, МИК11; 27.10.2026"],
        ["Задача", "Повтор генерации афиши фестиваля робототехники; вариант 1"],
        ["Фиксированные параметры", "SD-Turbo; закреплённая ревизия; seed 1001; 1 шаг; guidance 0; 512 × 512; CPU float32"],
        ["Изменяемое условие", "Независимый повтор с новым генератором; отдельно - повторное использование общего генератора"],
        ["Вход и выход", "Один текстовый запрос; 5 RGB PNG и 5 JSON-манифестов"],
        ["Допуск до запуска", "Совпадение пикселей; иначе PSNR >= 40 дБ для практически совпадающих"],
        ["Контроль", "SHA-256 файлов, пиксели, MSE, PSNR; повторный расчёт по сохранённым файлам"],
        ["Хранение", "artifacts/results.json, passport.json, run_A, run_B, error_A, error_B, fixed"],
        ["Воспроизводимый запуск", ".venv/Scripts/python.exe src/lab05_experiment.py (из LR05)"],
        ["Лицензия", "Stability AI Community License; учебное некоммерческое применение"],
    ],[135,339])
    add("<b>Вывод.</b> " + ("Гипотеза о побитовом совпадении A и B подтверждена в проверенной среде. "
        if repeat["sha_equal"] else "Побитовое совпадение A и B не получено; наблюдаемый результат указан в таблице. ") +
        "Проверка общего генератора показывает, почему одинаковый seed при создании объекта не обеспечивает "
        "повтор при продолжении его состояния. Новый генератор устраняет эту ошибку.")
    add("Угрозы валидности: один seed, один запрос, одна версия среды и CPU; новая сессия и другой компьютер "
        "не проверялись. Переход на GPU, другую точность, версии библиотек или способ кодирования PNG может "
        "изменить контрольные суммы. PSNR не измеряет художественное качество. Визуальное соответствие брифу "
        "оценивается по сохранённой паре, а не следует из равенства файлов.")
    add("Индивидуальный вклад: адаптация учебных функций для CPU, фиксация параметров до запуска, "
        "выполнение повторов, демонстрация и исправление ошибки, анализ артефактов и оформление отчёта. "
        "Код и текст подготовлены с помощью ИИ-ассистента.")

    # Page 8
    page(); head("8 Ответы на контрольные вопросы")
    answers=[
        ("1 Модель и конвейер", "Модель содержит архитектуру и веса. Конвейер объединяет токенизатор, текстовый кодировщик, "
         "сеть шумоподавления, scheduler и декодер. Приложение предоставляет интерфейс запуска."),
        ("2 Зачем нужна ревизия", "Имя репозитория может указывать на меняющиеся файлы. Полная ревизия закрепляет конкретный снимок."),
        ("3 Что фиксирует seed", "Начальное состояние генератора при определённом устройстве и типе данных. "
         "Он не закрепляет версии, алгоритмы, точность, платформу и текущее состояние уже использованного Generator."),
        ("4 Почему CPU Generator", "Он позволяет строить начальный шум на CPU при разных устройствах вычислений; "
         "это уменьшает различия источника случайности, но не гарантирует совпадение всех вычислений."),
        ("5 Что показал общий Generator", f"После первого вызова его состояние сдвинулось; PSNR между вызовами составил "
         f"{value_psnr(err['psnr_db'])} дБ. Свежий генератор восстановил результат."),
        ("6 Что доказывает SHA-256", "Совпадение хешей даёт сильное свидетельство равенства байтов. "
         "Оно не оценивает бриф, качество или переносимость. Разные файлы могут содержать одинаковые пиксели."),
        ("7 PSNR при MSE 65,025", "255² / 65,025 = 1000; 10 log10(1000) = 30 дБ. Это ниже допуска 40 дБ."),
        ("8 Смена float16 на float32", "Могут измениться и вычислительная точность, и начальный шум. "
         "Для разделения причин нужно один раз создать шум float32 и передать его в оба режима. Вариант 1 этого не требует."),
        ("9 Лицензия", "Указать модель, ревизию, ссылку на LICENSE.md, учебную цель и применимые ограничения. "
         "Для коммерческого использования отдельно проверить актуальные условия правообладателя."),
        ("10 Другая видеокарта", "Записать GPU, драйвер, CUDA, типы данных и версии; заново сохранить артефакты, "
         "посчитать метрики и сформулировать вывод для новой пары."),
    ]
    for q,a in answers:
        add(f"<b>{q}.</b> {a}","SmallRU")
    head("9 Источники и материалы")
    add("1. Методические указания к ЛР 5, разделы 3, 7, 8 и приложение А; PDF сохранён в assignment.<br/>"
        "2. Модель и лицензия закреплённой ревизии: "
        '<link href="https://huggingface.co/stabilityai/sd-turbo/tree/b261bac6fd2cf515557d5d0707481eafa0485ec2">'
        'huggingface.co/stabilityai/sd-turbo</link> (README.md и LICENSE.md).<br/>'
        '3. Diffusers Reproducibility: <link href="https://huggingface.co/docs/diffusers/using-diffusers/reusing_seeds">'
        'huggingface.co/docs/diffusers/using-diffusers/reusing_seeds</link>.<br/>'
        "Проверено 27.10.2026. Материалы: LR05.ipynb, src/, configs/, artifacts/, reports/.","SmallRU")
    def footer(canvas,doc):
        canvas.setFont("Arial",8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawRightString(A4[0]-58,28,str(doc.page))
    doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=58,leftMargin=58,topMargin=48,bottomMargin=48,
        title="Лабораторная работа 5 Вариант 1",author="Скрыпник Михаил Дмитриевич")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)

if __name__ == "__main__":
    main()
