.. SpreadsheetLayers documentation master file, created by
   sphinx-quickstart on Thu Jan 15 15:15:55 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

QGIS-SpreadSheetLayers
======================

QGIS plugin to load layers from spreadsheet files (\*.ods, \*.xls, \*.xlsx)

Description
-----------

This plugin adds a *Add spreadsheet layer* entry in *Layer* / *Add new Layer*
menu and a corresponding button in *Layers* toolbar. These two links open the
same dialog to load a layer from a spreadsheet file with some options:

* select file
* layer name
* sheet selection
* header at first line
* ignore some rows
* load geometry from x and y fields

When dialog is accepted, it creates a new GDAL VRT file in same folder as the
source data file and layer name, expanded with a *.vrt* suffix, which is
loaded into QGIS.

When reusing the same file twice, the dialog loads its values from the
existing *.vrt* file.

Limitations
-----------

Due to a GDAL/OGR lacks of functionalities:

- use of header line on a per file basis ;
- ignore lines at the beginning of file ;
- correct end of .xls files detection.

The plugin use an SQLITE select statement with offset and limit parameters
to extract corresponding data from the source file. When one of this
functionalities is in use, this could have some side effects.

With GDAL <= 1.11.1, the plugin can't load geometry. With graceful
degradation, geometry checkbox is then locked. To get the GDAL version in use,
run this commands in QGIS python console:

.. code::

    import osgeo.gdal
    print(osgeo.gdal.__version__)

When opening a spreadsheet file, GDAL/OGR will try to detect the data type of
columns (Date, Integer, Real, String, ...). This automatic detection occurs
outside of plugin header and ignore lines functionalities, so when using this,
GDAL/OGR should be unable to correctly detect data types.

Configuration
-------------

GDAL do not allow to define the presence of header line on a per layer basis,
this choice is made through environment variables for each driver
*OGR_ODS_HEADERS*, *OGR_XLS_HEADERS* and *OGR_XLSX_HEADERS*,
with tree possible values *FORCE*, *DISABLE* and *AUTO*.
For more details, consult the corresponding drivers documentation ie:
http://www.gdal.org/drv_ods.html, http://www.gdal.org/drv_xls.html
and http://www.gdal.org/drv_xlsx.html.

You can change this values in QGIS settings:

- open *Settings* / *Options* dialog;
- select *System* tab, and go to *Environment* section;
- check *Use custom variables*.
- add a new line. Example:

   *Overwrite* | *OGR_ODS_HEADERS* | *FORCE*

- restart QGIS to take this into consideration.

Development install (linux)
---------------------------

.. code::

   git clone git@github.com:camptocamp/QGIS-SpreadSheetLayers.git SpreadsheetLayers
   cd SpreadsheetLayers
   ln -s ${PWD}/SpreadsheetLayers ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins
   make

- run QGIS and activate SpreadsheetLayers plugin.

Release a new version
---------------------

First update l10n files:

.. code::

   make tx-pull

Then create a commit if relevant:

.. code::

   git add -p .
   git commit -m 'Update l10n'

Now update :code:`SpreadsheetLayers/metadata.txt` file with the version number.

For an experimental release:

.. code::

   version=X.Y.Z-alpha+build
   experimental=False

Or for a final release:

.. code::

   version=X.Y.Z
   experimental=True

And create a new commit, tag, and push on GitHub:

.. code::

   git add -p .
   git commit -m 'Release version ...'
   git push origin master

Then create the package and test it with you local QGIS:

.. code::

   make package deploy
   qgis

Then, if everything looks fine, you can create a tag:

.. code::

   git tag X.Y.Z
   git push origin X.Y.Z

Then log in to QGIS plugins repository: https://plugins.qgis.org/accounts/login/

And upload the file :code:`dist/SpreadsheetLayers.zip` here: https://plugins.qgis.org/plugins/SpreadsheetLayers/
