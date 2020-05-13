# --------------------------------------------------
# standard Makefile preamble
# see https://tech.davis-hansson.com/p/make/
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error Your Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >
# --------------------------------------------------

build: .build-sentinel

clean:
> rm -rf build
> rm -rf dist
> rm -f  .build-sentinel
.PHONY: clean

test:
> pytest tests/
.PHONY: test

push: test build
> twine check dist/*
> twine upload dist/*
.PHONY: push

.build-sentinel: $(shell find matsim/*.py) $(shell find docs/*) README.md setup.py
> rm -rf dist
> python3 setup.py sdist bdist_wheel
> twine check dist/*
> touch $@

