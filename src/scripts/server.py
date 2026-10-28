import base64
import asyncio
import io
import os
import sys
import tempfile
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Optional

import click
from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse, Response

from src.config.parser import ConfigParser
from src.converters.pdf import PdfConverter
from src.models import create_model_dict
from src.output import text_from_rendered
from src.settings import settings
from src.translation import translate_rendered_output

app_data = {}

UPLOAD_DIRECTORY = Path("./uploads")
UPLOAD_DIRECTORY.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_data["models"] = create_model_dict()
    yield
    app_data.pop("models", None)


app = FastAPI(
    title="AI Translator",
    description="Document processing, Markdown conversion, and automated translation.",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return HTMLResponse(ROOT_HTML)


@app.get("/ui")
async def ui():
    return HTMLResponse(UI_HTML)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


class CommonParams(BaseModel):
    filepath: Annotated[
        Optional[str], Field(description="The path to the document file to convert.")
    ]
    page_range: Annotated[
        Optional[str],
        Field(description="Page range to convert, e.g. 0,5-10,20."),
    ] = None
    scan_full_document: Annotated[
        bool,
        Field(description="Scan every page. If false and page_range is empty, page 0 is used."),
    ] = False
    force_ocr: Annotated[
        bool,
        Field(description="Force OCR on all pages of the PDF."),
    ] = False
    disable_ocr: Annotated[
        bool,
        Field(description="Disable OCR and use embedded text when possible."),
    ] = False
    disable_image_extraction: Annotated[
        bool,
        Field(description="Do not extract images into the output."),
    ] = False
    html_tables_in_markdown: Annotated[
        bool,
        Field(description="Keep complex tables as HTML when rendering Markdown."),
    ] = False
    paginate_output: Annotated[
        bool,
        Field(description="Separate output by page markers."),
    ] = False
    output_format: Annotated[
        str,
        Field(description="Output format: markdown, json, html, or chunks."),
    ] = "markdown"
    translate: Annotated[
        Optional[str],
        Field(description="Target language for Markdown translation, e.g. Russian."),
    ] = None
    use_llm: Annotated[
        bool,
        Field(description="Enable LLM processors during document conversion."),
    ] = False
    use_llm_translation: Annotated[
        bool,
        Field(description="Use LLM only for the translation stage."),
    ] = False
    llm_service: Annotated[
        Optional[str],
        Field(description="Full import path to an LLM service class."),
    ] = None
    ollama_base_url: Annotated[
        Optional[str],
        Field(description="Ollama base URL."),
    ] = None
    ollama_model: Annotated[
        Optional[str],
        Field(description="Ollama model name."),
    ] = None


def _normalize_params(params: CommonParams) -> CommonParams:
    if params.scan_full_document:
        params.page_range = None
    elif not params.page_range:
        params.page_range = "0"

    if params.force_ocr:
        params.disable_ocr = False

    if params.translate:
        params.use_llm_translation = True
        if not params.llm_service:
            params.llm_service = "src.services.ollama.OllamaService"

    return params


async def _convert_pdf(params: CommonParams):
    params = _normalize_params(params)

    if params.output_format not in ["markdown", "json", "html", "chunks"]:
        return {"success": False, "error": "Invalid output format."}

    if params.translate and params.output_format != "markdown":
        return {
            "success": False,
            "error": "Translation is currently supported only for markdown output.",
        }

    started_at = time.perf_counter()
    try:
        options = params.model_dump()
        config_parser = ConfigParser(options)
        config_dict = config_parser.generate_config_dict()
        config_dict["pdftext_workers"] = 1

        artifact_dict = dict(app_data["models"])
        converter = PdfConverter(
            config=config_dict,
            artifact_dict=artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )
        rendered = converter(params.filepath)

        if params.translate:
            rendered = translate_rendered_output(
                rendered,
                params.translate,
                llm_service=artifact_dict.get("llm_service"),
            )

        text, _, images = text_from_rendered(rendered)
        metadata = rendered.metadata
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}

    encoded_images = {}
    for name, image in images.items():
        byte_stream = io.BytesIO()
        image.save(byte_stream, format=settings.OUTPUT_IMAGE_FORMAT)
        encoded_images[name] = base64.b64encode(byte_stream.getvalue()).decode(
            settings.OUTPUT_ENCODING
        )

    elapsed = round(time.perf_counter() - started_at, 2)
    metadata.setdefault("ui", {})
    metadata["ui"].update(
        {
            "elapsed_seconds": elapsed,
            "scan_full_document": params.scan_full_document,
            "page_range": params.page_range,
        }
    )

    return {
        "format": params.output_format,
        "output": text,
        "images": encoded_images,
        "metadata": metadata,
        "elapsed_seconds": elapsed,
        "success": True,
    }


