# QGIS-SpreadSheetLayers
QGIS plugin to load layers from spreadsheet files (*.ods, *.xls, *.xlsx)

## Description

Adds a "Add spreadsheet layer" entry in *Layer* / *Add new Layer* menu and a
corresponding button in *Layers* toolbar. These two links open a "Add new
spreadsheet layer" dialog with some options (select file, layer name, sheet,
use header, ignore some rows, load geometry and select x and y fields).

When dialog is accepted, it creates a new GDAL VRT file in same folder as the
source data file, expanded with a *.vrt* suffix, which is loaded into QGIS.

When reusing the same file twice, the dialog loads its values from the
existing *.vrt* file.

## Requirements

With GDAL <= 1.11.1, the plugin works with graceful degradation, geometry
loading is locked when offset is not null, ie:

- if you ignore some lines at start of spreadsheet;
- if you use header line with corresponding GDAL functionality disabled.

## Runtime configuration

GDAL do not allow to define the presence of header line on a per layer basis,
this choice is made through environment variables for each driver
*OGR_ODS_HEADERS*, *OGR_XLS_HEADERS* and *OGR_XLSX_HEADERS*,
with tree possible values *FORCE*, *DISABLE* and *AUTO*.
For more details, consult the corresponding drivers documentation ie:
http://www.gdal.org/drv_ods.html, http://www.gdal.org/drv_xls.html
and http://www.gdal.org/drv_xlsx.html.

For each driver, the default value is *AUTO*, but automatic detection behavior
depends on driver:

- for *ODS* driver: *AUTO* equals to *FORCE*
- for *XLS* and *XLSX* drivers: *AUTO* equals to *DISABLE*

To enable the header checkbox in the plugin dialog, it's necessary that the
corresponding header environnement variable is considered as equal to
*DISABLE*. In other cases, the checkbox is checked and locked.

So, to load correctly *.ods* files without headers, you must set
*OGR_ODS_HEADERS* to *DISABLE*.

You can configure this in QGIS settings:

- open *Settings* / *Options* dialog;
- select *System* tab, and go to *Environnement* section;
- check *Use custom variables*.
- add a new line with values:

   *Append* | *OGR_ODS_HEADERS* | *DISABLE*

- restart QGIS to take this into consideration.

Conversely, if the plugin works with graceful degradation,
and you want to load geometry from a Excel file with headers,
you have to set *OGR_XLS_HEADERS* to *FORCE*.

## Development install (linux):

```
git clone git@github.com:camptocamp/QGIS-SpreadSheetLayers.git SpreadSheetLayers
ln -s SpreadSheetLayers ~/.qgis2/python/plugins/
cd SpreadSheetLayers
make
```

- run QGIS and activate SpreadSheetLayers plugin.
