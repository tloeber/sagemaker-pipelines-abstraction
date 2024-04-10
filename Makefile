SHELL := /bin/bash

env:
	@# Install Poetry into base environment, if not already present
	(python3 -m poetry --version > /dev/null) || pip3 install poetry

	@# Note that Poetry creates *editable* install for root project by default
	@# (unless package-mode is set to `false`)
	poetry install --all-extras --without scala_kernel

	@echo ""
	@echo "Please manually set this environment as default in IDE for this project."
	@echo "E.g., in the VSCode workspace file, add the following line:"
	@echo "\"settings\": {\"python.defaultInterpreterPath\": \"$(python3 -m poetry env info --executable)\"}"
	@echo "(This way you don't have to manually activate it for each shell using `python3 -m poetry shell`)"

	# @# This needs to happen *after* installing sagemaker-sdk
	python3 -m poetry shell || echo "Failed to activate newly created poetry env." # Doesn't work in Docker container
	make mark-sagemaker-sdk-as-typed

docker-env:
	docker image build --build-arg="PYTHON_VERSION=3.10" -t sm-pipelines-oo-env .

# So we can use Scala in Jupyter notebooks
scala-kernel:
	python3 -m poetry install --with scala_kernel
	python -m spylon_kernel install --user

env-update:
	python3 -m poetry update

mark-sagemaker-sdk-as-typed:
	PYTHON_MINOR_VERSION="$$(poetry run python -c 'import sys; print(sys.version_info.minor)')"; \
	PYTHON_DIR=$$(poetry env info --path); \
	touch $${PYTHON_DIR}/lib/python3.$${PYTHON_MINOR_VERSION}/site-packages/sagemaker/py.typed

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
	poetry run pytest tests/

lint:
	poetry run mypy src/sm_pipelines_oo --exclude '_tmp/' --exclude '_old/'

build:
	poetry build

publish:
	poetry publish
