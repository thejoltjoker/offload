"""Dialog-Style application."""
import time
import sys
import psutil
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QDialog
from PyQt5.QtWidgets import QLineEdit, QPushButton, QLabel, QFileDialog, QProgressBar, QComboBox
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy, QFrame
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QHBoxLayout, QFormLayout
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path

from offload import VERSION
from utils import setup_logger, disk_usage
from app import Offloader
from app import Settings
import utils
from styles import STYLES, COLORS

setup_logger('debug')


# QStyle.SP_DriveHDIcon
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class Timer(QThread):
    _time_signal = pyqtSignal(float)

    def __init__(self):
        super(Timer, self).__init__()
        self.start_time = time.time()
        self.time_left = 1
        self.running = True

    @property
    def running_time(self):
        return time.time() - self.start_time

    def run(self):
        print(self.time_left)
        while True:
            self._time_signal.emit(self.time_left)
            self.time_left -= 1
            time.sleep(1)
            if not self.running:
                break


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.settings = Settings()
        self.initUI()
        # Show UI
        self.show()

    def initUI(self):
        fontDB = QFontDatabase()
        fontDB.addApplicationFont(str(Path(__file__).parent / 'data' / 'fonts' / 'SourceSans3-Regular.otf'))
        fontDB.addApplicationFont(str(Path(__file__).parent / 'data' / 'fonts' / 'SourceSans3-Bold.otf'))
        fontDB.addApplicationFont(str(Path(__file__).parent / 'data' / 'fonts' / 'SourceSans3-Light.otf'))
        font = QFont('Source Sans 3')
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)

        mainLayout = QFormLayout()
        mainLayout.addRow(QLabel('Latest Destination:'), QLineEdit(str(self.settings.latest_destination)))

        structureLayout = QHBoxLayout()
        structureLayout.addWidget(QComboBox())
        structureLayout.addWidget(QComboBox())
        mainLayout.addRow(QLabel('Folder Structure:'), QComboBox())
        mainLayout.addRow(QLabel('File Naming:'), QComboBox())
        self.setLayout(mainLayout)


