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
	$(DOCKER_RUN_CMD) make -f docker.mk build

.PHONY: docker-build
docker-build: ## Build docker images
	docker build --tag camptocamp/qgis-spreadsheetlayers:latest ./docker


###############
# TRANSLATION
###############

tx-pull: ## Pull translations from transifex using tx client
	docker-compose run --rm --user `id -u` -v "$(HOME)/.transifexrc:/home/user/.transifexrc" tester make -f docker.mk tx-pull

tx-push: ## Push translations on transifex using tx client
	docker-compose run --rm --user `id -u` -v "$(HOME)/.transifexrc:/home/user/.transifexrc" tester make -f docker.mk tx-push


#############
# PACKAGING
#############

package: ## Create plugin archive
package: build
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
