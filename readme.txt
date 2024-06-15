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

