PLUGINNAME = SpreadsheetLayers
LOCALES = de fr ja ru

SOURCES := $(shell (cd $(PLUGINNAME) && find . -name "*.py") )
FORMS = $(shell (cd $(PLUGINNAME) && find . -name "*.ui") )


default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'

build: doc transcompile


#################
# DOCUMENTATION
#################

doc: ## Generate documentation files
	make -C help html
	mkdir -p $(PLUGINNAME)/help/
	cp -r help/build/html/* $(PLUGINNAME)/help/


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


###############
# TRANSLATION
###############

tx-pull: ## Pull translations from transifex using tx client
tx-pull: $(HOME)/.transifexrc
	mkdir -p $(PLUGINNAME)/i18n
	tx pull --all

tx-push: ## Push translations on transifex using tx client
tx-push: transup
	tx push --source

transup: ## Update translation catalogs
transup: $(PLUGINNAME)/i18n/SpreadsheetLayers_en.ts
transup: help/locale/index.pot

.INTERMEDIATE: $(PLUGINNAME)/SpreadsheetLayers.pro
.PHONY: $(PLUGINNAME)/SpreadsheetLayers.pro
$(PLUGINNAME)/SpreadsheetLayers.pro:
	echo "SOURCES = $(SOURCES)" > $@
	echo "FORMS = $(FORMS)" >> $@
	echo "TRANSLATIONS = i18n/SpreadsheetLayers_en.ts" >> $@
	echo "CODECFORTR = UTF-8" >> $@
	echo "CODECFORSRC = UTF-8" >> $@

.INTERMEDIATE: $(PLUGINNAME)/i18n/SpreadsheetLayers_en.ts
$(PLUGINNAME)/i18n/SpreadsheetLayers_en.ts: $(PLUGINNAME)/SpreadsheetLayers.pro
	mkdir -p $(dir $@)
	pylupdate5 -noobsolete $(PLUGINNAME)/SpreadsheetLayers.pro

.INTERMEDIATE: help/locale/index.pot
help/locale/index.pot:
	make -C help gettext

transcompile: ## Compile Qt .ts translation files into .qm binary format
transcompile:
	lrelease $(shell find -name *.ts)
