SHELL := /bin/bash

env:
	(python3 -m poetry --version > /dev/null) || pip3 install poetry
	python3 -m poetry lock
	python3 -m poetry install --all-extras

	@# This needs to happen *after* installing sagemaker-sdk
	python3 -m poetry shell
	make mark-sagemaker-sdk-as-typed

env-update:
	python3 -m poetry update

type-check:
	mypy src/smp_oo_examples --exclude '_tmp/' --exclude '_old/'

find-missing-typestubs:
	@# First *run* type check to refresh mypy cache, but ignore any errors for now.
	@mypy src/smp_oo_examples --exclude '_tmp/' &> /dev/null || echo ""
	@echo "Looking for missing type stubs. If any, abort install using 'N' and install directly "
	@echo "using 'poetry add --group dev <packages>'"
	@mypy --install-types

find-untyped-imports:
	@echo "Untyped imports ignored:"
	@# Note: -F is for fixed strings, so it's not interpreted as a regex
	@cat $$(find src/smp_oo_examples -type f -name '*.py') | grep -F 'type: ignore[import-untyped]' || echo "None found"
	@echo ""
	@echo "Untyped imports found:"
	@mypy src/smp_oo_examples --exclude '_tmp/' --exclude '_old/' |  grep -F 'import-untyped' || echo "None found"

mark-sagemaker-sdk-as-typed:
	@# todo: don't hard-code python version
	@python_dir=$$(poetry env info --path); \
	touch $${python_dir}/lib/python3.10/site-packages/sagemaker/py.typed
	# TODO: Generalize to any python version

test:
	poetry run pytest

build:
	poetry build

publish:
	poetry publish
