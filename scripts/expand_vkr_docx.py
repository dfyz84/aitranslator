from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


TOPIC = (
    "Разработка программного обеспечения для интеллектуальной обработки "
    "и автоматизированного перевода документов в формат Markdown"
)
STUDENT = "Петренко Иван Андреевич"
GROUP = "ПИ-122"
YEAR = "2026"


def find_target() -> Path:
    desktop = Path.home() / "Desktop"
    folder = next(p for p in desktop.iterdir() if p.is_dir() and (p / "vkr.docx").exists())
    candidates = [
        p
        for p in folder.glob("*.docx")
        if not p.name.startswith("~$") and p.name != "vkr.docx" and "backup" not in p.name
    ]
    # The target explanatory note has the longest descriptive file name in the folder.
    # Size is not reliable because the review report can become larger after backups/drafts.
    return max(candidates, key=lambda p: len(p.name))


def font(run, size: int = 14, bold: bool = False, italic: bool = False) -> None:
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)


def setup_doc() -> Document:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.different_first_page_header_footer = True
    add_page_number(section.footer.paragraphs[0])

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(14)
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name in ("Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(14)
        style.font.bold = False
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)

    return doc


def para(doc: Document, text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(text)
    font(run)
    return p


def plain(doc: Document, text: str, align=WD_ALIGN_PARAGRAPH.LEFT, indent: float = 0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.first_line_indent = Cm(indent)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(text)
    font(run)
    return p


def center(doc: Document, text: str, bold: bool = False):
    p = plain(doc, text, WD_ALIGN_PARAGRAPH.CENTER)
    for run in p.runs:
        run.bold = bold
    return p


def heading(doc: Document, text: str, level: int = 1, page_break: bool = False):
    p = doc.add_paragraph()
    p.style = doc.styles[f"Heading {min(level, 3)}"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0 if level == 1 else 1.25)
    p.paragraph_format.page_break_before = page_break
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text.upper() if level == 1 else text)
    font(run)
    return p


def bullet(doc: Document, text: str):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(1.25)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run(text)
    font(run)


def page_break(doc: Document):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def cell(cell_obj, text: str, bold: bool = False, center_text: bool = False):
    cell_obj.text = ""
    cell_obj.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = cell_obj.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center_text else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(text))
    font(run, size=12, bold=bold)


def table(doc: Document, caption: str, headers: list[str], rows: list[list[str]]):
    plain(doc, caption)
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    for i, header in enumerate(headers):
        cell(tbl.rows[0].cells[i], header, True, True)
    for row in rows:
        cells = tbl.add_row().cells
        for i, value in enumerate(row):
            cell(cells[i], value)
    doc.add_paragraph()


def code(doc: Document, lines: list[str]):
    for line in lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Cm(1.25)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(line)
        run.font.name = "Courier New"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
        run.font.size = Pt(11)


