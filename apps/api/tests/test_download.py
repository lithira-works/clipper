from pathlib import Path
from typing import Any

import pytest
import yt_dlp

from app.config import get_settings
from app.pipeline import download

BOT_CHECK = "ERROR: [youtube] x: Sign in to confirm you're not a bot."


class FakeYDL:
    """Records which attempts used cookies; fails anonymous attempts with `anon_error`."""

    calls: list[bool] = []
    anon_error: str | None = None

    def __init__(self, opts: dict[str, Any]) -> None:
        self.with_cookies = "cookiefile" in opts

    def __enter__(self) -> "FakeYDL":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def extract_info(self, url: str, download: bool = False) -> dict[str, Any]:
        FakeYDL.calls.append(self.with_cookies)
        if not self.with_cookies and FakeYDL.anon_error:
            raise yt_dlp.utils.DownloadError(FakeYDL.anon_error)
        return {"id": "abc", "duration": 60}


@pytest.fixture
def fake_ydl(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> type[FakeYDL]:
    FakeYDL.calls = []
    FakeYDL.anon_error = None
    monkeypatch.setattr(download.yt_dlp, "YoutubeDL", FakeYDL)
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n")
    monkeypatch.setattr(get_settings(), "ytdlp_cookies_file", cookies)
    return FakeYDL


def _probe(tmp_path: Path) -> Any:
    return download._with_cookie_fallback(
        tmp_path / "work", lambda ydl: ydl.extract_info("u", download=False)
    )


def test_anonymous_first_even_when_cookies_exist(fake_ydl: type[FakeYDL], tmp_path: Path) -> None:
    _probe(tmp_path)
    assert fake_ydl.calls == [False]


def test_cookies_used_only_after_bot_check(fake_ydl: type[FakeYDL], tmp_path: Path) -> None:
    fake_ydl.anon_error = BOT_CHECK
    assert _probe(tmp_path)["id"] == "abc"
    assert fake_ydl.calls == [False, True]


def test_other_errors_do_not_retry_with_cookies(fake_ydl: type[FakeYDL], tmp_path: Path) -> None:
    fake_ydl.anon_error = "ERROR: Private video"
    with pytest.raises(download.DownloadError, match="Private video"):
        _probe(tmp_path)
    assert fake_ydl.calls == [False]
