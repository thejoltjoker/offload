"""Dialog-Style application."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from offload import APP_DATA_PATH, VERSION, utils
from offload.app import Offloader
from offload.styles import COLORS, STYLES
from offload.utils import File, Settings, disk_usage, setup_logger

setup_logger("debug")


# Resolve fonts dir: py2app uses package/data, dev uses repo data/ or APP_DATA_PATH/data
def _fonts_dir():
    candidates = [
        Path(__file__).parent / "data" / "fonts",
        APP_DATA_PATH / "data" / "fonts",
        Path.cwd() / "data" / "fonts",
    ]
    for d in candidates:
        if d.is_dir() and (d / "SourceSans3-Regular.otf").exists():
            return d
    return None


def _apply_font(widget):
    """Load Source Sans 3 if available and set on widget; otherwise use system fallback."""
    font_dir = _fonts_dir()
    fontDB = QFontDatabase()
    if font_dir:
        for name in ("SourceSans3-Regular.otf", "SourceSans3-Bold.otf", "SourceSans3-Light.otf"):
            path = font_dir / name
            if path.exists():
                fontDB.addApplicationFont(str(path))
    families = QFontDatabase().families()
    if "Source Sans 3" in families:
        font = QFont("Source Sans 3")
    else:
        font = QFont("Helvetica Neue")  # macOS fallback
        logging.debug(
            "Source Sans 3 not found (add data/fonts/ with .otf files), using Helvetica Neue"
        )
    font.setStyleStrategy(QFont.PreferAntialias)
    widget.setFont(font)


# QStyle.SP_DriveHDIcon
class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class Timer(QThread):
    _time_signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()
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
            if self.time_left > 0:
                self.time_left -= 1
            time.sleep(1)
            if not self.running:
                break


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.example_file = File("IMG_01337.RAW")
        self.initUI()
        # Show UI
        # self.show()

    def initUI(self):
        self.resize(640, 260)
        _apply_font(self)

        # mainLayout = QVBoxLayout()
        mainLayout = QGridLayout()
        self.destinationLine = QLineEdit(str(self.settings.default_destination))
        self.destinationLine.textChanged.connect(self.defaultDestinationChange)
        # mainLayout.addWidget(QLabel('Default Destination:'), 0, 0, 1, 1)
        # mainLayout.addWidget(self.destinationLine, 0, 1, 1, 2)

        # Structure presets
        self.structureCombo = QComboBox()
        self.structureOptions = {
            0: "original",
            1: "taken_date",
            2: "year_month",
            3: "year",
            4: "flat",
        }
        self.structureCombo.addItem("Keep original")
        self.structureCombo.addItem("YYYY/YYYY-MM-DD")
        self.structureCombo.addItem("YYYY/MM")
        self.structureCombo.addItem("YYYY")
        self.structureCombo.addItem("Flat")

        # Set current item from settings
        currentStructure = list(self.structureOptions.values()).index(self.settings.structure)
        self.structureCombo.setCurrentIndex(currentStructure)
        # Add to layout and add an action
        self.structureCombo.currentIndexChanged.connect(self.folderStructureChange)
        mainLayout.addWidget(QLabel("Folder Structure:"), 1, 0, 1, 1)
        mainLayout.addWidget(self.structureCombo, 1, 1, 1, 2)

        # Prefix presets
        self.prefixCombo = QComboBox()
        self.prefixOptions = {0: "empty", 1: "taken_date", 2: "taken_date_time"}
        self.prefixCombo.addItem("No prefix")
        self.prefixCombo.addItem("YYMMDD")
        self.prefixCombo.addItem("YYMMDD_hhmmss")
        # Set current item from settings
        currentPrefix = list(self.prefixOptions.values()).index(self.settings.prefix)
        self.prefixCombo.setCurrentIndex(currentPrefix)
        # Connect action
        self.prefixCombo.currentIndexChanged.connect(self.prefixChange)
        # Add to layout
        mainLayout.addWidget(QLabel("Filename prefix:"), 2, 0, 1, 1)
        mainLayout.addWidget(self.prefixCombo, 2, 1, 1, 2)

        # Filename presets
        self.filenameCombo = QComboBox()
        self.filenameOptions = {0: None, 1: "camera_make", 2: "camera_model"}
        self.filenameCombo.addItem("Keep original")
        self.filenameCombo.addItem("Camera brand")
        self.filenameCombo.addItem("Camera model")
        # Set current item from settings
        if self.settings.filename != "None":
            currentFilename = list(self.filenameOptions.values()).index(self.settings.filename)
        else:
            currentFilename = 0
        self.filenameCombo.setCurrentIndex(currentFilename)

        # Connect action
        self.filenameCombo.currentIndexChanged.connect(self.filenameChange)
        # Add to layout
        mainLayout.addWidget(QLabel("Filename:"), 3, 0, 1, 1)
        mainLayout.addWidget(self.filenameCombo, 3, 1, 1, 2)

        # Filename presets
        self.exampleLabel = QLabel(
            "/Volumes/mcdaddy/media/photos/2021/2021-02-28/210228_IMG_01337.dng"
        )
        self.updateExampleLabel()
        # Add to layout
        mainLayout.addWidget(QLabel("Example:"), 4, 0, 1, 3)
        mainLayout.addWidget(self.exampleLabel, 5, 0, 1, 3)

        # Close button
        self.closeButton = QPushButton("Close")
        self.closeButton.clicked.connect(self.close)
        mainLayout.addWidget(self.closeButton, 6, 0, 1, 3)

        _apply_font(self)

        # Styling
        self.colors = COLORS
        self.styles = STYLES
        self.setStyleSheet(self.styles)

        self.setLayout(mainLayout)

    def updateExampleLabel(self):
        """Update the example label to be correct with the new settings"""
        label = ""
        path = Path("/Volumes/Storage/Pictures/IMG_01337.dng")
        prefix = utils.Preset.prefix(self.settings.prefix)
        structure = utils.Preset.structure(self.settings.structure)
        filename = path.name
        label = f"{path.parent}"

        if structure:
            subdir = f"{structure.format(date=datetime.now())}"
            label = f"{label}/{subdir}"

        if self.settings.filename == "camera_make":
            filename = "sony_003.dng"
        elif self.settings.filename == "camera_model":
            filename = "ilce-7m3_003.dng"

        if prefix:
            filename = f"{prefix.format(date=datetime.now())}_{filename}"

        label = f"{label}/{filename}"
        self.exampleLabel.setText(label)

    def defaultDestinationChange(self):
        self.settings.default_destination = self.destinationLine.text()
        self.updateExampleLabel()
        logging.info(f"Default destination changed to {self.settings.default_destination}")

    def folderStructureChange(self):
        self.settings.structure = self.structureOptions[self.structureCombo.currentIndex()]
        self.updateExampleLabel()
        logging.info(
            f"Folder structure changed to {self.structureOptions[self.structureCombo.currentIndex()]}"
        )

    def filenameChange(self):
        self.settings.filename = self.filenameOptions[self.filenameCombo.currentIndex()]
        self.updateExampleLabel()
        logging.info(
            f"Filename changed to {self.filenameOptions[self.filenameCombo.currentIndex()]}"
        )

    def prefixChange(self):
        self.settings.prefix = self.prefixOptions[self.prefixCombo.currentIndex()]
        self.updateExampleLabel()
        logging.info(f"Prefix changed to {self.prefixOptions[self.prefixCombo.currentIndex()]}")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set central widget
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)

        self.offloader = None
        self.settings = Settings()

        # Paths
        self.sourcePath = None
        # self.sourcePath = Path().home()

        # Load smallest drive as source path
        vols = self.volumes()
        if vols:
            smallest_vol = min(vols, key=vols.get)
            # Only pick volumes smaller than 129 GB
            if vols[smallest_vol] / 1024**3 < 129:
                self.sourcePath = Path(smallest_vol)

        _apply_font(self)

        self.sourceSize = 0
        self.destPath = self.settings.destination()
        self.destSize = 0
        self.iconSize = 48
        self.colors = COLORS
        self.styles = STYLES
        self.styleOffloadBtnActive = f"""
                border-radius: 21px;
                padding: 10px 30px;
                background:{self.colors["gray"]}; 
                color: {self.colors["bg"]};
            """
        self.styleOffloadBtnFinished = f"""
                        border-radius: 21px;
                        padding: 10px 30px;
                        background:{self.colors["green"]}; 
                        color: {self.colors["bg"]};
                    """

        # App settings
        self.setWindowTitle(f"Offload {VERSION}")
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
        arrow = QLabel("→")
        arrow.setObjectName("arrow")
        midLayout.addWidget(arrow)

        # Settings
        settingsButton = QPushButton("...")
        settingsButton.clicked.connect(self.settingsDialog)
        midLayout.addWidget(settingsButton)

        # Add middle layout and spacer
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
        mainPathsLayout.addWidget(QLabel("Source:"))
        self.sourcePathLabel = self.pathLabel("")
        if self.sourcePath:
            self.sourcePathLabel = self.pathLabel(self.sourcePath)
        self.sourcePathLabel.setObjectName("source-path")
        mainPathsLayout.addWidget(self.sourcePathLabel)
        mainPathsLayout.addSpacerItem(QSpacerItem(50, 10, QSizePolicy.MinimumExpanding))

        # Destination path
        mainPathsLayout.addWidget(QLabel("Destination:"))
        self.destPathLabel = self.pathLabel(self.destPath)
        self.destPathLabel.setObjectName("dest-path")
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
        self.progressFiles = QLabel("1. Pick a source folder")
        self.progressFiles.setMinimumWidth(250)
        self.progressFiles.setAlignment(QtCore.Qt.AlignLeft)
        self.progressPercent = QLabel("2. Pick a destination folder")
        self.progressPercent.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.progressTime = QLabel("3. Press Offload")
        self.progressTime.setMinimumWidth(250)
        self.progressTime.setAlignment(QtCore.Qt.AlignRight)
        subProgressBarLayout.addWidget(self.progressFiles)
        subProgressBarLayout.addStretch()
        subProgressBarLayout.addWidget(self.progressPercent)
        subProgressBarLayout.addStretch()
        subProgressBarLayout.addWidget(self.progressTime)
        mainLayout.addLayout(subProgressBarLayout)

        # Offload button
        self.offloadButton = QPushButton("Offload")
        self.offloadButton.setObjectName("offload-btn")
        self.offloadButton.clicked.connect(self.offload)
        mainLayout.addWidget(self.offloadButton, 0, QtCore.Qt.AlignCenter)
        # mainLayout.addSpacing(5)
        # mainLayout.addWidget(QTextBrowser())

        self._centralWidget.setLayout(mainLayout)

    def settingsDialog(self):
        """Open the settings dialog to make changes to settings"""
        # app = QApplication(sys.argv)
        logging.debug("Settings dialog opened")
        settings = SettingsDialog()
        settings.exec_()

        # Load settings from file
        # self.offloader.update_from_settings()

    def updateProgressBar(self, progress):
        self.progressBar.setValue(int(progress.get("percentage", 0)))
        self.progressFiles.setText(progress.get("action", ""))
        self.progressPercent.setText(f"{int(progress.get('percentage', ''))}%")
        self.timer.time_left = progress.get("time")
        if progress["is_finished"] and self.offloader._running:
            self.finished()
        elif progress["is_finished"] and not self.offloader._running:
            self.canceled()
        self.updateDestInfo()

    def canceled(self):
        self.timer.running = False
        self.progressFiles.setText("Writing report")
        self.progressTime.setText("Offload canceled")
        self.offloadButton.setText("Canceled")
        self.offloadButton.setStyleSheet(
            f"#offload-btn {{background:{self.colors['dark-orange']};color:{self.colors['bg']};}}"
        )
        self.offloadButton.clicked.disconnect()
        self.offloadButton.clicked.connect(self.close)

    def finished(self):
        self.progressBar.setValue(100)
        self.progressBar.setStyleSheet(
            f"QProgressBar::chunk {{background: {COLORS['green']}; border-radius: 5px;}}"
        )
        self.progressPercent.setText("100%")
        self.progressTime.setText("Finished")
        self.timer.running = False
        self.offloadButton.setText("Done")
        self.offloadButton.setStyleSheet(
            f"#offload-btn {{background:{self.colors['green']};color:{self.colors['bg']};}}"
        )
        self.offloadButton.clicked.disconnect()
        self.offloadButton.clicked.connect(self.close)

    def updateTime(self, value):
        self.progressTime.setText(f"Approx. {utils.time_to_string(value)} left")

    def offload(self):
        if self.sourcePath:
            self.timer.start()
            self.offloader.start()
            self.offloadButton.setText("Offloading")
            self.offloadButton.setStyleSheet(self.styleOffloadBtnActive)
            self.offloadButton.clicked.disconnect()
            self.offloadButton.clicked.connect(self.stopOffload)

    def stopOffload(self):
        """Cancel the running offload"""
        self.offloader._running = False

    def initOffloader(self):
        self.offloader = Offloader(
            source=self.sourcePath,
            dest=self.destPath,
            structure=self.settings.structure,
            filename=self.settings.filename,
            prefix=self.settings.prefix,
            mode="copy",
            dryrun=False,
            log_level="debug",
        )
        self.offloader._progress_signal.connect(self.updateProgressBar)
        self.timer = Timer()
        self.timer._time_signal.connect(self.updateTime)
        self.updateSourceInfo()
        self.updateDestInfo()

    def updateSourceInfo(self):
        self.sourceInfoLabel.setText(
            f"{self.offloader.source_files.count} files, {self.offloader.source_files.hsize}"
        )

    def updateDestInfo(self):
        self.destInfoLabel.setText(f"{disk_usage(self.destPath, human=True).free} free")

    def sourceColumn(self):
        # Source title
        self.sourceTitleLabel = QLabel("Press Browse")
        if self.sourcePath:
            self.sourceTitleLabel = QLabel(self.sourcePath.name)
        self.sourceTitleLabel.setMinimumWidth(250)
        self.sourceTitleLabel.setObjectName("source-title")
        self.sourceTitleLabel.setAlignment(QtCore.Qt.AlignCenter)

        # Source info
        self.sourceInfoLabel = QLabel()
        self.sourceInfoLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.sourceInfoLabel.setText("0 files, 0 MB")

        # Browse button
        sourceBrowseButton = QPushButton("Browse")
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
        self.destTitleLabel.setObjectName("dest-title")
        self.destTitleLabel.setAlignment(QtCore.Qt.AlignCenter)

        # dest info
        self.destInfoLabel = QLabel()
        self.destInfoLabel.setAlignment(QtCore.Qt.AlignCenter)

        # Browse button
        destBrowseButton = QPushButton("Browse")
        destBrowseButton.clicked.connect(self.browseDest)

        # Full layout
        destLayout = QVBoxLayout()
        destLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        destLayout.addWidget(self.destTitleLabel)
        destLayout.addWidget(self.destInfoLabel)
        destLayout.addWidget(destBrowseButton)

        return destLayout

    def browse(self, start_dir=""):
        """Open a file browser dialog"""
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(
            None, "Select Folder", str(start_dir), QFileDialog.ShowDirsOnly
        )
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
        label.setTextInteractionFlags(
            QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse
        )
        return label

    def pathLabelText(self, path: Path):
        return (
            f'<a href="file:///{path.resolve()}" style="color:{self.colors["primary"]};text-decoration:none;">'
            f"{path.resolve()}"
            f"</a>"
        )

    @staticmethod
    def volumes():
        """Return a list of volumes mounted on the system"""
        if sys.platform == "darwin":
            vols = {}
            for p in psutil.disk_partitions():
                if "Volumes" in p.mountpoint:
                    if "Recovery" not in p.mountpoint:
                        vols[p.mountpoint] = psutil.disk_usage(p.mountpoint).total
            if vols:
                logging.debug(vols)
                logging.debug(min(vols, key=vols.get))
            return vols


def run():
    """Run the app"""
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    # app.main = GUI()
    gui = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
