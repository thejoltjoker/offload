#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Camera Offload
---
This script is used for transferring files and verifying them using a checksum.
"""

import os
import logging
import argparse
import time
import csv
import json
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from offload import APP_DATA_PATH, REPORTS_PATH, EXCLUDE_FILES, utils


class Settings:
    def __init__(self):
        """
        Object for storing and getting offloader settings
        """
        self._path = APP_DATA_PATH / 'settings.json'
        self._default_settings = {'latest_destination': str(Path().home().resolve()),
                                  'pushbullet': None,
                                  'folder_structure': 'taken_date',
                                  'prefix': 'taken_date'}
        self._init_settings()

    def _init_settings(self):
        """Init settings object"""
        if not self._path.is_file():
            with self._path.open('w') as json_file:
                json.dump({}, json_file)

    @property
    def latest_destination(self):
        """Get latest offload destination

        Returns:
            Path: path to latest offload destination
        """
        dest = self._read_setting('latest_destination')
        # Return home path if no former destination stored
        if dest:
            return Path(dest)
        else:
            return Path().home()

    @latest_destination.setter
    def latest_destination(self, path):
        """Set latest offload destination"""
        path = Path(path)
        self._write_settings(latest_destination=str(path.resolve()))

    def _write_settings(self, **settings):
        """Write settings to disk"""
        with self._path.open('w') as json_file:
            json.dump({k: str(v) for k, v in settings.items()}, json_file)

    def _read_setting(self, setting):
        """Read settings from disk"""
        with self._path.open('r') as json_file:
            json_data = json.load(json_file)
            return json_data.get(setting)


class Offloader(QThread):
    _progress_signal = pyqtSignal(dict)

    def __init__(self, source, dest, structure, filename, prefix, mode, dryrun, log_level):
        super(Offloader, self).__init__()
        self._logger = utils.setup_logger(log_level)
        self._today = datetime.now()
        self._source = Path(source)
        self._destination = Path(dest)
        self._structure = structure
        self._filename = filename
        self._prefix = prefix
        self._mode = mode
        self._dryrun = dryrun
        self._exclude = EXCLUDE_FILES
        self._signal = {'percentage': 0, 'action': '', 'time': '', 'is_finished': False}
        self._running = True

        # Properties
        logging.info("Getting list of files")
        self.source_files = FileList(self._source, exclude=self._exclude)
        self.source_files.sort()

        # Offload attributes
        self.ol_time_started = 0
        self.ol_bytes_transferred = 0

        # Set some variables
        self.destination_folders = []
        self.skipped_files = []
        self.processed_files = []
        self.errored_files = []

        # Report
        self.report = Report()

    @property
    def source(self):
        """Get the source directory"""
        return self._source

    @source.setter
    def source(self, path):
        """Set the source directory"""
        if Path(path).is_dir():
            self._source = Path(path)
            self.source_files = FileList(self._source, exclude=self._exclude)
        else:
            logging.error(f'{path} is not a valid directory')

    @property
    def destination(self):
        """Get the source directory"""
        return self._destination

    @destination.setter
    def destination(self, path):
        """Set the source directory"""
        self._destination = Path(path)

    @property
    def structure(self):
        """Get the folder structure preset"""
        return self._structure

    @structure.setter
    def structure(self, preset):
        """Set the folder structure preset"""
        self._structure = preset

    @property
    def ol_percentage(self):
        return round((self.ol_bytes_transferred / self.source_files.size) * 100, 2)

    @property
    def ol_time_elapsed(self):
        return time.time() - self.ol_time_started

    @property
    def ol_bytes_remaining(self):
        return self.source_files.size - self.ol_bytes_transferred

    @property
    def ol_time_remaining(self):
        return self.ol_bytes_remaining / self.ol_speed if self.ol_speed else 0

    @property
    def ol_speed(self):
        return self.ol_bytes_transferred / self.ol_time_elapsed

    def offload(self):
        """Offload files"""
        # Offload start time
        self.ol_time_started = time.time()

        # Get list of files in source folder
        logging.info(f"Total file size: {self.source_files.hsize}")
        logging.info(f"Average file size: {utils.convert_size(self.source_files.avg_file_size)}")
        logging.info("---\n")

        # Iterate over all the files
        for file_id, source_file in enumerate(self.source_files.files):
            skip = False

            # Display how far along the transfer we are
            logging.info(f"Processing file {file_id + 1}/{len(self.source_files.files)} "
                         f"(~{self.ol_percentage}%) | {source_file.filename}")

            # Send signal to GUI
            self._signal['percentage'] = int(self.ol_percentage)
            self._signal['action'] = f'Processing file {file_id + 1}/{len(self.source_files.files)}'
            self._signal['time'] = self.ol_time_remaining
            self._progress_signal.emit(self._signal)

            # Create File object for destination file
            dest_folder = self._destination / utils.destination_folder(source_file.mdate, preset=self._structure)
            dest_file = File(dest_folder / source_file.filename, prefix=self._prefix)

            # Change filename
            if self._filename:
                dest_file.name = self._filename

            # Add prefix to filename
            dest_file.set_prefix(self._prefix, custom_date=source_file.mdate)

            # Add destination folder to list of destination folders
            if dest_folder not in self.destination_folders:
                self.destination_folders.append(dest_folder)

            # Write to report
            if not self._running:
                self.report.write(source_file, dest_file, 'Not started', checksum=False)
                continue

            # Print meta
            logging.info(f"File modification date: {source_file.mdate}")
            logging.info(f"Source path: {source_file.path}")
            logging.info(f"Destination path: {dest_file.path}")

            # Check for existing files and update filename
            while True:
                # Check if destination file exists
                if dest_file.is_file:
                    # Send signal to GUI
                    self._signal['action'] = f'Processing file {file_id + 1}/{len(self.source_files.files)} [verifying]'
                    self._progress_signal.emit(self._signal)

                    # Add increment
                    if dest_file.inc < 1:
                        logging.info("File with the same name exists in destination, comparing checksums")
                    else:
                        logging.debug(
                            f"File with incremented name {dest_file.filename} exists, comparing checksums")

                    # If checksums are matching
                    if utils.compare_checksums(source_file.checksum, dest_file.checksum):
                        logging.warning(f"File ({dest_file.filename}) with matching checksums "
                                        f"already exists in destination, skipping")
                        # Write to report
                        self.report.write(source_file, dest_file, 'Skipped')

                        self.skipped_files.append(source_file.path)

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
                if source_file.path.is_file():
                    if self._dryrun:
                        logging.info("DRYRUN ENABLED, NOT PERFORMING FILE ACTIONS")
                    else:
                        # Create destination folder
                        dest_file.path.parent.mkdir(exist_ok=True, parents=True)

                        # Send signal to GUI
                        self._signal[
                            'action'] = f'Processing file {file_id + 1}/{len(self.source_files.files)} [copying]'
                        self._progress_signal.emit(self._signal)

                        # Copy file
                        utils.pathlib_copy(source_file.path, dest_file.path)

                        # Send signal to GUI
                        self._signal[
                            'action'] = f'Processing file {file_id + 1}/{len(self.source_files.files)} [verifying]'
                        self._progress_signal.emit(self._signal)

                        # Verify file transfer
                        logging.info("Verifying transferred file")

                        # File transfer successful
                        if utils.compare_checksums(source_file.checksum, dest_file.checksum):
                            logging.info("File transferred successfully")

                            # Write to report
                            self.report.write(source_file, dest_file, 'Successful')

                            # Delete source file
                            if self._mode == "move":
                                source_file.delete()

                        # File transfer unsuccessful
                        else:
                            logging.error("File NOT transferred successfully, mismatching checksums")

                            # Write to report
                            self.report.write(source_file, dest_file, 'Failed')

                            self.errored_files.append({source_file.path: "Mismatching checksum after transfer"})

            # Add file size to total
            self.ol_bytes_transferred += source_file.size

            # Add file to processed files
            self.processed_files.append(source_file.filename)

            # Calculate remaining time
            logging.info(f"Elapsed time: {utils.time_to_string(self.ol_time_elapsed)}")

            # Log transfer speed
            logging.info(f"Avg. transfer speed: {utils.convert_size(self.ol_speed)}/s")

            logging.info(f"Size remaining: {utils.convert_size(self.ol_bytes_remaining)}")
            logging.info(f"Approx. time remaining: {self.ol_time_remaining}")
            logging.info("---\n")

        # Print created destination folders
        if self.destination_folders:
            # Sort folder for better output
            self.destination_folders.sort()

            logging.info(f"Created the following folders {', '.join([str(x.name) for x in self.destination_folders])}")
            logging.debug([str(x.resolve()) for x in self.destination_folders])

        logging.info(f"{len(self.processed_files)} files processed")
        logging.debug(f"Processed files: {self.processed_files}")

        logging.info(f"{len(self.destination_folders)} destination folders")
        logging.debug(f"Destination folders: {self.destination_folders}")

        logging.info(f"{len(self.skipped_files)} files skipped")
        logging.debug(f"Skipped files: {self.skipped_files}")

        # Save report to desktop
        print(self._running)
        self.report.save()
        self.report.write_html()
        self._signal['time'] = 0
        self._signal['is_finished'] = True
        self._progress_signal.emit(self._signal)
        return True

    def run(self):
        logging.info('Hello')
        self.offload()


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
        return utils.convert_size(self.size)

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

        # Set name from exif data based on a preset
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
        # Use file modification date if custom date is none
        if custom_date is None:
            date = self.mdate
        else:
            date = custom_date

        # Get filename prefix presets
        if utils.Preset.prefix(prefix) or prefix in ('empty', ''):
            self._prefix = utils.Preset.prefix(prefix)
            if self._prefix:
                self._prefix = self._prefix.format(date=date)
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


class Report:
    def __init__(self, report_format='csv'):
        self._date = datetime.now()
        self.format = report_format
        self.path = REPORTS_PATH / f"{self._date.strftime('%y%m%d%H%M')}_report.csv"
        self.html_path = self.path.parent / f'{self.path.stem}.html'
        self.html_template_path = APP_DATA_PATH / 'data' / 'report_template.html'

        if not self.path.parent.is_dir():
            self.path.parent.mkdir(exist_ok=True, parents=True)
        columns = ['Source Filename', 'Destination Filename', 'Status', 'Source Checksum', 'Destination Checksum',
                   'Source Path', 'Destination Path', 'Size', 'Modification Date']

        if not self.path.is_file():
            with self.path.open('w') as report:
                writer = csv.writer(report, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(columns)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write_html()

    def write_html(self):
        """Create html file from csv"""
        with self.path.open('r') as report:
            csv_reader = csv.reader(report, delimiter=',')
            line_count = 0
            table_columns = ''
            table_rows = []
            for row in csv_reader:
                if line_count == 0:
                    table_columns = '\n'.join([f'<th scope="col">{x}</th>' for x in row])
                    line_count += 1
                else:
                    cols = []
                    for col in row:
                        if col == 'Successful':
                            cols.append(f'\t<td><span class="text-success">{col}</span></td>')
                        elif col == 'Skipped':
                            cols.append(f'\t<td><span class="text-info">{col}</span></td>')
                        elif col == 'Failed':
                            cols.append(f'\t<td><span class="text-failed">{col}</span></td>')
                        else:
                            cols.append(f'\t<td>{col}</td>')
                    td = '\n'.join(cols)
                    table_rows.append(td)
                    line_count += 1
            table_rows = '\n'.join([f'<tr>\n{x}\n</tr>' for x in table_rows])
        logging.info(table_columns)
        logging.info(table_rows)

        html_report = self.html_template_path.read_text()
        html_report = html_report.format(date=self._date.strftime('%Y-%m-%d %H:%M'),
                                         table_columns=table_columns,
                                         table_rows=table_rows)
        self.html_path.write_text(html_report)
        return self.html_path

    def write(self, source: File, destination: File, status, checksum=True):
        with self.path.open('a') as report:
            writer = csv.writer(report, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            if checksum:
                columns = [source.filename, destination.filename, status,
                           source.checksum, destination.checksum,
                           source.path, destination.path, utils.convert_size(source.size), source.mdate]
            else:
                columns = [source.filename, destination.filename, status,
                           None, None,
                           source.path, destination.path, utils.convert_size(source.size), source.mdate]
            writer.writerow(columns)

    def save(self, path=None):
        if path is None:
            path = Path().home() / 'Desktop' / f"Offload_Report_{self._date.strftime('%Y-%m-%d_%H%M')}.csv"
        utils.pathlib_copy(self.path, path)


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
    # utils.update_recent_paths(destination)
    Settings.latest_destination = destination

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

    # Run offload
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


if __name__ == "__main__":
    cli()
