# AI Translator

Программная система для интеллектуальной обработки документов, преобразования их
в Markdown и последующего автоматизированного перевода с использованием LLM.

Проект используется как практическая часть выпускной квалификационной работы по
теме: «Разработка программного обеспечения для интеллектуальной обработки и
автоматизированного перевода документов в формат Markdown».

## Возможности

- Извлечение содержимого из PDF и других документных форматов.
- Распознавание структуры страниц: заголовки, текстовые блоки, таблицы, списки,
  формулы, изображения.
- Преобразование результата в Markdown, HTML, JSON или chunks.
- Пакетная и одиночная обработка документов через CLI.
- Серверный режим через FastAPI.
- Автоматизированный перевод Markdown через LLM-сервис.

## Архитектура

Основной конвейер обработки:

```text
providers -> builders -> processors -> renderers -> translation
```

- `providers` загружают входные документы и приводят их к единому интерфейсу.
- `builders` строят layout, строки и OCR-представление документа.
- `processors` нормализуют структуру, порядок чтения, таблицы, списки, формулы и
  другие блоки.
- `renderers` формируют итоговый Markdown, HTML, JSON или chunks.
- `translation` выполняет перевод Markdown с разбиением на фрагменты и
  постобработкой результата.

## Установка

Рекомендуемая версия Python: 3.10-3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install poetry
.\.venv\Scripts\poetry.exe install
```

Для работы OCR и моделей может потребоваться установка версии PyTorch,
подходящей под вашу CUDA или CPU-конфигурацию.

## Примеры запуска

Конвертация одного PDF в Markdown:

```powershell
.\.venv\Scripts\python.exe convert_single.py 2601.00100v1.pdf --output_format markdown --output_dir out
```

Конвертация с переводом через локальный Ollama:

```powershell
.\.venv\Scripts\python.exe convert_single.py 2601.00100v1.pdf `
  --output_format markdown `
  --use_llm_translation `
  --llm_service src.services.ollama.OllamaService `
  --ollama_base_url http://localhost:11434 `
  --ollama_model llama3.2 `
  --translate Russian `
  --output_dir out
```

Запуск API:

```powershell
.\.venv\Scripts\python.exe server.py --host 127.0.0.1 --port 8000
```

После запуска документация API доступна по адресу:

```text
http://127.0.0.1:8000/docs
```

## Практическая ценность

Система снижает ручные трудозатраты на обработку и перевод технических
документов, помогает сохранять структуру исходных материалов и ускоряет
подготовку Markdown-документации для дальнейшей публикации, анализа или
использования в инженерных процессах.
