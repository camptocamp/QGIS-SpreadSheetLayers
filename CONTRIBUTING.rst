Contributing
============

Development install (linux)
---------------------------

.. code::

   git clone git@github.com:camptocamp/QGIS-SpreadSheetLayers.git SpreadsheetLayers
   cd SpreadsheetLayers
   make build
   make link

- run QGIS and activate SpreadsheetLayers plugin.

The :code:`link` target creates the symbolic link in the QGIS profile
directory given by :code:`QGISDIR`, which defaults to
:code:`.local/share/QGIS/QGIS4/profiles/default` (relative to your
:code:`$HOME`). Override it to target another QGIS version or profile:

.. code::

   make link QGISDIR=.local/share/QGIS/QGIS3/profiles/default

Docker environment
------------------

Linters, tests and packaging run in a Docker image based on the official
:code:`qgis/qgis` images. Build it with:

.. code::

   make docker-build

The QGIS version defaults to the one set in the :code:`Makefile` and can be
selected with the :code:`QGIS_VERSION` variable:

.. code::

   make docker-build test QGIS_VERSION=3.44

Each version is tagged separately
(:code:`camptocamp/qgis-spreadsheetlayers:<version>`), so images for several
QGIS versions can coexist. To use a version for all the commands of your
terminal session, export it:

.. code::

   export QGIS_VERSION=3.44

Then run the checks and the tests suite:

.. code::

   make check
   make test

Or run QGIS desktop with the plugin loaded:

.. code::

   make qgis

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