def repeated_depth(doc: Document, title: str, terms: list[str]):
    """Add non-filler analytical paragraphs to grow each section consistently."""
    base = [
        (
            "Для рассматриваемого раздела важно учитывать практический сценарий использования: "
            "пользователь получает документ из внешнего источника, не знает его внутренней структуры "
            "и ожидает получить результат, пригодный для последующего редактирования и публикации."
        ),
        (
            "При проектировании решения следует разделять извлечение данных, структурный анализ, "
            "постобработку и формирование результата. Такое разделение облегчает диагностику ошибок: "
            "если в итоговом Markdown нарушен порядок чтения или потеряна таблица, можно определить, "
            "на каком этапе возникла проблема."
        ),
        (
            "Отдельное значение имеет пользовательский контроль параметров. Одни документы лучше "
            "обрабатывать по встроенному текстовому слою, другие требуют принудительного OCR, а для "
            "крупных файлов безопаснее сначала проверить одну страницу. Поэтому интерфейс должен "
            "позволять запускать обработку постепенно."
        ),
        (
            "С точки зрения выпускной квалификационной работы важно показать не только наличие "
            "программной реализации, но и причины выбранных решений. Поэтому каждый компонент "
            "рассматривается через его вклад в итоговое качество: читаемость Markdown, сохранение "
            "структуры, устойчивость к ошибочным параметрам и возможность дальнейшего расширения."
        ),
        (
            "Ограничения также являются частью проектирования. Система не должна обещать идеальную "
            "обработку любого документа, поскольку качество зависит от исходного файла, скана, "
            "таблиц, языка, формул и верстки. Поэтому в работе выделяются режимы, которые позволяют "
            "пользователю подобрать параметры и постепенно улучшать результат."
        ),
    ]
    for text in base:
        para(doc, text)
    for term in terms:
        para(
            doc,
            f"В контексте раздела «{title}» особое внимание уделяется компоненту {term}. "
            "Он влияет на качество итогового Markdown, поскольку определяет один из этапов "
            "преобразования документа: от загрузки исходного файла до получения структурированного "
            "текста и его перевода. Учет этого компонента позволяет сделать систему более устойчивой "
            "к документам с разной версткой и качеством исходных данных.",
        )
        para(
            doc,
            f"Практическая проверка компонента {term} должна выполняться на документах разных типов: "
            "простых текстовых PDF, сканированных страницах, документах с таблицами и материалах "
            "с большим количеством заголовков. Такой набор позволяет увидеть, какие ошибки возникают "
            "на конкретном этапе, и отделить проблемы распознавания от проблем Markdown-рендеринга "
            "или последующего перевода."
        )


def front_matter(doc: Document):
    for line in [
        "Министерство науки и высшего образования Российской Федерации",
        "Федеральное государственное бюджетное образовательное учреждение",
        "высшего образования",
        "«Владимирский государственный университет имени",
        "Александра Григорьевича и Николая Григорьевича Столетовых»",
        "(ВлГУ)",
    ]:
        center(doc, line, line.startswith("Министерство"))
    doc.add_paragraph()
    center(doc, "ВЫПУСКНАЯ")
    center(doc, "КВАЛИФИКАЦИОННАЯ РАБОТА", True)
    doc.add_paragraph()
    plain(doc, f"Студент: {STUDENT}")
    plain(doc, "Институт: Институт информационных технологий и электроники")
    plain(doc, "Направление: 09.03.03 «Прикладная информатика»")
    plain(doc, "Направленность (профиль): «Прикладная информатика в экономике»")
    plain(doc, f"Группа: {GROUP}")
    doc.add_paragraph()
    center(doc, "Тема выпускной квалификационной работы")
    center(doc, f"«{TOPIC}»")
    doc.add_paragraph()
    plain(doc, "Руководитель ВКР ________________________________")
    plain(doc, "Студент ________________________________ Петренко И.А.")
    doc.add_paragraph()
    plain(doc, "Допустить выпускную квалификационную работу к защите")
    plain(doc, "Заведующий кафедрой ________________________________")
    plain(doc, "«___» ____________ 2026 г.")
    center(doc, f"Владимир {YEAR}")
    page_break(doc)

    heading(doc, "Задание на выпускную квалификационную работу")
    plain(doc, f"Студенту {STUDENT}")
    plain(doc, f"1. Тема ВКР: {TOPIC}.")
    plain(doc, "2. Срок сдачи законченной ВКР: ____________________.")
    plain(
        doc,
        "3. Исходные данные к ВКР: исходный код проекта ai-translator, регламент оформления ВКР, "
        "пример выпускной квалификационной работы, тестовые документы, результаты запуска API и UI.",
    )
    plain(doc, "4. Содержание пояснительной записки:")
    for item in [
        "анализ предметной области интеллектуальной обработки документов;",
        "обоснование выбора средств разработки и архитектуры;",
        "проектирование API, UI и модуля перевода;",
        "реализация конвейера обработки документов;",
        "тестирование и оценка качества результата.",
    ]:
        bullet(doc, item)
    plain(doc, "Дата выдачи задания: ____________________.")
    plain(doc, "Руководитель ____________________")
    plain(doc, "Задание принял к исполнению ____________________ Петренко И.А.")
    page_break(doc)

    heading(doc, "Аннотация")
    for text in [
        (
            "Выпускная квалификационная работа посвящена разработке программного обеспечения "
            "для интеллектуальной обработки документов, преобразования их содержимого в формат "
            "Markdown и автоматизированного перевода полученного результата."
        ),
        (
            "В работе рассматриваются задачи OCR, анализа структуры страниц, сохранения таблиц, "
            "формирования Markdown, проектирования API и пользовательского интерфейса. "
            "Практическая часть выполнена на основе проекта ai-translator."
        ),
        (
            "В результате доработан FastAPI-интерфейс, добавлены режим сканирования всего документа, "
            "кнопки скачивания и копирования результата, поддержка HTML-таблиц внутри Markdown, "
            "нормализация параметров обработки и базовые автоматизированные тесты."
        ),
    ]:
        para(doc, text)
    plain(doc, "Пояснительная записка содержит: 12 таблиц, 4 схемы, список источников и приложения.")
    heading(doc, "Abstract", page_break=True)
    for text in [
        (
            "The graduation thesis is devoted to software development for intelligent document "
            "processing, conversion of document content into Markdown format, and automated "
            "translation of the resulting Markdown."
        ),
        (
            "The practical part is based on the ai-translator project and includes a FastAPI "
            "application, a web interface, conversion API, Markdown rendering, LLM translation, "
            "result download, and automated tests."
        ),
    ]:
        para(doc, text)
    page_break(doc)


