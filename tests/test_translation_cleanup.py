from src.translation.translator import (
    _finalize_translated_markdown,
    _join_translated_segments,
)


def test_finalize_translated_markdown_removes_chunk_wrappers():
    raw = (
        "<MARKDOWN>\n"
        "## Заголовок\n\n"
        "Первый абзац.\n"
        "</MARKDOWN><MARKDOWN>\n"
        "Второй абзац.\n"
        "</MARKDOWN>"
    )

    cleaned = _finalize_translated_markdown(raw)

    assert "<MARKDOWN>" not in cleaned
    assert "</MARKDOWN>" not in cleaned
    assert "## Заголовок" in cleaned
    assert "Первый абзац." in cleaned
    assert "Второй абзац." in cleaned


def test_join_translated_segments_keeps_table_and_next_paragraph_separate():
    segments = [
        "| Заголовок | Значение |\n| --- | --- |\n| A | B |",
        "Когда таблица имеет заголовки столбцов, каждый элемент относится к одному столбцу.",
    ]

    joined = _join_translated_segments(segments)

    assert "| A | B |\n\nКогда таблица" in joined
