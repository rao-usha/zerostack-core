PY=python
PIP=pip
FRONTEND_DIR=frontend
BACKEND_DIR=backend
API_MAIN=$(BACKEND_DIR)/main.py
DB_URL=postgresql+psycopg://nex:nex@localhost:5432/nex

.PHONY: verify format lint type test build smokes clean

verify: format lint type test build smokes

format:
	$(PY) -m black $(BACKEND_DIR)

lint:
	ruff check $(BACKEND_DIR)
	bandit -q -r $(BACKEND_DIR) || true

type:
	mypy $(BACKEND_DIR) --ignore-missing-imports

test:
	pytest -q --maxfail=1 --disable-warnings

build:
	cd $(FRONTEND_DIR) && npm ci && npm run build

smokes:
	bash scripts/smoke_backend.sh $(DB_URL)

clean:
	bash scripts/cleanup.sh

