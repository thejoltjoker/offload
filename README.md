# Camera Offloader 📷️

A command line tool for offloading files from memory cards and external drives.

## Features

- Transfer files from a memory card or removable drive
- Checksum verification using xxhash
- File renaming based on date or custom prefix
- Create a new date based folder structure or use the original one

### Todo
- presets in gui
- redo time estimate
- launch filelist in thread

## Usage

usage: app.py [-h][-s source] [-d DESTINATION][-f {original,taken_date,offload_date,flat}] [-p PREFIX][-m]
[--dryrun][--debug-log]

### Source

`-s SOURCE, --source SOURCE`

The source folder. Leave blank for input dialog with list of volumes.

### Destination

`-d DESTINATION, --destination DESTINATION`

The destination folder. Leave blank for input dialog.

### Folder structure

`-f {original, taken_date, offload_date, flat}, --folder-structure {original, taken_date, offload_date, flat}`

Set the folder structure. Default: taken_date

#### original

Uses the original folder structure and just transfers the file into the new root.

#### taken_date

Creates a folder structure according to `%Y`/`%Y-%m-%d`(2019/2019-11-26) based on the file modification date.

#### offload_date

Sets the prefix according to `%y%m%d`(191126) based on the offload date.

#### flat

Transfers the files into the root without creating any subfolders.

### Prefix

-p PREFIX, --prefix PREFIX

Set the filename prefix. Enter a custom prefix,
"taken_date" or "offload_date" for templates. Default:
taken_date

#### taken_date

Sets the prefix according to `%y%m%d` based on the file modification date.

#### offload_date

Sets the prefix according to `%y%m%d` based on the offload date.

### Move

-m, --move Move files instead of copy

### Dryrun

--dryrun Run the script without actually changing any files

### Debug log

--debug-log Show the log with debugging messages


## Credits
- Source Sans Pro https://github.com/adobe-fonts/source-sans-pro