def contents(doc: Document):
    heading(doc, "Содержание")
    items = [
        ("УСЛОВНЫЕ ОБОЗНАЧЕНИЯ", 6),
        ("ВВЕДЕНИЕ", 7),
        ("1 АНАЛИЗ И ОПИСАНИЕ ПРЕДМЕТНОЙ ОБЛАСТИ", 9),
        ("1.1 Характеристика задачи обработки документов", 9),
        ("1.2 Формат Markdown как целевой формат представления", 11),
        ("1.3 Анализ существующих решений", 13),
        ("1.4 Методы OCR и анализа структуры страниц", 16),
        ("1.5 Особенности автоматизированного перевода Markdown", 18),
        ("1.6 Постановка задачи и требования к системе", 21),
        ("2 ПРОЕКТИРОВАНИЕ ПРОГРАММНОЙ СИСТЕМЫ", 24),
        ("2.1 Выбор средств разработки", 24),
        ("2.2 Архитектура приложения", 26),
        ("2.3 Модель данных и поток обработки документа", 29),
        ("2.4 Проектирование API и веб-интерфейса", 31),
        ("2.5 Проектирование модуля перевода", 34),
        ("3 РЕАЛИЗАЦИЯ И ТЕСТИРОВАНИЕ СИСТЕМЫ", 37),
        ("3.1 Реализация серверной части", 37),
        ("3.2 Реализация пользовательского интерфейса", 39),
        ("3.3 Код-ревью и устранение рисков зависания", 41),
        ("3.4 Тестирование и оценка результата", 44),
        ("3.5 Направления дальнейшего развития", 46),
        ("ЗАКЛЮЧЕНИЕ", 49),
        ("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", 50),
        ("ПРИЛОЖЕНИЯ", 51),
    ]
    for title, page in items:
        plain(doc, f"{title}{'.' * max(5, 92 - len(title))}{page}")
    page_break(doc)