@app.post("/src")
async def convert_pdf(params: CommonParams):
    return await _convert_pdf(params)


@app.post("/src/upload")
async def convert_pdf_upload(
    page_range: Optional[str] = Form(default=None),
    scan_full_document: Optional[bool] = Form(default=False),
    force_ocr: Optional[bool] = Form(default=False),
    disable_ocr: Optional[bool] = Form(default=False),
    disable_image_extraction: Optional[bool] = Form(default=False),
    html_tables_in_markdown: Optional[bool] = Form(default=False),
    paginate_output: Optional[bool] = Form(default=False),
    output_format: Optional[str] = Form(default="markdown"),
    translate: Optional[str] = Form(default=None),
    use_llm: Optional[bool] = Form(default=False),
    use_llm_translation: Optional[bool] = Form(default=False),
    llm_service: Optional[str] = Form(default=None),
    ollama_base_url: Optional[str] = Form(default=None),
    ollama_model: Optional[str] = Form(default=None),
    file: UploadFile = File(..., description="Document file to convert."),
):
    suffix = Path(file.filename or "document.pdf").suffix or ".pdf"
    upload_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=UPLOAD_DIRECTORY,
        ) as upload_file:
            upload_path = upload_file.name
            upload_file.write(await file.read())

        params = CommonParams(
            filepath=upload_path,
            page_range=page_range or None,
            scan_full_document=bool(scan_full_document),
            force_ocr=bool(force_ocr),
            disable_ocr=bool(disable_ocr),
            disable_image_extraction=bool(disable_image_extraction),
            html_tables_in_markdown=bool(html_tables_in_markdown),
            paginate_output=bool(paginate_output),
            output_format=output_format or "markdown",
            translate=translate or None,
            use_llm=bool(use_llm),
            use_llm_translation=bool(use_llm_translation),
            llm_service=llm_service or None,
            ollama_base_url=ollama_base_url or None,
            ollama_model=ollama_model or None,
        )
        return await _convert_pdf(params)
    finally:
        if upload_path and os.path.exists(upload_path):
            os.remove(upload_path)


@click.command()
@click.option("--port", type=int, default=8000, help="Port to run the server on")
@click.option("--host", type=str, default="127.0.0.1", help="Host to run the server on")
def server_cli(port: int, host: str):
    import uvicorn

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run(app, host=host, port=port, loop="asyncio")


