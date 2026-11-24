
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
	$(PYTEST) tests/unit/

test-integration: venv
	$(PYTEST) tests/integration/

test-e2e: venv
	$(PYTHON) app.py & \
	SERVER_PID=$$!; \
	trap "kill $$SERVER_PID 2>/dev/null || true" EXIT; \
	sleep 2; \
	npx cypress open
	
test: test-unit test-integration

coverage: venv
	$(PYTEST) -v --cov=app --cov=src --cov-branch --cov-report=term-missing tests/

clean:
	rm -rf $(VENV_DIR) .pytest_cache .coverage htmlcov