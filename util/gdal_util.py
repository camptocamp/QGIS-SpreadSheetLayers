# -*- coding: utf-8 -*-

import os
import tempfile
from osgeo import ogr

def testGdal():
    # Inspired from gdal test ogr_vrt_34
    # https://github.com/OSGeo/gdal/commit/82074ed5bd67d2efbfbcea50c5416856d9c5826d
    path = os.path.join(tempfile.gettempdir(), 'gdal_test.csv')
    f = open(path, 'wb')
    f.write('x,y\n'.encode('ascii'))
    f.write('2,49\n'.encode('ascii'))
    f.close()

    vrt_xml = """
<OGRVRTDataSource>
    <OGRVRTLayer name="test">
        <SrcDataSource relativeToVRT="0">tmp/test.csv</SrcDataSource>
        <SrcSql dialect="sqlite">SELECT * FROM test</SrcSql>
        <GeometryField encoding="PointFromColumns" x="x" y="y"/>
        <Field name="x" type="Real"/>
        <Field name="y" type="Real"/>
    </OGRVRTLayer>
</OGRVRTDataSource>"""

    ds = ogr.Open( vrt_xml )
    
    lyr = ds.GetLayerByName( 'test' )
    lyr.SetIgnoredFields(['x', 'y'])
    f = lyr.GetNextFeature()
    result = True
    if f is None:
        result = False
    elif f.GetGeometryRef().ExportToWkt() != 'POINT (2 49)':
        result = False
        
    ds = None

    os.unlink(path)
    return result

GDAL_COMPAT = testGdal()
