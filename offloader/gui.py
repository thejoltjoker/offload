# Filename: dialog.py
"""Dialog-Style application."""

import sys
import psutil
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtWidgets import QLineEdit, QPushButton, QLabel, QTextBrowser, QFileDialog
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy, QFrame
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtCore
from pathlib import Path
from utils import setup_logger
from app import APP_DATA_PATH

setup_logger('debug')

# QStyle.SP_DriveHDIcon
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class GUI(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Paths
        vols = self.volumes()
        if vols:
            self.sourcePath = vols[0]
        else:
            self.sourcePath = Path()
        self.sourceSize = 0
        self.destPathHistory = APP_DATA_PATH / 'latest_destination.txt'
        self.destPath = self.getStoredDestPath()
        self.destSize = 0
        self.iconSize = 48
        self.stylePath = 'color: #4f555d; text-decoration: none;'
        self.styles = """
            QWidget{
                background: #282a2e;
                font-family: "Proxima Nova", helvetica, arial;
                font-size: 16px;
            }
            
            QPushButton {
                padding: 10px 15px;
                border-radius: 20px;
                background: #4f535b;
                color: #c5c8c6;
            }
            
            QPushButton:hover {
                background: #f0c674;
                color: #544033;
            }
            
            #offload-btn {
                padding: 10px 30px;
                background:#f1bf5c; 
                color: #544033;
            } 
                
            #offload-btn:hover{
                background: #f0c674;
            }
            
            #source-title, #destination-title{
                font-size: 32px;
                font-weight: bold;
            }                         
            
            #source-label, #destination-label{
                color: #707880; 
                font-weight: bold;
            }
            """
        # App settings
        self.setWindowTitle('Camera Offload')
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet(self.styles)
        # self.setWindowFlags(QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint))
        mainLayout = QVBoxLayout()
        mainColsLayout = QHBoxLayout()

        # Set main layout
        mainColsLayout.addLayout(self.sourceColumn())
        mainColsLayout.addSpacerItem(QSpacerItem(50, 10, QSizePolicy.MinimumExpanding))
        mainColsLayout.addWidget(QLabel('➡'))
        mainColsLayout.addSpacerItem(QSpacerItem(50, 10, QSizePolicy.MinimumExpanding))

        # Destination column
        mainColsLayout.addLayout(self.destinationColumn())
        mainLayout.addLayout(mainColsLayout)
        mainLayout.addWidget(QHLine())
        offloadButton = QPushButton('Offload')
        offloadButton.setObjectName('offload-btn')
        mainLayout.addWidget(offloadButton, 0, QtCore.Qt.AlignCenter)
        # mainLayout.addSpacing(5)
        # mainLayout.addWidget(QTextBrowser())

        self.setLayout(mainLayout)

        # Show UI
        self.show()

    def getStoredDestPath(self):
        logging.debug(self.destPathHistory)
        if self.destPathHistory.is_file:
            return Path(self.destPathHistory.read_text())
        return Path().home()

    def setStoredDestPath(self):
        if not self.destPathHistory.parent.is_dir():
            self.destPathHistory.parent.mkdir(parents=True)
        self.destPathHistory.write_text(str(self.destPath.resolve()))

    def sourceColumn(self):
        # Title
        sourceLabel = QLabel('Source')
        sourceLabel.setObjectName('source-label')

        # Source title
        self.sourceTitleLabel = QLabel(self.sourcePath.name)
        self.sourceTitleLabel.setObjectName('source-title')

        # Source path
        self.sourcePathLabel = self.pathLabel(self.sourcePath)

        # Set icon depending on path
        self.sourceIconPixmap = self.iconPixmap(self.sourcePath)
        self.sourceIconLabel = QLabel()
        self.sourceIconLabel.setPixmap(self.sourceIconPixmap)
        # Browse button
        sourceBrowseButton = QPushButton('Browse')
        sourceBrowseButton.clicked.connect(self.browseSource)

        # Browse layout
        sourceBrowseLayout = QHBoxLayout()
        sourceBrowseLayout.addWidget(self.sourceIconLabel)  # Icon
        sourceBrowseLayout.addWidget(self.sourceTitleLabel, alignment=QtCore.Qt.AlignLeft)  # Name
        sourceBrowseLayout.addStretch()  # Left align title
        sourceBrowseLayout.addWidget(sourceBrowseButton)  # Button

        # Full layout
        sourceLayout = QVBoxLayout()
        sourceLayout.addWidget(sourceLabel)
        sourceLayout.addLayout(sourceBrowseLayout)
        sourceLayout.addWidget(self.sourcePathLabel)

        return sourceLayout

    def destinationColumn(self):
        # Title
        destLabel = QLabel('Destination')
        destLabel.setObjectName('destination-label')

        # Destination title
        self.destTitleLabel = QLabel(self.destPath.name)
        self.destTitleLabel.setObjectName('destination-title')

        # Destination path
        self.destPathLabel = self.pathLabel(self.destPath)

        # Set icon depending on path
        self.destIconPixmap = self.iconPixmap(self.destPath)
        self.destIconLabel = QLabel()
        self.destIconLabel.setPixmap(self.destIconPixmap)

        # Browse button
        destBrowseButton = QPushButton('Browse')
        destBrowseButton.clicked.connect(self.browseDest)

        # Browse layout
        destBrowseLayout = QHBoxLayout()
        destBrowseLayout.addWidget(self.destIconLabel)  # Icon
        destBrowseLayout.addWidget(self.destTitleLabel, alignment=QtCore.Qt.AlignLeft)  # Name
        destBrowseLayout.addStretch()  # Left align title
        destBrowseLayout.addWidget(destBrowseButton)  # Button

        # Full layout
        destLayout = QVBoxLayout()
        destLayout.addWidget(destLabel)
        destLayout.addLayout(destBrowseLayout)
        destLayout.addWidget(self.destPathLabel)

        return destLayout

    def browse(self, start_dir=''):
        """Open a file browser dialog"""
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, 'Select Folder', str(start_dir), QFileDialog.ShowDirsOnly)
        return Path(folder_path)

    def browseSource(self):
        path = self.browse(start_dir=self.sourcePath)
        self.sourcePath = path
        self.updateSource()

    def browseDest(self):
        path = self.browse(start_dir=self.destPath)
        self.destPath = path
        self.setStoredDestPath()
        self.updateDest()

    def updateSource(self):
        self.sourceTitleLabel.setText(self.sourcePath.name)
        self.sourcePathLabel.setText(self.pathLabelText(self.sourcePath))
        self.sourceIconPixmap = self.iconPixmap(self.sourcePath)
        self.sourceIconLabel.setPixmap(self.sourceIconPixmap)

    def updateDest(self):
        self.destTitleLabel.setText(self.destPath.name)
        self.destPathLabel.setText(self.pathLabelText(self.destPath))
        self.destIconPixmap = self.iconPixmap(self.destPath)
        self.destIconLabel.setPixmap(self.destIconPixmap)

    def iconPixmap(self, path: Path):
        """Decide which icon to use based on path"""
        icon = QIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        if sys.platform == 'darwin' and 'Volumes' in str(path.resolve()):
            icon = QIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))

        iconPixmap = QPixmap(icon.pixmap(QtCore.QSize(self.iconSize, self.iconSize)))
        return iconPixmap

    def pathLabel(self, path: Path):
        text = self.pathLabelText(path)
        label = QLabel()
        label.setText(text)
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
        return label

    def pathLabelText(self, path: Path):
        return f'<a href="file:///{path.resolve()}" style="{self.stylePath}">{path.resolve()}</a>'

    @staticmethod
    def volumes():
        """Return a list of volumes mounted on the system"""
        if sys.platform == 'darwin':
            vols = [Path(x.mountpoint) for x in psutil.disk_partitions() if 'Volumes' in x.mountpoint]
            return vols


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    gui = GUI()
    sys.exit(app.exec_())
