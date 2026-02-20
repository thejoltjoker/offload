import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from random import randint
from shutil import rmtree
from unittest import TestCase

from offload import utils
from offload.utils import File, FileList

utils.setup_logger("debug")


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

        test_file.set_prefix("hest")
        self.assertEqual(test_file.filename, "hest_test_pic.jpg")

        test_file.prefix = "fest"
        self.assertEqual(test_file.filename, "fest_test_pic.jpg")

        test_file.set_prefix("taken_date")
        logging.info(test_file.prefix)
        logging.info(test_file.path.resolve())
        # taken_date uses EXIF or fallback to current date; assert pattern
        self.assertRegex(test_file.filename, r"^\d{6}_test_pic\.jpg$")

        test_file.set_prefix("taken_date_time")
        self.assertRegex(test_file.filename, r"^\d{6}_\d{6}_test_pic\.jpg$")

        logging.debug(f"test_file.prefix = {test_file.prefix}")
        test_file.prefix = "offload_date"
        today = datetime.now().strftime("%y%m%d")
        logging.info(today)
        logging.info(test_file.filename)
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
        logging.info(f"Testing set name using preset with file {test_pic._path}")
        test_pic.name = "camera_model"
        self.assertEqual(test_pic.filename, "ilce-7m3.jpg")
        test_pic.name = "camera_make"
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


