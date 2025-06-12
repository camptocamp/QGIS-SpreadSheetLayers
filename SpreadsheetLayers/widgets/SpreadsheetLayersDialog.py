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
from pathlib import *
import sys
if sys.version_info.major == 3 and sys.version_info.minor >= 6:
    # from qgis.PyQt.QtWidgets import QDialogButtonBox
    is_qt6 = True
else:
    is_qt6 = False

import sqlite3

# Ajout du dossier "libs" au PYTHONPATH pour les dépendances embarquées
libs_path = Path(__file__).resolve().parent / "libs"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

# Import des dépendances embarquées
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pyexcel_ods3
from openpyxl import Workbook

try:
    from PyQt6.QtWidgets import QMessageBox
except ImportError:
    from PyQt5.QtWidgets import QMessageBox

import datetime
import re
from enum import Enum
import importlib.resources as pkg_resources
from tempfile import gettempdir

from osgeo import ogr
import subprocess

from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsWkbTypes, QgsMessageLog, QgsVectorLayer, QgsProject
from qgis.gui import QgsMessageBar
from qgis.PyQt import QtCore
from qgis.PyQt import QtGui
from qgis.PyQt import QtWidgets
from qgis.PyQt import uic

from qgis.PyQt.QtCore import QPropertyAnimation, QEasingCurve, QTimer
from qgis.PyQt.QtWidgets import QComboBox, QLineEdit, QLabel

from SpreadsheetLayers.util.gdal_util import GDAL_COMPAT

# Compatibilité Qt5 / Qt6 pour les enums déplacés
try:
    DisplayRole = QtCore.Qt.ItemDataRole.DisplayRole
    EditRole = QtCore.Qt.ItemDataRole.EditRole
    AlignCenter = QtCore.Qt.AlignmentFlag.AlignCenter
    AlignLeft = QtCore.Qt.AlignmentFlag.AlignLeft
    AlignRight = QtCore.Qt.AlignmentFlag.AlignRight
    AlignVCenter = QtCore.Qt.AlignmentFlag.AlignVCenter
    Checked = QtCore.Qt.CheckState.Checked
    Unchecked = QtCore.Qt.CheckState.Unchecked
    Gray = QtCore.Qt.GlobalColor.gray
except AttributeError:
    DisplayRole = QtCore.Qt.DisplayRole
    EditRole = EditRole
    AlignCenter = AlignCenter
    AlignLeft = AlignLeft
    AlignRight = AlignRight
    AlignVCenter = AlignVCenter
    Checked = QtCore.Qt.Checked
    Unchecked = QtCore.Qt.Unchecked
    Gray = QtCore.Qt.gray

class GeometryEncoding(Enum):
    WKT = 1
    WKB = 2
    PointFromColumns = 3


class GeometryType(Enum):
    wkbNone = 1
    wkbUnknown = 2
    wkbPoint = 3
    wkbLineString = 4
    wkbPolygon = 5
    wkbMultiPoint = 6
    wkbMultiLineString = 7
    wkbMultiPolygon = 8
    wkbGeometryCollection = 9


GEOMETRY_TYPES = (
    (QgsWkbTypes.NoGeometry, GeometryType.wkbNone),
    (QgsWkbTypes.Unknown, GeometryType.wkbUnknown),
    (QgsWkbTypes.Point, GeometryType.wkbPoint),
    (QgsWkbTypes.LineString, GeometryType.wkbLineString),
    (QgsWkbTypes.Polygon, GeometryType.wkbPolygon),
    (QgsWkbTypes.MultiPoint, GeometryType.wkbMultiPoint),
    (QgsWkbTypes.MultiLineString, GeometryType.wkbMultiLineString),
    (QgsWkbTypes.MultiPolygon, GeometryType.wkbMultiPolygon),
    (QgsWkbTypes.GeometryCollection, GeometryType.wkbGeometryCollection),
)


