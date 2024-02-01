SHELL := /bin/bash

env:
	@# Install Poetry into base environment, if not already present
	(python3 -m poetry --version > /dev/null) || pip3 install poetry

	@# Note that Poetry creates *editable* install for root project by default
	python3 -m poetry install --all-extras --without scala_kernel

	@echo ""
	@echo "Please manually set this environment as default in IDE for this project."
	@echo "E.g., in the VSCode workspace file, add the following line:"
	@echo "\"settings\": {\"python.defaultInterpreterPath\": \"$(python3 -m poetry env info --executable)\"}"
	@echo "(This way you don't have to manually activate it for each shell using `python3 -m poetry shell`)"

	@# This needs to happen *after* installing sagemaker-sdk
	python3 -m poetry shell
	make mark-sagemaker-sdk-as-typed

# So we can use Scala in Jupyter notebooks
scala-kernel:
	python3 -m poetry install --with scala_kernel
	python -m spylon_kernel install --user

env-update:
	python3 -m poetry update

find-missing-typestubs:
	@echo "Looking for missing type stubs. If any, abort install using 'N' and install directly "
	@echo "using 'poetry add --group dev <packages>'"
	@mypy --install-types

mark-sagemaker-sdk-as-typed:
	@# todo: don't hard-code python version
	@python_dir=$$(poetry env info --path); \
	touch $${python_dir}/lib/python3.10/site-packages/sagemaker/py.typed

type-check:
	mypy src/sm_pipelines_oo

test:
	poetry run pytest

build:
	poetry build

publish:
	poetry publish