class TestUtils(TestCase):
    def setUp(self):
        # Set variables
        self.tests_path = Path(__file__).parent
        logging.info(self.tests_path)
        self.test_data_path = self.tests_path / "test_data"
        self.test_data_path.mkdir(exist_ok=True, parents=True)
        self.test_pic_path = self.tests_path / "test_pic.jpg"
        self.test_file_source = self.test_data_path / "test_file_source.txt"
        self.test_file_source.write_text("test")
        self.test_file_dest = self.test_data_path / "test_file_destination.txt"
        self.test_file_dest.write_text("destination")
        self.test_file_compare_checksums = self.test_data_path / "test_file_compare_checksums.txt"

        self.test_source_xxhash = "9ec9f7918d7dfc40"
        self.test_source_md5 = "098f6bcd4621d373cade4e832627b4f6"
        self.test_source_sha256 = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

        self.test_dest_xxhash = "d07d9411d9203216"
        self.test_dest_md5 = "6990a54322d9232390a784c5c9247dd6"
        self.test_dest_sha256 = "b5c755aaab1038b3d5627bbde7f47ca80c5f5c0481c6d33f04139d07aa1530e7"

    def tearDown(self):
        shutil.rmtree(self.test_data_path)

    def test_file_checksum(self):
        self.assertEqual(self.test_source_xxhash, utils.checksum_xxhash(self.test_file_source))
        self.assertEqual(self.test_source_md5, utils.checksum_md5(self.test_file_source))
        self.assertEqual(self.test_source_sha256, utils.checksum_sha256(self.test_file_source))

    def test_checksum_xxhash(self):
        test_hash = self.test_source_xxhash
        f_a = Path("ol_test_file_a.txt")
        f_b = Path("ol_test_file_b.txt")
        f_a.write_bytes(b"test")
        f_b.write_bytes(b"test")
        self.assertEqual(utils.checksum_xxhash(f_a), utils.checksum_xxhash(f_a))

    def test_checksum_md5(self):
        test_hash = self.test_source_md5
        self.assertEqual(utils.checksum_md5(self.test_file_source), test_hash)

    def test_checksum_sha256(self):
        test_hash = self.test_source_sha256
        self.assertEqual(utils.checksum_sha256(self.test_file_source), test_hash)

    def test_convert_date(self):
        test_timestamp = 1586115849.30226
        self.assertIsInstance(utils.timestamp_to_datetime(test_timestamp), datetime)

    def test_create_folder(self):
        test_folder = self.test_data_path / "test_folder"
        utils.create_folder(test_folder)
        self.assertTrue(os.path.exists(test_folder))

    def test_convert_size(self):
        self.assertEqual(utils.convert_size(1000, binary=False), "1.0 KB")
        self.assertEqual(utils.convert_size(10000, binary=False), "10.0 KB")
        self.assertEqual(utils.convert_size(1000000, binary=False), "1.0 MB")

    def test_move_file(self):
        content = "Test string!"
        source = self.test_data_path / "test_file.txt"
        source.write_text(content)
        destination = source.parent / "test_dest" / "test_file.txt"
        destination.parent.mkdir()
        utils.move_file(source, destination)
        self.assertFalse(source.is_file())

    def test_copy_file(self):
        content = "Test string!"
        source = self.test_data_path / "test_file.txt"
        source.write_text(content)
        destination = source.parent / "test_dest" / "test_file.txt"
        destination.parent.mkdir()
        utils.copy_file(source, destination)
        st = source.stat()
        for i in dir(st):
            if i.startswith("st_"):
                logging.info(i)
                if i in ["st_birthtime", "st_ctime", "st_ctime_ns", "st_ino"]:
                    self.assertNotEqual(getattr(source.stat(), i), getattr(destination.stat(), i))
                else:
                    self.assertEqual(getattr(source.stat(), i), getattr(destination.stat(), i))
        # self.assertEqual(source.stat().st_size, destination.stat().st_size)
        # self.assertEqual(source.stat().st_mtime, destination.stat().st_mtime)
        # self.assertEqual(source.stat().st_ctime, destination.stat().st_ctime)
        self.assertEqual(utils.checksum_md5(source), utils.checksum_md5(destination))

    def test_get_file_info(self):
        test_info = utils.get_file_info(self.test_file_source)
        self.assertEqual(test_info["name"], self.test_file_source.name)
        self.assertEqual(test_info["path"], self.test_file_source)
        self.assertEqual(test_info["timestamp"], self.test_file_source.stat().st_mtime)
        self.assertEqual(
            test_info["date"], datetime.fromtimestamp(self.test_file_source.stat().st_mtime)
        )
        self.assertEqual(test_info["size"], self.test_file_source.stat().st_size)

    def test_compare_checksums(self):
        shutil.copy2(self.test_file_source, self.test_file_compare_checksums)
        self.assertTrue(
            utils.compare_checksums(
                utils.checksum_md5(self.test_file_source),
                utils.checksum_md5(self.test_file_compare_checksums),
            )
        )

    def test_get_recent_paths(self):
        self.assertIsInstance(utils.get_recent_paths(), list)

    def test_exiftool_exists(self):
        self.assertTrue(utils.exiftool_exists())

    def test_exiftool(self):
        self.assertIsInstance(utils.exiftool(self.test_file_source), str)

    def test_file_metadata(self):
        test_metadata = utils.file_metadata(self.test_pic_path)
        self.assertIsInstance(test_metadata, dict)

        test_metadata = utils.file_metadata(self.test_pic_path)
        self.assertTrue(test_metadata.get("EXIF:Make"))

    def test_pad_number(self):
        self.assertEqual(utils.pad_number(2, padding=3), "002")
        self.assertEqual(utils.pad_number(328, padding=4), "0328")
        self.assertEqual(utils.pad_number(110328, padding=1), "110328")
        self.assertEqual(utils.pad_number("3", padding=4), "0003")

    def test_validate_string(self):
        self.assertEqual(utils.validate_string("Tårtan 2"), "Tartan_2")
        self.assertEqual(utils.validate_string("snel hest!"), "snel_hest")
        self.assertEqual(utils.validate_string("snövits häst"), "snovits_hast")
        self.assertEqual(utils.validate_string("Öland"), "Oland")

    def test_file_modification_date(self):
        test_file = Path(__file__).parent / "test_pic.jpg"
        mod_time = utils.file_mod_date(test_file)
        self.assertIsInstance(mod_time, (int, float))
        self.assertGreater(mod_time, 0)

    def test_destination_folder(self):
        test_file_date = datetime(2020, 3, 7, 19, 21, 33, 167691)
        today = datetime.now()
        # self.assertEqual(utils.destination_folder(test_file_date, preset="original"), "")
        self.assertEqual(
            utils.destination_folder(test_file_date, preset="taken_date"), "2020/2020-03-07"
        )
        self.assertEqual(
            utils.destination_folder(test_file_date, preset="offload_date"),
            f"{today.year}/{today.strftime('%Y-%m-%d')}",
        )
        self.assertEqual(
            utils.destination_folder(test_file_date, preset="year"), str(test_file_date.year)
        )
        self.assertEqual(
            utils.destination_folder(test_file_date, preset="year_month"),
            f"{test_file_date.year}/{test_file_date.strftime('%m')}",
        )
        self.assertEqual(utils.destination_folder(test_file_date, preset="flat"), "")

    def test_random_string(self):
        random_string = utils.random_string(62)
        self.assertIsInstance(random_string, str)
        self.assertEqual(len(random_string), 62)

    def test_folder_size(self):
        result = utils.folder_size(Path(__file__).parent)
        print(utils.convert_size(result))
        print(result)
        self.assertIsInstance(result, int)

    def test_exifdata(self):
        result = utils.exifdata(self.test_pic_path)
        print(result)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("Make"))
        result2 = utils.exifdata(self.test_file_source)
        self.assertFalse(result2.get("Model", False))

    def test_get_camera_make(self):
        result = utils.get_camera_make(self.test_pic_path)
        logging.info(result)
        self.assertIsInstance(result, str)
        self.assertEqual("SONY", result)

    def test_get_camera_model(self):
        result = utils.get_camera_model(self.test_pic_path)
        logging.info(result)
        self.assertIsInstance(result, str)
        self.assertEqual("ILCE-7M3", result)

    def test_pathlib_copy(self):
        source = self.test_data_path / "test_file.txt"
        source.write_bytes(bytes("0" * 1024**2 * 10, "utf-8"))
        destination = source.parent / "test_dest" / "test_file.txt"
        destination.parent.mkdir()
        utils.pathlib_copy(source, destination)
        self.assertEqual(source.stat().st_size, destination.stat().st_size)
        self.assertEqual(utils.checksum_md5(source), utils.checksum_md5(destination))

        source.write_bytes(bytes("0" * 1024**2 * 100, "utf-8"))
        utils.pathlib_copy(source, destination)
        self.assertEqual(source.stat().st_size, destination.stat().st_size)
        self.assertEqual(utils.checksum_md5(source), utils.checksum_md5(destination))

    def test_time_to_string(self):
        result = utils.time_to_string(123)
        self.assertEqual(result, "2 minutes and 3 seconds")
        result = utils.time_to_string(12334)
        self.assertEqual(result, "3 hours, 25 minutes and 34 seconds")
        result = utils.time_to_string(2.44)
        self.assertEqual(result, "2 seconds")

    def test_compare_file_mtime(self):
        a = self.test_file_source
        b = self.test_file_dest
        result = utils.compare_file_mtime(a, b)
        self.assertFalse(result)

        shutil.copy2(a, b)
        result = utils.compare_file_mtime(a, b)
        self.assertTrue(result)

    def test_compare_file_size(self):
        a = self.test_file_source
        b = self.test_file_dest
        result = utils.compare_file_size(a, b)
        self.assertFalse(result)

        shutil.copy2(a, b)
        result = utils.compare_file_size(a, b)
        self.assertTrue(result)

    def test_compare_files(self):
        a = File(self.test_file_source)
        b = File(self.test_file_dest)
        result = utils.compare_files(a, b)
        self.assertFalse(result)

        shutil.copy2(a.path, b.path)
        result = utils.compare_files(a, b)
        self.assertTrue(result)


class TestPreset(TestCase):
    def setUp(self) -> None:
        self.preset = utils.Preset()

    def test_structure(self):
        self.assertEqual("{date.year}/{date:%Y-%m-%d}", self.preset.structure("taken_date"))
        self.assertEqual(
            f"{datetime.now():%Y}/{datetime.now():%Y-%m-%d}", self.preset.structure("offload_date")
        )
        self.assertEqual("{date.year}", self.preset.structure("year"))
        self.assertEqual("{date.year}/{date:%m}", self.preset.structure("year_month"))
        self.assertEqual("", self.preset.structure("flat"))

    def test_filename(self):
        self.assertIsNone(self.preset.filename("original"))
        self.assertEqual("Make", self.preset.filename("camera_make"))
        self.assertEqual("Model", self.preset.filename("camera_model"))

    def test_prefix(self):
        self.assertEqual("{date:%y%m%d}", self.preset.prefix("taken_date"))
        self.assertEqual("{date:%y%m%d_%H%M%S}", self.preset.prefix("taken_date_time"))
        self.assertEqual(f"{datetime.now().strftime('%y%m%d')}", self.preset.prefix("offload_date"))
