from src.scripts.server import UI_HTML, CommonParams, _normalize_params


def test_web_ui_contains_upload_form_actions_and_markdown_options():
    assert 'id="convertForm"' in UI_HTML
    assert "/src/upload" in UI_HTML
    assert "AI Translator" in UI_HTML
    assert "scan_full_document" in UI_HTML
    assert "downloadButton" in UI_HTML
    assert "copyButton" in UI_HTML
    assert "html_tables_in_markdown" in UI_HTML


def test_common_params_accept_translation_language_and_ollama_settings():
    params = CommonParams(
        filepath="sample.pdf",
        output_format="markdown",
        translate="Russian",
        use_llm_translation=True,
        llm_service="src.services.ollama.OllamaService",
    )

    assert params.translate == "Russian"
    assert params.use_llm_translation is True


def test_normalize_params_uses_first_page_when_full_scan_is_disabled():
    params = _normalize_params(CommonParams(filepath="sample.pdf"))

    assert params.page_range == "0"
    assert params.scan_full_document is False


def test_normalize_params_clears_page_range_for_full_document_scan():
    params = _normalize_params(
        CommonParams(filepath="sample.pdf", page_range="0", scan_full_document=True)
    )

    assert params.page_range is None
