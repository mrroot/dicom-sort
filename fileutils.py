import os
import shutil
import logging
import pydicom
import zipfile
import tarfile
import rarfile
import uuid
from tqdm import tqdm
import patoolib



# Setup custom logger
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)  # Hide all log messages
patoolib.util.logfunc = logger.error


def is_dicom_file(file_path):
    """Check if a file is DICOM compliant."""
    try:
        pydicom.dcmread(file_path)
        return True
    except pydicom.errors.InvalidDicomError:
        return False
    except PermissionError:
        print(f"Permission denied: {file_path}")
        return False
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False


def is_valid_archive(archive_path):
    """
    Check if the archive is valid and contains content.
    """
    try:
        if archive_path.lower().endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                if zip_ref.namelist():
                    return True
        elif archive_path.lower().endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tbz', '.tar')):
            with tarfile.open(archive_path, 'r') as tar_ref:
                if tar_ref.getnames():
                    return True
        elif archive_path.lower().endswith('.rar'):
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                if rar_ref.namelist():
                    return True
    except Exception as e:
        logging.error(f"Invalid archive {archive_path}: {e}")
    return False


def unpack_archive(archive_path, destination):
    """
    Unpacks an archive (zip, tar, rar) to the specified destination directory.
    The content of the archive will be unpacked into a folder named after the archive.
    """
    archive_name = os.path.splitext(os.path.basename(archive_path))[0]
    extract_path = os.path.join(destination, archive_name)

    if not os.path.exists(extract_path):
        os.makedirs(extract_path)

    try:
        if archive_path.lower().endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        elif archive_path.lower().endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tbz', '.tar')):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_path)
        elif archive_path.lower().endswith('.rar'):
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(extract_path)
        else:
            logging.warning(f"Unsupported archive format: {archive_path}")
            return False

        logging.info(f"Unpacked {archive_path} to {extract_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to unpack {archive_path}: {e}")
        return False


def scan_for_archives(directory):
    """
    Scans for archive files in the specified directory and returns a list of paths to the archive files.
    Supported formats: zip, tar.gz, tgz, tar.bz2, tbz, tar, rar.
    """
    archive_files = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            if file.lower().endswith(('.zip', '.tar.gz', '.tgz', '.tar.bz2', '.tbz', '.tar', '.rar')):
                archive_files.append(os.path.join(dirpath, file))
    return archive_files


def unpack_archives(source):
    """
    Unpacks all valid archives in the source directory.
    Each archive is unpacked into a new folder named after the archive.
    """
    archive_files = scan_for_archives(source)

    with tqdm(total=len(archive_files), desc="Unpacking archives", unit="archive",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} archives unpacked") as pbar:
        for archive_path in archive_files:
            if is_valid_archive(archive_path):
                unpack_archive(archive_path, source)
            else:
                logging.warning(f"Skipping invalid or empty archive: {archive_path}")
            pbar.update(1)
def get_total_size(source):
    """Calculate the total size of all files and the size of DICOM files in the source directory with a progress bar."""
    total_size = 0
    dicom_size = 0
    file_paths = []

    # Collect all file paths
    for dirpath, dirnames, filenames in os.walk(source):
        for f in filenames:
            file_paths.append(os.path.join(dirpath, f))

    # Calculate sizes with progress bar
    with tqdm(total=len(file_paths), desc="Calculating sizes", unit="file") as pbar:
        for fp in file_paths:
            if os.path.isfile(fp):
                file_size = os.path.getsize(fp)
                total_size += file_size
                if is_dicom_file(fp):
                    dicom_size += file_size
            pbar.update(1)

    return total_size, dicom_size


def get_dicom_tags(filepath):
    """Extract required DICOM tags from the file."""
    try:
        ds = pydicom.dcmread(filepath, stop_before_pixels=True)
        patient_name = ds.get("PatientName", "Unknown")
        modality = ds.get("Modality", "Unknown")
        study_description = ds.get("StudyDescription", "Unknown")
        study_date = ds.get("StudyDate", "Unknown")
        series_number = ds.get("SeriesNumber", "0")
        instance_number = ds.get("InstanceNumber", "0")
        instance_uuid = ds.get("InstanceUUID", None)
        return patient_name, modality, study_description, study_date, series_number, instance_number, instance_uuid

    except Exception as e:
        print(f"Error extracting DICOM tags from {filepath}: {e}")
        return "Unknown", "Unknown", "Unknown", "Unknown", "0", "0"


