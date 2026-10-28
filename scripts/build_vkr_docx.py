from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


DESKTOP_DIR = Path(r"C:\Users\AdmiN\Desktop")
OUT_DIR = DESKTOP_DIR / "ВКР_Петренко_Иван_Андреевич"
MAIN_DOCX = OUT_DIR / "Пояснительная_записка_ВКР_Петренко_Иван_Андреевич.docx"
REVIEW_DOCX = OUT_DIR / "Отчет_по_код_ревью_и_доработкам.docx"


TOPIC = (
    "Разработка программного обеспечения для интеллектуальной обработки "
    "и автоматизированного перевода документов в формат Markdown"
)


def set_cell_text(cell, text: str, bold: bool = False) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    fld_char_1 = OxmlElement("w:fldChar")
    fld_char_1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char_2 = OxmlElement("w:fldChar")
    fld_char_2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_1)
    run._r.append(instr_text)
    run._r.append(fld_char_2)


def configure_section(section) -> None:
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(1.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.different_first_page_header_footer = True
    add_page_number(section.footer.paragraphs[0])


def setup_doc() -> Document:
    doc = Document()
    configure_section(doc.sections[0])
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for style_name in ["Heading 1", "Heading 2", "Heading 3"]:
        style = styles[style_name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(14)
        style.font.bold = False
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(12)

    return doc


def add_center(doc: Document, text: str, bold: bool = False, size: int = 14) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)


def add_body(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.line_spacing = 1.5
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def add_plain(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)


def add_struct_heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.style = doc.styles["Normal"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.page_break_before = True
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text.upper())
    run.bold = False
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)


def add_chapter(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.style = doc.styles["Normal"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.page_break_before = True
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text.upper())
    run.bold = False
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)


def add_subheading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.style = doc.styles["Normal"]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text)
    run.bold = False
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph("– " + item)
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.paragraph_format.left_indent = Cm(1.25)
        p.paragraph_format.line_spacing = 1.5
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def add_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5


def add_table(doc: Document, headers: list[str], rows: list[list[str]], caption: str) -> None:
    add_plain(doc, caption)
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value)
    doc.add_paragraph()


def add_title_page(doc: Document) -> None:
    add_center(doc, "Министерство науки и высшего образования Российской Федерации", True)
    add_center(doc, "Федеральное государственное бюджетное образовательное учреждение")
    add_center(doc, "высшего образования")
    add_center(doc, "«Владимирский государственный университет имени")
    add_center(doc, "Александра Григорьевича и Николая Григорьевича Столетовых»")
    add_center(doc, "(ВлГУ)")
    doc.add_paragraph()
    add_center(doc, "ВЫПУСКНАЯ")
    add_center(doc, "КВАЛИФИКАЦИОННАЯ РАБОТА", True)
    doc.add_paragraph()
    add_plain(doc, "Студент: Петренко Иван Андреевич")
    add_plain(doc, "Институт: Институт информационных технологий и электроники")
    add_plain(doc, "Направление: 09.03.03 «Прикладная информатика»")
    add_plain(doc, "Группа: ПИ-122")
    doc.add_paragraph()
    add_center(doc, "Тема выпускной квалификационной работы")
    add_center(doc, f"«{TOPIC}»")
    doc.add_paragraph()
    add_plain(doc, "Руководитель ВКР ________________________________")
    add_plain(doc, "Студент ________________________________ Петренко И.А.")
    doc.add_paragraph()
    add_plain(doc, "Допустить выпускную квалификационную работу к защите")
    add_plain(doc, "Заведующий кафедрой ________________________________")
    add_center(doc, "Владимир 2026")


def add_assignment(doc: Document) -> None:
    add_struct_heading(doc, "Задание на выпускную квалификационную работу")
    add_plain(doc, "Студенту Петренко Ивану Андреевичу")
    add_plain(doc, f"1. Тема ВКР: {TOPIC}.")
    add_plain(doc, "2. Срок сдачи законченной ВКР: ____________________.")
    add_plain(doc, "3. Исходные данные к ВКР: проект ai-translator, регламент оформления ВКР, пример выпускной квалификационной работы, тестовые документы для конвертации.")
    add_plain(doc, "4. Содержание пояснительной записки:")
    add_bullets(
        doc,
        [
            "анализ предметной области и существующих способов обработки документов;",
            "обоснование выбора средств разработки;",
            "проектирование архитектуры программной системы;",
            "реализация конвейера обработки, веб-интерфейса и модуля перевода;",
            "тестирование и оценка практической эффективности.",
        ],
    )
    add_plain(doc, "Дата выдачи задания: ____________________.")
    add_plain(doc, "Руководитель ____________________")
    add_plain(doc, "Задание принял к исполнению ____________________ Петренко И.А.")


