# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpreadsheetLayersPlugin
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
import os.path
from qgis.core import QGis, QgsVectorLayer, QgsMapLayerRegistry
from PyQt4 import QtCore, QtGui
# Initialize Qt resources from file resources.py
from .ui import resources_rc
# Import the code for the dialog
from .widgets.SpreadsheetLayersDialog import SpreadsheetLayersDialog


class SpreadsheetLayersPlugin(QtCore.QObject):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        super(SpreadsheetLayersPlugin, self).__init__()
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QtCore.QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SpreadsheetLayers_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QtCore.QTranslator()
            self.translator.load(locale_path)

            if QtCore.qVersion() > '4.3.3':
                QtCore.QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.action = QtGui.QAction(
            QtGui.QIcon(':/plugins/SpreadsheetLayers/icon/mActionAddSpreadsheetLayer.svg'),
            self.tr("Add spreadsheet layer"),
            self)
        self.action.triggered.connect(self.showDialog)
        if QGis.QGIS_VERSION_INT > 20400:
            self.iface.addLayerMenu().addAction(self.action)
        else:
            menu = self.iface.layerMenu()
            for action in menu.actions():
                if action.isSeparator():
                    break
            self.iface.layerMenu().insertAction(action, self.action)
        self.iface.layerToolBar().addAction(self.action)

    def unload(self):
        if hasattr(self, 'action'):
            if QGis.QGIS_VERSION_INT > 20400:
                self.iface.addLayerMenu().removeAction(self.action)
            else:
                self.iface.layerMenu().removeAction(self.action)
            self.iface.layerToolBar().removeAction(self.action)

    def showDialog(self):
        dlg = SpreadsheetLayersDialog(self.iface.mainWindow())
        dlg.show()
        if dlg.exec_():
            layer = QgsVectorLayer(dlg.vrtPath(), dlg.layerName(), 'ogr')

            '''
            layer = QgsVectorLayer("?field=id:integer&field=name", dlg.layerName(), "memory")
            pr = layer.dataProvider()
            from qgis.core import QgsField
            pr.addAttributes([QgsField("name", QVariant.String),
                                QgsField("age", QVariant.Int),
                                QgsField("size", QVariant.Double)])

            # add a feature
            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(10, 10)))
            fet.setAttributes(["Johny", 2, 0.3])
            pr.addFeatures([fet])
            '''

            if not layer.isValid():
                print "Layer failed to load"
            else:
                QgsMapLayerRegistry.instance().addMapLayer(layer)
        dlg.deleteLater()
