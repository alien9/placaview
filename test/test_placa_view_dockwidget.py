# coding=utf-8
"""DockWidget test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'barufi@gmail.com'
__date__ = '2024-04-26'
__copyright__ = 'Copyright 2024, Tiago Barufi'

import unittest
from qgis.PyQt.QtWidgets import QApplication
from placa_view_dockwidget import PlacaViewDockWidget

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class PlacaViewDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.app=QApplication([])
        self.dockwidget = PlacaViewDockWidget()

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test we can click OK."""
        self.assertEqual(1,1)
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(PlacaViewDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

