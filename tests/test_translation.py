from src.translation.translator import (
    _chunk_text,
    _is_cyrillic_char,
    _resolve_language,
    _translation_is_valid,
)


def test_translation_resolves_russian_language_name_and_alias():
    assert _resolve_language("Russian")["code"] == "ru"
    assert _resolve_language("русский")["code"] == "ru"


def test_translation_chunking_preserves_markdown_code_blocks():
    text = "# Title\n\n```python\nprint('hello')\n```\n\n" + "Paragraph.\n" * 40
    chunks = _chunk_text(text, max_chunk_chars=120)

    assert "```python\nprint('hello')\n```\n" in chunks[0]
    assert "".join(chunks) == text


def test_translation_validation_accepts_meaningful_russian_output():
    translated = "Это корректный русский технический перевод документа."

    assert _is_cyrillic_char("Я")
    assert _translation_is_valid("technical source text", translated)
