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

version:
> npx standard-version
.PHONY: version

# The script produces wrong file names with hyphen. These are now rejected by pypi and fixed here.

.build-sentinel: $(shell find matsim/*.py) $(shell find docs/*) README.md setup.py VERSION
> rm -rf dist
> python3 setup.py sdist bdist_wheel
> for f in dist/matsim-tools-*.tar.gz; do [ -e "$$f" ] && mv "$$f" "$${f/matsim-tools/matsim_tools}"; done
> twine check dist/*
> touch $@

