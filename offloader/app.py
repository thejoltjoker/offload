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

exclude_files = ["MEDIAPRO.XML",
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
                 ".DS_Store"]


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
        source_list = FileList(self.source)

        logging.info(f"Total file size: {utils.convert_size(source_list.total_size)}")
        logging.info(f"Average file size: {utils.convert_size(source_list.total_size / len(source_list.files))}")
        logging.info("---\n")

        # Setup variables for stats
        total_transferred_size = 0
        start_time = time.time()

        for file_id, source_file in source_list.files.items():
            # Display how far along the transfer we are
            transfer_percentage = round((total_transferred_size / source_list.total_size) * 100, 2)
            logging.info(f"Processing file {file_id}/{len(source_list.files)} "
                         f"(~{transfer_percentage}%) | {source_file.filename}")

            # Create File object for destination file
            dest_folder = self.destination / utils.destination_folder(source_file.mdate, preset=self.structure)
            dest_path = dest_folder / source_file.filename
            dest_file = File(dest_path)

            # Add prefix to filename
            dest_file.add_prefix(self.prefix, custom_date=source_file.mdate)

            # Add destination folder to list of destination folders
            if dest_folder not in dest_folders:
                dest_folders.append(dest_folder)

            # Print meta
            logging.info(f"File modification date: {source_file.mdate}")
            logging.info(f"Source path: {source_file.path}")
            logging.info(f"Destination path: {dest_file.path}")

            # Check for existing files and update filename
            while True:
                if dest_file.path.is_file():
                    if dest_file.inc < 1:
                        logging.info("File with the same name exists in destination, comparing checksums")
                    else:
                        logging.debug(f"File with incremented name {dest_file.filename} exists. Incrementing again")

                    # If checksums are matching
                    if utils.compare_checksums(source_file.path, dest_file.path):
                        logging.warning(f"File ({dest_file.filename}) with matching checksums "
                                        f"already exists in destination, skipping")
                        skipped_files.append(source_file.path)
                        break
                    else:
                        logging.warning(f"File ({dest_file.filename}) with the same name already exists in destination,"
                                        f" adding incremental")
                        dest_file.increment_filename()

                        continue
                else:
                    break
            # Perform file actions
            if self.dryrun:
                logging.info("DRYRUN ENABLED, NOT PERFORMING FILE ACTIONS")
            else:
                # Create destination folder
                dest_file.path.parent.mkdir(exist_ok=True, parents=True)

                # Get checksum of source file for verification
                source_file.update_checksum()

                if self.mode == "copy":
                    utils.copy_file(source_file.path, dest_file.path)

                elif self.mode == "move":
                    utils.move_file(source_file.path, dest_file.path)

                logging.info("Verifying transferred file")
                dest_file.update_checksum()

                if dest_file.checksum == source_file.checksum:
                    logging.info("File transferred successfully")
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

            size_remaining = source_list.total_size - total_transferred_size
            time_remaining = size_remaining / bytes_per_second
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
    def __init__(self, directory, exclude=None):
        self.directory = Path(directory)

        self.files = None
        self.total_size = None

        self.exclude = []
        if isinstance(exclude, list):
            self.exclude.extend(exclude)
        elif isinstance(exclude, str):
            self.exclude.append(exclude)

        # Update file list
        self.update_list()

    def update_list(self):
        """Get list of files in a folder and its subfolders"""
        # Get file list
        files = [x for x in self.directory.rglob("*") if x.is_file()]

        # Remove exlude files
        self.files = {n: File(x) for n, x in enumerate(files) if x.name not in self.exclude}

        # Update total size
        self.update_total_size()
        return True

    def update_total_size(self):
        self.total_size = sum([y.size for x, y in self.files.items()])
        return True


class File:
    def __init__(self, path):
        self.path = Path(path)
        self.relative_path = None
        self.filename = self.path.name
        self.prefix = None
        self.name = self.path.stem
        self.ext = self.path.suffix.strip(".")
        self.inc = 0
        self.inc_pad = 3

        # These variables are None unless file exists
        self.mtime = None
        self.mdate = None
        self.size = 0
        self.metadata = None
        self.checksum = None

        # Update with file variables if it exists
        self.update(checksum=True)

    def update(self, checksum=False, metadata=False):
        """Update all properties"""
        self.update_filename()
        self.update_path()
        self.update_time()
        self.update_size()

        if checksum:
            self.update_checksum()
        if metadata:
            self.update_metadata()

    def update_size(self):
        """Update the size property"""
        if self.path.is_file():
            self.size = self.path.stat().st_size
            return True
        else:
            return False

    def update_time(self):
        """Update the time and date properties"""
        if self.path.is_file():
            self.mtime = self.path.stat().st_mtime
            self.mdate = datetime.fromtimestamp(self.mtime)
            return True
        else:
            return False

    def update_path(self):
        """Update the path property"""
        self.path = self.path.parent / self.filename
        return True

    def update_checksum(self, hashtype="xxhash"):
        """Get the file checksum"""
        if self.path.is_file():
            self.checksum = utils.file_checksum(self.path, hashtype=hashtype)
            return True
        else:
            return False

    def update_filename(self):
        """Update the current filename with prefix and padding"""
        filename = self.name
        if self.prefix:
            filename = f"{self.prefix}_{filename}"
        if self.inc >= 1:
            inc = utils.pad_number(self.inc, padding=self.inc_pad)
            filename = f"{filename}_{inc}"

        filename = f"{filename}.{self.ext}"
        self.filename = filename

        return filename

    def update_metadata(self):
        """Get the file metadata using exiftool"""
        if self.path.is_file():
            self.metadata = utils.file_metadata(self.path)
            return True
        else:
            return False

    def increment_filename(self, padding=None):
        """Add incremental or count up"""
        self.inc += 1
        if padding:
            self.inc_pad = padding

        self.update()
        return True

    def add_prefix(self, prefix, custom_date=None):
        if custom_date is None:
            date = self.mdate
        else:
            date = custom_date

        prefixes = {"taken_date": date.strftime("%y%m%d"),
                    "taken_date_time": date.strftime("%y%m%d_%H%M%S"),
                    "offload_date": datetime.now().strftime("%y%m%d")}

        if prefixes.get(prefix) or prefix in ("empty", ""):
            self.prefix = prefixes.get(prefix)
        else:
            self.prefix = prefix
        self.update()
        return True

    def add_relative_path(self, relative_to):
        """Add/update the relative path property"""
        self.relative_path = self.path.relative_to(relative_to)
        return True

    def change_path(self, path):
        """Change the path"""
        self.path = Path(path) / self.filename
        return True

    def change_name(self, name, validate=True):
        """Change the name property. Some presets available:
        - camera_model
        - camera_make"""
        new_name = str(name)

        presets = {
            "camera_model": "EXIF:Model",
            "camera_make": "EXIF:Make"
        }

        if presets.get(name):
            if not self.metadata:
                self.update_metadata()
            new_name = self.metadata.get(presets[name], "unknown").lower()

        if validate:
            new_name = utils.validate_string(new_name)

        self.name = new_name
        self.update()
        return True


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
