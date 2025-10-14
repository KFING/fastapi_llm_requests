SHELL:=bash
NOWSTAMP := $(shell bash -c 'date -u +"%Y%m%dT%H%M%S"')
CWD := $(shell bash -c 'pwd')

.PHONY: setup
setup:
	poetry install --sync
	make compose-up
	make migrations-run
	#git config core.hooksPath dev/.githooks

.PHONY: dev
dev:
	make format
	make lint
	make compose-up
	make test

safety:
	#poetry run safety check --full-report
	poetry run pip check
	poetry check

.PHONY: lint
lint:
	poetry run ruff check --respect-gitignore --fix --extend-exclude tests ./
	poetry run ruff format --diff --respect-gitignore
	poetry run mypy --exclude migration/ .
	poetry run pyright src/

.PHONY: format
format:
	poetry run ruff format --respect-gitignore --preview .

.PHONY: test
test:
	ENV=test poetry run pytest -vv --exitfirst --failed-first --log-level debug

.PHONY: test_mocked
test_mocked:
	TEST_MOCK_CACHE=1 ENV=test poetry run pytest -vv --exitfirst --failed-first

.PHONY: test_no_logs
test_no_logs:
	TEST_NO_TRACEBACK=1 ENV=test poetry run pytest -vv --capture=no --exitfirst --failed-first

.PHONY: test_failed
test_failed:
	make test-failed

.PHONY: test-failed
test-failed:
	ENV=test PYTHONPATH=${CWD} poetry run pytest -vv --full-trace --failed-first --exitfirst --last-failed --show-capture=all

.PHONY: test-specific
test-specific:
	# add your test here
	ENV=test PYTHONPATH=${CWD} poetry run pytest -vv --full-trace --failed-first --exitfirst --show-capture=all ./tests/tests/checkout/test_paddle_webhook.py

.PHONY: test-cov
test-cov:
	ENV=test PYTHONPATH=${CWD} poetry run pytest \
		--cov=src \
		--cov=external \
		--cov-report=xml \
		--cov-report=html \
		--cov-report=term-missing:skip-covered \
		--cov-fail-under=70.0

.PHONY: app_api
app_api:
	poetry run uvicorn src.app_api.main:get_app \
		--timeout-graceful-shutdown 10 \
		--limit-max-requests 1024 \
		--loop asyncio \
		--use-colors \
		--reload \
		--host 0.0.0.0 \
		--port 41234 \
		--log-level error \
		--no-access-log

.PHONY: compose-up
compose-up:
	docker compose up --build --remove-orphans --wait -d keycloak_db keycloak postgres

.PHONY: compose-down
compose-down:
	docker compose down

