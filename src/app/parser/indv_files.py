"""
indv_files.py

This module provides functionality to process individual files from a Foremost output directory
and store them in a database, along with optional copying of image files to a persistent output
directory organised by file extension.

Main features:
- Extracts file metadata using ExifTool, with a Python fallback for problematic files.
- Creates SQLAlchemy File objects with metadata suitable for database storage.
- Computes SHA-256 hashes for each file.
- Copies image files (jpg, jpeg, png, gif, webp, svg) to an output directory structured by extension.
- Handles batch processing and per-file fallback for reliability.
- Supports database insertion of File objects while gracefully handling exceptions.

Key functions:
- `extract_exiftool_data(files, file_paths, is_python)`:
    Extracts metadata from a list of files using ExifTool in batches, with Python fallback.

- `create_database_objects(subdir_files, image_id, audit_table, is_python)`:
    Creates SQLAlchemy File objects from metadata and audit table information.

- `hash_and_store(subdir, files, image_name, output_path)`:
    Computes SHA-256 hashes and optionally copies image files to output directory organised by extension.

- `parse_files(input_path, output_path, image_id, audit_table, image_name)`:
    Iterates through all subdirectories of a Foremost output folder, extracts metadata,
    creates File objects, computes hashes, copies image files, and stores data in the database.

Notes:
- Only files with extensions jpg, jpeg, png, gif, webp and svg are copied to the output directory and only if the CLI parameter is set.
- Files are read in 4096-byte chunks for memory-efficient hashing and copying.
- Tracks files that required Python-based metadata extraction.
- Relies on helper modules: `magic` and `exiftool`.
- Designed to handle large directories with many files while minimising the risk of crashes
  due to problematic files or ExifTool failures.
"""

import os
import magic
import hashlib
import sys
import exiftool

from pathlib import Path
from exiftool.exceptions import ExifToolExecuteError

from app.db import connect_database
from app.models.file import File
from app.crud.file import insert_files

# Need the following for the database:
# - image_id
# - file_name
# - file_extension
# - file_mime
# - file_size
# - file_offset
# - file_path
# - file_hash
# - is_duplicate
# - more_metadata

# read information from foremost's audit.txt file
filename = "audit.txt"

# run exiftool in batches to be able to isolate faulty files
batch_size = 500

#################################################
# parse files
#################################################

# run exiftool on the files to extract the metadata
def extract_exiftool_data(files: list[Path], file_paths: list[str], is_python: set) -> tuple[dict, set]:
    """
    Extracts metadata from a list of files using ExifTool in batches, with a Python fallback for problematic files.

    This function processes files in batches (default 500) to efficiently extract metadata. If a batch fails,
    it retries each file individually with ExifTool. If a single file still fails, it extracts basic metadata
    (filename, extension, MIME type, file type, file size) using Python and the `magic` library.

    Args:
        files (list[Path]): List of Path objects representing files to process.
        file_paths (list[str]): List of file paths corresponding to `files`.
        is_python (set): Set to store filenames for which Python fallback was used.

    Returns:
        tuple:
            dict: Dictionary mapping each filename to a metadata dictionary. Each metadata dictionary may
                  include keys like 'File:FileName', 'File:FileTypeExtension', 'File:FileType',
                  'File:MIMEType', and 'File:FileSize'.
            set: Updated `is_python` set with filenames that required Python fallback.

    Notes:
        - Relies on `exiftool.ExifToolHelper` and `magic.Magic`.
        - Handles batch and individual ExifTool failures gracefully.
    """

    # store the files of this subdir in a dict with "name":{subdict}
    subdir_files = {}

    # initialize magic once for fallback
    mime_yes = magic.Magic(mime=True)
    mime_no = magic.Magic(mime=False)

    # run exiftool in batches
    ## based on https://stackoverflow.com/questions/41868890/how-to-loop-through-a-python-list-in-batch
    for i in range(0, len(file_paths), batch_size):
        batch = files[i:i + batch_size]
        try:
            ## based on https://sylikc.github.io/pyexiftool/examples.html
            with exiftool.ExifToolHelper() as ex:
                for file in ex.get_metadata(batch):
                    subdir_files[file['File:FileName']] = file
        # if one file fails, exiftool fails for whole batch, so try to run it individually
        # and extract the faulty file
        except ExifToolExecuteError:
            print("Could not run exiftool as batch. Trying individually.")
            for filepath in batch:
                try:
                    with exiftool.ExifToolHelper() as ex:
                        # this is for PyCharm, not so charmy actually, sometimes very stupidy
                        # noinspection PyTypeChecker
                        file_metadata = ex.get_metadata(filepath)
                        for file in file_metadata:
                            subdir_files[file['File:FileName']] = file
                except ExifToolExecuteError:
                    # this is the faulty file, extract metadata with python instead
                    print(f"Could not run exiftool on file {Path(filepath).parts[-2:]}. "
                          f"Extracting metadata with Python.", file=sys.stderr)

                    file_dict = {
                        "File:FileName": Path(filepath).name,
                        # this is .bmp but exiftool returns BMP so we need to change that
                        "File:FileTypeExtension": Path(filepath).suffix.lstrip('.').upper(),
                        "File:FileType": mime_no.from_file(filepath),
                        "File:MIMEType": mime_yes.from_file(filepath),
                        "File:FileSize": Path(filepath).stat().st_size
                    }
                    subdir_files[Path(filepath).name] = file_dict
                    is_python.add(Path(filepath).name)
    return subdir_files, is_python

