# -*- coding: utf-8 -*-
from pathlib import Path
import tempfile
from osgeo import ogr
ogr.DontUseExceptions()
# ogr.UseExceptions()

def testGdal():
    # Inspired from gdal test ogr_vrt_34
    tmp_dir = Path(tempfile.gettempdir())
    path = tmp_dir / "gdal_test.csv"

    path.write_text("x,y\n2,49\n", encoding="ascii")

    vrt_xml = f"""
<OGRVRTDataSource>
    <OGRVRTLayer name="gdal_test">
        <SrcDataSource relativeToVRT="0">{path}</SrcDataSource>
        <SrcSql dialect="sqlite">SELECT * FROM gdal_test</SrcSql>
        <GeometryField encoding="PointFromColumns" x="x" y="y"/>
        <Field name="x" type="Real"/>
        <Field name="y" type="Real"/>
    </OGRVRTLayer>
</OGRVRTDataSource>"""

    ds = ogr.Open(vrt_xml)
    lyr = ds.GetLayer(0)
    lyr.SetIgnoredFields(["x", "y"])
    f = lyr.GetNextFeature()

    result = (
        f is not None
        and f.GetGeometryRef().ExportToWkt() == "POINT (2 49)"
    )

    # Clean up
    f = None
    lyr = None
    ds = None
    path.unlink(missing_ok=True)

    return result

GDAL_COMPAT = testGdal()
