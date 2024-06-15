import os
import sys
import pydicom
from pydicom.uid import RLELossless, ExplicitVRLittleEndian
import logging
import subprocess
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    filename='dcmsort.log',
    level=logging.DEBUG,  # Change to DEBUG level to capture more details
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filemode='w'  # Overwrite the log file on each run
)


def decompress_and_prepare(ds):
    """ Decompress and prepare the dataset for recompression """
    ds.decompress()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    if 'PhotometricInterpretation' not in ds:
        ds.PhotometricInterpretation = 'MONOCHROME2'
    return ds


def send_dicom_files(directory, alias, config, verbose=False):
    try:
        # Get DCMTK bin path
        dcmtk_bin_path = config.get('DEFAULT', 'dcmtk_bin_path', fallback=None)
        if not dcmtk_bin_path:
            raise ValueError("DCMTK bin path not specified in the configuration file.")

        dcmsend_exe = os.path.join(dcmtk_bin_path, 'dcmsend.exe')

        # Get DICOM node information
        if alias not in config['DEFAULT']:
            raise ValueError(f"Alias '{alias}' not found in the configuration file.")

        node_info = config['DEFAULT'][alias].strip().split(',')
        if len(node_info) != 3:
            raise ValueError(f"Invalid configuration for alias '{alias}'. Expected format: AE_TITLE,HOST,PORT")

        ae_title = node_info[0].strip()
        host = node_info[1].strip()
        port = int(node_info[2].strip())

        # Build the dcmsend command
        command = [
            dcmsend_exe, host, str(port),
            '-aec', ae_title,
            '-aet', config['DEFAULT'].get('own', 'DCMSEND'),
            '--scan-directories', '--recurse', directory
        ]

        if verbose:
            command.append('--verbose')
            print(f"Executing command: {' '.join(command)}")

        # Execute the command and capture the output
        result = subprocess.run(command, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)
            logging.info(result.stdout)

        if result.stderr:
            print(result.stderr, file=sys.stderr)
            logging.error(result.stderr)

        if result.returncode != 0:
            raise RuntimeError(f"dcmsend failed with return code {result.returncode}: {result.stderr}")

        logging.info(f"DICOM files sent successfully using alias '{alias}'")

    except Exception as e:
        if verbose:
            print(f"Failed to send DICOM files: {e}")
        logging.error(f"Failed to send DICOM files: {e}")
def ensure_pixel_data_length(ds):
    """ Ensure the pixel data has the correct length """
    rows = ds.Rows
    cols = ds.Columns
    samples_per_pixel = ds.SamplesPerPixel if 'SamplesPerPixel' in ds else 1
    bits_allocated = ds.BitsAllocated if 'BitsAllocated' in ds else 8
    expected_length = rows * cols * samples_per_pixel * (bits_allocated // 8)

    actual_length = len(ds.PixelData)

    if actual_length != expected_length:
        raise ValueError(f"Pixel data length mismatch: expected {expected_length} bytes, got {actual_length} bytes")

    return ds.PixelData


def compress_dicom_files(directory, verbose=False):
    dicom_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.dcm'):
                dicom_files.append(os.path.join(root, file))

    with tqdm(total=len(dicom_files), desc="Compressing DICOM files", unit="file",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} DICOM files compressed") as pbar:
        for filepath in dicom_files:
            try:
                ds = pydicom.dcmread(filepath)
                ds = decompress_and_prepare(ds)
                ds.compress(pydicom.uid.RLELossless)
                ds.save_as(filepath)
                if verbose:
                    print(f"Compressed {filepath}")
                logging.info(f"Compressed {filepath}")
            except Exception as e:
                if verbose:
                    print(f"Failed to compress {filepath}: {e}")
                logging.error(f"Failed to compress {filepath}: {e}")
            pbar.update(1)

    if verbose:
        print(f"Compressed {len(dicom_files)} DICOM files.")
    logging.info(f"Compressed {len(dicom_files)} DICOM files.")


def decompress_dicom_files(directory, verbose=False):
    dicom_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.dcm'):
                dicom_files.append(os.path.join(root, file))

    with tqdm(total=len(dicom_files), desc="Decompressing DICOM files", unit="file",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} DICOM files decompressed") as pbar:
        for filepath in dicom_files:
            try:
                ds = pydicom.dcmread(filepath)
                if ds.file_meta.TransferSyntaxUID.is_compressed:
                    ds.decompress()
                    ds.save_as(filepath)
                    if verbose:
                        print(f"Decompressed {filepath}")
                    logging.info(f"Decompressed {filepath}")
                else:
                    if verbose:
                        print(f"File {filepath} is already uncompressed")
                    logging.info(f"File {filepath} is already uncompressed")
            except Exception as e:
                if verbose:
                    print(f"Failed to decompress {filepath}: {e}")
                logging.error(f"Failed to decompress {filepath}: {e}")
            pbar.update(1)

    if verbose:
        print(f"Decompressed {len(dicom_files)} DICOM files.")
    logging.info(f"Decompressed {len(dicom_files)} DICOM files.")