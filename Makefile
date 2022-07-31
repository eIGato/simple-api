SHELL := /bin/bash

SOURCES := $(shell find app -name "*.py")
TESTS := $(shell find tests -name "*.py")

PIP_COMPILE = docker run --rm \
	--mount type=bind,src=$(shell pwd),target=/src \
	-w /src \
	--user $(shell id -u):$(shell id -g) \
	otkds/piptools:python3.10 \
	compile --cache-dir=/src/.piptools-cache

## Build

.PHONY: build requirements up

build: .buildts

.buildts: Dockerfile requirements.txt requirements-dev.txt
	docker-compose build app
	touch $@

up: .buildts
	docker-compose up app

requirements: requirements.txt requirements-dev.txt

requirements.txt: requirements.in
	$(PIP_COMPILE) requirements.in -o $@.new
	mv $@.new $@

requirements-dev.txt: requirements.txt requirements-dev.in
	$(PIP_COMPILE) requirements-dev.in -o $@.new
	mv $@.new $@

## DB

.PHONY: new-migration reset-db sync-db

reset-db: .buildts
	docker-compose run --rm app bash -c "python -m alembic downgrade base && python -m alembic upgrade head"

sync-db: .buildts
	docker-compose run --rm app python -m alembic upgrade head

new-migration: .buildts
	@test -n "$(message)" || \
		(echo $$'\e[01;31m'"Usage: make new-migration message=..."$$'\e[0m' && false)
	docker-compose run --rm app python -m alembic revision --autogenerate -m "$(message)"

## Test

.PHONY: test coverage

test .coverage: $(SOURCES) $(TESTS) | .buildts
	docker-compose run --rm app python -m pytest

coverage: .coverage
	docker-compose run --rm app coverage report --rcfile=setup.cfg

coverage.xml: .coverage
	docker-compose run --rm app coverage xml --rcfile=setup.cfg

## Code style

.PHONY: autoformat setup-git-hooks static-check

autoformat:
	docker-compose run --rm app autoflake \
		--in-place \
		--recursive \
		--remove-all-unused-imports \
		--ignore-init-module-imports \
		--remove-unused-variables \
		.
	docker-compose run --rm app isort .
	docker-compose run --rm app black .

static-check:
	docker-compose run --rm app flake8
	docker-compose run --rm app mypy

setup-git-hooks:
	src/hooks/setup-git-hooks.sh
