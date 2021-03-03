#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
script_name.py
Description of script_name.py.
"""

import logging
import shutil
import math
import time
import json
import subprocess
import hashlib
import string
import random
import os
import xxhash
from PIL import Image
from PIL import UnidentifiedImageError
from PIL.ExifTags import TAGS
from pathlib import Path
from pathlib import PosixPath
from datetime import datetime
from collections import namedtuple
from offload import APP_DATA_PATH, LOGS_PATH, REPORTS_PATH


class Preset:
    @staticmethod
    def structure(preset):
        presets = {'taken_date': '{date.year}/{date:%Y-%m-%d}',
                   # The datetime needs to be formatted here to prevent KeyError
                   'offload_date': f'{datetime.now().strftime("%Y")}/{datetime.now().strftime("%Y-%m-%d")}',
                   'year_month': '{date.year}/{date:%m}',
                   'year': '{date.year}',
                   'flat': ''}
        return presets.get(preset)

    @staticmethod
    def filename(preset):
        presets = {'original': None,
                   'camera_make': 'Make',
                   'camera_model': 'Model'}
        return presets.get(preset)

    @staticmethod
    def prefix(preset):
        presets = {'None': None,
                   '': None,
                   'empty': None,
                   'taken_date': '{date:%y%m%d}',
                   'taken_date_time': '{date:%y%m%d_%H%M%S}',
                   # The datetime needs to be formatted here to prevent KeyError
                   'offload_date': f'{datetime.now().strftime("%y%m%d")}'}
        return presets.get(preset)


def setup_logger(level="info"):
    """Create a logger with file and stream handler
    :return logger object"""
    # Create logger
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()

    if level == 'debug':
        logger.setLevel(logging.DEBUG)
    elif level == 'info':
        logger.setLevel(logging.INFO)
    elif level == 'error':
        logger.setLevel(logging.ERROR)

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create file handler and set level to debug
    log_folder = LOGS_PATH
    log_folder.mkdir(exist_ok=True, parents=True)
    log_filename = f"{datetime.now().strftime('%y%m%d%H%M')}_offload.log"
    fh = logging.FileHandler(log_folder / log_filename, mode='w')
    fh.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)-8s - %(message)s')

    # Add formatter
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


def file_checksum(filename, hashtype="xxhash", block_size=65536):
    """Get the checksum for a file"""
    # Choose a hash type
    if hashtype == "xxhash":
        return checksum_xxhash(filename, block_size=block_size)
    elif hashtype == "md5":
        return checksum_md5(filename, block_size=block_size)
    elif hashtype == "sha256":
        return checksum_sha256(filename, block_size=block_size)


def checksum_xxhash(file_path, block_size=65536):
    """Get xxhash checksum for a file"""
    if xxhash is None:
        raise Exception("xxhash not available on this platform.  Try 'pip install xxhash'")
    else:
        h = xxhash.xxh3_64()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
        return h.hexdigest()


def checksum_md5(file_path, block_size=65536):
    """Get md5 checksum for a file"""
    h = hashlib.md5()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
        return h.hexdigest()


def checksum_sha256(file_path, block_size=65536):
    """Get sha256 checksum for a file"""
    h = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
        return h.hexdigest()


def timestamp_to_datetime(timestamp):
    """Convert date from timestamp
    :return datetime object"""
    return datetime.fromtimestamp(timestamp)


def create_folder(folder):
    """Create a folder if it doesn't exist"""
    folder = Path(folder)
    if not folder.is_dir():
        folder.mkdir(parents=True)
    return folder


def time_to_string(seconds):
    """Return a readable time format"""
    if seconds == 0:
        return '0 seconds'

    h, s = divmod(seconds, 3600)
    m, s = divmod(s, 60)
    if h != 1:
        h_s = 'hours'
    else:
        h_s = 'hour'
    if m != 1:
        m_s = 'minutes'
    else:
        m_s = 'minute'
    if s != 1:
        s_s = 'seconds'
    else:
        s_s = 'second'
    time_string = ''
    if h:
        time_string = f'{int(h)} {h_s}, {int(m)} {m_s} and {int(s)} {s_s}'
    elif m:
        time_string = f'{int(m)} {m_s} and {int(s)} {s_s}'
    else:
        time_string = f'{int(s)} {s_s}'
    return time_string


