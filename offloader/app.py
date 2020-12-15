#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Camera Offload
---
This script is used for transferring files and verifying them using a checksum.
"""
# TODO multiple destinations
# TODO make it easier to customize
# TODO clean up code
# TODO create report

import os
import logging
import argparse
import time
import utils
from pathlib import Path
from datetime import datetime
import sys

try:
    import xxhash

    CHECKSUM_METHOD = 'xxhash'

except ImportError:
    xxhash = None
    CHECKSUM_METHOD = 'md5'

if sys.platform == 'darwin':
    APP_DATA_PATH = Path('~/Library/Application Support/CaffeineCreations/Offloader')
elif sys.platform == 'win64':
    APP_DATA_PATH = Path('~/Library/Application Support/CaffeineCreations/Offloader')
else:
    APP_DATA_PATH = Path(__file__).parent

exclude_files = ["MEDIAPRO.XML",
                 "Icon",
                 "STATUS.BIN",
                 "SONYCARD.IND",
                 "AVIN0001.INP",
                 "AVIN0001.BNP",
                 "MOVIEOBJ.BDM",
                 "PRV00001.BIN",
                 "INDEX.BDM",
                 "fseventsd-uuid",
                 ".dropbox.device",
                 "AVIN0001.INT",
                 "mdb.bk",
                 "mdb.db",
                 "Get_started_with_GoPro.url",
                 ".Spotlight-V100",
                 "VolumeConfiguration.plist",
                 "psid.db",
                 "indexState",
                 "0.indexHead",
                 "0.indexGroups",
                 "live.0.indexPostings",
                 "live.0.indexIds",
                 "live.0.indexBigDates",
                 "live.0.indexGroups",
                 "live.0.indexPositions",
                 "live.0.indexDirectory",
                 "live.0.indexCompactDirectory",
                 "live.0.indexArrays",
                 "live.0.shadowIndexHead",
                 "live.0.directoryStoreFile",
                 "live.0.directoryStoreFile.shadow",
                 "store.db",
                 ".store.db",
                 "reverseDirectoryStore",
                 "tmp.spotlight.state",
                 "shutdown_time",
                 "reverseDirectoryStore.shadow",
                 "0.shadowIndexHead",
                 "store.updates",
                 "permStore",
                 "live.1.indexHead",
                 "live.1.indexIds",
                 "0.shadowIndexGroups",
                 "live.1.indexUpdates",
                 "live.2.indexHead",
                 "live.2.indexIds",
                 "live.2.indexBigDates",
                 "live.2.indexGroups",
                 "live.0.shadowIndexGroups",
                 "reverseStore.updates",
                 "live.1.indexBigDates",
                 "tmp.spotlight.loc",
                 "live.1.indexGroups",
                 "live.1.indexPostings",
                 "live.1.indexTermIds",
                 "live.1.indexDirectory",
                 "live.1.indexCompactDirectory",
                 "live.1.indexArrays",
                 "live.2.indexPostings",
                 "live.1.directoryStoreFile",
                 "live.1.shadowIndexHead",
                 "live.1.shadowIndexTermIds",
                 "live.1.shadowIndexArrays",
                 "live.1.shadowIndexCompactDirectory",
                 "live.1.shadowIndexDirectory",
                 "live.1.directoryStoreFile.shadow",
                 "live.1.shadowIndexGroups",
                 "live.2.indexTermIds",
                 "live.2.indexPositions",
                 "live.2.indexPositionTable",
                 "live.2.indexDirectory",
                 "live.2.indexCompactDirectory",
                 "live.2.indexArrays",
                 "live.2.indexUpdates",
                 "live.2.directoryStoreFile",
                 "live.2.shadowIndexHead",
                 "live.2.shadowIndexTermIds",
                 "live.2.shadowIndexPositionTable",
                 "live.2.shadowIndexArrays",
                 "live.2.shadowIndexCompactDirectory",
                 "live.2.shadowIndexDirectory",
                 "live.2.directoryStoreFile.shadow",
                 "live.2.shadowIndexGroups",
                 "live.0.indexHead",
                 "journal.412",
                 "retire.411",
                 ".DS_Store",
                 "fseventsd-uuid.",
                 ".dropbox.device",
                 "Icon?",
                 "Icon\r.",
                 "Icon\r",
                 "store_generation.",
                 "store_generation.\r",
                 ".Spotlight-V100"]


class Offloader:
    def __init__(self, source, dest, structure, filename, prefix, mode, dryrun, log_level):
        self.logger = utils.setup_logger(log_level)
        self.today = datetime.now()
        self.source = Path(source)
        self.destination = Path(dest)
        self.structure = structure
        self.filename = filename
        self.prefix = prefix
        self.mode = mode
        self.dryrun = dryrun
        self.exclude = exclude_files

    def offload(self):
        """Offload files"""
        # Set some variables
        dest_folders = []
        skipped_files = []
        processed_files = []
        errored_files = []

        # Get list of files in source folder
        logging.info("Getting list of files")
        source_list = FileList(self.source, exclude=exclude_files)

        logging.info(f"Total file size: {utils.convert_size(source_list.size)}")
        logging.info(f"Average file size: {utils.convert_size(source_list.size / len(source_list.files))}")
        logging.info("---\n")

        # Setup variables for stats
        total_transferred_size = 0
        start_time = time.time()

        # Iterate over all the files
        for file_id, source_file in source_list.files.items():
            logging.debug([x for x in source_file.__dict__.items()])
            skip = False
            # Display how far along the transfer we are
            transfer_percentage = round(
                (total_transferred_size / source_list.size) * 100, 2)
            logging.info(f"Processing file {file_id + 1}/{len(source_list.files)} "
                         f"(~{transfer_percentage}%) | {source_file.filename}")

            # Create File object for destination file
            dest_folder = self.destination / utils.destination_folder(source_file.mdate, preset=self.structure)
            dest_path = dest_folder / source_file.filename
            dest_file = File(dest_path, prefix=self.prefix)
            # Change filename
            if self.filename:
                dest_file.name = self.filename

            # Add prefix to filename
            dest_file.set_prefix(self.prefix, custom_date=source_file.mdate)

            # Add destination folder to list of destination folders
            if dest_folder not in dest_folders:
                dest_folders.append(dest_folder)

            # Print meta
            logging.info(f"File modification date: {source_file.mdate}")
            logging.info(f"Source path: {source_file.path}")
            logging.info(f"Destination path: {dest_file.path}")

            # Check for existing files and update filename
            while True:
                # Check if destination file exists
                if dest_file.is_file:
                    if dest_file.inc < 1:
                        logging.info("File with the same name exists in destination, comparing checksums")
                    else:
                        logging.debug(f"File with incremented name {dest_file.filename} exists, comparing checksums")

                    # If checksums are matching
                    if utils.compare_checksums(source_file.checksum, dest_file.checksum):
                        logging.warning(f"File ({dest_file.filename}) with matching checksums "
                                        f"already exists in destination, skipping")
                        skipped_files.append(source_file.path)
                        skip = True
                        break
                    else:
                        logging.warning(
                            f"File ({dest_file.filename}) with the same name already exists in destination,"
                            f" adding incremental")
                        dest_file.increment_filename()
                        logging.debug(f'Incremented filename is {dest_file.filename}')

                        continue
                else:
                    break

            # Perform file actions
            if not skip:
                if self.dryrun:
                    logging.info("DRYRUN ENABLED, NOT PERFORMING FILE ACTIONS")
                else:
                    # Create destination folder
                    dest_file.path.parent.mkdir(exist_ok=True, parents=True)

                    # Copy file
                    logging.debug(f'{source_file.path} -> {dest_file.path}')
                    utils.copy_file(source_file.path, dest_file.path)
                    logging.debug(f'{dest_file.is_file}, {dest_file.checksum}')
                    logging.info("Verifying transferred file")
                    if utils.compare_checksums(source_file.checksum, dest_file.checksum):
                        logging.info("File transferred successfully")
                        if self.mode == "move":
                            source_file.delete()
                    else:
                        logging.error("File NOT transferred successfully, mismatching checksums")
                        errored_files.append({source_file.path: "Mismatching checksum after transfer"})

            # Add file size to total
            total_transferred_size += source_file.size

            # Add file to processed files
            processed_files.append(source_file.filename)

            # Calculate remaining time
            elapsed_time = time.time() - start_time
            logging.info(f"Elapsed time: {time.strftime('%-M min %-S sec', time.gmtime(elapsed_time))}")

            bytes_per_second = total_transferred_size / elapsed_time
            logging.info(f"Avg. transfer speed: {utils.convert_size(bytes_per_second)}/s")

            size_remaining = source_list.size - total_transferred_size
            if bytes_per_second != 0:
                time_remaining = size_remaining / bytes_per_second
            else:
                time_remaining = 1
            logging.info(f"Size remaining: {utils.convert_size(size_remaining)}")
            logging.info(f"Approx. time remaining: {time.strftime('%-M min %-S sec', time.gmtime(time_remaining))}")
            logging.info("---\n")

        # Print created destination folders
        if dest_folders:
            # Sort folder for better output
            dest_folders.sort()

            logging.info(f"Created the following folders {', '.join([str(x.name) for x in dest_folders])}")
            logging.debug([str(x.resolve()) for x in dest_folders])

        logging.info(f"{len(processed_files)} files processed")
        logging.debug(f"Processed files: {processed_files}")

        logging.info(f"{len(dest_folders)} destination folders")
        logging.debug(f"Destination folders: {dest_folders}")

        logging.info(f"{len(skipped_files)} files skipped")
        logging.debug(f"Skipped files: {skipped_files}")
        return True


class FileList:
    def __init__(self, path, exclude=None):
        """A list of files as File objects

        Args:
            path: path to the root directory to scan for files
            exclude: list of filenames to ignore when adding files to list
        """
        self._path = Path(path)
        self.files = None

        self.exclude = []
        if isinstance(exclude, list):
            self.exclude.extend(exclude)
        elif isinstance(exclude, str):
            self.exclude.append(exclude)

        # Update file list
        self.update()

    def update(self):
        """Get list of files in a folder and its subfolders"""
        # Get all files in path
        files = [x for x in self._path.rglob("*") if x.is_file() and x.name not in self.exclude]
        logging.debug(f"All files in source: {files}")

        # Create a dict with all files that aren't in exclude list
        self.files = {}
        for n, f in enumerate(files):
            logging.debug(f.name)
            self.files[n] = File(f)
            logging.debug(f"Added {f.name} to file list ({n + 1}/{len(files)})")

    @property
    def size(self) -> int:
        """Return total file size of all files in list"""
        return sum([y.size for x, y in self.files.items()])

    @property
    def count(self) -> int:
        """Return the number of files in list"""
        return len(self.files)


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
        return self.path.is_file()

    @property
    def filename(self):
        """Update the current filename with prefix and padding"""
        fname = self.name
        if self.prefix:
            fname = f"{self.prefix}_{fname}"
        if self.inc >= 1:
            inc = utils.pad_number(self.inc, padding=self.inc_pad)
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

        # Set name from exifdata based on a preset
        presets = {
            "camera_model": "Model",
            "camera_make": "Make"
        }

        if presets.get(name):
            new_name = self.exifdata.get(presets[name], "unknown").lower()

        # Validate file name and remove/replace illegal characters
        if validate:
            new_name = utils.validate_string(new_name)

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
            self._checksum = utils.file_checksum(self.path)
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
            return utils.exifdata(self.path)
        elif self._path.is_file():
            return utils.exifdata(self._path)
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
        if custom_date is None:
            date = self.mdate
        else:
            date = custom_date

        prefixes = {"taken_date": date.strftime("%y%m%d"),
                    "taken_date_time": date.strftime("%y%m%d_%H%M%S"),
                    "offload_date": datetime.now().strftime("%y%m%d")}

        if prefixes.get(prefix) or prefix in ("empty", ""):
            self._prefix = prefixes.get(prefix)
        else:
            self._prefix = prefix

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


def cli():
    """Command line interface"""
    # Create the parser
    parser = argparse.ArgumentParser(
        description="Offload files with checksum verification")

    # Add the arguments
    parser.add_argument("-s", "--source",
                        type=str,
                        help="The source folder",
                        action="store")

    parser.add_argument("-d", "--destination",
                        type=str,
                        help="The destination folder",
                        action="store")

    parser.add_argument("-f", "--folder-structure",
                        choices=["original", "taken_date",
                                 "offload_date", "year", "year_month", "flat"],
                        dest="structure",
                        default="taken_date",
                        help="Set the folder structure.\nDefault: taken_date",
                        action="store")

    parser.add_argument("-n", "--name",
                        type=str,
                        help="Set a new filename",
                        action="store")

    parser.add_argument("-p", "--prefix",
                        help="Set the filename prefix. Enter a custom prefix, \"taken_date\", \"taken_date_time\" or "
                             "\"offload_date\" for templates. \"none\" for no prefix.\nDefault: taken_date",
                        default="taken_date",
                        action="store")

    parser.add_argument("-m", "--move",
                        help="Move files instead of copy",
                        action="store_true")

    parser.add_argument("--dryrun",
                        help="Run the script without actually changing any files",
                        action="store_true")

    parser.add_argument("--debug-log",
                        dest="log_level",
                        help="Show the log with debugging messages",
                        action="store_true")

    # Execute the parse_args() method
    args = parser.parse_args()

    # Print the title
    print("================")
    print("CAMERA OFFLOADER")
    print("================")
    print("")

    confirmation = False

    if args.source is None:
        confirmation = True
        volumes = {}
        if os.name == "posix":
            volumes = {n: str(v) for (n, v) in enumerate(
                Path("/Volumes").iterdir(), 1)}
        print(f"Choose a volume to offload from, or enter a custom path:")
        for n, vol in volumes.items():
            print(f"{n}: {vol}")

        while True:
            try:
                source_input = input("> ").strip()
                if Path(source_input).is_dir():
                    source = Path(source_input)
                    break
                elif volumes.get(int(source_input)):
                    source = volumes[int(source_input)]
                    break
                else:
                    print("Invalid choice. Try again.")

            except Exception as e:
                print("Invalid selection")
                exit(1)
    else:
        source = args.source

    print("")

    if args.destination is None:
        confirmation = True
        recent_paths = {n: str(v) for (n, v) in enumerate(
            utils.get_recent_paths(), 1)}
        if recent_paths:
            print(
                f"Enter the path to your destination folder or use one of these recent paths:")
            for n, path in recent_paths.items():
                print(f"{n}: {path}")
        else:
            print(f"Enter the path to your destination folder:")

        while True:
            try:
                dest_input = input("> ").strip()
                if dest_input.isdigit():
                    destination = recent_paths[int(dest_input)]
                    break
                else:
                    if Path(dest_input).exists():
                        destination = dest_input
                        break

                    else:
                        print("Path does not exist. Try again.")

            except Exception as e:
                print("Invalid input")
                exit(1)

    else:
        destination = args.destination

    # Save destination path for history
    utils.update_recent_paths(destination)

    # Set the folder structure
    folder_structure = args.structure

    # Set the transfer mode
    if args.move:
        mode = "move"
    else:
        mode = "copy"

    # Set the log level
    if args.log_level:
        log_level = "debug"
    else:
        log_level = "info"

    # Confirmation dialog
    if confirmation:
        print("---")
        print("\nPre-transfer summary\n")
        print(f"Source path: {source}")
        print(f"Destination path: {destination}")
        print("")
        print(f"Mode: {mode}")
        print(f"Folder structure: {folder_structure}")
        if args.name:
            print(f"Name: {args.name}")
        print(f"Prefix: {args.prefix}")
        print(f"Log level: {log_level}")
        if args.dryrun:
            print("")
            print("THIS IS A DRYRUN. NO FILES WILL BE TRANSFERRED.")
        print("")
        print("Press enter to continue or any other key to cancel")
        if input():
            quit()
        print("")

    # Run offloader
    ol = Offloader(source=source,
                   dest=destination,
                   structure=folder_structure,
                   filename=args.name,
                   prefix=args.prefix,
                   mode=mode,
                   dryrun=args.dryrun,
                   log_level=log_level
                   )
    ol.offload()


def main():
    pass


if __name__ == "__main__":
    cli()