# create the file objects to store in the database
def create_database_objects(subdir_files: dict, image_id: int, audit_table: dict, is_python: set) -> list[File]:
    """
    Creates SQLAlchemy File objects from extracted metadata to store in the database.

    Args:
        subdir_files (dict): Dictionary mapping filenames to metadata dictionaries
                             (as returned by `extract_exiftool_data`).
        image_id (int): ID of the parent Image record in the database.
        audit_table (dict): Dictionary with additional file info (size, offset, comment)
                            parsed from the foremost audit table.
        is_python (set): Set of filenames for which metadata was extracted via Python fallback.

    Returns:
        list[File]: List of File ORM objects ready to be inserted into the database.

    Notes:
        - Marks `is_exiftool` False for files that used Python fallback, True otherwise.
        - Strips metadata keys from `more_metadata` that are already stored in dedicated columns
          to avoid redundancy.
    """
    # create list of file objects
    files = []
    for key, value in subdir_files.items():
        # create the file object
        file = File()
        file.image_id = image_id
        file.file_name = key
        file.file_type = value.get('File:FileType')
        file.file_extension = value.get('File:FileTypeExtension')
        file.file_mime = value.get('File:MIMEType')
        file.file_size = value.get('File:FileSize')

        audit_info = audit_table.get(file.file_name, {})
        file.file_offset = audit_info.get('File Offset')
        file.foremost_comment = audit_info.get('Comment')

        if file.file_name in is_python:
            file.is_exiftool = False
        else:
            file.is_exiftool = True

        # drop all of the metadata in more_metadata that we already have in file.* or don't need
        exclude = ['File:FileTypeExtension',
                   'SourceFile',
                   'File:FileType',
                   'File:MIMEType',
                   'File:FileSize',
                   'File:FileModifyDate',
                   'File:FileAccessDate',
                   'File:FileCreateDate',
                   'File:FileInodeChangeDate',
                   'File:FileName',
                   'ExifTool:ExifToolVersion',
                   'File:Directory'
                   ]

        file.more_metadata = subdir_files[file.file_name]
        for pop in exclude:
            file.more_metadata.pop(pop, None)

        files.append(file)
    return files

