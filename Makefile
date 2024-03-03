SHELL := /bin/bash

env:
	@# Install Poetry into base environment, if not already present
	(python3 -m poetry --version > /dev/null) || pip3 install poetry

	@# Note that Poetry creates *editable* install for root project by default
	@# (unless package-mode is set to `false`)
	 -m poetry install --all-extras --without scala_kernel

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

mark-sagemaker-sdk-as-typed:
	@# todo: don't hard-code python version
	@python_dir=$$(poetry env info --path); \
	touch $${python_dir}/lib/python3.10/site-packages/sagemaker/py.typed
	# TODO: Generalize to any python version

type-check:
	mypy src/sm_pipelines_oo --exclude '_tmp/' --exclude '_old/'

find-missing-typestubs:
	@# First *run* type check to refresh mypy cache, but ignore any errors for now.
	@mypy src/sm_pipelines_oo --exclude '_tmp/' &> /dev/null || echo ""
	@echo "Looking for missing type stubs. If any, abort install using 'N' and install directly "
	@echo "using 'poetry add --group dev <packages>'"
	@mypy --install-types

find-untyped-imports:
	@echo "Untyped imports ignored:"
	@# Note: -F is for fixed strings, so it's not interpreted as a regex
	@cat $$(find src/sm_pipelines_oo -type f -name '*.py') | grep -F 'type: ignore[import-untyped]' || echo "None found"
	@echo ""
	@echo "Untyped imports found:"
	@mypy src/sm_pipelines_oo --exclude '_tmp/' --exclude '_old/' |  grep -F 'import-untyped' || echo "None found"

test:
	poetry run pytest

build:
	poetry build

publish:
	poetry publish
