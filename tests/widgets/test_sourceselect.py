import os
from unittest.mock import patch

from qgis.gui import (
    QgsAbstractDataSourceWidget,
    QgsGui,
    QgsSourceSelectProvider,
)

from tests import QgisTestCase
from tests import INPUT_PATH, OUTPUT_PATH


class TestSpreadsheetLayersSourceSelect(QgisTestCase):
    def create_provider(self):
        from SpreadsheetLayers.widgets.sourceselect import (
            SpreadsheetLayersSourceSelectProvider,
        )

        return SpreadsheetLayersSourceSelectProvider()

    def create_widget(self):
        return self.create_provider().createDataSourceWidget(None)

    def test_provider_returns_source_select_widget(self):
        widget = self.create_widget()
        assert isinstance(widget, QgsAbstractDataSourceWidget)
        widget.deleteLater()

    def test_provider_ordering_before_metadata_search(self):
        provider = self.create_provider()
        assert provider.ordering() == QgsSourceSelectProvider.OrderSearchProvider - 1000
        assert provider.ordering() < QgsSourceSelectProvider.OrderSearchProvider

    def test_provider_registration_in_registry(self):
        registry = QgsGui.instance().sourceSelectProviderRegistry()
        provider = self.create_provider()
        registry.addProvider(provider)
        try:
            assert provider in registry.providers()
        finally:
            registry.removeProvider(provider)

    def test_add_button_clicked_writes_vrt(self):
        widget = self.create_widget()
        path = os.path.join(INPUT_PATH, "x_y.ods")
        widget._dialog.setFilePath(path)
        widget._dialog.afterOpenFile()

        vrt_path = os.path.join(OUTPUT_PATH, "x_y.ods.x_y.vrt")
        if os.path.exists(vrt_path):
            os.remove(vrt_path)

        with patch(
            "SpreadsheetLayers.widgets.SpreadsheetLayersDialog.SpreadsheetLayersDialog.vrtPath",
            return_value=vrt_path,
        ):
            widget.addButtonClicked()

        assert os.path.exists(vrt_path)
        widget.deleteLater()
