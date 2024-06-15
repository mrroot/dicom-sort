import argparse
import os
import sys
import configparser
import fileutils
import dicomutils
import logging

# Configure logging
logging.basicConfig(
    filename='dcmsort.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filemode='w'  # Overwrite the log file on each run
)


def load_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def main():
    parser = argparse.ArgumentParser(
        description="A command-line script to optionally unpack archives, copy DICOM compliant files, compress, decompress, and send them to a PACS.",
        epilog=(
            "\nExamples of usage:\n"
            "  1. Copy DICOM files from source to destination:\n"
            "     python dcmsort.py -s /path/to/source -d /path/to/destination\n"
            "\n"
            "  2. Unpack archives in the source directory, copy files, and compress them using RLE:\n"
            "     python dcmsort.py -s /path/to/source -d /path/to/destination -u -c\n"
            "\n"
            "  3. Decompress DICOM files in the destination directory:\n"
            "     python dcmsort.py -s /path/to/source -d /path/to/destination --decompress\n"
            "\n"
            "  4. Send DICOM files to a PACS using alias:\n"
            "     python dcmsort.py -s /path/to/source --send NodeAlias\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Adding arguments with short options
    parser.add_argument('-s', '--source', type=str, metavar='/path/to/source/', help="Source directory", required=True)

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-d', '--destination', type=str, metavar='/path/to/destination/', help="Destination directory")
    group.add_argument('--send', type=str, metavar='NodeAlias', help="Send DICOM files to PACS using alias")

    parser.add_argument('-u', '--unzip', action='store_true', help="Unpack archives in the source directory")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('-c', '--compress', action='store_true', help="Compress DICOM files using RLE")
    parser.add_argument('--decompress', action='store_true', help="Decompress DICOM files")
    parser.add_argument('--yes', action='store_true', help="Automatically confirm all operations")
    parser.add_argument('--nosize', action='store_true',
                        help="Do not calculate total files size, it can take long time on large dataset")

    # Check if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Parsing arguments
    args = parser.parse_args()

    # Use absolute paths
    source = os.path.abspath(args.source)
    destination = os.path.abspath(args.destination) if args.destination else None

    if args.verbose:
        print(f"Verbose mode enabled.")
        print(f"Source directory: {source}")
        if destination:
            print(f"Destination directory: {destination}")

    # Load configuration
    config_path = 'dcmsort.conf'
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' does not exist.")
        return
    config = load_config(config_path)

    if args.verbose:
        print(f"Configuration loaded from {config_path}")

    # Check if source directory exists
    if not os.path.exists(source):
        print(f"Error: Source directory '{source}' does not exist.")
        return

    # Check if only --source is present
    if not (args.destination or args.send or args.unzip or args.compress or args.decompress):
        parser.print_help()
        print(
            "\nError: At least one of the following options is required to perform actions on the source folder: -d, --send, -u, -c, or --decompress")
        sys.exit(1)

    # Handle unzipping if specified
    if args.unzip:
        print("Unpacking archives...")
        fileutils.unpack_archives(source)

    if destination:
        # Calculate total size of all files and DICOM files in the source directory if --nosize is not specified
        if not args.nosize:
            total_size, dicom_size = fileutils.get_total_size(source)
            print(f"Total size of all files in source: {total_size / (1024 * 1024):.2f} MB")
            print(f"Total size of DICOM files in source: {dicom_size / (1024 * 1024):.2f} MB")

        # Ask for permission to copy if --yes is not specified
        if not args.yes:
            confirm = input("Do you want to proceed with the copy? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("Copy operation aborted.")
                return

        # Perform the copy of DICOM files
        success = fileutils.copy_directory(source, destination, args.verbose, args.yes)
        if success and args.verbose:
            print("DICOM files copy operation completed.")

        # Handle compression if specified
        if args.compress:
            print("Compressing DICOM files using RLE method.")
            dicomutils.compress_dicom_files(destination, args.verbose)

        # Handle decompression if specified
        if args.decompress:
            print("Decompressing DICOM files.")
            dicomutils.decompress_dicom_files(destination, args.verbose)
    else:
        # Handle operations on the source directory if --destination is omitted
        if args.compress:
            print("Compressing DICOM files using RLE method in the source directory.")
            dicomutils.compress_dicom_files(source, args.verbose)

        if args.decompress:
            print("Decompressing DICOM files in the source directory.")
            dicomutils.decompress_dicom_files(source, args.verbose)

    # Handle sending if specified
    if args.send:
        print(f"Sending DICOM files to PACS using alias '{args.send}'")
        dicomutils.send_dicom_files(source, args.send, config, args.verbose)


if __name__ == "__main__":
    main()