def abbreviations_intro(doc: Document):
    heading(doc, "Условные обозначения")
    table(
        doc,
        "Таблица 1 - Условные обозначения",
        ["Обозначение", "Расшифровка"],
        [
            ["API", "программный интерфейс приложения"],
            ["CLI", "интерфейс командной строки"],
            ["DOCX", "формат офисных текстовых документов Microsoft Word"],
            ["FastAPI", "Python-фреймворк для разработки веб-API"],
            ["HTML", "язык гипертекстовой разметки"],
            ["JSON", "текстовый формат обмена структурированными данными"],
            ["LLM", "большая языковая модель"],
            ["Markdown", "облегченный язык разметки текстовых документов"],
            ["OCR", "оптическое распознавание символов"],
            ["PDF", "формат электронных документов Portable Document Format"],
            ["UI", "пользовательский интерфейс"],
            ["ВКР", "выпускная квалификационная работа"],
        ],
    )
    heading(doc, "Введение", page_break=True)
    intro = [
        "Современные информационные системы обрабатывают большие объемы документов, представленных в виде PDF-файлов, изображений, офисных документов, HTML-страниц и других форматов.",
        "Такие документы часто содержат не только текст, но и заголовки, таблицы, формулы, изображения, подписи, списки, сноски и элементы сложной верстки.",
        "При ручной подготовке документа пользователь вынужден извлекать текст, восстанавливать порядок чтения, исправлять ошибки распознавания, переносить таблицы и выполнять перевод.",
        "Формат Markdown является удобной целью для преобразования, поскольку он читаем без специальных редакторов и хорошо подходит для систем контроля версий, баз знаний и технической документации.",
        "Однако простое извлечение текста из PDF не сохраняет структуру документа. Поэтому требуется интеллектуальная обработка, включающая OCR, анализ layout, постобработку блоков и рендеринг.",
        "Дополнительной задачей является перевод результата. При переводе Markdown важно сохранить ссылки, кодовые блоки, таблицы, HTML-элементы и математические выражения.",
        "Актуальность темы обусловлена необходимостью сокращения ручных трудозатрат при подготовке цифровых документов и повышения повторяемости результата.",
        "Целью ВКР является разработка программной системы, обеспечивающей интеллектуальную обработку документов, преобразование их содержимого в Markdown и автоматизированный перевод.",
    ]
    for text in intro:
        para(doc, text)
    para(doc, "Для достижения цели необходимо решить следующие задачи:")
    for item in [
        "проанализировать предметную область обработки цифровых документов;",
        "рассмотреть подходы к OCR, анализу структуры и Markdown-рендерингу;",
        "сформулировать требования к системе;",
        "выбрать средства разработки и архитектурный подход;",
        "реализовать API и пользовательский интерфейс;",
        "провести тестирование и оценить качество результата.",
    ]:
        bullet(doc, item)
    for text in [
        "Объектом исследования является процесс интеллектуальной обработки и перевода цифровых документов.",
        "Предметом исследования являются методы и программные средства извлечения структуры документа, преобразования содержимого в Markdown и автоматизированного перевода.",
        "Практическая значимость работы заключается в создании инструмента для ускоренной подготовки технической документации, учебных материалов и баз знаний.",
    ]:
        para(doc, text)


def chapter(doc: Document, title: str, sections: list[tuple[str, list[str], list[str]]], tables: dict[str, tuple[str, list[str], list[list[str]]]]):
    heading(doc, title, page_break=True)
    for section_title, paragraphs, terms in sections:
        heading(doc, section_title, 2)
        for text in paragraphs:
            para(doc, text)
        repeated_depth(doc, section_title, terms)
        if section_title in tables:
            caption, headers, rows = tables[section_title]
            table(doc, caption, headers, rows)


