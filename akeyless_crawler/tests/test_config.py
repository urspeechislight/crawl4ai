from pathlib import Path

import pytest

from akeyless_crawler.config import CrawlConfig, extract_domain, is_same_domain, normalize_url


def test_extract_domain() -> None:
    assert extract_domain("https://docs.akeyless.io/docs") == "docs.akeyless.io"


def test_normalize_url() -> None:
    assert normalize_url("HTTPS://docs.akeyless.io/docs") == "https://docs.akeyless.io/docs"
    assert normalize_url("https://docs.akeyless.io/docs#fragment") == "https://docs.akeyless.io/docs"


def test_is_same_domain() -> None:
    allowed = {"docs.akeyless.io"}
    assert is_same_domain("https://docs.akeyless.io/docs", allowed)
    assert not is_same_domain("https://example.com", allowed)


def test_from_urls_creates_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "artifacts"
    config = CrawlConfig.from_urls(["https://docs.akeyless.io/docs"], out_dir)
    assert config.output_dir.exists()
    assert config.output_dir == out_dir.resolve()


def test_from_urls_requires_seed() -> None:
    with pytest.raises(ValueError):
        CrawlConfig.from_urls([], "artifacts")