ROOT_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Translator</title>
  <style>
    body { font-family: Georgia, "Times New Roman", serif; margin: 40px; color: #1f2933; background: #f7f5ef; }
    a { color: #126149; font-weight: 700; }
  </style>
</head>
<body>
  <h1>AI Translator</h1>
  <p>&#1042;&#1077;&#1073;-&#1080;&#1085;&#1090;&#1077;&#1088;&#1092;&#1077;&#1081;&#1089; &#1076;&#1083;&#1103; &#1086;&#1073;&#1088;&#1072;&#1073;&#1086;&#1090;&#1082;&#1080; &#1076;&#1086;&#1082;&#1091;&#1084;&#1077;&#1085;&#1090;&#1086;&#1074;, &#1082;&#1086;&#1085;&#1074;&#1077;&#1088;&#1090;&#1072;&#1094;&#1080;&#1080; &#1074; Markdown &#1080; &#1072;&#1074;&#1090;&#1086;&#1084;&#1072;&#1090;&#1080;&#1079;&#1080;&#1088;&#1086;&#1074;&#1072;&#1085;&#1085;&#1086;&#1075;&#1086; &#1087;&#1077;&#1088;&#1077;&#1074;&#1086;&#1076;&#1072;.</p>
  <p><a href="/ui">&#1054;&#1090;&#1082;&#1088;&#1099;&#1090;&#1100; &#1080;&#1085;&#1090;&#1077;&#1088;&#1092;&#1077;&#1081;&#1089;</a> &middot; <a href="/docs">API</a></p>
</body>
</html>
"""


UI_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Translator</title>
  <style>
    :root {
      --paper: #f6f3ec;
      --panel: #fffdf7;
      --ink: #1d2a27;
      --muted: #66746f;
      --line: #d9d2c3;
      --accent: #0f6b52;
      --accent-dark: #084737;
      --danger: #9f2f2f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: linear-gradient(180deg, rgba(15, 107, 82, 0.08), transparent 260px), var(--paper);
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
    }
    header { padding: 28px 32px 18px; border-bottom: 1px solid var(--line); }
    h1 { margin: 0; font-size: 32px; line-height: 1.15; }
    header p { margin: 8px 0 0; color: var(--muted); max-width: 900px; }
    main { display: grid; grid-template-columns: minmax(300px, 430px) minmax(0, 1fr); gap: 24px; padding: 24px 32px 32px; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px; box-shadow: 0 10px 30px rgba(41, 37, 29, 0.06); }
    label { display: block; margin: 14px 0 6px; font-weight: 700; }
    input[type="file"], input[type="text"], select {
      width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 10px 11px; background: #fff; color: var(--ink); font: inherit;
    }
    .checks { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 14px; margin-top: 14px; }
    .checks label { display: flex; gap: 8px; align-items: center; margin: 0; font-weight: 400; }
    .hint { margin: 6px 0 0; color: var(--muted); font-size: 13px; line-height: 1.35; }
    button { width: 100%; margin-top: 18px; border: 0; border-radius: 6px; padding: 12px 14px; background: var(--accent); color: white; font: inherit; font-weight: 700; cursor: pointer; }
    button:hover { background: var(--accent-dark); }
    button:disabled { opacity: 0.65; cursor: wait; }
    button.secondary { background: #6d756d; }
    button.secondary:hover { background: #4f574f; }
    .result-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
    .result-head h2 { margin: 0; font-size: 22px; }
    .actions { display: flex; align-items: center; gap: 8px; }
    .action-button { width: auto; margin: 0; padding: 8px 12px; }
    .progress-wrap { display: none; margin: 12px 0; }
    .progress-bar { height: 10px; border: 1px solid var(--line); border-radius: 999px; overflow: hidden; background: #ebe5d8; }
    .progress-fill { height: 100%; width: 0%; background: var(--accent); transition: width 0.45s ease; }
    .progress-text { margin-top: 6px; color: var(--muted); font-size: 14px; }
    pre {
      min-height: 520px; max-height: 70vh; overflow: auto; margin: 0; padding: 16px; border: 1px solid var(--line); border-radius: 6px;
      background: #171b1a; color: #edf5ef; font: 14px/1.55 Consolas, "Courier New", monospace; white-space: pre-wrap; word-break: break-word;
    }
    .meta { margin-top: 12px; color: var(--muted); font-size: 14px; }
    .error { color: var(--danger); font-weight: 700; }
    @media (max-width: 900px) { main { grid-template-columns: 1fr; padding: 18px; } header { padding: 22px 18px 14px; } .checks { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>AI Translator</h1>
    <p>&#1048;&#1085;&#1090;&#1077;&#1083;&#1083;&#1077;&#1082;&#1090;&#1091;&#1072;&#1083;&#1100;&#1085;&#1072;&#1103; &#1086;&#1073;&#1088;&#1072;&#1073;&#1086;&#1090;&#1082;&#1072; &#1076;&#1086;&#1082;&#1091;&#1084;&#1077;&#1085;&#1090;&#1086;&#1074;, &#1082;&#1086;&#1085;&#1074;&#1077;&#1088;&#1090;&#1072;&#1094;&#1080;&#1103; &#1074; Markdown &#1080; &#1072;&#1074;&#1090;&#1086;&#1084;&#1072;&#1090;&#1080;&#1079;&#1080;&#1088;&#1086;&#1074;&#1072;&#1085;&#1085;&#1099;&#1081; &#1087;&#1077;&#1088;&#1077;&#1074;&#1086;&#1076;.</p>
  </header>
  <main>
    <section>
      <form id="convertForm">
        <label for="file">&#1044;&#1086;&#1082;&#1091;&#1084;&#1077;&#1085;&#1090;</label>
        <input id="file" name="file" type="file" accept=".pdf,.png,.jpg,.jpeg,.docx,.pptx,.xlsx,.html,.epub" required>

        <label for="page_range">&#1044;&#1080;&#1072;&#1087;&#1072;&#1079;&#1086;&#1085; &#1089;&#1090;&#1088;&#1072;&#1085;&#1080;&#1094;</label>
        <input id="page_range" name="page_range" type="text" value="0" placeholder="0 &#1080;&#1083;&#1080; 0-2">
        <p class="hint">&#1055;&#1086; &#1091;&#1084;&#1086;&#1083;&#1095;&#1072;&#1085;&#1080;&#1102; &#1086;&#1073;&#1088;&#1072;&#1073;&#1072;&#1090;&#1099;&#1074;&#1072;&#1077;&#1090;&#1089;&#1103; &#1087;&#1077;&#1088;&#1074;&#1072;&#1103; &#1089;&#1090;&#1088;&#1072;&#1085;&#1080;&#1094;&#1072;, &#1095;&#1090;&#1086;&#1073;&#1099; &#1085;&#1077; &#1079;&#1072;&#1074;&#1080;&#1089;&#1072;&#1090;&#1100; &#1085;&#1072; &#1073;&#1086;&#1083;&#1100;&#1096;&#1080;&#1093; PDF. &#1044;&#1083;&#1103; &#1074;&#1089;&#1077;&#1075;&#1086; &#1092;&#1072;&#1081;&#1083;&#1072; &#1074;&#1082;&#1083;&#1102;&#1095;&#1080;&#1090;&#1077; &#1075;&#1072;&#1083;&#1086;&#1095;&#1082;&#1091; &#1085;&#1080;&#1078;&#1077;.</p>

        <label for="output_format">&#1060;&#1086;&#1088;&#1084;&#1072;&#1090; &#1088;&#1077;&#1079;&#1091;&#1083;&#1100;&#1090;&#1072;&#1090;&#1072;</label>
        <select id="output_format" name="output_format">
          <option value="markdown">Markdown</option>
          <option value="html">HTML</option>
          <option value="json">JSON</option>
          <option value="chunks">Chunks</option>
        </select>

        <label for="translate">&#1055;&#1077;&#1088;&#1077;&#1074;&#1086;&#1076;</label>
        <select id="translate" name="translate">
          <option value="">&#1041;&#1077;&#1079; &#1087;&#1077;&#1088;&#1077;&#1074;&#1086;&#1076;&#1072;</option>
          <option value="Russian">&#1053;&#1072; &#1088;&#1091;&#1089;&#1089;&#1082;&#1080;&#1081; &#1095;&#1077;&#1088;&#1077;&#1079; LLM</option>
        </select>

        <label for="ollama_model">&#1052;&#1086;&#1076;&#1077;&#1083;&#1100; Ollama</label>
        <input id="ollama_model" name="ollama_model" type="text" placeholder="llama3.2">

        <div class="checks">
          <label><input type="checkbox" name="scan_full_document" id="scanFullDocument"> &#1057;&#1082;&#1072;&#1085;&#1080;&#1088;&#1086;&#1074;&#1072;&#1090;&#1100; &#1074;&#1077;&#1089;&#1100; &#1076;&#1086;&#1082;&#1091;&#1084;&#1077;&#1085;&#1090;</label>
          <label><input type="checkbox" name="disable_ocr" id="disableOcr" checked> &#1041;&#1077;&#1079; OCR</label>
          <label><input type="checkbox" name="force_ocr" id="forceOcr"> &#1055;&#1088;&#1080;&#1085;&#1091;&#1076;&#1080;&#1090;&#1077;&#1083;&#1100;&#1085;&#1099;&#1081; OCR</label>
          <label><input type="checkbox" name="disable_image_extraction" checked> &#1041;&#1077;&#1079; &#1080;&#1079;&#1086;&#1073;&#1088;&#1072;&#1078;&#1077;&#1085;&#1080;&#1081;</label>
          <label><input type="checkbox" name="html_tables_in_markdown" id="htmlTables"> HTML-&#1090;&#1072;&#1073;&#1083;&#1080;&#1094;&#1099; &#1074; Markdown</label>
          <label><input type="checkbox" name="paginate_output"> &#1056;&#1072;&#1079;&#1073;&#1080;&#1090;&#1100; &#1087;&#1086; &#1089;&#1090;&#1088;&#1072;&#1085;&#1080;&#1094;&#1072;&#1084;</label>
        </div>
        <p class="hint">&#1045;&#1089;&#1083;&#1080; Markdown &#1082;&#1088;&#1080;&#1074;&#1086; &#1087;&#1077;&#1088;&#1077;&#1085;&#1086;&#1089;&#1080;&#1090; &#1090;&#1072;&#1073;&#1083;&#1080;&#1094;&#1099;, &#1074;&#1082;&#1083;&#1102;&#1095;&#1080;&#1090;&#1077; HTML-&#1090;&#1072;&#1073;&#1083;&#1080;&#1094;&#1099;. &#1045;&#1089;&#1083;&#1080; PDF &#1089;&#1082;&#1072;&#1085;&#1080;&#1088;&#1086;&#1074;&#1072;&#1085;&#1085;&#1099;&#1081;, &#1089;&#1085;&#1080;&#1084;&#1080;&#1090;&#1077; &#171;&#1041;&#1077;&#1079; OCR&#187; &#1080; &#1074;&#1082;&#1083;&#1102;&#1095;&#1080;&#1090;&#1077; &#171;&#1055;&#1088;&#1080;&#1085;&#1091;&#1076;&#1080;&#1090;&#1077;&#1083;&#1100;&#1085;&#1099;&#1081; OCR&#187;.</p>

        <button id="runButton" type="submit">&#1054;&#1073;&#1088;&#1072;&#1073;&#1086;&#1090;&#1072;&#1090;&#1100; &#1076;&#1086;&#1082;&#1091;&#1084;&#1077;&#1085;&#1090;</button>
      </form>
    </section>
    <section>
      <div class="result-head">
        <h2>&#1056;&#1077;&#1079;&#1091;&#1083;&#1100;&#1090;&#1072;&#1090;</h2>
        <div class="actions">
          <button class="action-button secondary" id="copyButton" type="button" disabled>&#1057;&#1082;&#1086;&#1087;&#1080;&#1088;&#1086;&#1074;&#1072;&#1090;&#1100;</button>
          <button class="action-button" id="downloadButton" type="button" disabled>&#1057;&#1082;&#1072;&#1095;&#1072;&#1090;&#1100;</button>
        </div>
      </div>
      <div class="progress-wrap" id="progressWrap">
        <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
        <div class="progress-text" id="progressText"></div>
      </div>
      <pre id="output">&#1047;&#1072;&#1075;&#1088;&#1091;&#1079;&#1080;&#1090;&#1077; &#1076;&#1086;&#1082;&#1091;&#1084;&#1077;&#1085;&#1090; &#1080; &#1079;&#1072;&#1087;&#1091;&#1089;&#1090;&#1080;&#1090;&#1077; &#1086;&#1073;&#1088;&#1072;&#1073;&#1086;&#1090;&#1082;&#1091;.</pre>
      <div class="meta" id="meta"></div>
    </section>
  </main>
  <script>
    const form = document.getElementById("convertForm");
    const pageRange = document.getElementById("page_range");
    const scanFullDocument = document.getElementById("scanFullDocument");
    const disableOcr = document.getElementById("disableOcr");
    const forceOcr = document.getElementById("forceOcr");
    const output = document.getElementById("output");
    const meta = document.getElementById("meta");
    const runButton = document.getElementById("runButton");
    const copyButton = document.getElementById("copyButton");
    const downloadButton = document.getElementById("downloadButton");
    const progressWrap = document.getElementById("progressWrap");
    const progressFill = document.getElementById("progressFill");
    const progressText = document.getElementById("progressText");
    let latestOutput = "";
    let latestExt = "md";
    let progressTimer = null;

    function setBoolean(formData, name) {
      formData.set(name, form.elements[name].checked ? "true" : "false");
    }

    function startProgress() {
      const stages = [
        [8, "&#1055;&#1086;&#1076;&#1075;&#1086;&#1090;&#1086;&#1074;&#1082;&#1072; &#1092;&#1072;&#1081;&#1083;&#1072;..."],
        [24, "&#1047;&#1072;&#1075;&#1088;&#1091;&#1079;&#1082;&#1072; &#1084;&#1086;&#1076;&#1077;&#1083;&#1077;&#1081;..."],
        [46, "&#1040;&#1085;&#1072;&#1083;&#1080;&#1079; layout &#1080; &#1073;&#1083;&#1086;&#1082;&#1086;&#1074;..."],
        [68, "&#1060;&#1086;&#1088;&#1084;&#1080;&#1088;&#1086;&#1074;&#1072;&#1085;&#1080;&#1077; Markdown..."],
        [82, "&#1055;&#1086;&#1089;&#1090;&#1086;&#1073;&#1088;&#1072;&#1073;&#1086;&#1090;&#1082;&#1072;..."],
        [92, "&#1054;&#1078;&#1080;&#1076;&#1072;&#1085;&#1080;&#1077; &#1086;&#1090;&#1074;&#1077;&#1090;&#1072;..."]
      ];
      let index = 0;
      progressWrap.style.display = "block";
      progressFill.style.width = "0%";
      progressText.innerHTML = stages[0][1];
      progressTimer = setInterval(() => {
        const stage = stages[Math.min(index, stages.length - 1)];
        progressFill.style.width = stage[0] + "%";
        progressText.innerHTML = stage[1];
        index += 1;
      }, 1400);
    }

    function finishProgress() {
      clearInterval(progressTimer);
      progressFill.style.width = "100%";
      progressText.innerHTML = "&#1043;&#1086;&#1090;&#1086;&#1074;&#1086;";
    }

    scanFullDocument.addEventListener("change", () => {
      pageRange.disabled = scanFullDocument.checked;
      pageRange.value = scanFullDocument.checked ? "" : "0";
    });

    forceOcr.addEventListener("change", () => {
      if (forceOcr.checked) disableOcr.checked = false;
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      setBoolean(formData, "scan_full_document");
      setBoolean(formData, "disable_ocr");
      setBoolean(formData, "force_ocr");
      setBoolean(formData, "disable_image_extraction");
      setBoolean(formData, "html_tables_in_markdown");
      setBoolean(formData, "paginate_output");
      formData.set("use_llm_translation", formData.get("translate") ? "true" : "false");
      formData.set("llm_service", "src.services.ollama.OllamaService");

      output.textContent = "Document is processing...";
      output.className = "";
      meta.textContent = "";
      runButton.disabled = true;
      copyButton.disabled = true;
      downloadButton.disabled = true;
      startProgress();

      try {
        const response = await fetch("/src/upload", { method: "POST", body: formData });
        const data = await response.json();
        if (!data.success) {
          output.textContent = data.error || "Conversion failed.";
          output.className = "error";
          return;
        }
        latestOutput = data.output || "";
        latestExt = data.format === "markdown" ? "md" : (data.format === "chunks" ? "json" : data.format);
        output.textContent = latestOutput;
        meta.textContent = "";
        copyButton.disabled = !latestOutput;
        downloadButton.disabled = false;
      } catch (error) {
        output.textContent = error.toString();
        output.className = "error";
      } finally {
        finishProgress();
        runButton.disabled = false;
      }
    });

    copyButton.addEventListener("click", async () => {
      if (!latestOutput) return;
      try {
        await navigator.clipboard.writeText(latestOutput);
        meta.textContent = meta.textContent + " Copied.";
      } catch (error) {
        output.focus();
        document.execCommand("selectAll");
        document.execCommand("copy");
      }
    });

    downloadButton.addEventListener("click", () => {
      if (!latestOutput) return;
      const mimeTypes = {
        md: "text/markdown;charset=utf-8",
        html: "text/html;charset=utf-8",
        json: "application/json;charset=utf-8"
      };
      const blob = new Blob([latestOutput], { type: mimeTypes[latestExt] || "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `converted-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.${latestExt}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    server_cli()