class GUI(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offloader = None
        self.settings = Settings()
        # Paths
        # self.sourcePath = None
        self.sourcePath = Path().home() / 'Desktop' / 'offload' / 'kalla'
        vols = self.volumes()
        if vols:
            smallest_vol = min(vols, key=vols.get)
            # Only pick volumes smaller than 129 GB
            if vols[smallest_vol] / 1024 ** 3 < 129:
                self.sourcePath = Path(smallest_vol)

        fontDB = QFontDatabase()
        fontDB.addApplicationFont(str(Path(__file__).parent / 'data' / 'fonts' / 'SourceSans3-Regular.otf'))
        fontDB.addApplicationFont(str(Path(__file__).parent / 'data' / 'fonts' / 'SourceSans3-Bold.otf'))
        fontDB.addApplicationFont(str(Path(__file__).parent / 'data' / 'fonts' / 'SourceSans3-Light.otf'))
        font = QFont('Source Sans 3')
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        self.sourceSize = 0
        self.destPath = self.settings.latest_destination
        self.destSize = 0
        self.iconSize = 48
        self.colors = COLORS
        self.styles = STYLES
        self.styleOffloadBtnActive = f"""
                border-radius: 21px;
                padding: 10px 30px;
                background:{self.colors['gray']}; 
                color: {self.colors['bg']};
            """
        self.styleOffloadBtnFinished = f"""
                        border-radius: 21px;
                        padding: 10px 30px;
                        background:{self.colors['green']}; 
                        color: {self.colors['bg']};
                    """

        # App settings
        self.setWindowTitle(f'Offload {VERSION}')
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DirLinkIcon))
        # self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet(self.styles)
        self.initUI()

        # Show UI
        self.show()

        # Init offload
        if self.sourcePath:
            self.initOffloader()

    def initUI(self):
        mainLayout = QVBoxLayout()
        mainColsLayout = QHBoxLayout()

        # mainColsLayout
        # Source column
        mainColsLayout.addSpacerItem(QSpacerItem(100, 10, QSizePolicy.MinimumExpanding))
        mainColsLayout.addLayout(self.sourceColumn())

        # Arrow
        mainColsLayout.addSpacerItem(QSpacerItem(100, 10, QSizePolicy.MinimumExpanding))
        midLayout = QVBoxLayout()
        arrow = QLabel('→')
        arrow.setObjectName('arrow')
        midLayout.addWidget(arrow)
        settingsButton = QPushButton('...')
        midLayout.addWidget(settingsButton)
        mainColsLayout.addLayout(midLayout)
        mainColsLayout.addSpacerItem(QSpacerItem(100, 10, QSizePolicy.MinimumExpanding))

        # Destination column
        mainColsLayout.addLayout(self.destColumn())
        mainColsLayout.addSpacerItem(QSpacerItem(100, 10, QSizePolicy.MinimumExpanding))

        # mainLayout
        mainLayout.addStretch()
        mainLayout.addSpacerItem(QSpacerItem(0, 50, QSizePolicy.MinimumExpanding))
        mainLayout.addLayout(mainColsLayout)
        mainLayout.addSpacerItem(QSpacerItem(0, 50, QSizePolicy.MinimumExpanding))
        mainLayout.addStretch()
        # mainLayout.addWidget(QHLine())

        # Paths
        mainPathsLayout = QHBoxLayout()
        # Source path
        mainPathsLayout.addWidget(QLabel('Source:'))
        self.sourcePathLabel = self.pathLabel('')
        if self.sourcePath:
            self.sourcePathLabel = self.pathLabel(self.sourcePath)
        self.sourcePathLabel.setObjectName('source-path')
        mainPathsLayout.addWidget(self.sourcePathLabel)
        mainPathsLayout.addSpacerItem(QSpacerItem(50, 10, QSizePolicy.MinimumExpanding))

        # Destination path
        mainPathsLayout.addWidget(QLabel('Destination:'))
        self.destPathLabel = self.pathLabel(self.destPath)
        self.destPathLabel.setObjectName('dest-path')
        self.destPathLabel.setText(self.pathLabelText(self.destPath))
        mainPathsLayout.addWidget(self.destPathLabel)
        self.updateDestInfo()

        mainLayout.addLayout(mainPathsLayout)
        # Progress
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFixedHeight(10)
        mainLayout.addWidget(self.progressBar)

        subProgressBarLayout = QHBoxLayout()
        self.progressFiles = QLabel('1. Pick a source folder')
        self.progressFiles.setMinimumWidth(250)
        self.progressFiles.setAlignment(QtCore.Qt.AlignLeft)
        self.progressPercent = QLabel('2. Pick a destination folder')
        self.progressPercent.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.progressTime = QLabel('3. Press Offload')
        self.progressTime.setMinimumWidth(250)
        self.progressTime.setAlignment(QtCore.Qt.AlignRight)
        subProgressBarLayout.addWidget(self.progressFiles)
        subProgressBarLayout.addStretch()
        subProgressBarLayout.addWidget(self.progressPercent)
        subProgressBarLayout.addStretch()
        subProgressBarLayout.addWidget(self.progressTime)
        mainLayout.addLayout(subProgressBarLayout)

        # Offload button
        self.offloadButton = QPushButton('Offload')
        self.offloadButton.setObjectName('offload-btn')
        self.offloadButton.clicked.connect(self.offload)
        mainLayout.addWidget(self.offloadButton, 0, QtCore.Qt.AlignCenter)
        # mainLayout.addSpacing(5)
        # mainLayout.addWidget(QTextBrowser())

        self.setLayout(mainLayout)

    def updateProgressBar(self, progress):
        self.progressBar.setValue(int(progress.get('percentage', 0)))
        self.progressFiles.setText(progress.get('action', ''))
        self.progressPercent.setText(f'{int(progress.get("percentage", ""))}%')
        self.timer.time_left = progress.get('time')
        if progress['is_finished'] and self.offloader._running:
            self.finished()
        elif progress['is_finished'] and not self.offloader._running:
            self.canceled()
        self.updateDestInfo()

    def canceled(self):
        self.timer.running = False
        self.progressFiles.setText('Writing report')
        self.progressTime.setText('Offload canceled')
        self.offloadButton.setText('Canceled')
        self.offloadButton.setStyleSheet(
            f"#offload-btn {{background:{self.colors['dark-orange']};color:{self.colors['bg']};}}")
        self.offloadButton.clicked.disconnect()
        self.offloadButton.clicked.connect(self.close)

    def finished(self):
        self.progressBar.setValue(100)
        self.progressBar.setStyleSheet(
            f"QProgressBar::chunk {{background: {COLORS['green']}; border-radius: 5px;}}")
        self.progressPercent.setText(f'100%')
        self.progressTime.setText(f"Finished")
        self.timer.running = False
        self.offloadButton.setText('Done')
        self.offloadButton.setStyleSheet(
            f"#offload-btn {{background:{self.colors['green']};color:{self.colors['bg']};}}")
        self.offloadButton.clicked.disconnect()
        self.offloadButton.clicked.connect(self.close)

    def updateTime(self, value):
        self.progressTime.setText(f"Approx. {utils.time_to_string(value)} left")

    def offload(self):
        if self.sourcePath:
            self.timer.start()
            self.offloader.start()
            self.offloadButton.setText('Offloading')
            self.offloadButton.setStyleSheet(self.styleOffloadBtnActive)
            self.offloadButton.clicked.disconnect()
            self.offloadButton.clicked.connect(self.stopOffload)

    def stopOffload(self):
        """Cancel the running offload"""
        self.offloader._running = False

    def initOffloader(self):
        self.offloader = Offloader(source=self.sourcePath,
                                   dest=self.destPath,
                                   structure='taken_date',
                                   filename=None,
                                   prefix='taken_date',
                                   mode='copy',
                                   dryrun=False,
                                   log_level='debug')
        self.offloader._progress_signal.connect(self.updateProgressBar)
        self.timer = Timer()
        self.timer._time_signal.connect(self.updateTime)
        self.updateSourceInfo()
        self.updateDestInfo()

    def updateSourceInfo(self):
        self.sourceInfoLabel.setText(f'{self.offloader.source_files.count} files, {self.offloader.source_files.hsize}')

    def updateDestInfo(self):
        self.destInfoLabel.setText(f'{disk_usage(self.destPath, human=True).free} free')

    def sourceColumn(self):
        # Source title
        self.sourceTitleLabel = QLabel('Press Browse')
        if self.sourcePath:
            self.sourceTitleLabel = QLabel(self.sourcePath.name)
        self.sourceTitleLabel.setMinimumWidth(250)
        self.sourceTitleLabel.setObjectName('source-title')
        self.sourceTitleLabel.setAlignment(QtCore.Qt.AlignCenter)

        # Source info
        self.sourceInfoLabel = QLabel()
        self.sourceInfoLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.sourceInfoLabel.setText(f'0 files, 0 MB')

        # Browse button
        sourceBrowseButton = QPushButton('Browse')
        sourceBrowseButton.clicked.connect(self.browseSource)

        # Full layout
        sourceLayout = QVBoxLayout()
        sourceLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        sourceLayout.addWidget(self.sourceTitleLabel)
        sourceLayout.addWidget(self.sourceInfoLabel)
        sourceLayout.addWidget(sourceBrowseButton)
        return sourceLayout

    def destColumn(self):
        # dest title
        self.destTitleLabel = QLabel(self.destPath.name)
        self.destTitleLabel.setMinimumWidth(250)
        self.destTitleLabel.setObjectName('dest-title')
        self.destTitleLabel.setAlignment(QtCore.Qt.AlignCenter)

        # dest info
        self.destInfoLabel = QLabel()
        self.destInfoLabel.setAlignment(QtCore.Qt.AlignCenter)

        # Browse button
        destBrowseButton = QPushButton('Browse')
        destBrowseButton.clicked.connect(self.browseDest)

        # Full layout
        destLayout = QVBoxLayout()
        destLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        destLayout.addWidget(self.destTitleLabel)
        destLayout.addWidget(self.destInfoLabel)
        destLayout.addWidget(destBrowseButton)

        return destLayout

    def browse(self, start_dir=''):
        """Open a file browser dialog"""
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, 'Select Folder', str(start_dir), QFileDialog.ShowDirsOnly)
        if folder_path:
            return Path(folder_path)

    def browseSource(self):
        start_dir = self.sourcePath
        if not self.sourcePath:
            start_dir = Path().home()
        path = self.browse(start_dir=start_dir)

        if path:
            self.sourcePath = path
            if not self.offloader:
                self.initOffloader()
            self.updateSource()

    def browseDest(self):
        # Update ui
        path = self.browse(start_dir=self.destPath)
        if path:
            self.destPath = path
            self.settings.latest_destination = self.destPath
            self.updateDest()
            # Update offload
            self.offloader.destination = self.destPath

    def updateSource(self):
        # Update ui
        self.sourceTitleLabel.setText(self.sourcePath.name)
        self.sourcePathLabel.setText(self.pathLabelText(self.sourcePath))

        # Update offload
        self.offloader.source = self.sourcePath
        self.updateSourceInfo()

    def updateDest(self):
        self.destTitleLabel.setText(self.destPath.name)
        self.destPathLabel.setText(self.pathLabelText(self.destPath))
        self.updateDestInfo()

    def pathLabel(self, path):
        text = path
        if isinstance(path, Path):
            text = self.pathLabelText(path)
        label = QLabel()
        label.setText(text)
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
        return label

    def pathLabelText(self, path: Path):
        return f'<a href="file:///{path.resolve()}" style="color:{self.colors["primary"]};text-decoration:none;">' \
               f'{path.resolve()}' \
               f'</a>'

    @staticmethod
    def volumes():
        """Return a list of volumes mounted on the system"""
        if sys.platform == 'darwin':
            vols = {}
            for p in psutil.disk_partitions():
                if 'Volumes' in p.mountpoint:
                    if 'Recovery' not in p.mountpoint:
                        vols[p.mountpoint] = psutil.disk_usage(p.mountpoint).total
            if vols:
                logging.debug(vols)
                logging.debug(min(vols, key=vols.get))
            return vols


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    gui = GUI()
    sys.exit(app.exec_())