def remove_read_only(filepath):
    if not os.access(filepath, os.W_OK):
        os.chmod(filepath, 0o777)


def scan_for_dicom_files(directory):
    total_files = sum([len(files) for r, d, files in os.walk(directory)])
    dicom_files = []

    with tqdm(total=total_files, desc="Scanning for DICOM files", unit="file",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} files scanned") as pbar:
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                src_file = os.path.join(dirpath, f)
                if is_dicom_file(src_file):
                    dicom_files.append(src_file)
                pbar.update(1)

    return dicom_files


def copy_directory(source, destination, verbose=False, yes=False):
    """Copy only DICOM compliant files from source to destination with hierarchical paths based on DICOM tags and a
    progress bar."""
    if os.path.exists(destination):
        if not yes:
            print(f"Destination '{destination}' already exists.")
            choice = input("Choose an option: (a) Append new files - default, (d) Delete destination directory, (c) Cancel operation: ").strip().lower()
            if choice == 'd':
                confirm = input("All folders and files in the destination directory will be deleted, use with caution. Do you want to delete all contents? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    shutil.rmtree(destination)
                    if verbose:
                        print(f"Existing destination directory '{destination}' removed.")
                else:
                    print("Operation canceled.")
                    return False
            elif choice == 'c':
                print("Copy operation canceled.")
                return False
            elif choice == 'a':
                print("Appending to existing directory.")
            else:
                print("Invalid choice. Appending to existing directory by default.")
        else:
            shutil.rmtree(destination)
            if verbose:
                print(f"Existing destination directory '{destination}' removed.")

    os.makedirs(destination, exist_ok=True)

    # Scan for DICOM compliant files to copy
    dicom_files = scan_for_dicom_files(source)

    # Copy DICOM files with progress bar
    with tqdm(total=len(dicom_files), desc="Copying DICOM files", unit="file",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} DICOM files copied") as pbar:
        for src_file in dicom_files:
            patient_name, modality, study_description, study_date, series_number, instance_number, instance_uuid = get_dicom_tags(src_file)

            # Skip files with missing PatientName or Modality
            if patient_name == "Unknown" or modality == "Unknown":
                if verbose:
                    print(f"Skipping file {src_file}: Missing PatientName or Modality")
                logging.warning(f"Skipping file {src_file}: Missing PatientName or Modality")
                pbar.update(1)
                continue

            # Ensure all directory names are valid
            patient_name = sanitize_string(patient_name)
            modality = sanitize_string(modality)
            study_description = sanitize_string(study_description)
            study_date = sanitize_string(study_date)
            series_number = sanitize_string(series_number)
            instance_number = sanitize_string(instance_number)

            # Use InstanceUUID if available, otherwise generate a new UUID
            unique_id = str(instance_uuid) if instance_uuid else str(uuid.uuid4())
            unique_filename = f"{instance_number}_{unique_id}.dcm"

            dest_dir = os.path.join(destination, patient_name, f"{modality}_{study_description}_{study_date}",
                                    series_number)
            dest_file = os.path.join(dest_dir, unique_filename)

            # Skip file if it already exists
            if os.path.exists(dest_file):
                if verbose:
                    print(f"Skipping file {dest_file}: File already exists")
                logging.info(f"Skipping file {dest_file}: File already exists")
                pbar.update(1)
                continue

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            try:
                remove_read_only(src_file)  # Remove read-only attribute before copying
                shutil.copy2(src_file, dest_file)
            except PermissionError as e:
                if verbose:
                    print(f"PermissionError: {e}. Attempting to change permissions.")
                logging.error(f"PermissionError: {e}. Attempting to change permissions.")
                os.chmod(src_file, 0o777)
                shutil.copy2(src_file, dest_file)

            pbar.update(1)

    if verbose:
        print(f"Copied DICOM files from '{source}' to '{destination}'.")
    return True


def sanitize_string(value):
    return "".join([c if c.isalnum() else "_" for c in str(value)])