# create the hash and store the file in the Docker volume
def hash_and_store(subdir: Path, files: list[File], image_name: str, output_path: Path, copy_images: bool):
    """
    Computes SHA-256 hashes for a list of files and copies image files to an output directory
    organised by file extension.

    Each file in `files` will have its SHA-256 hash calculated and stored in `file.file_hash`.
    If the file is an image (jpg, jpeg, png, gif, webp, svg), it is copied into a subdirectory
    under `output_path` named after the image and grouped by its extension. The path to the copied
    file is stored in `file.file_path`.

    Args:
        subdir (Path): Path to the folder containing the original files.
        files (list[File]): List of File objects to process.
        image_name (str): Name of the image, used to create the output subdirectory.
        output_path (Path): Base path where image files will be copied.
        copy_images (bool): Whether or not to copy image files into subdirectory under `output_path`.

    Notes:
        - Only files with extensions jpg, jpeg, png, gif, webp, svg are copied.
        - Reads files in 4096-byte chunks to handle large files efficiently.
        - Updates each File object with `file_hash` and `file_path`.
    """
    # use 4096 byte chunks to read in file
    buffer = 4096

    # image files that are copied to output directory
    image_extensions = {"jpg", "jpeg", "png", "gif", "webp", "svg"}

    for file in files:
        # use SHA-256 hash function
        sha256 = hashlib.sha256()  # type: ignore[attr-defined]

        path = os.path.join(subdir.resolve(), file.file_name)
        with open(path, 'rb') as binary:
            while True:
                data = binary.read(buffer)
                if not data:
                    break
                sha256.update(data)
            file.file_hash = sha256.hexdigest()

            # store images files (jpg, jpeg, png, gif, webp, svg) in output directory
            if copy_images:
                ext = file.file_extension.lower()
                if ext in image_extensions:
                    # create a dir for every extension
                    ext_dir = os.path.join(output_path, image_name, str(ext))
                    os.makedirs(ext_dir, exist_ok=True)
                    # create file path
                    output_file_path = os.path.join(ext_dir, str(file.file_name))
                    file.file_path = str(output_file_path)
                    with open(path, "rb") as src, open(output_file_path, "wb") as dst:
                        while True:
                            chunk = src.read(buffer)
                            if not chunk:
                                break
                            dst.write(chunk)
            else:
                file.file_path = None

# going through files per extension/subfolder because:
# if exiftool raises exception, there is no metadata for any file
# so running it on all files at once is not safe
# but running it for every file individually takes ages
def parse_files(input_path: Path, output_path: Path, image_id: int, audit_table: dict, image_name: str, copy_images: bool) -> bool:
    """
    Processes files in the Foremost output directory to extract metadata, create database objects,
    compute hashes and copy image files to the output directory.

    This function iterates over all subdirectories of `input_path` in sorted order for consistency. For each subdirectory:
      1. Lists all files.
      2. Extracts metadata using ExifTool in batches, falling back to Python methods for problematic files.
      3. Creates SQLAlchemy File objects for the database.
      4. Computes SHA-256 hashes and copies image files (jpg, jpeg, png, gif, webp, svg) to
         `output_path/<image_name>/<extension>/`.
      5. Inserts File objects into the database.

    Args:
        input_path (Path): Root path of the Foremost output directory containing files and subfolders.
        output_path (Path): Base directory where image files will be copied by extension.
        image_id (int): ID of the parent Image record in the database.
        audit_table (dict): Dictionary containing additional file metadata parsed from `audit.txt`.
        image_name (str): Name of the image, used to create the output subdirectory.
        copy_images (bool): Whether or not to copy image files into subdirectory under `output_path`.

    Returns:
        bool: True if all files were processed successfully, False if an exception occurred.

    Notes:
        - Uses `extract_exiftool_data()`, `create_database_objects()`, `hash_and_store()` and `insert_files()`.
        - If any database operation fails, the function raises an exception internally and returns False.
        - Files are read in 4096-byte chunks for efficient hashing.
        - The `is_python` set tracks files where Python fallback was used instead of ExifTool.
    """
    # adding this in case someone else also tries to remove some files
    # while the app is actively parsing through them
    # does not help much but at least it's crashing nicely
    try:
        for subdir in sorted(input_path.rglob('*')):
            if subdir.is_dir():

                print(f"Processing {subdir.name} files...")

                # get a list of files and the file paths
                files = [file for file in subdir.glob('*') if file.is_file()]
                file_paths = [str(file) for file in files]

                # if exiftool could not be run for a file, store that file here
                is_python = set()

                # run exiftool and store data for files
                subdir_files, is_python = extract_exiftool_data(files, file_paths, is_python)

                # create file objects for database
                file_objects = create_database_objects(subdir_files, image_id, audit_table, is_python)

                # create the hashes and write the files to the persistent volume
                hash_and_store(subdir, file_objects, image_name, output_path, copy_images)

                session = connect_database()
                if session is None:
                    raise Exception("Could not connect to the database")

                # store the files in the database
                if insert_files(file_objects, session) < 0:
                    # this means, something went wrong with the database transaction
                    # stop now, image is corrupt
                    raise Exception("Something went wrong while inserting files")

        return True
    except Exception as e:
        print(f"Something went wrong while parsing files: {e}", file=sys.stderr)
        return False