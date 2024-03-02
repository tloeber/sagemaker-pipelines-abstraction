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

find-missing-typestubs:
	@# First *run* type check to refresh mypy cache, but ignore any errors for now.
	@mypy src/sm_pipelines_oo --exclude '_tmp/' &> /dev/null || echo ""
	@echo "Looking for missing type stubs. If any, abort install using 'N' and install directly "
	@echo "using 'poetry add --group dev <packages>'"
	@mypy --install-types

mark-sagemaker-sdk-as-typed:
	@# todo: don't hard-code python version
	@python_dir=$$(poetry env info --path); \
	touch $${python_dir}/lib/python3.10/site-packages/sagemaker/py.typed
	# TODO: Generalize to any python version

type-check:
	mypy src/smp_oo_examples --exclude '_tmp/'

test:
	poetry run pytest

build:
	poetry build

publish:
	poetry publish
