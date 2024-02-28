SHELL := /bin/bash

env:
	(python3 -m poetry --version > /dev/null) || pip3 install poetry
	python3 -m poetry lock
	python3 -m poetry install --all-extras