
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(PYTHON) -m pytest

.PHONY: venv test-all coverage clean

venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR); \
		echo "Ambiente virtual criado."; \
	else \
		echo "Ambiente virtual já existe."; \
	fi
	$(PIP) install -r requirements.txt

test-all: venv
	$(PYTEST) -v tests/

coverage: venv
	$(PYTEST) tests/ --cov=src --cov-report=term-missing

clean:
	rm -rf $(VENV_DIR) .pytest_cache .coverage htmlcov
