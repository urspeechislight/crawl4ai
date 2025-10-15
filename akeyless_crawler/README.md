# Akeyless Documentation Crawler

This project provides a self-contained crawler that downloads the entire contents of the
[Akeyless documentation site](https://docs.akeyless.io) for the main documentation and API reference
sections.

## Features

- Deterministic crawling of `https://docs.akeyless.io/docs` and `https://docs.akeyless.io/reference`.
- Asset-aware download that captures linked stylesheets, scripts, images, and additional pages.
- Resilient retries with polite rate limiting and transparent logging via `rich`.
- CLI built with [Typer](https://typer.tiangolo.com/) for ease of use.
- Reproducible tooling through a dedicated Python virtual environment, `Makefile`, and `pre-commit` hooks.

## Getting started

```bash
cd akeyless_crawler
make setup        # creates ./venv and installs dependencies
source venv/bin/activate
make crawl        # downloads the documentation into ./artifacts
```

The crawler writes a manifest to `artifacts/manifest.json` describing every fetched URL.

## Available commands

- `make setup` – create the virtual environment and install requirements.
- `make crawl` – execute the crawler against the default start URLs.
- `make crawl EXTRA="--start-url https://example.com"` – pass extra arguments to the crawler.
- `make lint` – run static analysis with Ruff and format checks with Black.
- `make test` – run unit tests.
- `make clean` – remove build artifacts and cached data.

## Pre-commit hooks

Install the pre-commit hooks to guard the workflow:

```bash
source venv/bin/activate
pre-commit install
```

This repository ships with a `.pre-commit-config.yaml` that runs Ruff, Black, and `pytest --maxfail=1`.

## Configuration

Override crawler behaviour through CLI flags. Run `python -m akeyless_crawler.cli --help` for all options.

Key options include:

- `--output-dir`: Destination directory (default: `artifacts`).
- `--rate-limit`: Seconds to wait between requests.
- `--max-pages`: Optional ceiling to avoid runaway crawls.
- `--include-assets/--skip-assets`: Control asset downloading.

## Project layout

```
akeyless_crawler/
├── Makefile
├── README.md
├── requirements.txt
├── .pre-commit-config.yaml
├── src/
│   └── akeyless_crawler/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── crawler.py
│       └── storage.py
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   └── test_utils.py
└── scripts/
    └── run_checks.py
```

