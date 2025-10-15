"""Configuration primitives for the Akeyless crawler."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Set


@dataclass(slots=True)
class CrawlConfig:
    """Runtime configuration for the crawler."""

    start_urls: tuple[str, ...]
    allowed_domains: Set[str]
    output_dir: Path
    rate_limit: float = 0.5
    request_timeout: float = 30.0
    max_pages: int | None = None
    include_assets: bool = True

    @classmethod
    def from_urls(
        cls,
        start_urls: Iterable[str],
        output_dir: str | Path,
        *,
        rate_limit: float = 0.5,
        request_timeout: float = 30.0,
        max_pages: int | None = None,
        include_assets: bool = True,
    ) -> "CrawlConfig":
        """Build a config inferring allowed domains from the provided start URLs."""

        normalized_urls = tuple(start_urls)
        if not normalized_urls:
            msg = "At least one start URL must be provided"
            raise ValueError(msg)

        domains = {extract_domain(url) for url in normalized_urls}
        destination = Path(output_dir).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        return cls(
            start_urls=normalized_urls,
            allowed_domains=domains,
            output_dir=destination,
            rate_limit=rate_limit,
            request_timeout=request_timeout,
            max_pages=max_pages,
            include_assets=include_assets,
        )


def extract_domain(url: str) -> str:
    """Return the network location for a URL."""

    from urllib.parse import urlparse

    parsed = urlparse(url)
    if not parsed.netloc:
        msg = f"URL '{url}' is missing a network location"
        raise ValueError(msg)
    return parsed.netloc.lower()


def is_same_domain(url: str, allowed: Set[str]) -> bool:
    """Check whether ``url`` belongs to one of the allowed domains."""

    from urllib.parse import urlparse

    netloc = urlparse(url).netloc.lower()
    return netloc in {domain.lower() for domain in allowed}


def normalize_url(url: str) -> str:
    """Return a canonical representation of ``url`` for deduplication."""

    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    normalized = parsed._replace(scheme=scheme, netloc=netloc, path=path, fragment="", query=parsed.query)
    return urlunparse(normalized)
