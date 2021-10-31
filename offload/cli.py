#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
script_name.py
Description of script_name.py.
"""
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


def main():
    """docstring for main"""
    pass


if __name__ == '__main__':
    main()
