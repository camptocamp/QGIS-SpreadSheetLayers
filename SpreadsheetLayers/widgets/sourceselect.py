# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpreadsheetLayersSourceSelect
                                 A QGIS plugin
 Load layers from MS Excel and OpenOffice spreadsheets
                              -------------------
        begin                : 2026-08-04
        copyright            : (C) 2026 by Camptocamp
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

from importlib import resources

from qgis.core import QgsProviderRegistry
from qgis.gui import QgsAbstractDataSourceWidget, QgsSourceSelectProvider
from qgis.PyQt import QtCore, QtGui, QtWidgets

from SpreadsheetLayers.widgets.SpreadsheetLayersDialog import SpreadsheetLayersDialog


class SpreadsheetLayersSourceSelect(QgsAbstractDataSourceWidget):
    """Source select widget embedded in the Data Source Manager dialog.

    It reuses the standalone SpreadsheetLayersDialog as a plain child widget
    and relies on the Data Source Manager buttons to add the layer.
    """

    def __init__(self, parent=None, fl=QtCore.Qt.WindowType.Widget, widgetMode=None):
        if widgetMode is None:
            widgetMode = QgsProviderRegistry.WidgetMode.Embedded
        super().__init__(parent, fl, widgetMode)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._dialog = None
        self._createDialog()

    def _createDialog(self):
        if self._dialog is not None:
            self._layout.removeWidget(self._dialog)
            self._dialog.setParent(None)
            self._dialog.deleteLater()

        self._dialog = SpreadsheetLayersDialog(self)
        self._dialog.setWindowFlags(QtCore.Qt.WindowType.Widget)
        self._layout.addWidget(self._dialog)

        # Turn the dialog button box into Add / Close / Help buttons and route
        # the "Add" button to addButtonClicked() (same pattern as Delimited Text).
        self.setupButtons(self._dialog.buttonBox)
        help_button = self._dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Help
        )
        if help_button is not None:
            help_button.hide()

        # setupButtons() disables the "Add" button and only re-enables it
        # through the enableButtons signal. Keep it enabled, validation is
        # done when the button is clicked (same behaviour as the standalone
        # dialog where the OK button is always active).
        self.enableButtons.emit(True)

    def addButtonClicked(self):
        if not self._dialog.validate():
            return
        if not self._dialog.writeVrt():
            return

        datasource = self._dialog.vrtPath()
        layer_name = self._dialog.layerName()
        self.emit_addVectorLayer(datasource, layer_name)

        if self.widgetMode() == QgsProviderRegistry.WidgetMode.Standalone:
            self.accept()

    def emit_addVectorLayer(self, datasource, layer_name):
        # addVectorLayer is deprecated but remains the signal handled by the
        # Data Source Manager in both QGIS 3.44 and 4.2 (see
        # QgsDataSourceManagerDialog::makeConnections).
        self.addVectorLayer.emit(datasource, layer_name, "ogr")

    def reset(self):
        # The Data Source Manager recycles this widget: it is created once and
        # only reset() is called on every reopening of the dialog (see
        # QgisApp::dataSourceManager). A reused Qt dialog is not repainted
        # after being hidden and shown again (Qt 5.12+, e.g. under Wayland),
        # leaving the page blank/black. Destroying and recreating the embedded
        # dialog on each reset() guarantees a fresh widget is painted on every
        # reopen.
        self._createDialog()


class SpreadsheetLayersSourceSelectProvider(QgsSourceSelectProvider):
    """Provider adding a Spreadsheet Layers tab to the Data Source Manager."""

    def providerKey(self):
        return "spreadsheet"

    def text(self):
        return "Add Spreadsheet Layer\u2026"

    def toolTip(self):
        return "Add a layer from a spreadsheet file (*.ods, *.xls, *.xlsx)"

    def icon(self):
        icon_path = (
            resources.files("SpreadsheetLayers")
            / "resources"
            / "icon"
            / "mActionAddSpreadsheetLayer.svg"
        )
        return QtGui.QIcon(str(icon_path))

    def ordering(self):
        # Tabs are sorted by ascending ordering(). Native tabs use
        # OrderLocalProvider=0, OrderDatabaseProvider=1000,
        # OrderRemoteProvider=2000, OrderSearchProvider=4000 (e.g. the
        # "metadata search" tab) and OrderOtherProvider=5000. Returning
        # OrderSearchProvider - 1000 places the tab after the remote
        # providers and just before the metadata search tab.
        return QgsSourceSelectProvider.OrderSearchProvider - 1000

    def createDataSourceWidget(
        self, parent=None, fl=QtCore.Qt.WindowType.Widget, widgetMode=None
    ):
        if widgetMode is None:
            widgetMode = QgsProviderRegistry.WidgetMode.Embedded
        return SpreadsheetLayersSourceSelect(parent, fl, widgetMode)
