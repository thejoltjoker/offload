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
from PIL import Image
from PIL import UnidentifiedImageError
from PIL.ExifTags import TAGS
from pathlib import Path
from pathlib import PosixPath
from datetime import datetime

try:
    import xxhash
except ImportError:
    xxhash = None


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
    log_folder = Path(__file__).parent / "logs"
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
        raise Exception(
            "xxhash not available on this platform.  Try 'pip install xxhash'")
    else:
        h = xxhash.xxh64()

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


def convert_size(size_bytes):
    """Convert a file size from bytes to a human readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def move_file(source, destination):
    """Move a file"""
    shutil.move(source, destination)
    return True


def copy_file(source, destination):
    """Copy a file"""
    shutil.copyfile(source, destination)
    return True


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


# def compare_checksums(source, destination, hashtype="xxhash"):
#     source_hash = file_checksum(source, hashtype=hashtype)
#     dest_hash = file_checksum(destination, hashtype=hashtype)
#     if dest_hash == source_hash:
#         logging.info(
#             f"Checksums match: {source_hash} (source) | {dest_hash} (destination)")
#         return True
#     else:
#         logging.info(
#             f"Checksums mismatch: {source_hash} (source)| {dest_hash} (destination)")
#         return False


def compare_checksums(a, b):
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


def format_file_name(name, ext, prefix=None, incremental=None, padding=3):
    """Create a new filename"""
    output_filename = name
    if ext.startswith("."):
        ext = ext[1:]
    if prefix:
        if name.startswith(prefix):
            logging.debug(
                f"Filename already starts with {prefix}. Not adding prefix")
        else:
            output_filename = f"{prefix}_{output_filename}"
    if incremental:
        inc = pad_number(incremental, padding=padding)
        output_filename = f"{output_filename}_{inc}"

    output_filename = f"{output_filename}.{ext}"
    return output_filename


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
        img = Image.open(path)
        exifdata = {TAGS.get(k, k): v for k, v in img.getexif().items()}
        return exifdata
    return {}


def is_image_file(path):
    """Check if a file is a recognized image file"""
    try:
        Image.open(path)
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


def main():
    """docstring for main"""
    # path = "/Users/johannes/Dropbox/Camera Uploads/2013-08-26 14.34.00.jpg"
    # pprint(get_metadata(path))
    print(random_string(256))


if __name__ == '__main__':
    main()
