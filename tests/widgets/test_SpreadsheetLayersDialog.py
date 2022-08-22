import os
from unittest.mock import patch

from tests import QgisTestCase
from tests import INPUT_PATH, OUTPUT_PATH


class TestSpreadsheetLayersDialog(QgisTestCase):
    def create_dialog(self):
        from SpreadsheetLayers.widgets.SpreadsheetLayersDialog import (
            SpreadsheetLayersDialog,
        )

        dlg = SpreadsheetLayersDialog()
        return dlg

    def test_init(self):
        self.create_dialog()

    def test_readVrt_xy(self):
        from SpreadsheetLayers.widgets.SpreadsheetLayersDialog import (
            GeometryEncoding,
            GeometryType,
        )

        dlg = self.create_dialog()

        path = os.path.join(INPUT_PATH, "x_y.ods")
        dlg.setFilePath(path)
        dlg.afterOpenFile()
        assert dlg.sheet() == "x_y"
        assert dlg.layerName() == "x_y-x_y"
        assert dlg.header() is False
        assert dlg.geometry() is True
        assert dlg.geometryEncoding() == GeometryEncoding.PointFromColumns
        assert dlg.xField() == "Longitude"
        assert dlg.yField() == "Latitude"
        assert dlg.geometryType() == GeometryType.wkbPoint
        assert dlg.crs() == "EPSG:4326"

    def test_writeVrt_xy(self):
        dlg = self.create_dialog()

        path = os.path.join(INPUT_PATH, "x_y.ods")
        dlg.setFilePath(path)
        dlg.afterOpenFile()

        with patch(
            "SpreadsheetLayers.widgets.SpreadsheetLayersDialog.SpreadsheetLayersDialog.vrtPath",
            return_value=os.path.join(OUTPUT_PATH, "x_y.ods.x_y.vrt"),
        ):
            dlg.writeVrt(overwrite=True)

        with open(
            os.path.join(INPUT_PATH, "x_y.ods.x_y.vrt"), mode="rt", encoding="utf-8"
        ) as expected_file, open(
            os.path.join(OUTPUT_PATH, "x_y.ods.x_y.vrt"),
            mode="rt",
            encoding="utf-8",
        ) as output_file:
            assert output_file.read() == expected_file.read()

    def test_readVrt_wkt_point(self):
        from SpreadsheetLayers.widgets.SpreadsheetLayersDialog import (
            GeometryEncoding,
            GeometryType,
        )

        dlg = self.create_dialog()

        path = os.path.join(INPUT_PATH, "wkt_point.ods")
        dlg.setFilePath(path)
        dlg.afterOpenFile()
        assert dlg.sheet() == "wkt_point"
        assert dlg.layerName() == "wkt_point-wkt_point"
        assert dlg.header() is False
        assert dlg.geometry() is True
        assert dlg.geometryEncoding() == GeometryEncoding.WKT
        assert dlg.geometryField() == "wkt"
        assert dlg.geometryType() == GeometryType.wkbPoint
        assert dlg.crs() == "EPSG:4326"

    def test_writeVrt_wkt_point(self):
        dlg = self.create_dialog()

        path = os.path.join(INPUT_PATH, "wkt_point.ods")
        dlg.setFilePath(path)
        dlg.afterOpenFile()

        with patch(
            "SpreadsheetLayers.widgets.SpreadsheetLayersDialog.SpreadsheetLayersDialog.vrtPath",
            return_value=os.path.join(OUTPUT_PATH, "wkt_point.ods.wkt_point.vrt"),
        ):
            dlg.writeVrt(overwrite=True)

        with open(
            os.path.join(INPUT_PATH, "wkt_point.ods.wkt_point.vrt"),
            mode="rt",
            encoding="utf-8",
        ) as expected_file, open(
            os.path.join(OUTPUT_PATH, "wkt_point.ods.wkt_point.vrt"),
            mode="rt",
            encoding="utf-8",
        ) as output_file:
            assert output_file.read() == expected_file.read()

    def test_readVrt_wkt_polygon(self):
        from SpreadsheetLayers.widgets.SpreadsheetLayersDialog import (
            GeometryEncoding,
            GeometryType,
        )

        dlg = self.create_dialog()

        path = os.path.join(INPUT_PATH, "wkt_polygon.ods")
        dlg.setFilePath(path)
        dlg.afterOpenFile()
        assert dlg.sheet() == "wkt_polygon"
        assert dlg.layerName() == "wkt_polygon-wkt_polygon"
        assert dlg.header() is False
        assert dlg.geometry() is True
        assert dlg.geometryEncoding() == GeometryEncoding.WKT
        assert dlg.geometryField() == "wkt"
        assert dlg.geometryType() == GeometryType.wkbPolygon
        assert dlg.crs() == "EPSG:4326"

    def test_writeVrt_wkt_polygon(self):
        dlg = self.create_dialog()

        path = os.path.join(INPUT_PATH, "wkt_polygon.ods")
        dlg.setFilePath(path)
        dlg.afterOpenFile()

        with patch(
            "SpreadsheetLayers.widgets.SpreadsheetLayersDialog.SpreadsheetLayersDialog.vrtPath",
            return_value=os.path.join(OUTPUT_PATH, "wkt_polygon.ods.wkt_polygon.vrt"),
        ):
            dlg.writeVrt(overwrite=True)

        with open(
            os.path.join(INPUT_PATH, "wkt_polygon.ods.wkt_polygon.vrt"),
            mode="rt",
            encoding="utf-8",
        ) as expected_file, open(
            os.path.join(OUTPUT_PATH, "wkt_polygon.ods.wkt_polygon.vrt"),
            mode="rt",
            encoding="utf-8",
        ) as output_file:
            assert output_file.read() == expected_file.read()
