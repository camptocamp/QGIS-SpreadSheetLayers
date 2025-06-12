# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpreadsheetLayersPlugin
                                 A QGIS plugin
 Load layers from MS Excel and OpenOffice spreadsheets
                             -------------------
        begin                : 2014-10-30
        copyright            : (C) 2014 by Camptocamp
        email                : info@camptocamp.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
from pathlib import Path
import sys

# Ajout du dossier "libs" au PYTHONPATH pour les dépendances embarquées
libs_path = Path(__file__).resolve().parent / "libs"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SpreadsheetLayersPlugin class from file SpreadsheetLayersPlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #

    from .SpreadsheetLayersPlugin import SpreadsheetLayersPlugin

    return SpreadsheetLayersPlugin(iface)
