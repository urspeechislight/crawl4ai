"""Web crawler implementation."""

from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, Set

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.console import Console
from rich.progress import Progress

from .config import CrawlConfig, is_same_domain, normalize_url
from .storage import StorageManager

console = Console()


@dataclass
class PageRecord:
    """Metadata for a fetched URL."""

    url: str
    status: int
    path: str
    kind: str
    referrers: Set[str] = field(default_factory=set)


class Crawler:
    """Breadth-first crawler with polite rate limiting."""

    def __init__(self, config: CrawlConfig) -> None:
        self.config = config
        self.storage = StorageManager(config.output_dir)
        self.visited: Dict[str, PageRecord] = {}
        self.session = self._build_session()
        self.queue: Deque[str] = deque(normalize_url(url) for url in config.start_urls)
        self.seen: Set[str] = set(self.queue)
        self.referrers_map: Dict[str, Set[str]] = {}

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(
            {
                "User-Agent": "akeyless-crawler/1.0 (https://github.com/)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        return session

    def crawl(self) -> Dict[str, PageRecord]:
        progress = Progress(transient=True)
        total = self.config.max_pages if self.config.max_pages is not None else None
        task_id = progress.add_task("crawling", total=total)

        with progress:
            while self.queue:
                if self.config.max_pages and len(self.visited) >= self.config.max_pages:
                    break

                url = self.queue.popleft()
                if url in self.visited:
                    continue

                try:
                    record = self._fetch(url)
                except Exception as exc:  # noqa: BLE001
                    console.print(f"[red]Failed to fetch {url}: {exc}")
                    continue

                record.referrers = set(self.referrers_map.get(url, set()))
                self.visited[url] = record
                progress.advance(task_id)
                time.sleep(self.config.rate_limit)

        self._write_manifest()
        return self.visited

    def _fetch(self, url: str) -> PageRecord:
        response = self.session.get(url, timeout=self.config.request_timeout)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            record = self._handle_html(url, response.text)
        else:
            path = str(self.storage.save_binary(url, response.content, mime_hint=content_type))
            record = PageRecord(url=url, status=response.status_code, path=path, kind="asset")

        return record

    def _handle_html(self, url: str, html: str) -> PageRecord:
        saved_path = str(self.storage.save_text(url, html))
        soup = BeautifulSoup(html, "html.parser")
        links = self._extract_links(url, soup)
        assets = self._extract_assets(url, soup) if self.config.include_assets else []

        for link in links:
            normalized = normalize_url(link)
            if not is_same_domain(normalized, self.config.allowed_domains):
                continue
            self.referrers_map.setdefault(normalized, set()).add(url)
            if normalized not in self.seen:
                self.queue.append(normalized)
                self.seen.add(normalized)

        if self.config.include_assets:
            for asset in assets:
                self._fetch_asset(asset, url)

        return PageRecord(url=url, status=200, path=saved_path, kind="html")

    def _fetch_asset(self, url: str, referrer: str) -> None:
        normalized = normalize_url(url)
        if not is_same_domain(normalized, self.config.allowed_domains):
            return

        self.referrers_map.setdefault(normalized, set()).add(referrer)
        if normalized in self.visited:
            self.visited[normalized].referrers.update(self.referrers_map[normalized])
            return
        if normalized in self.seen:
            return

        self.seen.add(normalized)
        try:
            response = self.session.get(normalized, timeout=self.config.request_timeout)
        except requests.RequestException as exc:  # noqa: PERF203
            console.print(f"[yellow]Skipping asset {normalized}: {exc}")
            return

        if response.status_code >= 400:
            console.print(f"[yellow]Skipping asset {normalized}, status {response.status_code}")
            return
        path = str(self.storage.save_binary(normalized, response.content, response.headers.get("Content-Type")))
        record = PageRecord(
            url=normalized,
            status=response.status_code,
            path=path,
            kind="asset",
            referrers=set(self.referrers_map.get(normalized, {referrer})),
        )
        self.visited[normalized] = record

    def _extract_links(self, base_url: str, soup: BeautifulSoup) -> Set[str]:
        from urllib.parse import urljoin

        anchors = {urljoin(base_url, tag.get("href")) for tag in soup.find_all("a", href=True)}
        filtered = {link for link in anchors if self._is_crawlable(link)}
        return filtered

    def _extract_assets(self, base_url: str, soup: BeautifulSoup) -> Set[str]:
        from urllib.parse import urljoin

        assets = set()
        for attr, selector in (("src", ["img", "script"]), ("href", ["link"])):
            for element_name in selector:
                for tag in soup.find_all(element_name, attrs={attr: True}):
                    assets.add(urljoin(base_url, tag.get(attr)))
        return {asset for asset in assets if self._is_asset(asset)}

    def _is_crawlable(self, url: str) -> bool:
        if not url.startswith("http"):
            return False
        return is_same_domain(url, self.config.allowed_domains)

    def _is_asset(self, url: str) -> bool:
        return self._is_crawlable(url)

    def _write_manifest(self) -> None:
        manifest_path = Path(self.config.output_dir) / "manifest.json"
        payload = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pages": [
                {
                    "url": record.url,
                    "status": record.status,
                    "path": record.path,
                    "kind": record.kind,
                    "referrers": sorted(record.referrers),
                }
                for record in self.visited.values()
            ],
        }
        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.log(f"Wrote manifest -> {manifest_path}")
