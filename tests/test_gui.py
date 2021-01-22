#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
script_name.py
Description of script_name.py.
"""
from unittest import TestCase
import sys
from PyQt5.QtWidgets import QApplication
from offload import gui as ogui

class TestGUI(TestCase):
    def test_volumes(self):
        result = ogui.GUI.volumes()
        self.fail()


class TestSettingsDialog(TestCase):
    def test_init(self):
        app = QApplication(sys.argv)
        gui = ogui.SettingsDialog()
        sys.exit(app.exec_())
