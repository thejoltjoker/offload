#!/usr/bin/env python
"""
script_name.py
Description of script_name.py.
"""

import sys
from unittest import TestCase

from offload import gui as ogui
from PyQt5.QtWidgets import QApplication


class TestGUI(TestCase):
    def test_volumes(self):
        result = ogui.MainWindow.volumes()
        self.assertTrue(result is None or isinstance(result, dict))


class TestSettingsDialog(TestCase):
    def test_init(self):
        app = QApplication(sys.argv)
        gui = ogui.SettingsDialog()
        gui.show()
        gui.close()
        # Do not call app.exec_() so the test process does not block or exit
