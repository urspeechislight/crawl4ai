from pathlib import Path

from akeyless_crawler.storage import StorageManager, guess_extension


def test_guess_extension_from_mime() -> None:
    assert guess_extension("https://example.com/file", "text/css") == ".css"


def test_guess_extension_from_url() -> None:
    assert guess_extension("https://example.com/file.css", None) == ""
    assert guess_extension("https://example.com/file", None) == ".bin"


def test_storage_manager_creates_paths(tmp_path: Path) -> None:
    storage = StorageManager(tmp_path)
    path = storage.save_text("https://docs.akeyless.io/docs", "<html></html>")
    assert path.exists()
    assert path.suffix == ".html"
