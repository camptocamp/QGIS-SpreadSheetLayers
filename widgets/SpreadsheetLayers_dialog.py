# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpreadsheetLayersPluginDialog
                                 A QGIS plugin
 Load layers from MS Excel and OpenOffice spreadsheets
                             -------------------
        begin                : 2014-10-30
        git sha              : $Format:%H$
        copyright            : (C) 2014 by Camptocamp
        email                : info@camptocamp.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic

from ..ui.ui_SpreadsheetLayers_dialog import Ui_SpreadsheetLayersPluginDialogBase


class SpreadsheetLayersPluginDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(SpreadsheetLayersPluginDialog, self).__init__(parent)
        self.ui = Ui_SpreadsheetLayersPluginDialogBase()
        self.ui.setupUi(self)