def convert_size(size_bytes, binary=False):
    """Convert a file size from bytes to a human readable format"""
    if size_bytes == 0:
        return "0B"
    if binary:
        mult = 1024
        size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    else:
        mult = 1000
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, mult)))
    p = math.pow(mult, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def move_file(source, destination):
    """Move a file"""
    shutil.move(source, destination)
    return True


def copy_file(source: Path, destination: Path):
    """Copy a file"""
    # shutil.copyfile
    # shutil.copyfile(source, destination)
    # pathlib
    destination.write_bytes(source.read_bytes())
    return True


def pathlib_copy(source: Path, destination: Path, chunk_size=262144):
    """Use pathlib to copy a file"""
    if source.stat().st_size >= (1024 ** 2 * 64):
        with source.open('rb') as src, destination.open('wb') as dest:
            for chunk in iter(lambda: src.read(chunk_size), b''):
                dest.write(chunk)
    else:
        destination.write_bytes(source.read_bytes())


def file_mod_date(file_path):
    """Return the modification time of a file"""
    if not isinstance(file_path, PosixPath):
        file_path = Path(file_path)

    return file_path.stat().st_mtime


def get_file_info(file_path):
    """Get basic info about the file
    :return file info dict
    :rtype dict"""
    file_path = Path(file_path)
    file_timestamp = file_mod_date(file_path)
    info = {
        "name": file_path.name,
        "path": file_path,
        "timestamp": file_timestamp,
        "date": datetime.fromtimestamp(file_timestamp),
        "size": file_path.stat().st_size
    }

    return info


def compare_checksums(a, b):
    """Compare two string values to see if they match

    Returns:
        Bool: True if checksums match, False if they don't
    """
    if a == b:
        logging.info(f"Checksums match: {a} (source) | {b} (destination)")
        return True
    logging.info(f"Checksums mismatch: {a} (source)| {b} (destination)")
    return False


def update_recent_paths(path):
    """Output path to recent paths"""
    # TODO use plain text instead of json
    output_path = Path(__file__).parent / "recent_paths.json"
    recent_paths = []

    try:
        with output_path.open("r") as file:
            recent_paths = json.load(file)
    except FileNotFoundError as e:
        pass

    # Remove path from list
    for n, p in enumerate(recent_paths):
        if path == p:
            recent_paths.pop(n)

    # Add path to top of list
    recent_paths.insert(0, path)

    # Write data
    try:
        with output_path.open("w") as file:
            json_file = json.dump(recent_paths[:5], file)
            return json_file
    except Exception as e:
        logging.error(e)


def get_recent_paths():
    """Get recent destination paths from file"""
    output_path = Path(__file__).parent / "recent_paths.json"
    recent_paths = []

    try:
        with output_path.open(mode="r") as file:
            data = json.load(file)
            if isinstance(data, list):
                recent_paths.extend(data)
            else:
                recent_paths.append(data)

    except FileNotFoundError:
        logging.debug("File not found. No recent paths stored yet")

    logging.debug(recent_paths)
    return recent_paths


def pad_number(number, padding=3):
    """Add zero padding to number"""
    number_string = str(number)
    padded_number = number_string.zfill(padding)
    return padded_number


def destination_folder(file_date, preset):
    """Get a destination path depending on the structure setting"""
    # TODO original file structure
    today = datetime.now()

    if preset == "taken_date":
        # Construct new structure from modification date
        if file_date is None:
            logging.warning("File has no date, using today's date")
            file_date = datetime.today()
        return f"{file_date.year}/{file_date.strftime('%Y-%m-%d')}"

    elif preset == "offload_date":
        # Construct new structure from modification date
        return f"{today.year}/{today.strftime('%Y-%m-%d')}"

    elif preset == "year":
        # Construct new structure from modification date
        return f"{file_date.year}"

    elif preset == "year_month":
        # Construct new structure from modification date
        return f"{file_date.year}/{file_date.strftime('%m')}"

    elif preset == "flat":
        # Put files straight into destination folder
        return ""


def random_string(length=50):
    """Return a string of random letters"""
    chars = string.ascii_letters
    r_int = random.randint
    return "".join([chars[r_int(0, len(chars) - 1)] for x in range(length)])


def disk_usage(path: Path, human=False):
    """Return disk usage statistics about the given path."""
    DiskUsage = namedtuple('DiskUsage', 'total used free')
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    if human:
        return DiskUsage(convert_size(total), convert_size(used), convert_size(free))
    return DiskUsage(total, used, free)


def validate_string(invalid_string):
    """Replace or remove invalid characters in a string"""
    valid_string = str(invalid_string)
    valid_chars = f"-_.{string.ascii_letters}{string.digits}"
    char_table = {
        "å": "a",
        "ä": "a",
        "ö": "o",
        "Å": "A",
        "Ä": "A",
        "Ö": "O",
        " ": "_"
    }
    for k, v in char_table.items():
        valid_string = valid_string.replace(k, v)

    valid_string = "".join(c for c in valid_string if c in valid_chars)

    return valid_string


def folder_size(path):
    path = Path(path)
    size = sum([x.stat().st_size for x in path.rglob("*") if x.is_file()])
    return size


def get_file_list(folder_path, exclude=None):
    """Get a list of files in a folder and its subfolders"""
    # Start timer
    start_time = time.time()
    # Convert path to Path object
    directory = Path(folder_path)

    logging.info(f"Looking for files in {directory.resolve()}")
    files = [x for x in directory.rglob("*") if x.is_file()]
    logging.info(f"{len(files)} files found")
    logging.info(f"Getting file info for {len(files)} files")

    # Setup exclude list
    if exclude is None:
        exclude = []

    # Set some other variables
    file_list = {}
    file_id = 1
    total_file_size = 0

    # Iterate through the file list
    for file in files:
        if file.name not in exclude:
            logging.info(f"Getting file info for {file.name}")
            file_list[file_id] = get_file_info(file)
            logging.info(f"File info: {file_list[file_id]}")

            # Append file size to total file size
            total_file_size += file_list[file_id]["size"]

            # Increment file id
            file_id += 1

            logging.info(f"{file_id - 1} files collected")
            logging.info(
                f"Total size collected: {convert_size(total_file_size)}")

    elapsed_time = time.time() - start_time

    logging.info(
        f"Collected file info for {len(file_list)} files in {time.strftime('%-S seconds', time.gmtime(elapsed_time))}")
    logging.info(f"Total size collected: {convert_size(total_file_size)}")

    return file_list


def exiftool(file_path):
    """Run exiftool in subprocess and return the output"""
    cmd = ['exiftool', '-G', '-j', '-sort', file_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    try:
        outs, errs = proc.communicate(timeout=15)
        return outs.decode("utf-8").strip()
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
        return errs.decode("utf-8").strip()


def exiftool_exists():
    """Checks if exiftool exists"""
    if shutil.which("exiftool"):
        return True
    else:
        logging.error("Exiftool could not be found")
        return False


def exifdata(path: Path):
    """Get exifdata from a picture using pillow"""
    if is_image_file(path):
        with Image.open(path) as img:
            exifdata = {TAGS.get(k, k): v for k, v in img.getexif().items()}
            logging.debug(f'Exifdata for {path}')
            logging.debug(exifdata)
            return exifdata
    return {}


def get_camera_make(path: Path):
    """Get the camera make from image metadata"""
    exif = exifdata(path)
    return exif.get('Make', 'unknown')


def get_camera_model(path: Path):
    """Get the camera model from image metadata"""
    exif = exifdata(path)
    return exif.get('Model', 'unknown')


def is_image_file(path):
    """Check if a file is a recognized image file"""
    try:
        with Image.open(path) as img:
            return True
    except UnidentifiedImageError as e:
        logging.error(f'{path} is not a recognized image file')
        return False


def file_metadata(file_path):
    """Get exif data using exiftool"""
    if exiftool_exists():
        raw_meta = exiftool(file_path)
        if raw_meta:
            return json.loads(raw_meta)[0]
        else:
            return raw_meta
    else:
        return None


class FileList:
    def __init__(self, path, exclude=None):
        """A list of files as File objects

        Args:
            path: path to the root directory to scan for files
            exclude: list of filenames to ignore when adding files to list
        """
        self._path = Path(path)
        self.files = []

        self.exclude = []
        if isinstance(exclude, list):
            self.exclude.extend(exclude)
        elif isinstance(exclude, str):
            self.exclude.append(exclude)

        # Update file list
        self.update()

    def sort(self):
        """Sort list by modification date"""
        self.files.sort(key=lambda f: f.mtime)

    def update(self):
        """Get list of files in a folder and its subfolders"""
        # Get all files in path
        files = [x for x in self._path.rglob("*") if x.is_file() and x.name not in self.exclude]
        logging.debug(f"All files in source: {files}")

        # Create a dict with all files that aren't in exclude list
        for n, f in enumerate(files):
            logging.debug(f.name)
            self.files.append(File(f))
            logging.debug(f"Added {f.name} to file list ({n + 1}/{len(files)})")

    @property
    def size(self) -> int:
        """Return total file size of all files in list"""
        return sum([x.size for x in self.files])

    @property
    def hsize(self) -> str:
        return convert_size(self.size)

    @property
    def count(self) -> int:
        """Return the number of files in list"""
        return len(self.files)

    @property
    def avg_file_size(self) -> int:
        """Return average file size of files in list"""
        return int(self.size / self.count)


class File:
    def __init__(self, path, prefix=None, incremental_padding=3):
        """File object.

        Args:
            path: path to an existing file or a placeholder path for new file
            prefix: custom prefix or based on a template
            incremental_padding: the amount of zero's too put before the incremental number
        """
        self._path = Path(path)
        # Discard object if given path is a directory
        if self._path.is_dir():
            logging.error(f'{path} is a folder')
            exit()
        # Setup attributes
        self._checksum = ''
        self._size = 0
        self._prefix = prefix
        self._name = self._path.stem
        self.inc = 0
        self.inc_pad = incremental_padding
        self.ext = self._path.suffix.strip('.')
        self.relative_path = None

    @property
    def is_file(self):
        """Check if the file exists"""
        exists = self.path.is_file()
        # if exists:
        #     logging.debug(f'{self.path} exists')
        # else:
        #     logging.debug(f'{self.path} does not exist')
        return exists

    @property
    def filename(self):
        """Update the current filename with prefix and padding"""
        fname = self.name
        if self.prefix:
            fname = f"{self.prefix}_{fname}"
        if self.inc >= 1:
            inc = pad_number(self.inc, padding=self.inc_pad)
            fname = f"{fname}_{inc}"

        fname = f"{fname}.{self.ext}"

        return fname

    @property
    def name(self):
        """Return the name of the file without prefix, incremental or extension"""
        return self._name

    @name.setter
    def name(self, name, validate=True):
        """Change the name property

        Args:
            name: the new name of the file. Presets available:
                - camera_model
                - camera_make
            validate: validate filename to make sure it works on all filesystems"""

        new_name = str(name)

        # Set name from exif data based on a preset
        preset = Preset()
        if preset.filename(name):
            logging.debug(self.exifdata)
            new_name = self.exifdata.get(preset.filename(name), "unknown").lower()

        # Validate file name and remove/replace illegal characters
        if validate:
            new_name = validate_string(new_name)

        self._name = new_name

    @property
    def path(self):
        """Return the path property"""
        return self._path.parent / self.filename

    @path.setter
    def path(self, path):
        """Change the path"""
        path = Path(path)
        if path.is_file():
            self._path = path.parent / self.filename
        else:
            self._path = path / self.filename

    @property
    def checksum(self):
        """Return the xxhash checksum of the file

        Returns: file checksum
        """
        if self.is_file:
            self._checksum = file_checksum(self.path)
        return self._checksum

    @property
    def size(self) -> int:
        """Return the size of the file if it exists"""
        if self.is_file:
            self._size = self.path.stat().st_size
        return self._size

    @property
    def mdate(self):
        """Modification date"""
        return datetime.fromtimestamp(self.mtime)

    @property
    def mtime(self):
        """Modification time of the file"""
        if self.is_file:
            if self.path.stat().st_mtime:
                return self.path.stat().st_mtime

        elif self._path.is_file():
            if self._path.stat().st_mtime:
                return self._path.stat().st_mtime

        return datetime.timestamp(datetime.now())

    @property
    def exifdata(self) -> dict:
        """Get the file exifdata using exiftool"""
        if self.is_file:
            return exifdata(self.path)
        elif self._path.is_file():
            return exifdata(self._path)
        return {}

    @property
    def prefix(self):
        """Return the set prefix"""
        return self._prefix

    @prefix.setter
    def prefix(self, prefix):
        """Set a new prefix for the file

        Args:
            prefix: new prefix value. Presets are:
                - taken_date: %y%m%d
                - taken_date_time: %y%m%d_%H%M%S
                - offload_date: %y%m%d
        """
        self.set_prefix(prefix)

    def set_prefix(self, prefix, custom_date=None):
        """Set a new prefix for the file

        Args:
            prefix: new prefix value. Presets are:
                - taken_date: %y%m%d
                - taken_date_time: %y%m%d_%H%M%S
                - offload_date: %y%m%d
            custom_date: a custom date to use with presets
        """
        # Use file modification date if custom date is none
        if custom_date is None:
            date = self.mdate
        else:
            date = custom_date

        # Get filename prefix presets
        logging.debug(f'Given prefix is {prefix}')
        if Preset.prefix(prefix) or prefix in ('empty', ''):
            self._prefix = Preset.prefix(prefix)
            if self._prefix:
                logging.debug(f'self._prefix = {self._prefix}')
                self._prefix = self._prefix.format(date=date)
        else:
            self._prefix = prefix

    @property
    def duration(self):
        """Get duration if possible"""
        video = cv2.VideoCapture(self._path)
        duration = video.get(cv2.CAP_PROP_POS_MSEC)

        return duration

    @property
    def frames(self):
        """Get frame count"""
        video = cv2.VideoCapture(self._path)
        frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        return frame_count

    def increment_filename(self):
        """Add incremental or count up"""
        self.inc += 1

    def set_relative_path(self, relative_to):
        """Add/update the relative path property"""
        self.relative_path = self._path.relative_to(relative_to)
        return self.relative_path

    def delete(self):
        """Delete the file"""
        if self.path.is_file():
            self.path.unlink()


class Settings:
    def __init__(self):
        """
        Object for storing and getting offloader settings
        """

        self._path = APP_DATA_PATH / 'settings.json'
        self._default_settings = {'latest_destination': str(Path().home().resolve()),
                                  'default_destination': None,
                                  'structure': 'taken_date',
                                  'prefix': 'taken_date',
                                  'filename': None}
        self._init_settings()

    def _init_settings(self):
        """Init settings object"""
        if not self._path.is_file():
            with self._path.open('w') as json_file:
                json.dump(self._default_settings, json_file)
        else:
            for k, v in self._default_settings.items():
                if not self._read_setting(k):
                    self._write_settings(**{k: v})

    def _write_settings(self, **settings):
        """Write settings to disk"""
        current_settings = self._read_settings()
        for k, v in settings.items():
            current_settings[k] = str(v)

        with self._path.open('w') as json_file:
            json.dump(current_settings, json_file)

    def _read_settings(self):
        """Read settings from disk"""
        with self._path.open('r') as json_file:
            json_data = json.load(json_file)
            return json_data

    def _read_setting(self, setting):
        """Read settings from disk"""
        with self._path.open('r') as json_file:
            json_data = json.load(json_file)
            value = json_data.get(setting)
            if value == 'None':
                value = None
            return value

    @property
    def latest_destination(self):
        """Get latest offload destination

        Returns:
            Path: path to latest offload destination
        """
        dest = self._read_setting('latest_destination')
        # Return home path if no former destination stored
        if dest:
            dest_path = Path(dest)
        else:
            dest_path = Path().home()
        if dest_path.is_dir():
            return dest_path

        return Path().home()

    @latest_destination.setter
    def latest_destination(self, path):
        """Set latest offload destination"""
        path = Path(path)
        self._write_settings(latest_destination=str(path.resolve()))

    @property
    def default_destination(self):
        """Get default offload destination

        Returns:
            Path: path to latest offload destination
        """
        dest = self._read_setting('default_destination')
        # Return home path if no former destination stored
        if dest:
            dest_path = Path(dest)

            if dest_path.is_dir():
                return dest_path

        return None

    @default_destination.setter
    def default_destination(self, path):
        """Set latest offload destination"""
        path = Path(path)
        self._write_settings(default_destination=str(path.resolve()))

    def destination(self):
        """Get latest offload destination

        Returns:
            Path: path to latest offload destination
        """
        if self.default_destination:
            return self.default_destination
        elif self.latest_destination:
            return self.latest_destination

        return Path().home()

    @property
    def structure(self):
        """Get folder structure preset

        Returns:
            str: a folder structure preset
        """
        dest = self._read_setting('structure')

        return dest

    @structure.setter
    def structure(self, preset: str):
        """Set folder structure preset"""
        self._write_settings(structure=preset)

    @property
    def prefix(self):
        """Get prefix preset

        Returns:
            str: a filename prefix preset
        """
        prefix = self._read_setting('prefix')

        return prefix

    @prefix.setter
    def prefix(self, preset: str):
        """Set prefix preset"""
        self._write_settings(prefix=preset)

    @property
    def filename(self):
        """Get filename preset

        Returns:
            str: a filename preset
        """
        filename = self._read_setting('filename')

        return filename

    @filename.setter
    def filename(self, preset: str):
        """Set prefix preset"""
        self._write_settings(filename=preset)
