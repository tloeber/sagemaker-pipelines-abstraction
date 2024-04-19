SHELL := /bin/bash

# Variables to set by user
# ------------------------
# Set major and minor version of python to use
PYTHON_VERSION := 3.11

# *Derived* Variables (don't change)
# ----------------------------------
PYTHON := python${PYTHON_VERSION}
# Note: While it would be better organized to create this variable as part of the specific make
# command, it is easier to create a make variable here due to the complications from escaping, etc.
SAGEMAKER_PACKAGE_LOCATION=$(shell python -c "import importlib.util; print(importlib.util.find_spec('sagemaker').submodule_search_locations[0])")

env:
	# (Re-)create directory for virtual environments
	rm -rf .venv || echo "No existing virtual environment found."
	# Set poetry to install virtual environment into project folder, because otherwise venv name is not deterministic. See https://github.com/python-poetry/poetry/issues/263
	# Just in case, deactivate any activate environment first
	( deactivate &> /dev/null || echo "No virtual env active" ) && \
		${PYTHON} -m pip install poetry && \
		${PYTHON} -m poetry config virtualenvs.in-project true && \
		${PYTHON} -m poetry lock && \
		${PYTHON} -m poetry install --all-extras

	# @# This needs to happen *after* installing sagemaker-sdk
	make mark-sagemaker-sdk-as-typed

test-env:
	docker image build --build-arg="PYTHON_VERSION=3.10" -t sm-pipelines-oo-env-3.10 .
	docker image build --build-arg="PYTHON_VERSION=3.11" -t sm-pipelines-oo-env-3.11 .
	docker image build --build-arg="PYTHON_VERSION=3.12" -t sm-pipelines-oo-env-3.12 .

env-update:
	python3 -m poetry update

mark-sagemaker-sdk-as-typed:
	echo "Marking Sagemaker SDK as typed"
	touch ${SAGEMAKER_PACKAGE_LOCATION}/py.typed

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
	pytest tests/
	# Note: We're skipping tests in examples/ for now (they require different env)
lint:
	mypy src/sm_pipelines_oo --exclude '_tmp/' --exclude '_old/'

build:
	poetry build

publish:
	poetry publish