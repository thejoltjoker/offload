# Camera Offloader 📷️

A command line tool for offloading files from memory cards and external drives.

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

`-f {original,taken_date,offload_date,flat}, --folder-structure {original,taken_date,offload_date,flat}`

Set the folder structure. Default: taken_date

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
