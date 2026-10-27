import pytest
from pydantic import ValidationError

from app.pipeline.captions import YELLOW, build_ass, chunk_words
from app.pipeline.reframe import _lerp_expr
from app.pipeline.transcribe import Word
from app.schemas import CaptionStyle, JobCreate


def test_chunks_max_three_words() -> None:
    words = [Word(i * 0.3, i * 0.3 + 0.2, f"w{i}") for i in range(7)]
    assert [len(c) for c in chunk_words(words)] == [3, 3, 1]


def test_bold_ass_highlights_active_word_and_hook() -> None:
    words = [Word(10.0, 10.3, "this"), Word(10.4, 10.7, "is"), Word(10.8, 11.2, "{huge}")]
    ass = build_ass(words, 10.0, 12.0, CaptionStyle.bold, "Wait for it")
    assert "PlayResY: 1920" in ass
    assert "WAIT FOR IT" in ass
    assert ass.count(f"\\c{YELLOW}") == 3
    assert "{huge}" not in ass  # braces stripped so libass can't be injected


def test_none_style_keeps_only_hook() -> None:
    ass = build_ass([Word(0, 1, "hi")], 0, 2, CaptionStyle.none, "Hook")
    assert "Bold,," not in ass and "HOOK" in ass


def test_lerp_expr_is_escaped_for_filtergraph() -> None:
    expr = _lerp_expr([0, 1, 2], [0.0, 100.0, 100.0])
    assert "\\," in expr and "," not in expr.replace("\\,", "")


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/shorts/dQw4w9WgXcQ",
    ],
)
def test_accepts_youtube_urls(url: str) -> None:
    assert JobCreate(url=url).url == url


@pytest.mark.parametrize("url", ["https://vimeo.com/123", "file:///etc/passwd", "not a url"])
def test_rejects_non_youtube(url: str) -> None:
    with pytest.raises(ValidationError):
        JobCreate(url=url)


def test_duration_order() -> None:
    with pytest.raises(ValidationError):
        JobCreate(url="https://youtu.be/dQw4w9WgXcQ", min_duration=50, max_duration=40)
