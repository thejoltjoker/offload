import logging
from unittest import TestCase
from offload.app import Offloader, File, FileList, Report, Settings
from offload import utils
from pathlib import Path
from datetime import datetime
from random import randint
from shutil import rmtree
import json

utils.setup_logger('debug')


class TestOffloader(TestCase):
    def setUp(self):
        self.test_source = Path("test_data/memoryCard").resolve()
        self.test_source.mkdir(exist_ok=True, parents=True)
        for i in range(100):
            f = Path(self.test_source / f"{i:04}.jpg")
            f.write_text(utils.random_string(randint(1, 16384)))
        self.test_destination = Path("test_data/test_destination").resolve()
        self.test_structure = 'taken_date'
        self.test_offloader = Offloader(source=self.test_source,
                                        dest=self.test_destination,
                                        structure=self.test_structure,
                                        filename=None,
                                        prefix="taken_date",
                                        mode="copy",
                                        dryrun=False,
                                        log_level="debug")

    def tearDown(self) -> None:
        if self.test_source.exists():
            rmtree(self.test_source)
        if self.test_destination.exists():
            rmtree(self.test_destination)

    def test_offload_default_settings(self):
        ol = Offloader(source=self.test_source,
                       dest=self.test_destination,
                       structure="taken_date",
                       filename=None,
                       prefix="taken_date",
                       mode="copy",
                       dryrun=False,
                       log_level="debug")

        self.assertTrue(ol.offload())

    def test_offload_offload_date(self):
        ol = Offloader(source=self.test_source,
                       dest=self.test_destination,
                       structure="offload_date",
                       filename=None,
                       prefix=None,
                       mode="copy",
                       dryrun=False,
                       log_level="debug")

        self.assertTrue(ol.offload())

    def test_offload_custom_filename(self):
        ol = Offloader(source=self.test_source,
                       dest=self.test_destination,
                       structure="offload_date",
                       filename="test_name",
                       prefix=None,
                       mode="copy",
                       dryrun=False,
                       log_level="debug")

        self.assertTrue(ol.offload())

    def test_destination(self):
        self.assertEqual(self.test_offloader.destination, self.test_destination)
        new_dest = Path('test_dir')
        self.test_offloader.destination = 'test_dir'
        self.assertEqual(self.test_offloader.destination, new_dest)

    def test_source(self):
        self.assertEqual(self.test_offloader.source, self.test_source)
        new_dir = 'test_dir_noExist'
        self.test_offloader.source = new_dir
        self.assertNotEqual(self.test_offloader.source, Path(new_dir))

    def test_structure(self):
        self.assertEqual(self.test_offloader.structure, self.test_structure)
        preset = 'taken_date'
        self.test_offloader.structure = preset
        self.assertEqual(self.test_offloader.structure, preset)


