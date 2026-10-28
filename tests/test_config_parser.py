from src.config.parser import ConfigParser


def test_config_parser_uses_markdown_renderer_by_default():
    parser = ConfigParser({"output_format": "markdown"})

    assert parser.get_renderer() == "src.renderers.markdown.MarkdownRenderer"


def test_config_parser_keeps_llm_translation_disabled_without_flag():
    parser = ConfigParser({"output_format": "markdown"})

    assert parser.get_llm_service() is None


def test_config_parser_enables_ollama_service_for_markdown_translation():
    parser = ConfigParser(
        {
            "output_format": "markdown",
            "use_llm_translation": True,
            "llm_service": None,
        }
    )

    assert parser.get_llm_service() == "src.services.ollama.OllamaService"
