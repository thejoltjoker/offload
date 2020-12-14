#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
script_name.py
Description of script_name.py.
"""
from unittest import TestCase
import gui

def main():
    """docstring for main"""
    pass


if __name__ == '__main__':
    main()


class TestGUI(TestCase):
    def test_volumes(self):
        result = gui.GUI.volumes()
        self.fail()
