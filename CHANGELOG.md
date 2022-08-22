# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This is required to use [qgis-plugin-ci](https://opengisch.github.io/qgis-plugin-ci/)

<!-- ## Unreleased [{version_tag}](https://github.com/camptocamp/QGIS-SpreadSheetLayers/releases/tag/{version_tag}) - YYYY-MM-DD -->

## Version 2.1.0 (Unreleased)

- Add support for WKT and WKB encoded geometries
- Add translations for japanese
- Add translations for russian
- Add translations for german

## Version 2.0.1

- Fix help
- Add targets in Makefile
- Fix Info/Warning attributes now come from Qgis instead of QgsMessageBar

## Version 2.0.0

- Support for QGIS 3

## Version 1.0.1

- Add sheet name in default layer name.
- Handle non ascii characters in sheet names.
- Dynamically load .ui files.
- Handle non ascii characters in file paths.
- Add sheet name in .vrt filename to support multiple worksheets.
- Add russian translation file.

## Version 1.0

- Add changelog file.
- Add checkbox for end of file detection.
- Force encoding to UTF-8 before adding layer to layer tree.
- Fix column format selectors line position.
