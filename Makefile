#/***************************************************************************
# SpreadsheetLayersPlugin
#
# Load layers from MS Excel and OpenOffice spreadsheets
#							 -------------------
#		begin				: 2014-10-30
#		git sha				: $Format:%H$
#		copyright			: (C) 2014 by Camptocamp
#		email				: info@camptocamp.com
# ***************************************************************************/
#
#/***************************************************************************
# *																		 *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	 *
# *   (at your option) any later version.								   *
# *																		 *
# ***************************************************************************/

###################CONFIGURE HERE########################
PLUGINNAME = SpreadsheetLayers

#this can be overiden by calling QGIS_PREFIX_PATH=/my/path make
# DEFAULT_QGIS_PREFIX_PATH=/usr/local/qgis-master
DEFAULT_QGIS_PREFIX_PATH = /usr
QGISDIR ?= .local/share/QGIS/QGIS3/profiles/default
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/japanese
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/french
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/german
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/russian
###################END CONFIGURE#########################

SOURCES := $(shell (cd $(PLUGINNAME) && find . -name "*.py") )
FORMS = $(shell (cd $(PLUGINNAME) && find . -name "*.ui") )

# QGIS PATHS
ifndef QGIS_PREFIX_PATH
export QGIS_PREFIX_PATH=$(DEFAULT_QGIS_PREFIX_PATH)
endif

export LD_LIBRARY_PATH:="$(QGIS_PREFIX_PATH)/lib:$(LD_LIBRARY_PATH)"
export PYTHONPATH:=$(PYTHONPATH):$(QGIS_PREFIX_PATH)/share/qgis/python:$(CURDIR)

ifndef QGIS_DEBUG
# Default to Quiet version
export QGIS_DEBUG=0
export QGIS_LOG_FILE=/dev/null
export QGIS_DEBUG_FILE=/dev/null
endif

export DOCKER_BUILDKIT=1

DOCKER_RUN_CMD = docker-compose run --rm --user `id -u` tester

-include local.mk

default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'


################
# MAIN TARGETS
################

.PHONY: compile
compile: ## Create all runtime files
compile: doc transcompile

.PHONY: clean
clean: ## Delete generated files
	git clean -dfX

.PHONY: qgis
qgis: ## Run QGIS desktop
	docker-compose run --rm --user `id -u`:`id -g` qgis

.PHONY: check
check: ## Run linters
	$(DOCKER_RUN_CMD) make -f docker.mk check

.PHONY: black
black: ## Run black formatter
	$(DOCKER_RUN_CMD) make -f docker.mk black

.PHONY: tests
test: ## Run the automated tests suite
	$(DOCKER_RUN_CMD) make -f docker.mk pytest

.PHONY: nosetests
nosetests: ## Run the automated tests suite with nose (useful when QGIS crash)
	$(DOCKER_RUN_CMD) make -f docker.mk nosetests

.PHONY: test-overwrite-expected
test-overwrite-expected: ## Run the automated tests suite and overwrite expected results
	docker-compose run --rm --user `id -u` -e OVERWRITE_EXPECTED=true tester make -f docker.mk pytest

.PHONY: bash
bash: ## Run bash in tests container
	$(DOCKER_RUN_CMD) bash


build: docker-build

.PHONY: docker-build
docker-build: ## Build docker images
docker-build:
	docker build --tag camptocamp/qgis-spreadsheetlayers:latest ./docker


#################
# DOCUMENTATION
#################

doc: ## Generate documentation files
doc: venv tx-pull
	make -C help html
	mkdir -p $(PLUGINNAME)/help/
	cp -r help/build/html/* $(PLUGINNAME)/help/


###############
# TRANSLATION
###############

tx-pull: ## Pull translations from transifex using tx client
tx-pull: venv
	mkdir -p $(PLUGINNAME)/i18n
	.build/venv/bin/tx pull --all || true

tx-push: ## Push translations on transifex using tx client
tx-push: venv gettext
	.build/venv/bin/tx -d push -s

gettext: ## Update translation catalogs
gettext: $(PLUGINNAME)/i18n/SpreadsheetLayers_en.ts
gettext: help/locale/index.pot

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
help/locale/index.pot: venv
	make -C help gettext

transcompile: ## Compile Qt .ts translation files into .qm binary format
transcompile:
	lrelease $(shell find -name *.ts)


#############
# PACKAGING
#############

package: ## Create plugin archive
package: compile
	@echo
	@echo "------------------------------------"
	@echo "Exporting plugin to zip package.	"
	@echo "------------------------------------"
	mkdir -p dist
	rm -f dist/$(PLUGINNAME).zip
	zip dist/$(PLUGINNAME).zip -r $(PLUGINNAME) -x '*/__pycache__/*'
	echo "Created package: dist/$(PLUGINNAME).zip"

.PHONY: upload
upload: package
upload: ## Upload the plugin archive on QGIS official repository
	python3 ./scripts/upload_plugin.py --username $(OSGEO_USERNAME) --password $(OSGEO_PASSWORD) dist/SpreadsheetLayers.zip


#############
# DEBUGGING
#############

.PHONY: deploy
deploy: ## Deploy plugin to your QGIS plugin directory (to test zip archive)
deploy: package derase
	unzip dist/$(PLUGINNAME).zip -d $(HOME)/$(QGISDIR)/python/plugins/

.PHONY: derase
derase: ## Remove deployed plugin from your QGIS plugin directory
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

.PHONY: link
link: ## Create symbolic link to this folder in your QGIS plugins folder (for development)
link: derase
	ln -s $(shell pwd)/$(PLUGINNAME) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)


###############
# VIRTUAL ENV
###############

.PHONY: venv
venv: .build/requirements-dev.timestamp

.build/venv.timestamp:
	python3 -m venv --system-site-packages .build/venv
	touch $@

.build/requirements-dev.timestamp: .build/venv.timestamp docker/requirements-dev.txt
	.build/venv/bin/pip install -r docker/requirements-dev.txt
	touch $@
