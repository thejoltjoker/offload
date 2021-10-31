#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verify.py
Description of verify.py.
"""
from pathlib import Path
from offload.utils import FileList, File


class Verifier:
    def __init__(self, source, backups=None):
        if backups is None:
            self.backups = []
        self.source = source

    def get_source_files(self):
        """Get a filelist with the source files"""


def main():
    """docstring for main"""
    pass


if __name__ == '__main__':
    main()
