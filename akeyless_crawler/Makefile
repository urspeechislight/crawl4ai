.PHONY: setup crawl lint test clean hooks

PYTHON ?= python3
VENV ?= venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PIP) install -r requirements.txt

crawl: $(VENV)/bin/python
	$(VENV_PYTHON) -m akeyless_crawler.cli crawl \
	  --start-url https://docs.akeyless.io/docs \
	  --start-url https://docs.akeyless.io/reference \
	  $(EXTRA)

lint: $(VENV)/bin/python
	$(VENV)/bin/ruff check src tests
	$(VENV)/bin/black --check src tests

test: $(VENV)/bin/python
	$(VENV)/bin/pytest --maxfail=1 --disable-warnings -q

clean:
	rm -rf $(VENV) artifacts .pytest_cache .ruff_cache
	rm -rf src/__pycache__ tests/__pycache__

hooks: $(VENV)/bin/python
	$(VENV)/bin/pre-commit install

$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PIP) install -r requirements.txt

