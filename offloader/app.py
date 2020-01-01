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

exclude = ["MEDIAPRO.XML",
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
        self.source = source
        self.destination = dest
        self.structure = structure
        self.filename = filename
        self.prefix = prefix
        self.mode = mode
        self.dryrun = dryrun
        self.exclude = exclude

        # Settings
        self.prefixes = {"taken_date": "%y%m%d",
                         "taken_date_time": "%y%m%d_%H%M%S",
                         "offload_date": datetime.now().strftime("%y%m%d"),
                         "none": ""}

    def offload(self):
        """Offload files"""
        dest_folders = []
        skipped_files = []
        processed_files = []

        # Get list of files in source folder
        source_files = utils.get_file_list(self.source, exclude=self.exclude)

        # Calculate the total size of source files
        total_file_size = sum([source_files[x].get("size")
                               for x in source_files])

        # Setup variable for transferred size
        total_transferred_size = 0

        logging.info(f"Total file size: {utils.convert_size(total_file_size)}")
        logging.info(
            f"Average file size: {utils.convert_size(total_file_size / len(source_files))}")
        logging.info("---\n")

        # Get start time to calculate remaining time
        start_time = time.time()

        # Process files
        for file_id in source_files:
            # Reset the incremental number
            incremental = 0

            # Get file info for current file
            source_file = source_files[file_id]

            # Set destination file name base on source file name
            if self.filename:
                file_ext = Path(source_file.get("name")).suffix

                if self.filename == "camera_model":
                    metadata = utils.get_metadata(source_file["path"])
                    if metadata.get("EXIF:Model"):
                        filename = f"{metadata.get('EXIF:Model')}{file_ext}"
                    else:
                        logging.info("Couldn't find the camera model")
                        filename = f"unknown{file_ext}"

                elif self.filename == "camera_make":
                    metadata = utils.get_metadata(source_file["path"])
                    if metadata.get("EXIF:Make"):
                        filename = f"{metadata.get('EXIF:Make')}{file_ext}"
                    else:
                        logging.info("Couldn't find the camera make")
                        filename = f"unknown{file_ext}"

                elif self.filename == "validify":
                    # Make valid filename
                    pass

                else:
                    filename = f"{self.filename}{file_ext}"

            else:
                filename = source_file.get("name")

            # Set destination file name base on filename variable
            dest_file = {
                "name": filename
            }

            # Display how far along the transfer we are
            transfer_percentage = round((total_transferred_size / total_file_size) * 100, 2)
            logging.info(
                f"Processing file {file_id}/{len(source_files)} (~{transfer_percentage}%) | {source_file['name']}")

            # Get destination path based on the folder structure
            dest_file["path"] = self.get_destination_path(source_file)

            # Add prefix to the filename and path
            dest_file.update(self.add_prefix_to_filename(source_file, dest_file))

            # Print meta
            logging.info(f"File modification date: {source_file.get('date')}")
            logging.info(f"Source path: {source_file.get('path')}")
            logging.info(f"Destination path: {dest_file.get('path')}")

            # Check if file with same name exists
            while True:
                if dest_file["path"].exists():
                    logging.info("File with the same name exists in destination, comparing checksums")

                    # Get file info for existing file
                    dest_file = utils.get_file_info(dest_file["path"])

                    # Compare checksums
                    if utils.compare_checksums(source_file['path'], dest_file['path']):
                        logging.warning(
                            f"File ({dest_file['name']}) with matching checksums already exists in destination, skipping")
                        # logging.debug(f"Source: {source_file}")
                        # logging.debug(f"Destination: {dest_file}")

                        # Add file to skipped list
                        skipped_files.append(source_file["name"])
                        break

                    # If file with same name exists but has mismatching checksums
                    else:
                        logging.warning(
                            f"File ({dest_file['name']}) with the same name already exists in destination, adding incremental")
                        # logging.debug(f"Source: {source_file}")
                        # logging.debug(f"Destination: {dest_file}")

                        # Add incremental to filename
                        incremental += 1
                        dest_file["name"] = f"{source_file['path'].stem}_{incremental:03}{source_file['path'].suffix}"
                        dest_file["path"] = dest_file["path"].parent / \
                                            dest_file["name"]
                        logging.debug(
                            f"Added increment to filename {dest_file['name']}")
                else:
                    # If destination file doesn't exist
                    if self.dryrun:
                        logging.info("DRYRUN ENABLED, NOT COPYING")

                    else:
                        # Create destination folder
                        dest_file["path"].parent.mkdir(exist_ok=True, parents=True)

                        # Add folder to destination folders list
                        if dest_file["path"].parent not in dest_folders:
                            dest_folders.append(dest_file["path"].parent)

                        # Get checksum of source file for verification
                        source_file["checksum"] = utils.get_file_checksum(source_file["path"])

                        if self.mode == "copy":
                            utils.copy_file(source_file["path"], dest_file["path"])

                        elif self.mode == "move":
                            utils.move_file(source_file["path"], dest_file["path"])

                        logging.info("Verifying transferred file")
                        dest_file["checksum"] = utils.get_file_checksum(dest_file["path"])

                        if dest_file["checksum"] == source_file["checksum"]:
                            logging.info("File transferred successfully")
                        else:
                            logging.error("File NOT transferred successfully, mismatching checksums")
                    break

            # Add file size to total
            total_transferred_size += source_file['size']

            # Add file to processed files
            processed_files.append(dest_file["name"])

            # Calculate remaining time
            elapsed_time = time.time() - start_time
            logging.info(
                f"Elapsed time: {time.strftime('%-M min %-S sec', time.gmtime(elapsed_time))}")

            bytes_per_second = total_transferred_size / elapsed_time
            logging.info(
                f"Avg. transfer speed: {utils.convert_size(bytes_per_second)}/s")

            size_remaining = total_file_size - total_transferred_size
            time_remaining = size_remaining / bytes_per_second
            logging.info(
                f"Size remaining: {utils.convert_size(size_remaining)}")
            logging.info(
                f"Approx. time remaining: {time.strftime('%-M min %-S sec', time.gmtime(time_remaining))}")

            logging.info("---\n")

        if dest_folders:
            # Sort folder for better output
            dest_folders.sort()

            logging.info(
                f"Created the following folders {', '.join([str(x.name) for x in dest_folders])}")
            logging.debug([str(x.resolve()) for x in dest_folders])

        logging.info(f"{len(processed_files)} files processed")
        logging.debug(f"Processed files: {processed_files}")

        logging.info(f"{len(dest_folders)} destination folders")
        logging.debug(f"Destination folders: {dest_folders}")

        logging.info(f"{len(skipped_files)} files skipped")
        logging.debug(f"Skipped files: {skipped_files}")

    def get_destination_path(self, source_file):
        """Get a destination path depending on the structure setting
        :returns destination path
        :rtype string"""
        if self.structure == "original":
            # Use the same structure as source
            dest_path = Path(self.destination) / source_file["path"].relative_to(self.source)

        elif self.structure == "taken_date":
            # Construct new structure from modification date
            date_folders = f"{source_file['date'].year}/{source_file['date'].strftime('%Y-%m-%d')}"
            dest_path = Path(self.destination) / date_folders / source_file["name"]

        elif self.structure == "offload_date":
            # Construct new structure from modification date
            date_folders = f"{self.today.year}/{self.today.strftime('%Y-%m-%d')}"
            dest_path = Path(self.destination) / date_folders / source_file["name"]

        elif self.structure == "year":
            # Construct new structure from modification date
            date_folders = f"{source_file['date'].year}"
            dest_path = Path(self.destination) / date_folders / source_file["name"]

        elif self.structure == "flat":
            # Put files straight into destination folder
            dest_path = Path(self.destination) / source_file["name"]

        else:
            raise Exception("No valid file structure specified")

        return dest_path

    def add_prefix_to_filename(self, source_file, dest_file):
        """Add the set prefix to the filename
        :return destination file dict with update file path
        :rtype dict"""
        if not self.structure == "original":
            if self.prefix == "none":
                logging.info(f"Prefix is set to none. Not adding prefix")
                logging.debug(f"Filename {dest_file['name']}")

            else:
                if self.prefixes.get(self.prefix):
                    # The prefix is the date of the file modification date
                    if self.prefix == "taken_date":
                        prefix = f"{source_file['date'].strftime(self.prefixes['taken_date'])}"

                    elif self.prefix == "taken_date_time":
                        prefix = f"{source_file['date'].strftime(self.prefixes['taken_date_time'])}"

                    elif self.prefix == "offload_date":
                        prefix = f"{self.prefixes['offload_date']}"

                else:
                    prefix = self.prefix

                if dest_file["name"].startswith(prefix):
                    logging.info(
                        f"Filename already starts with {prefix}. Not adding prefix")
                    logging.debug(f"Filename {dest_file['name']}")


                else:
                    dest_file["name"] = f"{prefix}_{dest_file['name']}"
                    dest_file["path"] = dest_file["path"].parent / dest_file["name"]
                    logging.info(f"Prefix {prefix} added to {source_file['name']}")
                    logging.debug(f"New filename {dest_file['name']}")
                    logging.debug(f"New destination path {dest_file['path']}")

        return dest_file


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
                                 "offload_date", "year", "flat"],
                        dest="structure",
                        default="taken_date",
                        help="Set the folder structure.\nDefault: taken_date",
                        action="store")

    parser.add_argument("-n", "--name",
                        type=str,
                        help="Set a new filename",
                        action="store")

    parser.add_argument("-p", "--prefix",
                        help="Set the filename prefix. Enter a custom prefix, \"taken_date\", \"taken_date_time\" or \"offload_date\" for templates. \"none\" for no prefix.\nDefault: taken_date",
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
        if os.name == "posix":
            volumes = {n: str(v) for (n, v) in enumerate(
                Path("/Volumes").iterdir(), 1)}
        print(f"Choose a volume to offload from:")
        for n, vol in volumes.items():
            print(f"{n}: {vol}")

        while True:
            try:
                source_input = int(input("> ").strip())
                if volumes.get(source_input):
                    source = volumes[source_input]
                    break
                else:
                    print("Invalid choice. Try again.")

            except:
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

            except:
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
    o = Offloader(source="/Users/johannes/Desktop/offloader/source",
                  dest="/Users/johannes/Desktop/offloader/destination",
                  structure="offload_date",  # original, flat, taken_date, offload_date
                  prefix="offload_date",  # taken_date, offload_date, custom
                  mode="copy",
                  dryrun=True)
    o.offload()
    pass


if __name__ == "__main__":
    cli()