def add_annotation(doc: Document) -> None:
    add_struct_heading(doc, "Аннотация")
    add_body(
        doc,
        "Выпускная квалификационная работа посвящена разработке программного обеспечения "
        "для интеллектуальной обработки документов, преобразования их содержимого в формат "
        "Markdown и автоматизированного перевода полученного результата. Разработанная "
        "система предназначена для сокращения ручных трудозатрат при подготовке технической "
        "документации, сохранения структуры исходных материалов и повышения повторяемости "
        "результата обработки.",
    )
    add_body(
        doc,
        "В работе рассмотрены особенности обработки PDF и других документных форматов, "
        "проанализированы существующие подходы к OCR, структурному анализу и машинному "
        "переводу. В практической части реализована модульная архитектура, включающая "
        "загрузку документов, построение структуры страниц, постобработку блоков, "
        "формирование Markdown и веб-интерфейс пользователя.",
    )
    add_plain(doc, "Пояснительная записка содержит:")
    add_bullets(doc, ["разделы с анализом предметной области;", "описание проектирования и реализации;", "таблицы, рисунки и список источников."])

    add_struct_heading(doc, "Abstract")
    add_body(
        doc,
        "The graduation thesis is devoted to the development of software for intelligent "
        "document processing, conversion of document content into Markdown format, and "
        "automated translation of the resulting Markdown. The system is intended to reduce "
        "manual effort, preserve document structure, and improve reproducibility of document "
        "processing results.",
    )


