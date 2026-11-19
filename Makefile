
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(PYTHON) -m pytest
PORT ?= 5000

.PHONY: venv test-all coverage clean

venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR); \
		echo "Ambiente virtual criado."; \
	else \
		echo "Ambiente virtual já existe."; \
	fi
	$(PIP) install -r requirements.txt

run: venv
	PORT=$(PORT) $(PYTHON) app.py

test-unit: venv
    $(PYTEST) tests/test_arvore_parsing.py tests/test_trie_compacta.py tests/test_utils.py

test-integration: venv
    $(PYTEST) tests/test_app_integracao.py

test-all: test-unit test-integration

coverage: venv
	$(PYTEST) tests/ --cov=. --cov-report=term-missing

clean:
	rm -rf $(VENV_DIR) .pytest_cache .coverage htmlcov