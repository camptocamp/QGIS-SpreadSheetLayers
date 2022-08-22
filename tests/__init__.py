import os

# import qgis libs so that we set the correct sip api version
import qgis  # pylint: disable=W0611  # NOQA
from qgis import utils as qgis_utils

from qgis.testing import start_app, TestCase as QgisTestCase  # noqa
from qgis.testing.mocked import get_iface

QGIS_APP = start_app()
iface = get_iface()
qgis_utils.iface = iface

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
EXPECTED_PATH = os.path.join(DATA_PATH, "expected")
INPUT_PATH = os.path.join(DATA_PATH, "input")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", os.path.join(DATA_PATH, "output"))
TEMP_PATH = "/tmp"

OVERWRITE_EXPECTED = os.environ.get("OVERWRITE_EXPECTED", False)

os.makedirs(OUTPUT_PATH, exist_ok=True)
