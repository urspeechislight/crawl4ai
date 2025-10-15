"""Command-line interface for the crawler."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import CrawlConfig
from .crawler import Crawler

console = Console()

app = typer.Typer(help="Crawl the Akeyless documentation site.")


@app.command()
def crawl(
    start_url: Optional[list[str]] = typer.Option(
        None,
        "--start-url",
        help="Seed URL to crawl; can be provided multiple times.",
    ),
    output_dir: Path = typer.Option(Path("artifacts"), help="Directory to store crawled files."),
    rate_limit: float = typer.Option(0.5, min=0.0, help="Seconds to wait between requests."),
    request_timeout: float = typer.Option(30.0, min=1.0, help="Request timeout in seconds."),
    max_pages: Optional[int] = typer.Option(None, min=1, help="Optional maximum number of HTML pages."),
    include_assets: bool = typer.Option(True, help="Download linked images, scripts, and stylesheets."),
) -> None:
    """Execute the crawler."""

    seeds = start_url or ["https://docs.akeyless.io/docs", "https://docs.akeyless.io/reference"]
    config = CrawlConfig.from_urls(
        seeds,
        output_dir=output_dir,
        rate_limit=rate_limit,
        request_timeout=request_timeout,
        max_pages=max_pages,
        include_assets=include_assets,
    )

    console.log(f"Starting crawl with {len(config.start_urls)} seed URLs")
    crawler = Crawler(config)
    records = crawler.crawl()
    console.log(f"Crawl finished, fetched {len(records)} resources")


if __name__ == "__main__":
    app()
