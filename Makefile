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
DEFAULT_QGIS_PREFIX_PATH=/usr
QGISDIR ?= .local/share/QGIS/QGIS3/profiles/default
###################END CONFIGURE#########################

PLUGIN_UPLOAD = ./plugin_upload.py

PACKAGESSOURCES := $(shell find $(PACKAGES) -name "*.py")
SOURCES := SpreadsheetLayersPlugin.py $(PACKAGESSOURCES)
SOURCES_FOR_I18N = $(SOURCES:%=../%)
FORMS = $(shell find $(PACKAGES) -name "*.ui")
FORMS_FOR_I18N = $(FORMS:%=../%)

# QGIS PATHS
ifndef QGIS_PREFIX_PATH
export QGIS_PREFIX_PATH=$(DEFAULT_QGIS_PREFIX_PATH)
endif

export LD_LIBRARY_PATH:="$(QGIS_PREFIX_PATH)/lib:$(LD_LIBRARY_PATH)"
export PYTHONPATH:=$(PYTHONPATH):$(QGIS_PREFIX_PATH)/share/qgis/python:$(HOME)/.qgis2/python/plugins:$(CURDIR)/..:$(CURDIR)/lib/python2.7/site-packages/
export PYTHONPATH:=$(PYTHONPATH):$(CURDIR)/test  # PG

ifndef QGIS_DEBUG
# Default to Quiet version
export QGIS_DEBUG=0
export QGIS_LOG_FILE=/dev/null
export QGIS_DEBUG_FILE=/dev/null
endif

default: compile
.PHONY: clean transclean deploy doc help

help:
	@echo
	@echo "------------------"
	@echo "Available commands"
	@echo "------------------"
	@echo
	@echo 'make [compile]'
	@echo 'make clean'
	@echo 'make test'
	@echo 'make package VERSION=\<version\> HASH=\<hash\>'
	@echo 'make deploy'
	@echo 'make stylecheck|pep8|pylint'
	@echo 'make help'

test: compile transcompile
	@echo
	@echo "----------------------"
	@echo "Regression Test Suite"
	@echo "----------------------"

	@# Preceding dash means that make will continue in case of errors
	@-export PYTHONPATH=`pwd`:$(PYTHONPATH); \
		export QGIS_DEBUG=0; \
		export QGIS_LOG_FILE=/dev/null; \
		nosetests -v --with-id --with-coverage --cover-package=. \
		3>&1 1>&2 2>&3 3>&- || true
	@echo "----------------------"
	@echo "If you get a 'no module named qgis.core error, try sourcing"
	@echo "the helper script we have provided first then run make test."
	@echo "e.g. source run-env-linux.sh <path to qgis install>; make test"
	@echo "----------------------"
	
################COMPILE#######################
compile:
	@echo
	@echo "------------------------------"
	@echo "Compile ui and resources forms"
	@echo "------------------------------"
	mkdir -p .build
	virtualenv -p python3 .build/venv
	.build/venv/bin/pip install -r requirements.txt
	make -C resources
	make transcompile
	make html -C help

################CLEAN#######################
clean:
	@echo
	@echo "------------------------------"
	@echo "Clean ui and resources forms"
	@echo "------------------------------"
	rm -rf .build
	rm -f *.pyc
	make clean -C help
	make clean -C ui
	make clean -C resources

################TESTS#######################
.ONESHELL:
tests:
	@echo "------------------------------"
	@echo "Running test suite"
	@echo "------------------------------"
	export LD_LIBRARY_PATH=$(LD_LIBRARY_PATH)
	export PYTHONPATH=$(PYTHONPATH)
	./bin/pip install -q mock coverage
	unset GREP_OPTIONS
	nosetests -v test --nocapture --with-id --with-coverage --cover-package=$(PLUGINNAME) 3>&1 1>&2 2>&3 3>&- | \grep -v "^Object::" || true

################TRANSLATION#######################
updatei18nconf:
	echo "SOURCES = $(SOURCES_FOR_I18N)" > i18n/i18n.generatedconf
	echo "FORMS = $(FORMS_FOR_I18N)" >> i18n/i18n.generatedconf
	echo "TRANSLATIONS = $(TRANSLATIONS)" >> i18n/i18n.generatedconf
	echo "CODECFORTR = UTF-8" >> i18n/i18n.generatedconf
	echo "CODECFORSRC = UTF-8" >> i18n/i18n.generatedconf

# transup: update .ts translation files
transup: updatei18nconf
	pylupdate5 -noobsolete i18n/i18n.generatedconf
	rm -f i18n/i18n.generatedconf
	make transup -C help

# transcompile: compile translation files into .qm binary format
transcompile: $(TRANSLATIONS:%.ts=i18n/%.qm)

# transclean: deletes all .qm files
transclean:
	rm -f i18n/*.qm

%.qm : %.ts
	lrelease $<

deploy: ## Deploy plugin to your QGIS plugin directory (to test zip archive)
deploy: package derase
	unzip $(PLUGINNAME).zip -d $(HOME)/$(QGISDIR)/python/plugins/

derase: ## Remove deployed plugin from your QGIS plugin directory
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

################PACKAGE############################
# Create a zip package of the plugin named $(PLUGINNAME).zip.
# This requires use of git (your plugin development directory must be a
# git repository).

package: compile transcompile
	rm -f $(PLUGINNAME).zip
	rm -rf $(PLUGINNAME)/
	mkdir -p $(PLUGINNAME)/ui/
	cp ui/*.py $(PLUGINNAME)/ui/
	mkdir -p $(PLUGINNAME)/help/build
	cp -r help/build/html $(PLUGINNAME)/help/build/
	mkdir -p $(PLUGINNAME)/i18n/
	cp i18n/*.qm $(PLUGINNAME)/i18n/
	git archive -o $(PLUGINNAME).zip --prefix=$(PLUGINNAME)/ HEAD
	zip -d $(PLUGINNAME).zip $(PLUGINNAME)/\*Makefile
	zip -d $(PLUGINNAME).zip $(PLUGINNAME)/.gitignore
	zip -g $(PLUGINNAME).zip $(PLUGINNAME)/*/*
	zip -g $(PLUGINNAME).zip `find $(PLUGINNAME)/help/build/html`
	zip -g $(PLUGINNAME).zip $(PLUGINNAME)/*.qm
	rm -rf $(PLUGINNAME)/
	echo "Created package: $(PLUGINNAME).zip"

.PHONY: upload
upload: ## Upload plugin to QGIS Plugin repo
upload: package
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

################VALIDATION#######################
# validate syntax style
stylecheck: pep8 pylint

.ONESHELL:
pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@./bin/pip install -q pylint
	@export LD_LIBRARY_PATH=$(LD_LIBRARY_PATH)
	@export PYTHONPATH=$(PYTHONPATH)
	# @./bin/pylint --output-format=parseable --reports=y --rcfile=pylintrc $(PACKAGES_NO_UI) || true
	@./bin/pylint --reports=y --rcfile=pylintrc $(PACKAGES_NO_UI) || true

pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@./bin/pip install -q pep8
	@./bin/pep8 --repeat --ignore=E501 --exclude ui,lib,doc resources . || true

.PHONY: link
link: ## Create symbolic link to this folder in your QGIS plugins folder (for development)
link: derase
	ln -s $(shell pwd) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