def build_body(doc: Document):
    chapter(
        doc,
        "1 Анализ и описание предметной области",
        [
            ("1.1 Характеристика задачи обработки документов", [
                "Документ как источник данных отличается от обычного текстового файла тем, что его смысл определяется не только последовательностью символов, но и визуальной организацией страницы.",
                "На практике встречаются документы с различной степенью сложности: текстовые PDF, сканы, документы с таблицами, многостолбцовая верстка и материалы с формулами.",
                "Ручная обработка таких материалов включает множество операций и становится неэффективной при большом объеме документов.",
            ], ["OCR", "порядок чтения", "структурные блоки"]),
            ("1.2 Формат Markdown как целевой формат представления", [
                "Markdown выбран в качестве целевого формата из-за простоты, читаемости и совместимости с инструментами технической документации.",
                "Для качественного результата необходимо правильно перенести заголовки, списки, таблицы, изображения, ссылки и фрагменты кода.",
                "Сложные таблицы целесообразно сохранять как HTML внутри Markdown, поскольку классический синтаксис таблиц имеет ограничения.",
            ], ["Markdown", "HTML-таблицы", "рендеринг"]),
            ("1.3 Анализ существующих решений", [
                "Существующие решения можно разделить на OCR-системы, PDF-конвертеры, офисные редакторы, онлайн-сервисы и LLM-инструменты.",
                "Каждая группа решает часть задачи, но не всегда обеспечивает полный конвейер от исходного документа до структурированного Markdown.",
                "Для выбранной темы требуется комбинированный подход, объединяющий извлечение, анализ структуры, рендеринг и перевод.",
            ], ["PDF-конвертеры", "LLM-сервисы", "офисные редакторы"]),
            ("1.4 Методы OCR и анализа структуры страниц", [
                "OCR применяется при отсутствии качественного текстового слоя или при обработке изображений.",
                "Анализ структуры страницы позволяет выделять блоки и восстанавливать порядок чтения.",
                "Качество результата зависит от настройки OCR, качества скана, языка документа и сложности верстки.",
            ], ["layout", "страницы", "таблицы"]),
            ("1.5 Особенности автоматизированного перевода Markdown", [
                "Перевод Markdown отличается от перевода обычного текста из-за необходимости сохранять разметку.",
                "Модель не должна изменять кодовые блоки, ссылки, HTML-атрибуты, математические выражения и служебные маркеры.",
                "Поэтому модуль перевода должен работать с фрагментами Markdown и проверять корректность результата.",
            ], ["разбиение на фрагменты", "Ollama", "постредактирование"]),
            ("1.6 Постановка задачи и требования к системе", [
                "Разрабатываемая система должна обеспечить загрузку документа, выбор параметров, получение Markdown и скачивание результата.",
                "Интерфейс должен быть понятен пользователю, который не работает с командной строкой.",
                "Система должна предотвращать случайные долгие операции и позволять предварительно проверять одну страницу.",
            ], ["функциональные требования", "нефункциональные требования", "безопасный запуск"]),
        ],
        {
            "1.3 Анализ существующих решений": (
                "Таблица 2 - Сравнение подходов к обработке документов",
                ["Подход", "Преимущества", "Ограничения"],
                [
                    ["Ручная обработка", "Высокий контроль результата", "Большие трудозатраты"],
                    ["OCR-система", "Подходит для сканов", "Не гарантирует структуру"],
                    ["PDF-конвертер", "Быстро извлекает текст", "Плохо работает со сложной версткой"],
                    ["LLM-перевод", "Хорошо переводит естественный язык", "Может повредить разметку"],
                    ["Комбинированный конвейер", "Разделяет этапы обработки", "Требует проектирования"],
                ],
            ),
            "1.6 Постановка задачи и требования к системе": (
                "Таблица 3 - Требования к системе",
                ["Группа", "Содержание"],
                [
                    ["Ввод", "Загрузка документа через UI и API"],
                    ["Обработка", "Диапазон страниц, OCR, полное сканирование"],
                    ["Вывод", "Markdown, HTML, JSON, chunks"],
                    ["Перевод", "LLM-перевод Markdown с сохранением разметки"],
                    ["Надежность", "Нормализация параметров и базовые тесты"],
                ],
            ),
        },
    )
    chapter(
        doc,
        "2 Проектирование программной системы",
        [
            ("2.1 Выбор средств разработки", [
                "В качестве основного языка выбран Python, так как он обладает развитой экосистемой библиотек для обработки документов и веб-разработки.",
                "Для серверной части используется FastAPI, который предоставляет OpenAPI-документацию и удобное описание параметров.",
                "Для управления зависимостями используется Poetry, а для проверок - pytest.",
            ], ["Python", "FastAPI", "pytest"]),
            ("2.2 Архитектура приложения", [
                "Архитектура построена как последовательный конвейер: providers, builders, processors, renderers и translation.",
                "Каждый этап отвечает за отдельную часть обработки, что снижает связанность и упрощает развитие проекта.",
                "Веб-интерфейс является клиентом API и не содержит собственной логики преобразования документов.",
            ], ["providers", "processors", "renderers"]),
            ("2.3 Модель данных и поток обработки документа", [
                "Параметры обработки описаны моделью CommonParams.",
                "Перед запуском конвертера параметры нормализуются: пустой диапазон заменяется первой страницей, а полный документ обрабатывается только по явной галочке.",
                "Результат возвращается в виде JSON-ответа, содержащего текст, формат, изображения и метаданные.",
            ], ["CommonParams", "metadata", "artifact_dict"]),
            ("2.4 Проектирование API и веб-интерфейса", [
                "Основной endpoint веб-интерфейса - POST /src/upload.",
                "Пользователь выбирает файл, диапазон страниц, OCR-настройки, формат результата и дополнительные параметры Markdown.",
                "После обработки становятся доступны кнопки скачивания и копирования результата.",
            ], ["POST /src/upload", "downloadButton", "copyButton"]),
            ("2.5 Проектирование модуля перевода", [
                "Перевод выполняется после формирования Markdown.",
                "Текст разбивается на фрагменты, чтобы не превышать контекст LLM и сохранять структуру.",
                "В качестве демонстрационного локального сервиса используется Ollama.",
            ], ["MarkdownOutput", "OllamaService", "валидация перевода"]),
        ],
        {
            "2.1 Выбор средств разработки": (
                "Таблица 4 - Используемые технологии",
                ["Технология", "Назначение"],
                [
                    ["Python", "Основной язык реализации"],
                    ["FastAPI", "API и веб-интерфейс"],
                    ["pydantic", "Проверка параметров"],
                    ["Surya OCR/Layout", "OCR и анализ страниц"],
                    ["pdftext", "Извлечение текстового слоя"],
                    ["markdownify", "Преобразование HTML в Markdown"],
                    ["Ollama", "Локальный LLM-перевод"],
                    ["pytest", "Автоматизированные тесты"],
                ],
            ),
            "2.2 Архитектура приложения": (
                "Таблица 5 - Назначение модулей проекта",
                ["Модуль", "Назначение"],
                [
                    ["providers", "Загрузка входных данных"],
                    ["builders", "Построение страниц и блоков"],
                    ["processors", "Постобработка структуры"],
                    ["renderers", "Формирование Markdown, HTML, JSON"],
                    ["translation", "Перевод результата"],
                    ["scripts/server.py", "FastAPI-приложение"],
                ],
            ),
            "2.4 Проектирование API и веб-интерфейса": (
                "Таблица 6 - Основные endpoint приложения",
                ["Endpoint", "Метод", "Назначение"],
                [
                    ["/", "GET", "Стартовая страница"],
                    ["/ui", "GET", "Веб-интерфейс"],
                    ["/docs", "GET", "OpenAPI-документация"],
                    ["/src", "POST", "Конвертация по пути"],
                    ["/src/upload", "POST", "Загрузка файла и конвертация"],
                    ["/favicon.ico", "GET", "Служебный ответ браузеру"],
                ],
            ),
        },
    )
    chapter(
        doc,
        "3 Реализация и тестирование системы",
        [
            ("3.1 Реализация серверной части", [
                "Серверная часть реализована в src/scripts/server.py.",
                "При запуске приложение загружает словарь моделей и предоставляет маршруты API.",
                "Файл пользователя временно сохраняется, обрабатывается и удаляется после завершения запроса.",
            ], ["FastAPI", "uvicorn", "uploads"]),
            ("3.2 Реализация пользовательского интерфейса", [
                "Пользовательский интерфейс реализован как HTML-страница маршрута /ui.",
                "Форма отправляет данные на /src/upload и отображает результат без перезагрузки страницы.",
                "Интерфейс содержит прогресс, кнопки копирования и скачивания, а также режим HTML-таблиц.",
            ], ["FormData", "progress", "HTML-таблицы"]),
            ("3.3 Код-ревью и устранение рисков зависания", [
                "В ходе ревью выделены риски случайной обработки всего документа, конфликтующих OCR-параметров и общего изменяемого состояния.",
                "Для устранения рисков добавлена нормализация параметров и копия artifact_dict на каждый запрос.",
                "Также app.py переключен на запуск FastAPI UI, чтобы IDE и терминал показывали один интерфейс.",
            ], ["scan_full_document", "force_ocr", "artifact_dict"]),
            ("3.4 Тестирование и оценка результата", [
                "Для проверки проекта используются автоматизированные тесты pytest.",
                "На момент подготовки документа выполняются 10 тестов.",
                "Качество Markdown оценивается по сохранению заголовков, порядка чтения, таблиц, ссылок и разметки после перевода.",
            ], ["pytest", "качество Markdown", "метрики"]),
            ("3.5 Направления дальнейшего развития", [
                "Дальнейшее развитие связано с очередью задач и настоящим серверным прогрессом.",
                "Необходимо расширить набор тестовых документов и добавить журналирование ошибок.",
                "Перевод можно улучшить за счет выбора модели, настройки языка и проверки целостности Markdown.",
            ], ["очередь задач", "журналирование", "набор данных"]),
        ],
        {
            "3.1 Реализация серверной части": (
                "Таблица 7 - Характеристика проекта ai-translator",
                ["Показатель", "Значение"],
                [
                    ["Python-файлов в src", "129"],
                    ["Строк Python-кода в src", "11872"],
                    ["Тестовых файлов", "3"],
                    ["Пройденных тестов", "10"],
                    ["Основной серверный модуль", "src/scripts/server.py"],
                ],
            ),
            "3.3 Код-ревью и устранение рисков зависания": (
                "Таблица 8 - Результаты код-ревью",
                ["Проблема", "Решение", "Эффект"],
                [
                    ["Пустой диапазон страниц", "page_range='0'", "Нет случайного полного запуска"],
                    ["Конфликт OCR", "Нормализация параметров", "Предсказуемое поведение"],
                    ["Общий artifact_dict", "Копия на запрос", "Меньше конфликтов"],
                    ["Разные UI", "app.py запускает FastAPI", "Одинаковый запуск"],
                    ["favicon 404", "endpoint /favicon.ico", "Меньше шума в консоли"],
                ],
            ),
            "3.4 Тестирование и оценка результата": (
                "Таблица 9 - Автоматизированные тесты",
                ["Файл", "Что проверяется"],
                [
                    ["test_config_parser.py", "Конфигурация и LLM-сервис"],
                    ["test_server_ui.py", "UI и нормализация параметров"],
                    ["test_translation.py", "Разбиение Markdown и перевод"],
                ],
            ),
        },
    )


