PROJECT := $(notdir $(CURDIR))
VENV ?= $(HOME)/.venvs/$(PROJECT)

PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PREK := $(VENV)/bin/prek

.PHONY: setup check test clean

setup:
	python3.13 -m venv $(VENV)
	$(PIP) install -e ".[dev]"
	$(PREK) install

check:
	$(PREK) run --all-files

test:
	$(PYTHON) -m pytest

clean:
	rm -rf build dist *.egg-info src/*.egg-info
