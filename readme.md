# DICOM Sort Utility

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Description

This is commandline script, which can scan source directory for DICOM-compliant files, unzip all types of
archived files if proper argument is used, copy them to destination folder, decopress or compress uncompressed
Instead of copying it can send DICOM files from source folder to PACS using dcmsend utility from DCMTK toolkit
(tested on DCMTK v3.6.7 but should work on others).
For latter you need DCMTK downloaded, unzipped, and path to dcmtk/bin directory configured in dcmsort.conf
There you can also configure DICOM nodes.

Python version >= 3.10 (tested on 3.10.5 and 3.12.3)

To install virtual environment and requirements in it run install_venv.bat from its home (RECOMMENDED)
To run script within installed virtual environment run dcmsort.bat (it will pass commandline arguments to script)

To run dcmsort.py with system python dependencies (not recommended) you have to install requirements first:
pip install -r requirements.txt
then run
python dcmsort.py

## License

This project is licensed under the terms of the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Author

- **Andriy Yurtseniuk**
- **Email**: [yurtseniuk@gmail.com](mailto:yurtseniuk@gmail.com)
- **GitHub**: [mrroot](https://github.com/mrroot/dicom-sort)