class TestFile(TestCase):
    def setUp(self):
        self.test_file_name = "test_file.txt"
        self.test_data_path = Path(__file__).parent / "test_data"
        self.test_file_path = self.test_data_path / "test_files" / self.test_file_name
        self.test_pic_path = Path(__file__).parent / "test_pic.jpg"
        self.test_file_path.parent.mkdir(exist_ok=True, parents=True)

    def tearDown(self):
        if self.test_file_path.is_file():
            self.test_file_path.unlink()
        rmtree(self.test_data_path)

    def test_size(self):
        test_file = File(self.test_pic_path)
        print(test_file.size)
        self.assertGreater(test_file.size, 0)

    def test_increment_filename(self):
        test_file = File(self.test_file_name)
        self.assertEqual(test_file.filename, "test_file.txt")

        test_file.increment_filename()
        self.assertEqual(test_file.filename, "test_file_001.txt")

        test_file.inc = 52
        test_file.increment_filename()
        self.assertEqual(test_file.filename, "test_file_053.txt")

        test_file.inc_pad = 5
        test_file.increment_filename()
        self.assertEqual(test_file.filename, "test_file_00054.txt")

    def test_add_prefix(self):
        test_file = File(self.test_pic_path)

        self.assertEqual(test_file.filename, "test_pic.jpg")
        self.assertEqual(test_file.prefix, None)

        test_file.set_prefix('hest')
        self.assertEqual(test_file.filename, "hest_test_pic.jpg")

        test_file.prefix = "fest"
        self.assertEqual(test_file.filename, "fest_test_pic.jpg")

        test_file.set_prefix("taken_date")
        logging.info(test_file.prefix)
        logging.info(test_file.path.resolve())
        self.assertEqual("200307_test_pic.jpg", test_file.filename)

        test_file.set_prefix("taken_date_time")
        self.assertEqual(test_file.prefix, "200307_192133")
        self.assertEqual(test_file.filename, "200307_192133_test_pic.jpg")

        test_file.prefix = "offload_date"
        today = datetime.now().strftime("%y%m%d")
        self.assertEqual(f"{today}_test_pic.jpg", test_file.filename)

        test_file.prefix = "empty"
        self.assertEqual(test_file.prefix, None)

        test_file.set_prefix("")
        self.assertEqual(test_file.prefix, None)

    def test_update_relative_path(self):
        test_file = File(self.test_file_path)
        relative_to = Path(__file__).parent
        test_file.set_relative_path(relative_to)
        self.assertEqual(str(test_file.relative_path), "test_data/test_files/test_file.txt")

    def test_update_path(self):
        test_file = File(self.test_file_path)
        test_file.path = "/test"
        self.assertEqual(str(test_file.path), "/test/test_file.txt")

    def test_update_checksum(self):
        self.test_file_path.parent.mkdir(exist_ok=True, parents=True)
        self.test_file_path.write_text("test")
        test_file = File(self.test_file_path)
        self.assertEqual("9ec9f7918d7dfc40", test_file.checksum)

    def test_set_name(self):
        test_file = File(self.test_file_path)
        test_file.name = "jens"
        self.assertEqual(test_file.name, "jens")
        self.assertEqual(test_file.filename, "jens.txt")
        self.assertTrue(str(test_file.path).endswith("jens.txt"))

    def test_set_name_using_preset(self):
        test_pic = File(self.test_pic_path)
        test_pic.name = "camera_model"
        self.assertEqual(test_pic.filename, "ilce-7m3.jpg")
        test_pic.name = 'camera_make'
        self.assertEqual(test_pic.name, "sony")


class TestFileList(TestCase):
    def setUp(self):
        self.test_directory = Path(__file__).parent / "test_data" / "test_files"
        self.test_directory.mkdir(exist_ok=True, parents=True)

        # Test files
        for i in range(100):
            f = Path(self.test_directory / f"{i:04}.jpg")
            f.write_text(utils.random_string(randint(1, 4096)))

    def tearDown(self):
        rmtree(self.test_directory)
        pass

    def test_get_file_list(self):
        test_list = FileList(self.test_directory)
        self.assertEqual(len(test_list.files), 100)

    def test_update_total_size(self):
        test_list = FileList(self.test_directory)
        self.assertIsInstance(test_list.size, int)

    def test_sort(self):
        test_list = FileList(self.test_directory)
        list_sorted = sorted(test_list.files, key=lambda f: f.mtime)
        test_list.sort()
        self.assertEqual(list_sorted, test_list.files)


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
            self.reporter.write(f, f, 'Copied')

    def test_write_html(self):
        for f in self.source_files.files:
            self.reporter.write(f, f, 'Copied')
        self.reporter.write_html()
        self.assertTrue(Path(self.reporter.html_path).is_file())


class TestSettings(TestCase):
    def setUp(self) -> None:
        self.settings = Settings()
        self.settings._path = Path() / '_ol_test_settings.json'
        self.settings._path.touch()

    def tearDown(self) -> None:
        self.settings._path.unlink()

    def test_write_settings(self):
        self.settings._write_settings(latest_destination=Path())
        with self.settings._path.open('r') as json_file:
            result = json.load(json_file)
        self.assertEqual(result.get('latest_destination'), str(Path()))

    def test_read_setting(self):
        with self.settings._path.open('w') as json_file:
            json.dump({'latest_destination': str(Path())}, json_file)

        self.settings._read_setting('latest_destination')

        with self.settings._path.open('r') as json_file:
            result = json.load(json_file)

        self.assertEqual(result.get('latest_destination'), str(Path()))

    def test_latest_destination(self):
        p = Path() / 'ol_test_path'
        self.settings.latest_destination = p
        self.assertEqual(self.settings.latest_destination, p.resolve())