def add_contents(doc: Document) -> None:
    add_struct_heading(doc, "Содержание")
    items = [
        ("УСЛОВНЫЕ ОБОЗНАЧЕНИЯ", "6"),
        ("ВВЕДЕНИЕ", "7"),
        ("1 АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ", "10"),
        ("1.1 Характеристика задачи обработки документов", "10"),
        ("1.2 Анализ существующих решений", "13"),
        ("1.3 Постановка задачи автоматизации", "16"),
        ("2 ВЫБОР СРЕДСТВ РАЗРАБОТКИ", "19"),
        ("2.1 Выбор языка программирования и среды", "19"),
        ("2.2 Выбор технологий OCR, разметки и перевода", "22"),
        ("2.3 Обоснование архитектуры веб-приложения", "25"),
        ("3 ПРОЕКТИРОВАНИЕ И РЕАЛИЗАЦИЯ СИСТЕМЫ", "28"),
        ("3.1 Архитектура программного конвейера", "28"),
        ("3.2 Реализация веб-интерфейса", "32"),
        ("3.3 Тестирование и код-ревью", "35"),
        ("ЗАКЛЮЧЕНИЕ", "39"),
        ("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "41"),
    ]
    for title, page in items:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.5
        p.add_run(title)
        p.add_run("." * max(5, 88 - len(title)))
        p.add_run(page)


def add_abbreviations(doc: Document) -> None:
    add_struct_heading(doc, "Условные обозначения")
    terms = [
        ("API", "программный интерфейс приложения"),
        ("CLI", "интерфейс командной строки"),
        ("OCR", "оптическое распознавание символов"),
        ("LLM", "большая языковая модель"),
        ("Markdown", "облегченный язык разметки текстовых документов"),
        ("PDF", "формат электронных документов Portable Document Format"),
        ("UI", "пользовательский интерфейс"),
        ("ВКР", "выпускная квалификационная работа"),
    ]
    for key, desc in terms:
        add_plain(doc, f"{key} – {desc}.")


def add_intro(doc: Document) -> None:
    add_struct_heading(doc, "Введение")
    paragraphs = [
        "В современных информационных системах значительная часть данных хранится и передается в виде документов: PDF-файлов, изображений, офисных документов, таблиц, презентаций и HTML-страниц. Такие материалы часто содержат не только обычный текст, но и заголовки, таблицы, списки, формулы, изображения, ссылки и другие элементы структуры.",
        "При ручной обработке подобных документов пользователь вынужден отдельно извлекать текст, восстанавливать порядок чтения, исправлять ошибки распознавания, переносить содержимое в нужный формат и выполнять перевод. Этот процесс требует времени, зависит от квалификации исполнителя и плохо масштабируется при большом количестве документов.",
        "Особенно актуальной является задача преобразования документов в формат Markdown. Markdown широко используется в технической документации, системах контроля версий, базах знаний, статических сайтах, инструментах анализа текста и RAG-сценариях. Однако простое извлечение текста из PDF не решает задачу, поскольку часто теряются заголовки, таблицы, списки, формулы и связи между блоками.",
        "Актуальность темы обусловлена ростом количества цифровых документов и необходимостью автоматизировать их подготовку к использованию в современных информационных системах. Разработка программного обеспечения для интеллектуальной обработки и автоматизированного перевода документов позволяет сократить ручные трудозатраты, повысить повторяемость результата и ускорить подготовку технических материалов.",
        "Целью выпускной квалификационной работы является разработка программной системы, обеспечивающей интеллектуальную обработку документов, преобразование их содержимого в формат Markdown и автоматизированный перевод полученного результата с сохранением структуры.",
    ]
    for paragraph in paragraphs:
        add_body(doc, paragraph)
    add_body(doc, "Для достижения цели необходимо решить следующие задачи:")
    add_bullets(
        doc,
        [
            "проанализировать предметную область и существующие подходы к обработке документов;",
            "определить требования к системе преобразования документов в Markdown;",
            "выбрать средства разработки и библиотеки для OCR, анализа структуры, рендеринга и перевода;",
            "спроектировать архитектуру программной системы;",
            "реализовать конвейер обработки документов и пользовательский интерфейс;",
            "провести тестирование и оценить качество работы разработанного решения.",
        ],
    )
    add_body(doc, "Объектом исследования является процесс обработки и перевода цифровых документов.")
    add_body(doc, "Предметом исследования являются методы и программные средства извлечения структуры документа, преобразования содержимого в Markdown и автоматизированного перевода с использованием языковых моделей.")


def add_chapter_1(doc: Document) -> None:
    add_chapter(doc, "1 Анализ предметной области")
    add_subheading(doc, "1.1 Характеристика задачи обработки документов")
    for paragraph in [
        "Документы, используемые в учебной, инженерной и производственной деятельности, имеют сложную структуру. Даже если файл визуально выглядит как обычный текст, он может содержать несколько колонок, подписи к рисункам, таблицы, математические формулы, сноски, заголовки разных уровней и повторяющиеся элементы страниц.",
        "При переносе такого документа в другой формат важно сохранить не только текст, но и его логическую организацию. Для технической документации это особенно существенно: потеря заголовков, таблиц или формул снижает пригодность документа для дальнейшего использования.",
        "Ручной подход включает открытие документа, копирование текста, исправление ошибок, восстановление заголовков, перенос таблиц, ручное форматирование Markdown и последующий перевод. Такой процесс становится неэффективным при большом объеме материалов.",
        "Автоматизированная система должна получать файл на вход, определять тип документа, извлекать содержимое, анализировать структуру страниц, формировать внутреннее представление документа, преобразовывать его в целевой формат и при необходимости выполнять перевод.",
    ]:
        add_body(doc, paragraph)
    add_caption(doc, "Рисунок 1 – Обобщенная схема обработки документа")
    add_plain(doc, "Исходный документ → анализ структуры → нормализация блоков → Markdown → перевод → итоговый файл")

    add_subheading(doc, "1.2 Анализ существующих решений")
    for paragraph in [
        "Существующие инструменты можно разделить на OCR-системы, конвертеры PDF в текст или Markdown, онлайн-переводчики, LLM-сервисы и офисные редакторы с возможностями экспорта. Каждая группа решает только часть задачи.",
        "OCR-система может распознать символы, но не всегда корректно восстанавливает структуру документа. Конвертеры PDF часто хорошо работают с простыми текстовыми документами, но хуже справляются с таблицами, формулами и многоколоночной версткой.",
        "Переводчики способны перевести текст, но при прямом переводе Markdown могут повредить разметку, изменить кодовые блоки, ссылки или математические выражения. Поэтому требуется конвейер, где перевод выполняется после структурной обработки и формирования Markdown.",
    ]:
        add_body(doc, paragraph)
    add_table(
        doc,
        ["Группа решений", "Преимущества", "Ограничения"],
        [
            ["OCR-системы", "Распознают текст на изображениях", "Не гарантируют восстановление структуры"],
            ["PDF-конвертеры", "Быстро извлекают текст", "Теряют сложную верстку и таблицы"],
            ["LLM-переводчики", "Хорошо работают с техническим текстом", "Могут повредить Markdown-разметку"],
            ["Офисные редакторы", "Удобны для ручной правки", "Плохо подходят для массовой обработки"],
        ],
        "Таблица 1 – Сравнение существующих подходов к обработке документов",
    )

    add_subheading(doc, "1.3 Постановка задачи автоматизации")
    for paragraph in [
        "Разрабатываемая система должна обеспечивать обработку документов с сохранением их смысловой структуры. На вход система получает документ, после чего выполняет его анализ и преобразование в Markdown. При необходимости полученный Markdown передается в модуль автоматизированного перевода.",
        "К функциональным требованиям относятся загрузка документов через командную строку, API и веб-интерфейс; поддержка PDF и расширяемость для других форматов; извлечение текстовых блоков и структуры страниц; формирование результата в Markdown, HTML, JSON или chunks; выбор диапазона страниц; режим обработки всего документа; возможность отключения OCR или принудительного распознавания; автоматизированный перевод Markdown.",
        "Нефункциональные требования включают модульность архитектуры, возможность расширения отдельных этапов конвейера, воспроизводимость результата, понятный пользовательский интерфейс и наличие базовых тестов.",
    ]:
        add_body(doc, paragraph)


def add_chapter_2(doc: Document) -> None:
    add_chapter(doc, "2 Выбор средств разработки")
    add_subheading(doc, "2.1 Выбор языка программирования и среды")
    for paragraph in [
        "В качестве основного языка разработки выбран Python. Данный язык обладает развитой экосистемой библиотек для обработки документов, машинного обучения, OCR, веб-разработки и интеграции с внешними сервисами.",
        "Для управления зависимостями используется Poetry. Проект содержит файл pyproject.toml, в котором описаны основные и дополнительные зависимости. Для воспроизводимости окружения создано виртуальное окружение на Python 3.12.",
        "Использование Python также упрощает интеграцию с библиотеками Surya OCR/Layout, pdftext, markdownify, FastAPI, pydantic и клиентами LLM-сервисов.",
    ]:
        add_body(doc, paragraph)

    add_subheading(doc, "2.2 Выбор технологий OCR, разметки и перевода")
    for paragraph in [
        "Для анализа структуры страниц используется Surya OCR/Layout. Библиотека позволяет распознавать layout документа, выделять текстовые блоки и выполнять OCR для изображений и сканированных материалов.",
        "Для извлечения текстового слоя из PDF применяется pdftext. При наличии встроенного текста это позволяет ускорить обработку и не выполнять лишнее распознавание. Для преобразования HTML-представления в Markdown используется markdownify.",
        "Для автоматизированного перевода используется сервисный слой, поддерживающий Ollama, OpenAI-совместимые сервисы и Azure OpenAI. В текущей версии основной демонстрационный сценарий ориентирован на локальный Ollama, что позволяет запускать перевод без передачи данных во внешние облачные сервисы.",
    ]:
        add_body(doc, paragraph)
    add_table(
        doc,
        ["Компонент", "Назначение"],
        [
            ["Surya OCR/Layout", "Распознавание структуры страниц и OCR"],
            ["pdftext", "Извлечение встроенного текстового слоя PDF"],
            ["markdownify", "Преобразование HTML в Markdown"],
            ["FastAPI", "Реализация API и веб-интерфейса"],
            ["pydantic", "Описание структур данных и параметров"],
            ["Ollama", "Локальный запуск LLM для перевода"],
        ],
        "Таблица 2 – Используемые технологии и их назначение",
    )

    add_subheading(doc, "2.3 Обоснование архитектуры веб-приложения")
    for paragraph in [
        "Первоначально система могла использоваться через CLI, однако для демонстрации и практического применения был разработан веб-интерфейс. Такой подход повышает удобство пользователя, так как не требует знания командной строки.",
        "Веб-интерфейс реализован поверх существующего FastAPI-сервера. Пользователь может загрузить документ, выбрать диапазон страниц, включить режим сканирования всего документа, настроить OCR, выбрать формат результата и при необходимости включить перевод.",
        "Для длительной обработки добавлен индикатор прогресса. Он отражает этапы выполнения запроса и улучшает пользовательский опыт, поскольку пользователь видит, что система продолжает работать.",
    ]:
        add_body(doc, paragraph)


def add_chapter_3(doc: Document) -> None:
    add_chapter(doc, "3 Проектирование и реализация системы")
    add_subheading(doc, "3.1 Архитектура программного конвейера")
    for paragraph in [
        "Архитектура проекта построена как последовательность независимых этапов: providers, builders, processors, renderers и translation. Каждый этап решает отдельную задачу и передает результат следующему компоненту.",
        "Модуль providers отвечает за загрузку и унификацию входных форматов. Модули builders формируют представление страниц, строк и OCR-результатов. Модули processors выполняют постобработку: уточняют порядок чтения, объединяют строки, обрабатывают списки, таблицы, заголовки и специальные блоки.",
        "Модули renderers преобразуют внутреннее представление документа в Markdown, HTML, JSON или chunks. Модуль translation выполняет перевод Markdown с разбиением на фрагменты, проверкой результата и постобработкой.",
    ]:
        add_body(doc, paragraph)
    add_caption(doc, "Рисунок 2 – Архитектура программного конвейера ai-translator")
    add_plain(doc, "providers → builders → processors → renderers → translation")

    add_subheading(doc, "3.2 Реализация веб-интерфейса")
    for paragraph in [
        "В рамках доработки проекта был реализован пользовательский веб-интерфейс по адресу /ui. Интерфейс позволяет загрузить документ, выбрать формат результата, указать диапазон страниц, включить сканирование всего документа, настроить OCR и включить перевод.",
        "Для предотвращения случайной долгой обработки весь документ сканируется только при установленной пользователем галочке. Если диапазон страниц не указан и режим полного сканирования отключен, система по умолчанию обрабатывает первую страницу.",
        "Загрузка файлов выполняется во временный файл, который удаляется после завершения запроса. Это снижает риск накопления временных данных и исключает использование исходного имени файла как пути сохранения.",
    ]:
        add_body(doc, paragraph)

    add_subheading(doc, "3.3 Код-ревью и устранение рисков зависания")
    for paragraph in [
        "В ходе код-ревью были выявлены риски, которые могли ухудшать стабильность пользовательского сценария. Во-первых, общий словарь моделей использовался напрямую и мог изменяться при создании LLM-сервиса. Для уменьшения риска конфликтов при обработке запросов теперь используется копия словаря артефактов на каждый запрос.",
        "Во-вторых, пустой диапазон страниц ранее мог приводить к обработке всего документа без явного подтверждения пользователя. Теперь добавлен отдельный параметр scan_full_document, а при его отсутствии пустой диапазон заменяется на первую страницу.",
        "В-третьих, конфликтующие параметры OCR нормализуются: при принудительном OCR отключение OCR автоматически снимается. Это делает поведение системы более предсказуемым.",
        "Также добавлены smoke-тесты для конфигурации, переводчика и пользовательского интерфейса. Наличие базовых тестов позволяет быстрее обнаруживать регрессии при дальнейшей разработке.",
    ]:
        add_body(doc, paragraph)
    add_table(
        doc,
        ["Проблема", "Решение"],
        [
            ["Случайная обработка всего документа", "Добавлена галочка scan_full_document и дефолтная обработка первой страницы"],
            ["Общий изменяемый словарь моделей", "Используется копия artifact_dict на каждый запрос"],
            ["Конфликт OCR-параметров", "Параметры нормализуются перед запуском конвертера"],
            ["Отсутствие базовых проверок", "Добавлены smoke-тесты pytest"],
        ],
        "Таблица 3 – Результаты код-ревью и доработок",
    )


def add_conclusion_and_sources(doc: Document) -> None:
    add_struct_heading(doc, "Заключение")
    for paragraph in [
        "В ходе выполнения выпускной квалификационной работы начата разработка программной системы для интеллектуальной обработки документов, преобразования их содержимого в формат Markdown и автоматизированного перевода. Проведен анализ предметной области, определены основные проблемы ручной обработки документов и сформулированы требования к системе.",
        "В практической части подготовлена архитектура конвейера обработки документов, проверена работоспособность CLI-сценария, реализован веб-интерфейс пользователя, добавлен режим сканирования всего документа, индикатор прогресса и базовые smoke-тесты. Также проведено код-ревью серверной части и устранены риски, способные приводить к долгой или непредсказуемой обработке.",
        "Дальнейшее развитие работы предполагает расширение экспериментальной части, добавление измеримых метрик качества Markdown и перевода, подготовку набора тестовых документов и оформление экономического раздела.",
    ]:
        add_body(doc, paragraph)

    add_struct_heading(doc, "Список использованных источников")
    sources = [
        "ГОСТ 7.32-2001. Система стандартов по информации, библиотечному и издательскому делу. Отчет о научно-исследовательской работе. Структура и правила оформления.",
        "ГОСТ 2.105-95. Единая система конструкторской документации. Общие требования к текстовым документам.",
        "Регламент оформления выпускных квалификационных работ ВлГУ.",
        "Документация Python. URL: https://docs.python.org/",
        "Документация FastAPI. URL: https://fastapi.tiangolo.com/",
        "Документация Markdown. URL: https://www.markdownguide.org/",
        "Документация Poetry. URL: https://python-poetry.org/docs/",
        "Документация pydantic. URL: https://docs.pydantic.dev/",
        "Surya OCR project documentation. URL: https://github.com/VikParuchuri/surya",
        "OpenAI API documentation. URL: https://platform.openai.com/docs",
    ]
    for index, source in enumerate(sources, start=1):
        add_plain(doc, f"{index}. {source}")


def build_main_docx() -> None:
    doc = setup_doc()
    add_title_page(doc)
    add_assignment(doc)
    add_annotation(doc)
    add_contents(doc)
    add_abbreviations(doc)
    add_intro(doc)
    add_chapter_1(doc)
    add_chapter_2(doc)
    add_chapter_3(doc)
    add_conclusion_and_sources(doc)
    doc.save(MAIN_DOCX)


def build_review_docx() -> None:
    doc = setup_doc()
    add_center(doc, "Отчет по код-ревью и доработкам проекта ai-translator", True)
    add_plain(doc, "Студент: Петренко Иван Андреевич")
    add_plain(doc, "Группа: ПИ-122")
    add_plain(doc, "Дата: 06.05.2026")
    add_chapter(doc, "1 Выполненные исправления")
    add_bullets(
        doc,
        [
            "добавлена галочка «сканировать весь документ» в веб-интерфейс;",
            "добавлен визуальный индикатор прогресса обработки;",
            "добавлена нормализация диапазона страниц для предотвращения случайной долгой обработки;",
            "исключено изменение общего словаря моделей при обработке запроса;",
            "исправлена логика выбора LLM-сервиса для перевода;",
            "добавлены smoke-тесты для конфигурации, перевода и UI.",
        ],
    )
    add_chapter(doc, "2 Рекомендации по дальнейшему улучшению")
    add_bullets(
        doc,
        [
            "реализовать настоящую серверную очередь задач с polling-прогрессом;",
            "добавить ограничение максимального размера загружаемого файла;",
            "добавить журналирование ошибок конвертации в отдельный файл;",
            "расширить набор тестовых документов и метрик качества;",
            "добавить сохранение истории обработанных документов для демонстрации.",
        ],
    )
    doc.save(REVIEW_DOCX)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_main_docx()
    build_review_docx()
    print(MAIN_DOCX)
    print(REVIEW_DOCX)


if __name__ == "__main__":
    main()
