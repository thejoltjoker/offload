#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
script_name.py
Description of script_name.py.
"""
import os
import logging
import shutil
import math
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from pprint import pprint

try:
    import xxhash
except ImportError:
    xxhash = None
    import hashlib


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
    log_folder.mkdir(exist_ok=True)
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


def get_file_checksum(filename, hashtype="xxhash", block_size=65536):
    """Get the checksum for a file"""
    # Choose a hash type
    if hashtype == "xxhash":
        # Use xxhash if it exists
        if xxhash is None:
            raise Exception("xxhash not available on this platform.  Try 'pip install xxhash'")
        else:
            h = xxhash.xxh64()
    elif hashtype == "md5":
        h = hashlib.md5()
    elif hashtype == "sha256":
        h = hashlib.sha256()

    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
        return h.hexdigest()


def convert_date(timestamp):
    """Convert date from timestamp
    :return datetime object"""
    return datetime.fromtimestamp(timestamp)


def create_folder(folder):
    """Create a folder if it doesn't exist"""
    if not os.path.exists(folder):
        os.makedirs(folder)


def convert_size(size_bytes):
    """Convert a file size from bytes to a human readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def move_file(source, destination):
    """Move a file"""
    shutil.move(source, destination)


def copy_file(source, destination):
    """Copy a file"""
    shutil.copyfile(source, destination)


def get_file_info(file_path):
    """Get basic info about the file
    :return file info dict
    :rtype dict"""
    file_path = Path(file_path)
    file_timestamp = file_path.stat().st_mtime
    file_info = {
        "name": file_path.name,
        "path": file_path,
        "timestamp": file_timestamp,
        "date": datetime.fromtimestamp(file_timestamp),
        "size": file_path.stat().st_size
    }

    return file_info


def compare_checksums(source, destination, hashtype="xxhash"):
    source_hash = get_file_checksum(source, hashtype=hashtype)
    dest_hash = get_file_checksum(destination, hashtype=hashtype)
    if dest_hash == source_hash:
        logging.info(
            f"Checksums match: {source_hash} (source) | {dest_hash} (destination)")
        return True
    else:
        logging.info(
            f"Checksums mismatch: {source_hash} (source)| {dest_hash} (destination)")
        return False


def update_recent_paths(path):
    """Output path to recent paths"""
    output_path = Path(__file__).parent / "recent_paths.json"
    recent_paths = []

    try:
        with output_path.open("r") as file:
            recent_paths = json.load(file)
    except FileNotFoundError as e:
        logging.warning("File not found.")

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
            logging.debug(f"Getting file info for {file.name}")
            file_list[file_id] = get_file_info(file)
            logging.debug(f"File info: {file_list[file_id]}")

            # Append file size to total file size
            total_file_size += file_list[file_id]["size"]

            # Increment file id
            file_id += 1

            logging.info(f"{file_id - 1} files collected")
            logging.debug(
                f"Total size collected: {convert_size(total_file_size)}")

    elapsed_time = time.time() - start_time

    logging.info(
        f"Collected file info for {len(file_list)} files in {time.strftime('%-S seconds', time.gmtime(elapsed_time))}")
    logging.info(f"Total size collected: {convert_size(total_file_size)}")

    return file_list


def exiftool(file_path):
    """Run exiftool in subprocess and return the output"""
    cmd = ['exiftool', '-G', '-j', '-sort', file_path]
    try:
        s = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        s = s.stdout.read()

        return s.strip()

    except subprocess.CalledProcessError as e:
        logging.error(e)
        return None


def get_metadata(file_path):
    """Get exif data using exiftool"""
    if shutil.which("exiftool") is not None:
        raw_meta = exiftool(file_path)
        if raw_meta:
            # convert bytes to string
            exif = raw_meta.decode('utf-8').rstrip('\r\n')
            return json.loads(exif)[0]
        else:
            return raw_meta
    else:
        logging.error("Couldn't find exiftool")
        return None


def main():
    """docstring for main"""
    path = "/Users/johannes/Dropbox/Camera Uploads/2013-08-26 14.34.00.jpg"
    pprint(get_metadata(path))


if __name__ == '__main__':
    main()