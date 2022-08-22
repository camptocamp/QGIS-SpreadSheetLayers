PLUGINNAME = SpreadsheetLayers
LOCALES = de fr ja ru

default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'


########
# Lint #
########

.PHONY: check
check: ## Run all linters
check: black-check flake8

.PHONY: black
black:
	black $(PLUGINNAME) tests

.PHONY: black-check
black-check:
	black --check $(PLUGINNAME) tests

.PHONY: flake8
flake8:
	flake8 $(PLUGINNAME) tests


#########
# Tests #
#########

.PHONY: nosetests
nosetests: ## Run tests using nose
	nosetests -v --with-id --with-coverage --cover-package=$(PLUGINNAME) ${NOSETESTS_ARGS}

.PHONY: pytest
pytest:  ## Run tests using pytest
	pytest --cov --verbose --color=yes -vv ${PYTEST_ARGS}

.PHONY: coverage
coverage: ## Display coverage report
	coverage report -m
