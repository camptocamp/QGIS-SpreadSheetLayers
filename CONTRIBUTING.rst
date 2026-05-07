Contributing
============

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
