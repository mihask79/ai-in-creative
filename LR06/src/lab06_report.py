"""Build the report from actual measured artifacts and explicit visual review."""
import json
from pathlib import Path
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts'
OUT=ROOT/'reports/ЛР06_Отчет_вариант_1.pdf'

def main():
    r=json.loads((ART/'results.json').read_text(encoding='utf-8'))
    pre=r['preregistration']; env=r['environment']
    review=json.loads((ART/'visual_review.json').read_text(encoding='utf-8'))
    by={x['metric']:x for x in r['summary']}
    names=dict(clip='Сходство CLIP',edge='Энергия границ',contrast='Контраст',seconds='Время, с')
    for name,file in [('Arial','arial.ttf'),('ArialBold','arialbd.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
    pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
    st=getSampleStyleSheet()
    st.add(ParagraphStyle(name='RU',fontName='Arial',fontSize=10,leading=14,spaceAfter=8))
    st.add(ParagraphStyle(name='SmallRU',fontName='Arial',fontSize=8,leading=10.8,spaceAfter=4))
    st.add(ParagraphStyle(name='H',fontName='ArialBold',fontSize=16,leading=20,spaceAfter=14))
    st.add(ParagraphStyle(name='T',fontName='ArialBold',fontSize=23,leading=30,alignment=TA_CENTER,spaceAfter=20))
    st.add(ParagraphStyle(name='C',parent=st['RU'],alignment=TA_CENTER))
    story=[]
    def p(text,style='RU'): return Paragraph(text,st[style])
    def add(text,style='RU'): story.append(p(text,style))
    def head(text): add(text,'H')
    def page(): story.append(PageBreak())
    def table(headers,rows,widths):
        data=[[p(escape(str(v)),'SmallRU') for v in headers]]
        data += [[p(escape(str(v)),'SmallRU') for v in row] for row in rows]
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf5')),
            ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#ccd4dc')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.extend([t,Spacer(1,9)])
    def f(v,n=4): return f'{v:.{n}f}'.replace('.',',')
    def yes(v): return 'да' if v else 'нет'

    story.append(Spacer(1,40))
    add('Донской государственный технический университет','C')
    story.append(Spacer(1,45))
    add('Лабораторная работа № 6','T')
    add('Исследование параметров<br/>text-to-image генерации','T')
    add('Вариант 1. Афиша фестиваля робототехники<br/>Число шагов: 1 → 4','C')
    story.append(Spacer(1,40))
    add('Дисциплина: «Искусственный интеллект в креативных технологиях»','C')
    add('Выполнил: Скрыпник Михаил Дмитриевич<br/>Группа: МИК11','C')
    story.append(Spacer(1,50))
    add('Ростов-на-Дону, 2026<br/>Дата эксперимента: 27 октября 2026 года','C')
    story.append(Spacer(1,25))
    add('Фактическое выполнение: локальный Python, Windows, CPU float32. '
        'Работа содержит реальные измерения по пяти seed. Среда отличается от рекомендуемой Colab T4 float16; '
        'результаты демонстрационного примера не выдаются за собственные.','SmallRU')

    page(); head('1. Цель и постановка эксперимента')
    add('Цель: установить, как переход с одного на четыре шага SD-Turbo меняет соответствие брифу, '
        'энергию границ, контраст и время генерации при неизменных остальных условиях.')
    add('<b>Бриф.</b> Концепт афиши фестиваля робототехники: синий и янтарный цвета, светящийся силуэт '
        'механической руки, чистая композиция, без текста, логотипов и людей.')
    add('<b>Единственный изменяемый фактор:</b> num_inference_steps: A = 1, B = 4. '
        'В обоих режимах: 512 × 512, guidance_scale = 0,0, одинаковый запрос, CPU float32 и свежий CPU Generator '
        'для каждого вызова. Парная серия seed: 101, 102, 103, 104, 105.')
    add('<b>Исходный английский запрос:</b><br/>'+escape(pre['prompt']))
    add('<b>Гипотеза, записанная до запуска:</b> '+escape(pre['hypothesis']))
    add('Время записи: '+escape(pre['recorded_at'])+'. Запись сохранена в configs/preregistration.json; '
        'времена начала каждого измерения находятся в манифестах.')
    table(['Метрика','Практический допуск','Обоснование'],[
        ['CLIP','±1,0 пункта','Меньший сдвиг считаем малым для соответствия брифу.'],
        ['Энергия границ','±10% среднего A','Отсекает малые изменения резкости.'],
        ['Контраст','±10% среднего A','Отсекает малое изменение распределения яркости.'],
        ['Время','±20% среднего A','Замедление свыше 20% существенно для черновиков.']], [95,115,273])
    add('<b>Правило окупаемости:</b> '+escape(pre['payoff_rule']))
    add('Допуски являются заранее выбранным учебным правилом, а не универсальной нормой. '
        'Для энергии границ и контраста слово «улучшение» в классификации означает рост показателя, '
        'а эстетическое качество оценивается отдельно.')

    page(); head('2. Данные, модели и ход работы')
    add('Данные синтетические: один текстовый бриф и сгенерированные изображения. Фотографии реальных '
        'людей и чужие знаки в запрос не включены. Изображения рассматриваются как концепты, '
        'а не как технически достоверные изображения устройств.')
    table(['Компонент','Фактическое значение'],[
        ['Генератор',pre['model']],['Ревизия SD-Turbo',pre['revision']],
        ['Метрика CLIP',pre['clip_model']],['Ревизия CLIP',pre['clip_revision']],
        ['Среда',env['platform']],['Python / устройство',env['python']+' / CPU, float32, 4 потока'],
        ['PyTorch / Diffusers',env['packages']['torch']+' / '+env['packages']['diffusers']],
        ['Transformers / NumPy',env['packages']['transformers']+' / '+env['packages']['numpy']],
        ['Pillow / Accelerate',env['packages']['Pillow']+' / '+env['packages']['accelerate']],
        ['Внимание / детерминизм','PyTorch SDPA; slicing отключён; deterministic_algorithms=True']], [132,351])
    add('Веса SD-Turbo взяты из варианта fp16 закреплённого снимка и приведены к float32 для CPU. '
        'CLIP работает в float32. Все условия внутри пары A/B одинаковы, кроме числа шагов. '
        'Новый сеанс и другой вычислитель не проверялись.','SmallRU')
    add('<b>Протокол.</b> После записи гипотезы загружена SD-Turbo; выполнены прогревы обоих режимов на seed 0. '
        'Затем для каждого seed измерены A и B; время включает весь вызов генератора, исключает загрузку модели, '
        'сохранение PNG и расчёт метрик. После генерации CLIP оценивает каждое изображение относительно одного английского брифа.')
    add('<b>Фрагмент кода:</b><br/>generator = torch.Generator("cpu").manual_seed(seed)<br/>'
        'image = pipe(prompt=PROMPT, num_inference_steps=steps,<br/>'
        '&nbsp;&nbsp;guidance_scale=0.0, height=512, width=512, generator=generator).images[0]','SmallRU')
    add('<b>Лицензии.</b> Для SD-Turbo сохранена лицензия закреплённого снимка; работа использует модель в '
        'учебных некоммерческих целях. Для CLIP сохранена MIT License из репозитория OpenAI. '
        'Карточки моделей и тексты лицензий находятся в assignment/. Powered by Stability AI.','SmallRU')

    page(); head('3. Результаты измерений')
    table(['Режим','Seed','CLIP','Границы','Контраст','Время, с'],[
        [x['mode'],x['seed'],f(x['clip']),f(x['edge'],6),f(x['contrast'],6),f(x['seconds'],2)]
        for x in r['measurements']], [49,45,85,102,102,100])
    add('CLIP = 100 × cos(eI, eT). Яркость Y = 0,299R + 0,587G + 0,114B для RGB/255. '
        'Энергия границ: среднее hypot(SobelY, SobelX)/8 с отражением на границе. Контраст: std(Y). '
        'Числа в таблицах округлены; JSON и CSV содержат полную точность.','SmallRU')
    table(['Метрика','A','s(A)','B','Δ=B-A','|Δ|/s','>2s'],[
        [names[x['metric']],f(x['A']),f(x['s']),f(x['B']),f(x['delta']),f(x['ratio'],2),yes(x['criterion_2s'])]
        for x in r['summary']], [93,68,63,68,77,62,52])
    add('s - выборочное стандартное отклонение режима A (ddof=1) по пяти seed. '
        'Критерий |Δ| &gt; 2s показывает выход среднего сдвига за удвоенный разброс A между seed. '
        'Он не является формальным парным тестом и не задаёт вероятность ошибки или p-значение.','SmallRU')
    table(['Метрика','Изменение, %','Порог в единицах','По допуску'],[
        [names[x['metric']],f(x['percent'],1),f(x['threshold']),x['classification']]
        for x in r['summary']], [118,100,130,135])
    add('«Улучшение» энергии границ/контраста обозначает рост соответствующего показателя. '
        'Сводный вывод о качестве по этим словам не делается.','SmallRU')

    page(); head('4. Сравнительный лист и визуальная оценка')
    story.append(Image(str(ART/'comparison.png'),width=483,height=241.5))
    add('Seed 101: слева A (1 шаг), справа B (4 шага). Исходные изображения 512 × 512; '
        'сравнительный лист содержит уменьшенные копии 384 × 384.','SmallRU')
    add('<b>Наблюдение для seed 101.</b> '+escape(review['seed_101']))
    add('<b>Проверка главного объекта по всей серии.</b>')
    table(['Seed','Наблюдение'],[[x['seed'],x['observation']] for x in review['pairs']], [45,438])
    add('<b>Граница интерпретации.</b> '+escape(review['limitations']))
    count_a=sum(x['dominant_A'] for x in review['pairs'])
    count_b=sum(x['dominant_B'] for x in review['pairs'])
    add('По этой субъективной оценке рука или крупный сочленённый манипулятор является главным объектом '
        f'в {count_a} из 5 кадров A и {count_b} из 5 кадров B. Полное выполнение брифа всей серией не подтверждено.','SmallRU')

    page(); head('5. Намеренная ошибка и её диагностика')
    add('<b>Ошибка ожидания:</b> считать, что guidance_scale = 1,0 включает classifier-free guidance '
        'и усиливает соответствие запросу. Проверка выполнена отдельно от основного однофакторного эксперимента: '
        'seed 101, один шаг, тот же запрос и размер.')
    e1=r['guidance_check']['1.0']; e3=r['guidance_check']['3.0']
    table(['Guidance','CFG активен','PNG равен 0,0','PSNR к 0,0'],[
        ['0,0','нет','эталон','∞'],['1,0',yes(e1['cfg_active']),yes(e1['same_sha256']),str(e1['psnr_db'])],
        ['3,0',yes(e3['cfg_active']),yes(e3['same_sha256']),f(e3['psnr_db'],2)+' дБ']], [90,115,130,148])
    data=[[Image(str(ART/'A_101/result.png'),width=155,height=155),
           Image(str(ART/'guidance_1.png'),width=155,height=155),
           Image(str(ART/'guidance_3.png'),width=155,height=155)],
          [p('guidance 0,0','SmallRU'),p('guidance 1,0','SmallRU'),p('guidance 3,0','SmallRU')]]
    story.append(Table(data,colWidths=[161]*3))
    story.append(Spacer(1,12))
    add('SHA-256 для guidance 0,0 и 1,0:<br/>'+escape(e1['sha256']),'SmallRU')
    add('<b>Наблюдение.</b> Для 0,0 и 1,0 совпали байты PNG и пиксели; CFG=False. '
        'Для 3,0 CFG=True, изображение изменилось. Полные SHA-256, MSE, PSNR и состояния CFG '
        'сохранены в artifacts/guidance_check.json.')
    add('<b>Объяснение.</b> В используемом pipeline Diffusers CFG активируется при guidance_scale &gt; 1 '
        'и отсутствии отдельной условной проекции времени. При 0,0 и 1,0 здесь используется одинаковая ветвь генерации. '
        'Диагностика: вывести pipe.do_classifier_free_guidance сразу после вызова.')
    add('<b>Исправление.</b> Для обычной работы SD-Turbo оставить 0,0. Для диагностического изучения '
        'значения больше 1 явно отметить выход за рекомендованный режим. Нельзя переносить результат '
        'на другие модели с обычным CFG.')

    page(); head('6. Анализ, сравнение и вывод')
    for key in ['clip','edge','contrast','seconds']:
        x=by[key]
        add('<b>'+names[key]+'.</b> A='+f(x['A'])+', B='+f(x['B'])+', Δ='+f(x['delta'])+
            ' ('+f(x['percent'],1)+'%). По допуску: '+x['classification']+
            '; критерий 2s: '+yes(x['criterion_2s'])+'.')
    differing=[names[x['metric']] for x in r['summary'] if x['criterion_2s']!=x['outside_tolerance']]
    add('<b>Согласование критериев.</b> '+('Ответы критерия 2s и практического допуска различаются для: '+', '.join(differing)+'. '
        'Это разные вопросы: величина эффекта относительно разброса seed и относительно заранее выбранной полезной величины.'
        if differing else 'На фактической серии ответы 2s и практического допуска согласуются для всех четырёх метрик. '
        'Пример расхождения искусственно не подставляется: критерии всё равно имеют разный смысл.'))
    add('<b>Проверка гипотезы.</b> Рост энергии границ и времени подтверждён. '
        + ('Предположение о нейтральном CLIP подтвердилось по исходному допуску.' if abs(by['clip']['delta'])<=1 else
           'Предположение о нейтральном CLIP не подтвердилось по допуску: снижение '+f(abs(by['clip']['delta']),3)+
           ' пункта немного превышает порог 1,0. При удвоении допуска оно станет нейтральным; '
           'критерий 2s этого снижения не выделяет. Вывод о CLIP чувствителен к границе допуска.'),'SmallRU')
    add('<b>Чувствительность к допуску.</b> В таблице отмечен выход за порог при уменьшении и увеличении допуска вдвое.','SmallRU')
    table(['Метрика','0,5 допуска','Исходный','2 допуска'],[
        [names[x['metric']],yes(abs(x['delta'])>x['threshold']*0.5),yes(x['outside_tolerance']),yes(abs(x['delta'])>x['threshold']*2)]
        for x in r['summary']], [153,110,110,110])
    add('<b>Сопоставление с демонстрацией методички.</b> Ниже приведены опубликованные в методичке значения '
        'отдельного GPU-эксперимента; это внешние данные, а не наши измерения.','SmallRU')
    table(['Метрика','Демо A / B','Наши A / B'],[
        [names[k],demo,f(by[k]['A'])+' / '+f(by[k]['B'])] for k,demo in [
        ('clip','30,796 / 30,292'),('edge','0,0457 / 0,0920'),('contrast','0,1923 / 0,2778'),('seconds','0,2854 / 0,5266')]], [125,170,188])
    add('Различия допустимы: CPU float32, SDPA и версии среды отличаются от T4 float16. '
        'Время разных устройств напрямую не сравнивается; точного воспроизведения чисел GPU не заявляем.','SmallRU')
    add('<b>Объяснение.</b> Дополнительные шаги повторно уточняют скрытое представление и могут усилить '
        'мелкие структуры и перепады яркости. Это согласуется с ростом границ и контраста, если он наблюдается, '
        'но не гарантирует лучшего выполнения брифа. SD-Turbo обучена работать при малом числе шагов; '
        'соответствие запросу не обязано монотонно расти. Это интерпретация, а не отдельное измерение.','SmallRU')
    payoff=by['clip']['delta']>1 and by['seconds']['percent']<=20
    add('<b>Вывод.</b> '+('Численные условия окупаемости выполнены; окончательное решение зависит от узнаваемости объекта.' if payoff else
        'Для быстрых черновиков переход на четыре шага по заранее заданному правилу не окупился. ')+
        'Решение относится к этому брифу и пяти seed; рост границ и контраста сам по себе не подтверждает лучшее качество афиши.')
    add('<b>Угрозы валидности.</b> Один бриф, пять seed и одна модель; CLIP не проверяет механику руки, эстетику и '
        'точность деталей. Резкость растёт также от шума. Время измерено один раз для каждой пары, '
        'зависит от фоновой нагрузки, порядка A→B и состояния CPU. Прогрев снижает, но не устраняет эти факторы. '
        'Визуальная оценка субъективна. Для общей рекомендации нужны больше seed, несколько брифов, повторные замеры '
        'и слепая экспертная оценка.','SmallRU')

    page(); head('7. Ответы на контрольные вопросы (1-5)')
    answers=[
        ('1. Почему изменяется один фактор и нужна серия seed?',
         'При изменении нескольких факторов невозможно приписать эффект числу шагов. Одинаковые seed в A и B контролируют '
         'начальный шум, а пять seed показывают, насколько результат зависит от случайной композиции. Один seed не описывает разброс.'),
        ('2. Что означает |Δ| > 2s?',
         'Средний сдвиг превышает удвоенное выборочное стандартное отклонение режима A. Это учебная эвристика заметности '
         'на фоне разброса, не формальное доказательство причинности и не p-тест. '+
         ('В нашей серии критерии расходятся для '+', '.join(differing)+'.' if differing else
          'В нашей серии расхождения с допуском нет. Условный пример: при s=0,1, Δ=0,5 и допуске 1,0 критерий выполнен, а практический эффект нейтрален.')),
        ('3. Что измеряет CLIP и зачем английский бриф?',
         'CLIP измеряет косинусную близость векторов изображения и текста, умноженную на 100. Он не оценивает качество '
         'афиши целиком. Неизменный английский эталон сохраняет одну цель сравнения; у модели есть ограничения по языкам '
         'и длине текста. Это не формула CLIPScore с дополнительным масштабированием.'),
        ('4. Почему рост энергии границ не доказывает качество?',
         'Модуль градиента растёт и от полезных деталей, и от шума, ореолов, перегруженного фона и артефактов. '
         'Поэтому нужна проверка главного объекта, композиции и пригодности результата для афиши.'),
        ('5. Почему guidance 1,0 совпадает с 0,0?',
         'В данном pipeline CFG включается только при значении больше 1. На seed 101 для 0,0 и 1,0 совпали SHA-256 PNG '
         'и пиксели, а pipe.do_classifier_free_guidance=False. При 3,0 флаг True и изображение отличается. '
         'Для SD-Turbo рекомендован 0,0; другие модели требуют отдельной проверки.')]
    for q,a in answers: add('<b>'+q+'</b>'); add(a)

    page(); head('8. Вопросы (6-10), паспорт и источники')
    for q,a in [
        ('6. Что будет при 768 × 768?',
         'Это выход за рекомендуемые 512 × 512: возможны повторяющиеся детали, нарушение композиции и артефакты. '
         'В варианте 1 размер не менялся; собственных наблюдений для 768 × 768 нет.'),
        ('7. Время 0,30 → 0,55 с: изменение?',
         '(0,55 − 0,30)/0,30 × 100% = 83,33%. Генерация стала примерно в 1,83 раза дольше.'),
        ('8. Почему русский запрос сравнивают с английским брифом?',
         'Иначе изменятся одновременно изображение и эталон метрики, и сравнение будет отвечать на другой вопрос. '
         'Фиксированный эталон проверяет выполнение одного исходного задания. В этом варианте оба запроса английские.'),
        ('9. Как выбран допуск и что при удвоении?',
         'До запуска приняты ±1 пункт CLIP, ±10% для границ и контраста, ±20% времени как границы заметного для черновиков эффекта. '
         'Удвоение делает классификацию менее чувствительной; фактические ответы приведены в таблице чувствительности. '
         'Критерий 2s от изменения допуска не меняется.'),
        ('10. Что сохранить для воспроизведения?',
         'Ревизии SD-Turbo и CLIP, точный текст запроса, seed 101–105, шаги, guidance, размер, тип вычислений, '
         'устройство, версии библиотек, алгоритм внимания, генератор, прогрев, порядок вызовов и формулы метрик. '
         'Паспорт: artifacts/passport.json. Полное совпадение времени не ожидается.')]:
        add('<b>'+q+'</b> '+a,'SmallRU')
    add('<b>Материалы и индивидуальный вклад.</b> Подготовлены локальная адаптация библиотек, '
        'реальная серия генераций, расчёт метрик, проверка CFG, визуальная оценка, анализ допуска и отчёт. '
        'LR06.ipynb выполнен для независимой проверки сохранённых результатов; повторная генерация доступна '
        'через RUN_FULL_EXPERIMENT=True. Исходный журнал генерации сохранён отдельно. При подготовке кода '
        'и оформления использовался ИИ-помощник.','SmallRU')
    add('<b>Источники.</b>','SmallRU')
    add('1. Методические указания «Лабораторная работа № 6. Исследование параметров text-to-image генерации», '
        'предоставленный PDF: разделы 2-9 и приложение А. Демо-числа взяты из раздела 6.3.','SmallRU')
    add('2. <link href="https://huggingface.co/stabilityai/sd-turbo/blob/b261bac6fd2cf515557d5d0707481eafa0485ec2/README.md" color="blue">'
        'SD-Turbo: карточка закреплённой ревизии</link>; лицензия сохранена в assignment/model_LICENSE.md.','SmallRU')
    add('3. <link href="https://huggingface.co/openai/clip-vit-base-patch32/blob/3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268/README.md" color="blue">'
        'CLIP ViT-B/32: карточка закреплённой ревизии</link>; MIT License сохранена в assignment/CLIP_LICENSE.txt.','SmallRU')
    add('4. Sauer и др. Adversarial Diffusion Distillation, <link href="https://arxiv.org/abs/2311.17042" color="blue">arXiv:2311.17042</link>. '
        'Radford и др. Learning Transferable Visual Models From Natural Language Supervision, '
        '<link href="https://arxiv.org/abs/2103.00020" color="blue">arXiv:2103.00020</link>.','SmallRU')
    def footer(canvas,doc):
        canvas.setFont('Arial',8); canvas.setFillColor(colors.HexColor('#586777'))
        canvas.drawString(56,28,'ЛР06 · Вариант 1 · Скрыпник М. Д. · МИК11')
        canvas.drawRightString(A4[0]-56,28,str(doc.page))
    OUT.parent.mkdir(exist_ok=True)
    doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=56,leftMargin=56,topMargin=48,bottomMargin=48,
        title='ЛР06. Исследование параметров text-to-image. Вариант 1',author='Скрыпник Михаил Дмитриевич')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)

if __name__=='__main__': main()
