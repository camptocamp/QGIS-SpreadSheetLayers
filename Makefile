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
PACKAGES_NO_UI = widgets
PACKAGES = $(PACKAGES_NO_UI) ui
LANGUAGES = de fr ja ru
TRANSLATIONS = $(addprefix SpreadsheetLayers_, $(addsuffix .ts, $(LANGUAGES) ) )

#this can be overiden by calling QGIS_PREFIX_PATH=/my/path make
# DEFAULT_QGIS_PREFIX_PATH=/usr/local/qgis-master
DEFAULT_QGIS_PREFIX_PATH = /usr
QGISDIR ?= .local/share/QGIS/QGIS3/profiles/default
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/japanese
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/french
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/german
# QGISDIR ?= .local/share/QGIS/QGIS3/profiles/russian
###################END CONFIGURE#########################

SOURCES := $(shell (cd $(PLUGINNAME)/i18n && find .. -name "*.py") )
FORMS = $(shell (cd $(PLUGINNAME)/i18n && find .. -name "*.ui") )

toto:
	@echo $(SOURCES)
	@echo $(SOURCES_FOR_I18N)

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


default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'


.PHONY: compile
compile: ## Create all runtime files
compile: doc transcompile

.PHONY: clean
clean: ## Delete generated files
	@echo
	@echo "------------------------------"
	@echo "Clean ui and resources forms"
	@echo "------------------------------"
	rm -rf .build
	make clean -C help
	rm -f $(PLUGINNAME)/*.pyc
	rm -rf $(PLUGINNAME)/help
	rm -f $(PLUGINNAME)/i18n/*.qm


doc: ## Generate documentation files
doc: .build/requirements-dev.timestamp
	make -C help html
	cp -r help/build/html $(PLUGINNAME)/help


################TRANSLATION#######################

.PHONY: updatei18nconf
updatei18nconf:
	echo "SOURCES = $(SOURCES)" > $(PLUGINNAME)/i18n/i18n.generatedconf
	echo "FORMS = $(FORMS)" >> $(PLUGINNAME)/i18n/i18n.generatedconf
	echo "TRANSLATIONS = $(TRANSLATIONS)" >> $(PLUGINNAME)/i18n/i18n.generatedconf
	echo "CODECFORTR = UTF-8" >> $(PLUGINNAME)/i18n/i18n.generatedconf
	echo "CODECFORSRC = UTF-8" >> $(PLUGINNAME)/i18n/i18n.generatedconf

transup: ## Update .ts translation files
transup: updatei18nconf
	pylupdate5 -noobsolete $(PLUGINNAME)/i18n/i18n.generatedconf
	rm -f $(PLUGINNAME)/i18n/i18n.generatedconf
	make -C help transup

transcompile: ## Compile translation files into .qm binary format
transcompile: $(TRANSLATIONS:%.ts=$(PLUGINNAME)/i18n/%.qm)

%.qm : %.ts
	lrelease $<

.PHONY: deploy
deploy: ## Deploy plugin to your QGIS plugin directory (to test zip archive)
deploy: package derase
	unzip dist/$(PLUGINNAME).zip -d $(HOME)/$(QGISDIR)/python/plugins/

.PHONY: derase
derase: ## Remove deployed plugin from your QGIS plugin directory
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

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

.PHONY: link
link: ## Create symbolic link to this folder in your QGIS plugins folder (for development)
link: derase
	ln -s $(shell pwd)/$(PLUGINNAME) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)


.build/venv.timestamp:
	python3 -m venv --system-site-packages .build/venv
	touch $@

.build/requirements-dev.timestamp: .build/venv.timestamp requirements-dev.txt
	.build/venv/bin/pip install -r requirements-dev.txt
	touch $@
