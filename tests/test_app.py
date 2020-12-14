from unittest import TestCase
from app import Offloader
from app import File
from app import FileList
from pathlib import Path
from random import randint
from utils import random_string
from shutil import rmtree
import datetime


class TestOffloader(TestCase):
    def setUp(self):
        self.test_source = Path("test_data/memoryCard").resolve()
        self.test_source.mkdir(exist_ok=True, parents=True)
        for i in range(100):
            f = Path(self.test_source / f"{i:04}.jpg")
            f.write_text(random_string(randint(1, 4096)))
        self.test_destination = Path("test_data/test_destination").resolve()

    def tearDown(self) -> None:
        rmtree(self.test_source)
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
        test_file = File("test_pic.jpg")

        self.assertEqual(test_file.filename, "test_pic.jpg")
        self.assertEqual(test_file.prefix, None)

        test_file.set_prefix('hest')
        self.assertEqual(test_file.filename, "hest_test_pic.jpg")

        test_file.prefix = "fest"
        self.assertEqual(test_file.filename, "fest_test_pic.jpg")

        test_file.set_prefix("taken_date")
        self.assertEqual(test_file.filename, "200307_test_pic.jpg")

        test_file.set_prefix("taken_date_time")
        self.assertEqual(test_file.prefix, "200307_192133")
        self.assertEqual(test_file.filename, "200307_192133_test_pic.jpg")

        test_file.prefix = "offload_date"
        today = datetime.datetime.now().strftime("%y%m%d")
        self.assertEqual(test_file.filename, f"{today}_test_pic.jpg")

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
        test_file.change_path("/test")
        self.assertEqual(str(test_file.path), "/test/test_file.txt")

    def test_update_checksum(self):
        self.test_file_path.parent.mkdir(exist_ok=True, parents=True)
        self.test_file_path.write_text("test")
        test_file = File(self.test_file_path)
        self.assertEqual(test_file.checksum, "4fdcca5ddb678139")

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
            f.write_text(random_string(randint(1, 4096)))

    def tearDown(self):
        rmtree(self.test_directory)
        pass

    def test_get_file_list(self):
        test_list = FileList(self.test_directory)
        self.assertEqual(len(test_list.files), 100)

    def test_update_total_size(self):
        test_list = FileList(self.test_directory)
        self.assertIsInstance(test_list.size, int)
