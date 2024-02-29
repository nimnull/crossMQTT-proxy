TEST_ARGS ?=
BOLD := \033[1m
RESET := \033[0m
NAME ?=

test_local:
	poetry run pytest -sv "$(TEST_ARGS)"

.PHONY: install_poetry
install_poetry:
ifeq (,$(wildcard /opt/poetry/bin/poetry))
    curl -sSL https://install.python-poetry.org | python3 -
endif

.PHONY: setup
setup: install_poetry
	poetry install

.PHONY: setup_dev
setup_dev: setup
	pre-commit install

.PHONY: run_local
run_local:
	poetry run mqtt_bridge -c /opt/config.yaml

.PHONY: healthcheck
healthcheck:
	@echo "$(BOLD)Healthchecking docker process$(RESET)"
	@cat /proc/1/sched | head -n 1 && exit 0 || exit 1

build:
	docker build -t nimnull/mqtt-bridge:local .

shell:
	docker-compose run bridge /bin/bash

test:
	docker-compose down
	docker-compose run bridge make test_local TEST_ARGS="$(TEST_ARGS)"
