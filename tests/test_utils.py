from unittest import TestCase
import datetime
import os
import shutil
from pathlib import Path
from offload import utils
import logging
utils.setup_logger()


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
        f_a = Path('ol_test_file_a.txt')
        f_b = Path('ol_test_file_b.txt')
        f_a.write_bytes(b'test')
        f_b.write_bytes(b'test')
        self.assertEqual(utils.checksum_xxhash(f_a), utils.checksum_xxhash(f_a))

    def test_checksum_md5(self):
        test_hash = self.test_source_md5
        self.assertEqual(utils.checksum_md5(self.test_file_source), test_hash)

    def test_checksum_sha256(self):
        test_hash = self.test_source_sha256
        self.assertEqual(utils.checksum_sha256(self.test_file_source), test_hash)

    def test_convert_date(self):
        test_timestamp = 1586115849.30226
        self.assertIsInstance(utils.timestamp_to_datetime(test_timestamp), datetime.datetime)

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
        self.assertEqual(source.stat().st_size, destination.stat().st_size)
        self.assertEqual(utils.checksum_md5(source), utils.checksum_md5(destination))

    def test_get_file_info(self):
        test_info = utils.get_file_info(self.test_file_source)
        self.assertEqual(test_info["name"], self.test_file_source.name)
        self.assertEqual(test_info["path"], self.test_file_source)
        self.assertEqual(test_info["timestamp"], self.test_file_source.stat().st_mtime)
        self.assertEqual(test_info["date"], datetime.datetime.fromtimestamp(self.test_file_source.stat().st_mtime))
        self.assertEqual(test_info["size"], self.test_file_source.stat().st_size)

    def test_compare_checksums(self):
        shutil.copy2(self.test_file_source, self.test_file_compare_checksums)
        self.assertTrue(utils.compare_checksums(utils.checksum_md5(self.test_file_source),
                                                utils.checksum_md5(self.test_file_compare_checksums)))

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
        self.assertEqual(utils.file_mod_date(test_file), 1583605293.0)

    def test_destination_folder(self):
        test_file_date = datetime.datetime(2020, 3, 7, 19, 21, 33, 167691)
        today = datetime.datetime.now()
        # self.assertEqual(utils.destination_folder(test_file_date, preset="original"), "")
        self.assertEqual(utils.destination_folder(test_file_date, preset="taken_date"), "2020/2020-03-07")
        self.assertEqual(utils.destination_folder(test_file_date, preset="offload_date"),
                         f"{today.year}/{today.strftime('%Y-%m-%d')}")
        self.assertEqual(utils.destination_folder(test_file_date, preset="year"), str(test_file_date.year))
        self.assertEqual(utils.destination_folder(test_file_date, preset="year_month"),
                         f"{test_file_date.year}/{test_file_date.strftime('%m')}")
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
        self.assertTrue(result.get('Make'))
        result2 = utils.exifdata(self.test_file_source)
        self.assertFalse(result2.get('Model', False))

    def test_pathlib_copy(self):
        source = self.test_data_path / "test_file.txt"
        source.write_bytes(bytes('0' * 1024 ** 2 * 10, 'utf-8'))
        destination = source.parent / "test_dest" / "test_file.txt"
        destination.parent.mkdir()
        utils.pathlib_copy(source, destination)
        self.assertEqual(source.stat().st_size, destination.stat().st_size)
        self.assertEqual(utils.checksum_md5(source), utils.checksum_md5(destination))

        source.write_bytes(bytes('0' * 1024 ** 2 * 100, 'utf-8'))
        utils.pathlib_copy(source, destination)
        self.assertEqual(source.stat().st_size, destination.stat().st_size)
        self.assertEqual(utils.checksum_md5(source), utils.checksum_md5(destination))

    def test_time_to_string(self):
        result = utils.time_to_string(123)
        self.assertEqual(result, '2 minutes and 3 seconds')
        result = utils.time_to_string(12334)
        self.assertEqual(result, '3 hours, 25 minutes and 34 seconds')
        result = utils.time_to_string(2.44)
        self.assertEqual(result, '2 seconds')