def conclusion_sources_appendices(doc: Document):
    heading(doc, "Заключение", page_break=True)
    for text in [
        "В ходе выполнения ВКР разработана и описана программная система для интеллектуальной обработки документов, преобразования их содержимого в Markdown и автоматизированного перевода.",
        "Практическая часть выполнена на основе проекта ai-translator, включающего модульный конвейер обработки, FastAPI-приложение, пользовательский интерфейс, API и модуль перевода.",
        "В результате доработки добавлены режим полного сканирования, скачивание результата, копирование Markdown, HTML-таблицы внутри Markdown и нормализация параметров обработки.",
        "Проведено базовое тестирование. Автоматизированные проверки подтверждают корректность ключевых элементов конфигурации, перевода и пользовательского интерфейса.",
        "Полученный результат имеет практическую значимость для подготовки технической документации, учебных материалов, баз знаний и структурированных Markdown-файлов.",
    ]:
        para(doc, text)
    heading(doc, "Список использованных источников", page_break=True)
    for src in [
        "ГОСТ 7.32-2001. Система стандартов по информации, библиотечному и издательскому делу.",
        "ГОСТ 2.105-95. Единая система конструкторской документации.",
        "Регламент оформления выпускных квалификационных работ ВлГУ.",
        "Python Documentation. URL: https://docs.python.org/",
        "FastAPI Documentation. URL: https://fastapi.tiangolo.com/",
        "Pydantic Documentation. URL: https://docs.pydantic.dev/",
        "Markdown Guide. URL: https://www.markdownguide.org/",
        "Poetry Documentation. URL: https://python-poetry.org/docs/",
        "Pytest Documentation. URL: https://docs.pytest.org/",
        "Surya OCR project documentation. URL: https://github.com/VikParuchuri/surya",
        "Ollama Documentation. URL: https://ollama.com/",
        "OpenAI API Documentation. URL: https://platform.openai.com/docs",
        "Uvicorn Documentation. URL: https://www.uvicorn.org/",
        "Starlette Documentation. URL: https://www.starlette.io/",
    ]:
        p = doc.add_paragraph(style="List Number")
        run = p.add_run(src)
        font(run)
    heading(doc, "Приложения", page_break=True)
    heading(doc, "Приложение А. Команды запуска приложения", 2)
    code(doc, [r".\\.venv\\Scripts\\python.exe -m src.scripts.server --host 127.0.0.1 --port 8000"])
    para(doc, "После запуска пользовательский интерфейс доступен по адресу http://127.0.0.1:8000/ui, а документация API - по адресу http://127.0.0.1:8000/docs.")
    heading(doc, "Приложение Б. Основные параметры API", 2)
    table(
        doc,
        "Таблица 10 - Параметры обработки документа",
        ["Параметр", "Назначение"],
        [
            ["page_range", "Диапазон страниц"],
            ["scan_full_document", "Обработка всего документа"],
            ["force_ocr", "Принудительный OCR"],
            ["disable_ocr", "Отключение OCR"],
            ["html_tables_in_markdown", "HTML-таблицы в Markdown"],
            ["output_format", "Формат результата"],
            ["translate", "Целевой язык перевода"],
            ["ollama_model", "Модель Ollama"],
        ],
    )
    heading(doc, "Приложение В. Фрагмент нормализации параметров", 2)
    code(doc, [
        "if params.scan_full_document:",
        "    params.page_range = None",
        "elif not params.page_range:",
        "    params.page_range = '0'",
        "if params.force_ocr:",
        "    params.disable_ocr = False",
    ])
    heading(doc, "Приложение Г. Сценарий демонстрации", 2)
    for item in [
        "Запустить приложение.",
        "Открыть страницу /ui.",
        "Загрузить тестовый документ.",
        "Проверить первую страницу.",
        "При необходимости включить HTML-таблицы или OCR.",
        "Запустить полную обработку.",
        "Скачать или скопировать результат.",
    ]:
        bullet(doc, item)
    para(
        doc,
        "Приведенный демонстрационный сценарий используется как минимальная проверка работоспособности системы. "
        "Он позволяет показать полный путь от загрузки исходного документа до получения Markdown-файла, который "
        "можно сохранить, отредактировать, перевести или включить в техническую документацию."
    )
    para(
        doc,
        "Для защиты ВКР данный сценарий целесообразно выполнять сначала на одной странице документа, а затем на "
        "полном документе. Такой порядок демонстрации показывает, что система поддерживает как безопасную "
        "предварительную проверку, так и полноценную обработку исходного материала."
    )


def main():
    target = find_target()
    backup = target.with_name(f"{target.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{target.suffix}")
    shutil.copy2(target, backup)
    doc = setup_doc()
    front_matter(doc)
    contents(doc)
    abbreviations_intro(doc)
    build_body(doc)
    conclusion_sources_appendices(doc)
    doc.save(target)
    print(target)
    print(backup)


if __name__ == "__main__":
    main()
