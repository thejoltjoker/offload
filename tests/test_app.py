import json
import logging
import re
from datetime import datetime
from pathlib import Path
from random import randint
from shutil import rmtree
from unittest import TestCase

from offload import utils
from offload.app import Offloader, Report
from offload.utils import FileList, Settings

utils.setup_logger("debug")

TEST_PIC = Path(__file__).parent / "test_pic.jpg"


class TestOffloader(TestCase):
    def setUp(self):
        self.test_source = Path("test_data/memoryCard").resolve()
        self.test_source.mkdir(exist_ok=True, parents=True)
        for i in range(20):
            f = Path(self.test_source / f"{i:04}.jpg")
            if (i % 2) == 0:
                file_size = 5
                f.write_bytes(bytes(str(i) * 1024**2 * file_size, "utf-8"))
            else:
                f.write_bytes(TEST_PIC.read_bytes())
        self.test_destination = Path("test_data/test_destination").resolve()
        self.test_structure = "taken_date"
        self.test_offloader = Offloader(
            source=self.test_source,
            dest=self.test_destination,
            structure=self.test_structure,
            filename=None,
            prefix="taken_date",
            mode="copy",
            dryrun=False,
            log_level="debug",
        )

    def tearDown(self) -> None:
        if self.test_source.exists():
            rmtree(self.test_source)
        if self.test_destination.exists():
            rmtree(self.test_destination)

    def test_offload_offload_date(self):
        ol = Offloader(
            source=self.test_source,
            dest=self.test_destination,
            structure="offload_date",
            filename=None,
            prefix=None,
            mode="copy",
            dryrun=False,
            log_level="debug",
        )

        self.assertTrue(ol.offload())

    def test_offload_custom_filename(self):
        ol = Offloader(
            source=self.test_source,
            dest=self.test_destination,
            structure="offload_date",
            filename="test_name",
            prefix="empty",
            mode="copy",
            dryrun=False,
            log_level="debug",
        )

        self.assertTrue(ol.offload())

        # Check if files exist and are named correctly
        logging.debug(f"Checking if destination dir exists {self.test_destination}")
        self.assertTrue(self.test_destination.is_dir())

        # Check if it creates a date folder with the correct date
        date_folder = (
            self.test_destination
            / str(datetime.now().year)
            / str(datetime.now().strftime("%Y-%m-%d"))
        )
        logging.debug(f"Checking if destination subdir exists {date_folder}")
        self.assertTrue(date_folder.is_dir())

        # Check if the files are named correctly (filename="test_name" is not a preset, so Preset.filename returns None -> "unknown")
        for file in self.test_destination.rglob("*.*"):
            self.assertIsNotNone(re.search(r"unknown(_\d{3})?[.]\w+", file.name), msg=file.name)

    def test_offload_filename_camera_make(self):
        ol = Offloader(
            source=self.test_source,
            dest=self.test_destination,
            structure="offload_date",
            filename="camera_make",
            prefix="empty",
            mode="copy",
            dryrun=False,
            log_level="debug",
        )

        self.assertTrue(ol.offload())

        # Check if files exist and are named correctly
        logging.debug(f"Checking if destination dir exists {self.test_destination}")
        self.assertTrue(self.test_destination.is_dir())

        # Check if it creates a date folder with the correct date
        date_folder = (
            self.test_destination
            / str(datetime.now().year)
            / str(datetime.now().strftime("%Y-%m-%d"))
        )
        logging.debug(f"Checking if destination subdir exists {date_folder}")
        self.assertTrue(date_folder.is_dir())

        # Check if the files are named correctly
        for file in self.test_destination.rglob("*.*"):
            self.assertIsNotNone(re.search(r"(?:(sony)|(unknown))(_\d{3})?[.]\w{3}", file.name))

    def test_offload_default_settings(self):
        ol = Offloader(
            source=self.test_source,
            dest=self.test_destination,
            structure="taken_date",
            filename=None,
            prefix="taken_date",
            mode="copy",
            dryrun=False,
            log_level="debug",
        )

        self.assertTrue(ol.offload())

        # Check if files exist and are named correctly
        logging.debug(f"Checking if destination dir exists {self.test_destination}")
        self.assertTrue(self.test_destination.is_dir())
        # Check if it creates a date folder with the correct date
        date_folder = (
            self.test_destination
            / str(datetime.now().year)
            / str(datetime.now().strftime("%Y-%m-%d"))
        )
        logging.debug(f"Checking if destination subdir exists {date_folder}")
        self.assertTrue(date_folder.is_dir())

        # Check if the files are named correctly
        for file in self.test_destination.rglob("*.*"):
            self.assertIsNotNone(re.search(r"\d{6}_.+[.]\w{3}", file.name))

    def test_destination(self):
        self.assertEqual(self.test_offloader.destination, self.test_destination)
        new_dest = Path("test_dir")
        self.test_offloader.destination = "test_dir"
        self.assertEqual(self.test_offloader.destination, new_dest)

    def test_source(self):
        self.assertEqual(self.test_offloader.source, self.test_source)
        new_dir = "test_dir_noExist"
        self.test_offloader.source = new_dir
        self.assertNotEqual(self.test_offloader.source, Path(new_dir))

    def test_structure(self):
        self.assertEqual(self.test_offloader.structure, self.test_structure)
        preset = "taken_date"
        self.test_offloader.structure = preset
        self.assertEqual(self.test_offloader.structure, preset)


class TestReport(TestCase):
    def setUp(self) -> None:
        self.test_source = Path("test_data/memoryCard").resolve()
        self.test_source.mkdir(exist_ok=True, parents=True)
        for i in range(100):
            f = Path(self.test_source / f"{i:04}.jpg")
            f.write_text(utils.random_string(randint(1, 4096)))
        self.test_destination = Path("test_data/test_destination").resolve()
        self.reporter = Report()
        self.source_files = FileList(self.test_source)

    def tearDown(self) -> None:
        if self.test_source.exists():
            rmtree(self.test_source)
        if self.test_destination.exists():
            rmtree(self.test_destination)

    def test_write(self):
        for f in self.source_files.files:
            self.reporter.write(f, f, "Copied")

    def test_write_html(self):
        for f in self.source_files.files:
            self.reporter.write(f, f, "Copied")
        self.reporter.write_html()
        self.assertTrue(Path(self.reporter.html_path).is_file())


class TestSettings(TestCase):
    def setUp(self) -> None:
        self.settings = Settings()
        self.settings._path = Path() / "_ol_test_settings.json"
        self.settings._init_settings()

    def tearDown(self) -> None:
        # self.settings._path.unlink()
        pass

    def test_write_settings(self):
        self.settings._write_settings(latest_destination=Path())
        with self.settings._path.open("r") as json_file:
            result = json.load(json_file)
        self.assertEqual(result.get("latest_destination"), str(Path()))

    def test_read_setting(self):
        with self.settings._path.open("w") as json_file:
            json.dump({"latest_destination": str(Path())}, json_file)

        self.settings._read_setting("latest_destination")

        with self.settings._path.open("r") as json_file:
            result = json.load(json_file)

        self.assertEqual(result.get("latest_destination"), str(Path()))

    def test_latest_destination(self):
        p = Path() / "ol_test_path"
        p.mkdir(parents=True, exist_ok=True)
        self.settings.latest_destination = p
        self.assertEqual(self.settings.latest_destination, p.resolve())

    def test_folder_structure(self):
        s = "test_string"
        self.settings.structure = s
        self.assertEqual(self.settings.structure, s)
