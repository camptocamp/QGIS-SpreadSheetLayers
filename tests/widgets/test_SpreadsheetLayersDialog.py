import os

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QCheckBox, QComboBox

from tests import QgisTestCase
from tests import INPUT_PATH


class TestSpreadsheetLayersDialog(QgisTestCase):

    def create_dialog(self):
        from SpreadsheetLayers.widgets.SpreadsheetLayersDialog import SpreadsheetLayersDialog
        dlg = SpreadsheetLayersDialog()
        return dlg

    def test_init(self):
        self.create_dialog()

    def test_open_file_ods(self):
        dlg = self.create_dialog()

        path = os.path.join(INPUT_PATH, "test_entete_float.ods")
        dlg.setFilePath(path)
        dlg.afterOpenFile()
        assert dlg.sheet() == "Feuille1"
        assert dlg.layerName() == "test_entete_float-Feuille1"
        assert dlg.header() is False
        assert dlg.geometry() is True
        assert dlg.xField() == "Longitude"
        assert dlg.yField() == "Latitude"
        assert dlg.crs() == "EPSG:4326"