class GeometryEncodingsModel(QtCore.QAbstractListModel):
    """GeometryEncodingsModel provide a ListModel class to display encodings in QComboBox."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._encodings = (
            (self.tr("PointFromColumns"), GeometryEncoding.PointFromColumns),
            ("WKT", GeometryEncoding.WKT),
            ("WKB", GeometryEncoding.WKB),
        )

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._encodings)

    def data(self, index, role=DisplayRole):
        encoding = self._encodings[index.row()]
        if role == DisplayRole:
            return encoding[0]
        if role == EditRole:
            return encoding[1]


class GeometryTypesModel(QtCore.QAbstractListModel):
    """GeometryTypesModel provide a ListModel class to display types of geometries in QComboBox."""

    def rowCount(self, parent=QtCore.QModelIndex):
        return len(GEOMETRY_TYPES)

    def data(self, index, role=DisplayRole):
        geometry_type = GEOMETRY_TYPES[index.row()]
        if role == DisplayRole:
            if Qgis.QGIS_VERSION_INT >= 31800:
                return QgsWkbTypes.translatedDisplayString(geometry_type[0])
            else:
                return QgsWkbTypes.displayString(geometry_type[0])

        if role == EditRole:
            return geometry_type[1]


class FieldsModel(QtCore.QAbstractListModel):
    """FieldsModel provide a ListModel class to display fields in QComboBox."""

    def __init__(self, fields, parent=None):
        super(FieldsModel, self).__init__(parent)
        self._fields = fields

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._fields)

    def data(self, index, role=DisplayRole):
        field = self._fields[index.row()]
        if role == DisplayRole:
            return field["name"]
        if role == EditRole:
            return field["src"]


class OgrTableModel(QtGui.QStandardItemModel):
    """OgrTableModel provide a TableModel class
    for displaying OGR layers data.

    OGR layer is read at creation or by setLayer().
    All data are stored in parent QtCore.QStandardItemModel object.
    No reference to any OGR related object is kept.
    """

    def __init__(self, layer=None, fields=None, parent=None, maxRowCount=None):
        super(OgrTableModel, self).__init__(parent)
        self.maxRowCount = maxRowCount
        self.setLayer(layer)
        self.fields = fields

    def setLayer(self, layer):
        self.clear()
        if layer is None:
            return

        layerDefn = layer.GetLayerDefn()

        rows = min(layer.GetFeatureCount(), self.maxRowCount)
        columns = layerDefn.GetFieldCount()

        self.setRowCount(rows)
        self.setColumnCount(columns)

        # Headers
        for column in range(0, columns):
            fieldDefn = layerDefn.GetFieldDefn(column)
            fieldName = fieldDefn.GetNameRef()
            item = QtGui.QStandardItem(fieldName)
            self.setHorizontalHeaderItem(column, item)

        # Lines
        for row in range(0, rows):
            for column in range(0, columns):
                layer.SetNextByIndex(row)
                feature = layer.GetNextFeature()
                item = self.createItem(layerDefn, feature, column)
                self.setItem(row, column, item)

        # No header for column format line
        for column in range(0, columns):
            item = QtGui.QStandardItem("")
            self.setVerticalHeaderItem(rows, item)

    def createItem(self, layerDefn, feature, iField):
        fieldDefn = layerDefn.GetFieldDefn(iField)

        value = None
        if fieldDefn.GetType() == ogr.OFTDate:
            if feature.IsFieldSet(iField):
                value = datetime.date(*feature.GetFieldAsDateTime(iField)[:3])
            hAlign = AlignCenter

        elif fieldDefn.GetType() == ogr.OFTInteger:
            if feature.IsFieldSet(iField):
                value = feature.GetFieldAsInteger(iField)
            hAlign = AlignRight

        elif fieldDefn.GetType() == ogr.OFTReal:
            if feature.IsFieldSet(iField):
                value = feature.GetFieldAsDouble(iField)
            hAlign = AlignRight

        elif fieldDefn.GetType() == ogr.OFTString:
            if feature.IsFieldSet(iField):
                value = feature.GetFieldAsString(iField)
            hAlign = AlignLeft

        else:
            if feature.IsFieldSet(iField):
                value = feature.GetFieldAsString(iField)
            hAlign = AlignLeft

        if value is None:
            item = QtGui.QStandardItem("NULL")
            item.setForeground(QtGui.QBrush(Gray))
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
        else:
            item = QtGui.QStandardItem(str(value))
        item.setTextAlignment(hAlign | AlignVCenter)
        return item


ogrFieldTypes = []
for fieldType in [
    ogr.OFTInteger,
    ogr.OFTIntegerList,
    ogr.OFTReal,
    ogr.OFTRealList,
    ogr.OFTString,
    ogr.OFTStringList,
    # ogr.OFTWideString,
    # ogr.OFTWideStringList,
    ogr.OFTBinary,
    ogr.OFTDate,
    ogr.OFTTime,
    ogr.OFTDateTime,
    # ogr.OFTInteger64,
    # ogr.OFTInteger64List
]:
    ogrFieldTypes.append((fieldType, ogr.GetFieldTypeName(fieldType)))


class OgrFieldTypeDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(OgrFieldTypeDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QComboBox(parent)
        for value, text in ogrFieldTypes:
            editor.addItem(text, value)
        editor.setAutoFillBackground(True)
        return editor

    def setEditorData(self, editor, index):
        if not editor:
            return
        type = index.model().fields[index.column()]["type"]
        editor.setCurrentIndex(editor.findData(type))

    def setModelData(self, editor, model, index):
        if not editor:
            return
        type = editor.itemData(editor.currentIndex())
        model.fields[index.column()]["type"] = type


FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).resolve().parent.parent / "ui" / "ui_SpreadsheetLayersDialog.ui")

class SpreadsheetLayersDialog(QtWidgets.QDialog, FORM_CLASS):
    pluginKey = "SpreadsheetLayers"
    sampleRowCount = 20

    def __init__(self, parent=None):
        """Constructor."""
        super(SpreadsheetLayersDialog, self).__init__(parent)
        self.setupUi(self)
        self.validate_inputs()  # Vérifier l'état initial des champs

        self.dataSource = None
        self.layer = None
        self.fields = None
        self.sampleDatasource = None
        self.ogrHeadersLabel.setText("")

        self.messageBar = QgsMessageBar(self)

        # self.layout().insertWidget(0, self.messageBar)
        self.layout().addWidget(self.messageBar, 0, 0, 1, -1)

        encodings_model = GeometryEncodingsModel(self)
        self.geometryEncodingComboBox.setModel(encodings_model)

        geometry_types_model = GeometryTypesModel(self)
        self.geometryTypeComboBox.setModel(geometry_types_model)

        self.geometryBox.setChecked(False)
        self.sampleRefreshDisabled = False
        self.sampleView.setItemDelegate(OgrFieldTypeDelegate())

        self.layerNameEdit.textChanged.connect(self.validate_inputs)
        self.filePathEdit.textChanged.connect(self.validate_inputs)
        self.sheetBox.currentIndexChanged.connect(self.validate_inputs)
        self.checkboxVRT.stateChanged.connect(self.validate_inputs)
        self.checkboxSQLite.stateChanged.connect(self.validate_inputs)

        # Utiliser QTimer pour appeler validate_inputs après un court délai
        QtCore.QTimer.singleShot(100, self.validate_inputs)  # initial check

        # self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
        if is_qt6:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.validate_inputs()  # Validation initiale

    def convert_ods_to_xlsx(self, ods_path, xlsx_path):
        print(f"ods_Path : {ods_path} - xlsx_path : {xlsx_path}")
        # try:
        data = pyexcel_ods3.get_data(str(ods_path))
        print(f"data : {data}")
        wb = Workbook()
        ws = wb.active
        ws.title = next(iter(data))

        for sheet_name, rows in data.items():
            print(f"sheet_name : {sheet_name}")
            for row in rows:
                ws.append(row)
        wb.save(xlsx_path)
        return True
        # except Exception as e:
        #     QgsMessageLog.logMessage(f"Erreur lors de la conversion ODS → XLSX : {e}", "SpreadsheetLayers",
        #                              Qgis.Critical)
        # return False

    def blink_widget(self, widget):
        animation = QPropertyAnimation(widget, b"styleSheet")
        animation.setDuration(300)
        animation.setLoopCount(3)

        start_style = "background-color: #ffcccc;"
        end_style = "background-color: none;"

        animation.setStartValue(start_style)
        animation.setEndValue(end_style)
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        animation.start()
        widget._blink_animation = animation  # empêche le GC de l'arrêter

    def highlight_widget(self, widget, is_valid):
        if is_valid:
            widget.setStyleSheet("border: 1px solid green;")
        else:
            widget.setStyleSheet("border: 1px solid red;")

    def validate_inputs(self):
        """
        Fonction de validation des entrées, incluant la gestion des surlignages et des messages.
        """
        file_ok = bool(self.filePathEdit.text().strip())
        name_ok = bool(self.layerNameEdit.text().strip())
        sheet_ok = self.sheetBox.currentText().strip() != ""
        vrt_checked = self.checkboxVRT.isChecked()
        sqlite_checked = self.checkboxSQLite.isChecked()
        at_least_one_checked = vrt_checked or sqlite_checked

        vrt_ready = not vrt_checked or (vrt_checked and name_ok)
        sqlite_ready = not sqlite_checked or (sqlite_checked and name_ok and sheet_ok)

        valid = file_ok and name_ok and sheet_ok and vrt_ready and sqlite_ready and at_least_one_checked

        # self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(valid)
        if is_qt6:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(valid)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(valid)

        # Marquage visuel pour chaque champ
        self.highlight_widget(self.filePathEdit, file_ok)
        self.highlight_widget(self.layerNameEdit, name_ok)
        self.highlight_widget(self.sheetBox, sheet_ok)

        # Préparation du style QLabel de statut
        self.statusLabel.setAlignment(AlignVCenter | AlignLeft)
        self.statusLabel.setMinimumHeight(30)

        # Gestion des messages personnalisés
        if not sheet_ok and not at_least_one_checked:
            self.statusLabel.setText("⚠️ Feuille non sélectionnée et aucun format (VRT ou SQLite) n'a été choisi.")
            self.statusLabel.setStyleSheet("color: red; font-size: 14px; line-height: 20px;")
        elif not sheet_ok:
            self.statusLabel.setText("⚠️ Feuille non sélectionnée.")
            self.statusLabel.setStyleSheet("color: red; font-size: 14px; line-height: 20px;")
        elif not at_least_one_checked:
            self.statusLabel.setText("⚠️ Veuillez cocher au moins une case (VRT ou SQLite).")
            self.statusLabel.setStyleSheet("color: orange; font-size: 14px; line-height: 20px;")
        elif not file_ok:
            self.statusLabel.setText("⚠️ Fichier non sélectionné.")
            self.statusLabel.setStyleSheet("color: red; font-size: 14px; line-height: 20px;")
        elif not name_ok:
            self.statusLabel.setText("⚠️ Nom de couche manquant.")
            self.statusLabel.setStyleSheet("color: red; font-size: 14px; line-height: 20px;")
        elif vrt_checked and not vrt_ready:
            self.statusLabel.setText("⚠️ Informations manquantes pour le VRT.")
            self.statusLabel.setStyleSheet("color: red; font-size: 14px; line-height: 20px;")
        elif sqlite_checked and not sqlite_ready:
            self.statusLabel.setText("⚠️ Informations manquantes pour SQLite.")
            self.statusLabel.setStyleSheet("color: red; font-size: 14px; line-height: 20px;")
        else:
            self.statusLabel.setText("✅ Tout est prêt !")
            self.statusLabel.setStyleSheet("color: green; font-size: 14px; line-height: 20px;")

    def initialize_sheetbox(self):
        """
        Initialisation de la QComboBox sheetBox avec une ligne vide par défaut.
        """
        self.sheetBox.addItem("")  # Ajouter une ligne vide au début de la liste.

    def info(self, msg):
        self.messageBar.pushMessage(msg, Qgis.Info, 5)

    def warning(self, msg):
        self.messageBar.pushMessage(msg, Qgis.Warning, 5)

    def filePath(self):
        return self.filePathEdit.text()

    def setFilePath(self, path):
        self.filePathEdit.setText(path)

    @QtCore.pyqtSlot(name="on_filePathEdit_editingFinished")
    def on_filePathEdit_editingFinished(self):
        self.afterOpenFile()

    @QtCore.pyqtSlot(name="on_filePathButton_clicked")
    def on_filePathButton_clicked(self):
        settings = QtCore.QSettings()
        directory = settings.value(self.pluginKey + "/directory", "./")
        if not isinstance(directory, str):
            directory = str(directory)
        s, filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Choose a spreadsheet file to open"),
            directory,
            self.tr("Spreadsheet files") + " (*.ods *.xls *.xlsx);;"
            + self.tr("GDAL Virtual Format") + " (*.vrt);;"
            + self.tr("All files") + " (*.*)"
        )
        if s == "":
            return
        settings.setValue(self.pluginKey + "/directory", Path(s).parent)
        self.filePathEdit.setText(s)
        self.afterOpenFile()

    def afterOpenFile(self):
        self.sampleRefreshDisabled = True

        self.openDataSource()
        self.updateSheetBox()
        # Ici, on met à jour le widget layerNameEdit avec le nom de sortie basé sur le fichier ouvert
        if hasattr(self, "finfo"):
            self.setLayerName(self.finfo.completeBaseName())
        self.readVrt()

        self.sampleRefreshDisabled = False
        self.updateSampleView()

    def layerName(self):
        return self.layerNameEdit.text()

    def setLayerName(self, name):
        self.layerNameEdit.setText(name)

    def closeDataSource(self):
        if self.dataSource is not None:
            self.dataSource = None
            self.updateSheetBox()

    def openDataSource(self):
        self.closeDataSource()

        filePath = self.filePath()
        self.finfo = QtCore.QFileInfo(filePath)
        if not self.finfo.exists():
            return

        dataSource = ogr.Open(filePath, 0)
        if dataSource is None:
            self.messageBar.pushMessage("Could not open {}".format(filePath), Qgis.Warning, 5)
        self.dataSource = dataSource

        if self.dataSource and self.dataSource.GetDriver().GetName() in ["XLS"]:
            self.setEofDetection(True)
        else:
            self.setEofDetection(False)

    def closeSampleDatasource(self):
        if self.sampleDatasource is not None:
            self.sampleDatasource = None

    def openSampleDatasource(self):
        self.closeSampleDatasource()

        filePath = self.samplePath()
        finfo = QtCore.QFileInfo(filePath)
        if not finfo.exists():
            return False
        dataSource = ogr.Open(filePath, 0)
        if dataSource is None:
            self.messageBar.pushMessage("Could not open {}".format(filePath), Qgis.Warning, 5)
        self.sampleDatasource = dataSource

    def sheet(self):
        """
        Retourne le texte de la feuille actuellement sélectionnée.
        """
        return self.sheetBox.currentText()

    def setSheet(self, sheetName):
        print(f"index setSheet : {sheetName}")
        """
        Positionne la feuille dont le nom est sheetName dans le widget sheetBox.
        """
        index = self.sheetBox.findText(sheetName)

        if index > -1:
            # On bloque les signaux pour éviter un appel intempestif
            # self.sheetBox.blockSignals(True)
            # self.sheetBox.setCurrentIndex(index)
            # self.sheetBox.blockSignals(False)
            self.sheetBox.update()
            self.sheetBox.repaint()
            self.update()
            self.repaint()

        elif index == -1:
            print(f"La feuille '{sheetName}' n'a pas été trouvée dans sheetBox.")

    def updateSheetBox(self):
        """
        Met à jour le contenu de sheetBox en se basant sur les couches du dataSource.
        Lorsqu'un nouveau fichier est ouvert, on force l'affichage de la ligne vide (index 0),
        afin de n'afficher aucun nom de feuille par défaut.
        """
        self.sheetBox.clear()
        dataSource = self.dataSource
        if dataSource is None:
            return

        # Ajouter une ligne vide en première position
        self.sheetBox.addItem("")

        try:
            for i in range(dataSource.GetLayerCount()):
                layer = dataSource.GetLayer(i)
                self.sheetBox.addItem(layer.GetName(), layer)
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la récupération des couches : {e}\n"
                "Tentative de conversion du fichier ODS en XLSX..."
            )
            # Conversion ODS → XLSX
            source_file = self.filePathEdit.text()
            ods_path = Path(source_file)
            xlsx_path = ods_path.with_suffix(".xlsx")
            success = self.convert_ods_to_xlsx(ods_path, xlsx_path)
            if success:
                QtWidgets.QMessageBox.information(
                    self,
                    "Conversion réussie",
                    f"Le fichier ODS a été converti en XLSX.\nNouveau fichier : {xlsx_path.name}"
                )
                self.filePathEdit.setText(str(xlsx_path))
                self.loadFile(str(xlsx_path))
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Échec de conversion",
                    "La conversion en XLSX a échoué. Veuillez corriger manuellement le fichier."
                )
            return  # Sortie anticipée en cas d'erreur

        # À chaque ouverture de fichier, nous voulons que le sheetBox affiche la ligne vide.
        # self.sheetBox.blockSignals(True)
        self.sheetBox.setCurrentIndex(0)
        # self.sheetBox.blockSignals(False)
        self.validate_inputs()

    @QtCore.pyqtSlot(int)
    def on_sheetBox_currentIndexChanged(self, index):
        """
        Slot appelé lorsque l'utilisateur change la sélection dans sheetBox.
        Si l'item vide (index 0 ou texte vide) est sélectionné, on réinitialise simplement le layer.
        Sinon, on met à jour le layer et on affiche le nom de la feuille choisie dans layerNameEdit.
        Puis, on appelle updateSheetBox pour rafraîchir le content du widget.
        """
        selected_sheet = self.sheetBox.itemText(index).strip()
        if index == 0 or not selected_sheet:
            self.layer = None
            return

        # Mise à jour du layer et du nom de couche
        self.layer = self.sheetBox.itemData(index)
        self.setLayerName("{}-{}".format(self.finfo.completeBaseName(), selected_sheet))
        self.sheetBox.repaint()

        # Mises à jour complémentaires de l'interface
        self.countNonEmptyRows()
        self.updateFields()
        self.updateFieldBoxes()
        self.updateSampleView()

        # Appel à updateSheetBox pour rafraîchir la liste des feuilles
        # self.updateSheetBox()

    def linesToIgnore(self):
        return self.linesToIgnoreBox.value()

    def setLinesToIgnore(self, value):
        self.linesToIgnoreBox.setValue(value)

    @QtCore.pyqtSlot(int)
    def on_linesToIgnoreBox_valueChanged(self, value):
        self.updateFields()
        self.updateFieldBoxes()
        self.updateSampleView()

    def header(self):
        if hasattr(QtCore.Qt, 'CheckState'):
            # Qt6
            return self.headerBox.checkState() == QtCore.Qt.CheckState.Checked
        else:
            # Qt5
            return self.headerBox.checkState() == Checked

    def setHeader(self, value):
        self.headerBox.setCheckState(
            Checked if value else Unchecked
        )

    @QtCore.pyqtSlot(int)
    def on_headerBox_stateChanged(self, state):
        self.updateFields()
        self.updateFieldBoxes()
        self.updateSampleView()

    def offset(self):
        offset = self.linesToIgnore()
        if self.header():
            offset += 1
        return offset

    def setOffset(self, value):
        try:
            value = int(value)
        except ValueError:
            return False
        if self.header():
            value -= 1
        self.setLinesToIgnore(value)

    def limit(self):
        return self._non_empty_rows - self.offset()

    def eofDetection(self):
        return self.eofDetectionBox.checkState() == Checked

    def setEofDetection(self, value):
        # self.eofDetectionBox.setCheckState(
        #     Checked if value else Unchecked
        # )
        check_state = Checked if value else Unchecked
        self.checkboxVRT.setCheckState(check_state)

    @QtCore.pyqtSlot(int)
    def on_eofDetectionBox_stateChanged(self, state):
        self.countNonEmptyRows()
        self.updateSampleView()

    def countNonEmptyRows(self):
        if self.layer is None:
            return
        if self.eofDetection():
            self._non_empty_rows = 0

            layer = self.layer
            layerDefn = layer.GetLayerDefn()
            layer.SetNextByIndex(0)
            feature = layer.GetNextFeature()
            current_row = 1
            while feature is not None:
                # values = []

                for iField in range(0, layerDefn.GetFieldCount()):
                    # values.append(feature.GetFieldAsString(iField))
                    if feature.IsFieldSet(iField):
                        self._non_empty_rows = current_row

                feature = layer.GetNextFeature()
                current_row += 1
        else:
            self._non_empty_rows = self.layer.GetFeatureCount()

    def sql(self):
        sql = ("SELECT * FROM '{}'" " LIMIT {} OFFSET {}").format(
            self.sheet(), self.limit(), self.offset()
        )
        return sql

    def updateGeometry(self):
        if GDAL_COMPAT or self.offset() == 0:
            self.geometryBox.setEnabled(True)
            self.geometryBox.setToolTip("")
        else:
            self.geometryBox.setEnabled(False)
            msg = self.tr(
                "Used GDAL version doesn't support VRT layers with sqlite dialect"
                " mixed with PointFromColumn functionality.\n"
                "For more informations, consult the plugin documentation."
            )
            self.geometryBox.setToolTip(msg)

    def geometry(self):
        return self.geometryBox.isEnabled() and self.geometryBox.isChecked()

    def geometryEncoding(self):
        index = self.geometryEncodingComboBox.currentIndex()
        return self.geometryEncodingComboBox.itemData(index, EditRole)

    def setGeometryEncoding(self, value):
        self.geometryEncodingComboBox.setCurrentIndex(
            self.geometryEncodingComboBox.findData(value, EditRole)
        )

    @QtCore.pyqtSlot(int)
    def on_geometryEncodingComboBox_currentIndexChanged(self, index):
        if self.geometryEncoding() == GeometryEncoding.PointFromColumns:
            self.geometryFieldStackedWidget.setCurrentIndex(1)
        else:
            self.geometryFieldStackedWidget.setCurrentIndex(0)

    def geometryField(self):
        index = self.geometryFieldComboBox.currentIndex()
        if index == -1:
            return ""
        return self.geometryFieldComboBox.itemData(index, EditRole)

    def setGeometryField(self, fieldName):
        self.geometryFieldComboBox.setCurrentIndex(
            self.geometryFieldComboBox.findData(fieldName, EditRole)
        )

    def xField(self):
        index = self.xFieldBox.currentIndex()
        if index == -1:
            return ""
        return self.xFieldBox.itemData(index, EditRole)

    def setXField(self, fieldName):
        self.xFieldBox.setCurrentIndex(
            self.xFieldBox.findData(fieldName, EditRole)
        )

    def yField(self):
        index = self.yFieldBox.currentIndex()
        if index == -1:
            return ""
        return self.yFieldBox.itemData(index, EditRole)

    def setYField(self, fieldName):
        self.yFieldBox.setCurrentIndex(
            self.yFieldBox.findData(fieldName, EditRole)
        )

    def updateFieldBoxes(self):
        if self.offset() > 0:
            # return
            pass

        if self.layer is None:
            self.geometryFieldComboBox.clear()
            self.xFieldBox.clear()
            self.yFieldBox.clear()
            return

        model = FieldsModel(self.fields)

        geometryField = self.geometryField()
        xField = self.xField()
        yField = self.yField()

        self.geometryFieldComboBox.setModel(model)
        self.xFieldBox.setModel(model)
        self.yFieldBox.setModel(model)

        self.setGeometryField(geometryField)
        self.setXField(xField)
        self.setYField(yField)

        self.autoFill(self.geometryFieldComboBox, ["WKT", "WKB"])
        self.autoFill(self.xFieldBox, ["longitude", "lon", "x"])
        self.autoFill(self.yFieldBox, ["latitude", "lat", "y"])

    def autoFill(self, fieldComboBox, candidates):
        if fieldComboBox.currentIndex() != -1:
            return
        for candidate in candidates:
            for i in range(0, fieldComboBox.count()):
                fieldName = fieldComboBox.itemText(i)
                if fieldName.lower().find(candidate.lower()) != -1:
                    fieldComboBox.setCurrentIndex(i)
                    return

    def showGeometryFields(self):
        return self.showGeometryFieldsBox.isChecked()

    def setShowGeometryFields(self, value):
        self.showGeometryFieldsBox.setChecked(value)

    def geometryType(self):
        index = self.geometryTypeComboBox.currentIndex()
        if index == -1:
            return ""
        if self.geometryEncoding() == GeometryEncoding.PointFromColumns:
            return GeometryType.wkbPoint
        return self.geometryTypeComboBox.itemData(index, EditRole)

    def setGeometryType(self, value):
        self.geometryTypeComboBox.setCurrentIndex(
            self.geometryTypeComboBox.findData(value, EditRole)
        )

    def crs(self):
        return self.crsWidget.crs().authid()

    def setCrs(self, authid):
        crs = QgsCoordinateReferenceSystem()
        crs.createFromString(authid)
        self.crsWidget.setCrs(crs)

    def updateSampleView(self):
        if self.sampleRefreshDisabled:
            return
        self.updateGeometry()
        if self.layer is not None:
            self.writeSampleVrt()
            self.openSampleDatasource()
        layer = None
        dataSource = self.sampleDatasource
        if dataSource is not None:
            for i in range(0, dataSource.GetLayerCount()):
                layer = dataSource.GetLayer(i)
        if layer is None:
            self.sampleView.setModel(None)
            return
        self.sampleView.reset()
        model = OgrTableModel(
            layer, self.fields, parent=self, maxRowCount=self.sampleRowCount
        )
        self.sampleView.setModel(model)
        # Open persistent editor on last line (column format)
        for column in range(0, model.columnCount()):
            self.sampleView.openPersistentEditor(
                model.index(model.rowCount() - 1, column)
            )
        # Restore rows initial order
        vheader = self.sampleView.verticalHeader()
        for row in range(0, model.rowCount()):
            position = vheader.sectionPosition(row)
            if position != row:
                vheader.moveSection(position, row)
        # Move column format line at first
        vheader.moveSection(model.rowCount() - 1, 0)

    def validate(self):
        try:
            if self.dataSource is None:
                raise ValueError(self.tr("Please select an input file"))

            if self.layer is None:
                raise ValueError(self.tr("Please select a sheet"))

            if self.geometry():
                if self.geometryEncoding() == GeometryEncoding.PointFromColumns:
                    if self.xField() == "":
                        raise ValueError(self.tr("Please select an x field"))

                    if self.yField() == "":
                        raise ValueError(self.tr("Please select an y field"))
                else:
                    if self.geometryField() == "":
                        raise ValueError(self.tr("Please select a geometry field"))

        except ValueError as e:
            self.messageBar.pushMessage(str(e), Qgis.Warning, 5)
            return False

        return True

    def vrtPath(self):
        return "{}.{}.vrt".format(self.filePath(), self.sheet())

    def samplePath(self):
        filename = f"{Path(self.filePath()).name}.tmp.vrt"
        return str(Path(gettempdir()) / filename)

    def readVrt(self):
        if self.dataSource is None:
            return False

        vrtPath = self.vrtPath()
        vrtPathObj = Path(vrtPath)
        if not vrtPathObj.exists():
            return False

        file = QtCore.QFile(vrtPath)
        if not file.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            self.warning(f"Impossible to open VRT file {vrtPath}")
            return False

        self.geometryBox.setChecked(False)

        try:
            self.readVrtStream(file)
        except Exception:
            self.warning("An error occurs during existing VRT file loading")
            return False
        finally:
            file.close()

        # self.info("Existing VRT file has been loaded")
        return True

    def readVrtStream(self, file):
        stream = QtCore.QXmlStreamReader(file)

        stream.readNextStartElement()
        if stream.name() == "OGRVRTDataSource":
            stream.readNextStartElement()
            if stream.name() == "OGRVRTLayer":
                self.setLayerName(stream.attributes().value("name"))

                fields = []

                while stream.readNext() != QtCore.QXmlStreamReader.EndDocument:
                    if stream.isComment():
                        text = stream.text()
                        pattern = re.compile(r"Header=(\w+)")
                        match = pattern.search(text)
                        if match:
                            self.setHeader(eval(match.group(1)))

                    if stream.isStartElement():
                        if stream.name() == "SrcDataSource":
                            # do nothing : datasource should be already set
                            pass

                        elif stream.name() == "SrcLayer":
                            text = stream.readElementText()
                            self.setSheet(text)
                            self.setOffset(0)

                        elif stream.name() == "SrcSql":
                            text = stream.readElementText()

                            pattern = re.compile(r"FROM '(.+)'")
                            match = pattern.search(text)
                            if match:
                                self.setSheet(match.group(1))

                            pattern = re.compile(r"OFFSET (\d+)")
                            match = pattern.search(text)
                            if match:
                                self.setOffset(int(match.group(1)))

                        elif stream.name() == "Field":
                            fields.append(stream.attributes().value("name"))

                        elif stream.name() == "LayerSRS":
                            text = stream.readElementText()
                            self.setCrs(text)

                        elif stream.name() == "GeometryType":
                            geometry_type = GeometryType.__members__.get(
                                stream.readElementText(), None
                            )
                            if geometry_type is None:
                                self.setGeometryType(GeometryType.wkbNone)
                            else:
                                self.setGeometryType(geometry_type)
                            self.geometryBox.setChecked(
                                geometry_type not in (None, GeometryType.wkbNone)
                            )

                        elif stream.name() == "GeometryField":
                            encoding = GeometryEncoding.__members__.get(
                                stream.attributes().value("encoding"), None
                            )
                            if encoding:
                                self.setGeometryEncoding(encoding)
                            if encoding == GeometryEncoding.PointFromColumns:
                                self.setXField(stream.attributes().value("x"))
                                self.setYField(stream.attributes().value("y"))
                                self.setShowGeometryFields(
                                    stream.attributes().value("x") in fields
                                )
                            else:
                                self.setGeometryField(
                                    stream.attributes().value("field")
                                )
                                self.setShowGeometryFields(
                                    stream.attributes().value("field") in fields
                                )

                        if not stream.isEndElement():
                            stream.skipCurrentElement()

            stream.skipCurrentElement()

        stream.skipCurrentElement()

    def updateFields(self):
        if self.layer is None:
            self.fields = []
            return

        # Select header line
        if self.header() or self.offset() >= 1:
            self.layer.SetNextByIndex(self.offset() - 1)
            feature = self.layer.GetNextFeature()

        fields = []
        layerDefn = self.layer.GetLayerDefn()
        for iField in range(0, layerDefn.GetFieldCount()):
            fieldDefn = layerDefn.GetFieldDefn(iField)
            src = fieldDefn.GetNameRef()
            name = src
            if self.header() or self.offset() >= 1:
                name = feature.GetFieldAsString(iField) or name
            fields.append({"src": src, "name": name, "type": fieldDefn.GetType()})
        self.fields = fields

    def prepareVrt(self, sample=False, without_fields=False):
        buffer = QtCore.QBuffer()
        try:
            mode = QtCore.QIODevice.OpenModeFlag.ReadWrite  # Qt6
        except AttributeError:
            mode = QtCore.QBuffer.ReadWrite  # Qt5
        buffer.open(mode)

        stream = QtCore.QXmlStreamWriter(buffer)
        stream.setAutoFormatting(True)
        stream.writeStartDocument()
        stream.writeStartElement("OGRVRTDataSource")
        stream.writeStartElement("OGRVRTLayer")
        stream.writeAttribute("name", self.layerName())

        # Vérification de l'existence du fichier source
        file_path_obj = Path(self.filePath())
        if not file_path_obj.exists():
            print(f"Erreur : le fichier source '{file_path_obj}' n'existe pas.")
            return None

        stream.writeStartElement("SrcDataSource")
        if sample:
            stream.writeCharacters(self.filePath())
        else:
            stream.writeAttribute("relativeToVRT", "1")
            stream.writeCharacters(file_path_obj.name)
        stream.writeEndElement()

        stream.writeComment(f"Header={self.header()}")

        # Vérification de self.layer
        if self.layer is None:
            print("Erreur : self.layer est None, impossible de récupérer les champs.")
            return None

        if self.offset() > 0 or self._non_empty_rows != self.layer.GetFeatureCount():
            stream.writeStartElement("SrcSql")
            stream.writeAttribute("dialect", "sqlite")
            stream.writeCharacters(self.sql())
            stream.writeEndElement()
        else:
            stream.writeStartElement("SrcLayer")
            stream.writeCharacters(self.sheet())
            stream.writeEndElement()

        # Récupération des champs depuis la couche source
        layer_defn = self.layer.GetLayerDefn()
        source_fields = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
        print(f"Champs détectés dans la couche source : {source_fields}")

        # Vérification et suppression des doublons
        seen_fields = {}
        self.unique_fields = []

        for field in self.fields:
            name = field["name"]

            if name not in seen_fields:
                seen_fields[name] = 1
                self.unique_fields.append(field)
            else:
                new_name = f"{name}_{seen_fields[name]}"
                field["name"] = new_name
                self.unique_fields.append(field)
                seen_fields[name] += 1
                print(f"Avertissement : Champ dupliqué détecté et renommé {new_name}")

        print(f"Liste des champs après déduplication : {[field['name'] for field in self.unique_fields]}")

        # Vérification et ajout des champs dans le VRT
        if not without_fields:
            if not self.unique_fields:
                print("Erreur : Aucun champ détecté, ajout d'un champ par défaut.")
                stream.writeStartElement("Field")
                stream.writeAttribute("name", "TestField")
                stream.writeAttribute("src", "TestField")
                stream.writeAttribute("type", "String")
                stream.writeEndElement()
            else:
                for field in self.unique_fields:
                    stream.writeStartElement("Field")
                    stream.writeAttribute("name", field["name"])
                    stream.writeAttribute("src", field["src"])

                    field_type = ogr.GetFieldTypeName(field["type"])
                    if field_type is None:
                        print(f"Erreur : Type OGR invalide pour le champ {field['name']}, défini sur 'String'.")
                        field_type = "String"

                    stream.writeAttribute("type", field_type)
                    stream.writeEndElement()

        if self.geometry() and not sample:
            stream.writeStartElement("GeometryType")
            stream.writeCharacters(self.geometryType().name)
            stream.writeEndElement()
            if self.crs():
                stream.writeStartElement("LayerSRS")
                stream.writeCharacters(self.crs())
                stream.writeEndElement()
            stream.writeStartElement("GeometryField")
            stream.writeAttribute("encoding", self.geometryEncoding().name)
            if self.geometryEncoding() == GeometryEncoding.PointFromColumns:
                stream.writeAttribute("x", self.xField())
                stream.writeAttribute("y", self.yField())
            else:
                stream.writeAttribute("field", self.geometryField())
            stream.writeEndElement()

        stream.writeEndElement()  # OGRVRTLayer
        stream.writeEndElement()  # OGRVRTDataSource
        stream.writeEndDocument()
        buffer.reset()
        content = buffer.readAll()
        buffer.close()

        print(f"Contenu du VRT généré : {content}")
        return content

    def add_layer_to_qgis(self, file_path: str, layer_name: str):
        layer = QgsVectorLayer(str(file_path), layer_name, "ogr")
        if not layer.isValid():
            QtWidgets.QMessageBox.critical(self, "Erreur", f"Impossible de charger la couche : {file_path}")
            return
        QgsProject.instance().addMapLayer(layer)

    def confirm_and_remove_file(self, path: Path, label: str = "") -> bool:
        if path.exists():
            reply = QtWidgets.QMessageBox.question(
                self,
                "Fichier existant",
                f"Le fichier {label or path.name} existe déjà.\nSouhaitez-vous le remplacer ?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                try:
                    path.unlink()  # Supprime le fichier
                    return True
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Erreur",
                        f"Impossible de supprimer le fichier :\n{e}"
                    )
                    return False
            else:
                return False
        return True

    def writeVrt(self, overwrite=False):
        content = self.prepareVrt()

        # Vérification du type et conversion en chaîne de caractères
        if isinstance(content, QtCore.QByteArray):
            content = content.data().decode('utf-8')  # Conversion correcte

        # Vérification du contenu généré
        if not content or len(content.strip()) == 0:
            print("Erreur : Le contenu du VRT est vide, annulation de l'écriture.")
            return False

        vrt_path = Path(self.vrtPath())

        # Détection compatibilité boutons QMessageBox
        try:
            Buttons = QtWidgets.QMessageBox.StandardButton  # Qt6
            YES = Buttons.Yes
            NO = Buttons.No
        except AttributeError:
            Buttons = QtWidgets.QMessageBox  # Qt5
            YES = Buttons.Yes
            NO = Buttons.No

        # Vérification de l'accès au fichier VRT
        if vrt_path.exists() and not vrt_path.is_file():
            print(f"Erreur : '{vrt_path}' existe mais n'est pas un fichier valide.")
            return False

        # Si le fichier existe, gérer la suppression selon les cases cochées
        if vrt_path.exists():
            old_content = vrt_path.read_text(encoding='utf-8')
            if content == old_content:
                print("Le fichier VRT est identique, aucune modification nécessaire.")
                return True

            if self.checkboxVRT.isChecked():
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Fichier existant",
                    f"Le fichier VRT '{vrt_path.name}' existe déjà.\nSouhaitez-vous le remplacer ?",
                    YES | NO,
                    NO
                )
                if reply == NO:
                    print("Remplacement annulé par l'utilisateur.")
                    return False

                try:
                    vrt_path.write_text(content, encoding='utf-8')
                    print(f"Fichier VRT remplacé avec succès : {vrt_path}")
                except Exception as e:
                    print(f"Erreur critique lors de l’écriture du fichier VRT '{vrt_path}': {e}")
                    self.warning(f"Erreur lors de l’écriture du fichier VRT : {e}")
                    return False

        # Écriture du fichier (si non déjà écrit plus haut)
        try:
            vrt_path.write_text(content, encoding='utf-8')
            print(f"Fichier VRT écrit avec succès : {vrt_path}")
        except Exception as e:
            print(f"Erreur critique lors de l’écriture du fichier VRT '{vrt_path}': {e}")
            self.warning(f"Erreur lors de l’écriture du fichier VRT : {e}")
            return False

        return True

    def writeSampleVrt(self, without_fields=False):
        content = self.prepareVrt(sample=True, without_fields=without_fields)

        # Affichage du contenu du VRT
        print(f"VRT généré par prepareVrt():\n{content}")

        # Vérifier que le fichier VRT peut être ouvert
        vrt_ds = ogr.Open(str(self.vrtPath()))
        if vrt_ds is None:
            print("Erreur : Impossible d'ouvrir le fichier VRT.")
            return False

        layer = vrt_ds.GetLayer()
        if layer is None:
            print("Erreur : Impossible de récupérer la couche du VRT.")
            return False

        layer_defn = layer.GetLayerDefn()
        if layer_defn is None:
            print("Erreur : Impossible de récupérer la définition de la couche.")
            return False

        # Extraire les champs
        fields = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
        print(f"Liste des champs détectés : {fields}")

        vrtPath = self.samplePath()
        file = QtCore.QFile(vrtPath)
        if file.exists():
            QtCore.QFile.remove(vrtPath)

        try:
            mode = QtCore.QIODevice.OpenModeFlag.ReadWrite | QtCore.QIODevice.OpenModeFlag.Text  # Qt6
        except AttributeError:
            mode = QtCore.QIODevice.ReadWrite | QtCore.QIODevice.Text  # Qt5

        if not file.open(mode):
            self.warning("Impossible d'ouvrir le fichier VRT {}".format(vrtPath))
            return False
        file.write(content)
        file.close()
        return True

    def accept(self, *args, **kwargs):
        if not self.validate():
            return False
        vrt_path = self.vrtPath()
        sqlite_file = None
        # Création du fichier VRT
        # if self.checkboxVRT.isChecked() or self.checkboxSQLite.isChecked():
        if not self.writeVrt(overwrite=True):
            return False
        # Création du fichier SQLite si demandé
        if self.checkboxSQLite.isChecked():
            sqlite_file = self.prepare_sqlite_path()
            self.create_sqlite_from_vrt(vrt_path, sqlite_file)

        # Ajout de la couche dans QGIS en fonction de la checkbox
        if self.checkboxSQLite.isChecked() and not self.checkboxVRT.isChecked():
            self.add_layer_to_qgis(sqlite_file, f"SQLite - {sqlite_file.stem}")
        elif self.checkboxVRT.isChecked() and not self.checkboxSQLite.isChecked():
            self.add_layer_to_qgis(vrt_path, f"VRT - {Path(vrt_path).stem}")
        elif self.checkboxVRT.isChecked() and self.checkboxSQLite.isChecked():
            # Priorité au SQLite si les deux sont cochés
            self.add_layer_to_qgis(sqlite_file, f"SQLite - {sqlite_file.stem}")

        return super(SpreadsheetLayersDialog, self).accept(*args, **kwargs)

    def prepare_sqlite_path(self) -> Path:
        """
        Construit le chemin du fichier SQLite dans le même dossier que le fichier source.
        """
        source_path = Path(self.filePathEdit.text().strip())
        sheet_name = self.sheetBox.currentText().strip()
        if not source_path.exists() or not sheet_name:
            return None  # Ou déclencher une gestion d’erreur
        base_name = source_path.stem  # Nom sans extension
        output_name = f"{base_name}-{sheet_name}.sqlite"
        output_path = source_path.parent / output_name
        return output_path

    def create_sqlite_from_vrt(self, vrt_path, sqlite_path):
        # Convertir les chemins en objets Path
        vrt_path = Path(vrt_path)
        sqlite_path = Path(sqlite_path)

        # Si le fichier VRT existe déjà et que la case est cochée, demander confirmation
        if vrt_path.exists():
            if self.checkboxVRT.isChecked():
                reply = QMessageBox.question(
                    self,
                    "Fichier VRT existant",
                    f"Le fichier VRT '{vrt_path.name}' existe déjà.\nSouhaitez-vous le remplacer ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return False

        # Suppression de l'ancien fichier SQLite pour repartir sur une base propre
        if sqlite_path.exists():
            try:
                sqlite_path.unlink()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer l'ancien fichier SQLite :\n{e}")
                return False

        # Ouverture du fichier VRT via OGR
        vrt_ds = ogr.Open(str(vrt_path))
        if vrt_ds is None:
            raise RuntimeError(f"Impossible d'ouvrir le fichier VRT : {vrt_path}")

        # Connexion à la base SQLite
        conn = sqlite3.connect(str(sqlite_path))
        cursor = conn.cursor()

        # Récupération du layer et de sa définition
        layer = vrt_ds.GetLayer()
        layer.ResetReading()  # S'assurer de repartir du début
        layer_defn = layer.GetLayerDefn()

        # Définir le nom de la table
        table_name = f"table_{layer.GetName()}"
        table_name_quoted = f'"{table_name}"'

        # Listes pour la création de la table et l'insertion des données
        sql_field_names = []  # Nom de colonnes (entre guillemets) pour l'INSERT
        raw_field_names = {}  # Mapping : nom "nettoyé" (possiblement complété) -> nom original (avec retours à la ligne)
        fields_sql = []  # Colonnes avec leur type pour le CREATE TABLE

        # Gestion des doublons en se basant sur le nom nettoyé en minuscules
        seen_fields = {}

        for i in range(layer_defn.GetFieldCount()):
            field_defn = layer_defn.GetFieldDefn(i)
            # Récupération du nom original (qui peut contenir des retours à la ligne)
            raw_name = field_defn.GetName()
            # Nettoyage : suppression des retours à la ligne et espaces superflus
            clean_name = " ".join(raw_name.split())

            # Pour éviter les doublons, comparer en minuscules
            normalized = clean_name.lower()
            if normalized in seen_fields:
                seen_fields[normalized] += 1
                field_name = f"{clean_name}_{seen_fields[normalized]}"
            else:
                seen_fields[normalized] = 1
                field_name = clean_name

            # Détermination du type de champ pour SQLite
            field_type = field_defn.GetFieldTypeName(field_defn.GetType()).lower()
            sqlite_type = "TEXT"  # Par défaut
            if field_type in ("integer", "integer64"):
                sqlite_type = "INTEGER"
            elif field_type == "real":
                sqlite_type = "REAL"

            # Préparer les parties pour la création de la table et l'insertion
            sql_field_names.append(f'"{field_name}"')
            # On stocke le mapping : nom nettoyé (possiblement avec suffixe) -> nom original
            raw_field_names[field_name] = raw_name
            fields_sql.append(f'"{field_name}" {sqlite_type}')

        # Création de la table SQLite
        create_sql = f'CREATE TABLE {table_name_quoted} ({", ".join(fields_sql)});'
        print("Requête SQL CREATE TABLE :", create_sql)
        cursor.execute(create_sql)

        # Construction de l'instruction INSERT
        placeholders = ', '.join(['?'] * len(sql_field_names))
        insert_sql = f'INSERT INTO {table_name_quoted} ({", ".join(sql_field_names)}) VALUES ({placeholders})'
        print("Requête SQL INSERT :", insert_sql)
        print("Nombre de features dans le VRT :", layer.GetFeatureCount())

        # Insertion des données dans la table
        for feature in layer:
            values = []
            for col in sql_field_names:
                # Récupérer le nom de colonne (nettoyé) sans les guillemets
                col_name = col.strip('"')
                # Récupérer le nom original (avec éventuels retour à la ligne)
                orig_field = raw_field_names.get(col_name)
                # Utiliser l'index du champ basé sur le nom original
                idx = layer_defn.GetFieldIndex(orig_field) if orig_field is not None else -1
                if idx != -1:
                    values.append(feature.GetField(idx))
                else:
                    print(f"Avertissement : Le champ '{orig_field}' est absent, valeur ignorée.")
                    values.append(None)
            cursor.execute(insert_sql, values)

        conn.commit()
        conn.close()

        print(f"Base SQLite '{sqlite_path}' créée avec succès depuis le fichier VRT.")
        return True


    @QtCore.pyqtSlot()
    def on_helpButton_clicked(self):
        help_path = pkg_resources.files('SpreadsheetLayers').joinpath('help')
        user_locale = QtCore.QSettings().value("locale/userLocale")[0:2]
        locale_path = help_path / user_locale
        if not locale_path.exists():
            locale_path = help_path / "en"
        path = locale_path / "index.html"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))