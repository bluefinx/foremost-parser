# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

import os
import shutil
import magic
import hashlib
import sys
import exiftool

from datetime import datetime
from dateutil import parser
from dateutil.parser import ParserError
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
# - timestamp_mod
# - timestamp_acc
# - timestamp_cre
# - timestamp_ino
# - is_duplicate
# - more_metadata

# read information from foremost's audit.txt file
filename = "audit.txt"

# run exiftool in batches to be able to isolate faulty files
batch_size = 500

# if exiftool could not be run for a file, store that file here
is_python = set()

#################################################
# parse files
#################################################

# delete all files and dirs
def delete_all_files(path):
    if os.path.exists(path) and os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                os.unlink(os.path.join(root, file))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

# delete all files for an image
def delete_files_in_image(image_id, path):
    dir_path = os.path.join(path, str(image_id))
    if os.path.isdir(dir_path):
        # my IDE suggested this so just going with this, sounds good
        shutil.rmtree(dir_path)

# run exiftool on the files to extract the metadata
def extract_exiftool_data(files, file_paths):
    # store the files of this subdir in a dict with "name":{subdict}
    subdir_files = {}
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
            print(f"Could not run exiftool as batch. Trying individually.", file=sys.stderr)
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
                    mime_yes = magic.Magic(mime=True)
                    mime_no = magic.Magic(mime=False)
                    file_dict = {
                        "File:FileName": Path(filepath).name,
                        # this is .bmp but exiftool return BMP so we need to change that
                        "File:FileTypeExtension": Path(filepath).suffix.lstrip('.').upper(),
                        "File:FileType": mime_no.from_file(filepath),
                        "File:MIMEType": mime_yes.from_file(filepath),
                        "File:FileSize": Path(filepath).stat().st_size,
                        "File:FileModifyDate": Path(filepath).stat().st_mtime,
                        "File:FileAccessDate": Path(filepath).stat().st_atime,
                        # so apparently that is the Inode Change Timestamp on Linux and the Creation Date Timestamp on Windows
                        # but that's why this file gets flagged as "no exiftool"
                        "File:FileCreateDate": Path(filepath).stat().st_ctime,
                    }
                    subdir_files[Path(filepath).name] = file_dict
                    is_python.add(Path(filepath).name)
    return subdir_files

# create the file objects to store in the database
def create_database_objects(subdir, subdir_files, image_id, table):
    # create list of file objects
    files = []
    for key, value in subdir_files.items():
        # create the file object
        file = File()
        file.image_id = image_id
        file.file_name = key
        file.file_type = value.get('File:FileType')
        file.file_extension = value.get('File:FileTypeExtension')
        file.file_mime_type = value.get('File:MIMEType')
        file.file_size = value.get('File:FileSize')
        file.file_offset = table[file.file_name].get('File Offset')
        file.foremost_comment = table[file.file_name].get('Comment')

        if file.file_name in is_python:
            file.is_exiftool = False
        else:
            file.is_exiftool = True

        # convert timestamps to write them to database
        # according to documentation, exiftool timestamps are: 2022:03:03 17:47:11-08:00
        # can convert with dateutil
        # convert timestamp to needed format first
        if file.is_exiftool:
            try:
                timestamp_mod = value.get('File:FileModifyDate')
                timestamp_acc = value.get('File:FileAccessDate')
                timestamp_cre = value.get('File:FileCreateDate')
                timestamp_ino = value.get('File:FileInodeChangeDate')

                if timestamp_mod is not None:
                    timestamp_mod = timestamp_mod.replace(":", "-", 2)
                    timestamp_mod = parser.parse(timestamp_mod)
                    file.timestamp_mod = timestamp_mod
                if timestamp_acc is not None:
                    timestamp_acc = timestamp_acc.replace(":", "-", 2)
                    timestamp_acc = parser.parse(timestamp_acc)
                    file.timestamp_acc = timestamp_acc
                if timestamp_cre is not None:
                    timestamp_cre = timestamp_cre.replace(":", "-", 2)
                    timestamp_cre = parser.parse(timestamp_cre)
                if timestamp_ino is not None:
                    timestamp_ino = timestamp_ino.replace(":", "-", 2)
                    timestamp_ino = parser.parse(timestamp_ino)
                    file.timestamp_ino = timestamp_ino

            except AttributeError:
                print(f"Could not convert Exiftool timestamps, skipping them.")
            except ParserError:
                print(f"Could not convert Exiftool timestamps, skipping them.")
        # the timestamps were extracted with python
        else:
            try:
                timestamp_mod = value.get('File:FileModifyDate')
                if timestamp_mod is not None:
                    file.timestamp_mod = datetime.fromtimestamp(timestamp_mod)
                timestamp_acc = value.get('File:FileAccessDate')
                if timestamp_acc is not None:
                    file.timestamp_acc = datetime.fromtimestamp(timestamp_acc)
                timestamp_cre = value.get('File:FileCreateDate')
                if timestamp_cre is not None:
                    file.timestamp_cre = datetime.fromtimestamp(timestamp_cre)
                timestamp_ino = value.get('File:FileInodeChangeDate')
                if timestamp_ino is not None:
                    file.timestamp_ino = datetime.fromtimestamp(timestamp_ino)

            except Exception as e:
                print(f"Could not convert Python timestamps, skipping them: {e}")


        # drop all of the metadata in more_metadata that we already have in file.* or don't need
        exclude = ['File:FileTypeExtension',
                   'SourceFile'
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
def hash_and_store(subdir, files, image_id, files_path):
    # use SHA-256 hash function
    sha256 = hashlib.sha256()
    # use 4096 byte chunks to read in file
    buffer = 4096

    for file in files:
        path = os.path.join(subdir.resolve(), file.file_name)
        with open(path, 'rb') as binary:
            while True:
                data = binary.read(buffer)
                if not data:
                    break
                sha256.update(data)
            file.file_hash = sha256.hexdigest()

            # store file in Docker container

            ## TODO a thought for when the tool is extended: https://stackoverflow.com/questions/16344454/where-is-better-to-store-uploaded-files-in-db-as-blob-or-in-folder-with-restrict

            # create, if not existing, image dir
            image_dir = os.path.join(files_path, str(image_id))
            os.makedirs(image_dir, exist_ok=True)
            # create file path
            file_path = os.path.join(image_dir, str(file.file_name))
            file.file_path = file_path
            # write file to /files
            with open(file_path, 'wb') as f:
                f.write(data)

# going through files per extension/subfolder because:
# if exiftool raises exception, there is no metadata for any file
# so running it on all files at once is not safe
# but running it for every file individually takes ages
# sort the sub folders for consistency
def parse_files(path, image_id, table, files_path):
    # adding this in case someone else also tries to remove some files
    # while the app is actively parsing through them
    # does not help much but at least it's crashing nicely
    try:
        for subdir in sorted(path.rglob('*')):
            if subdir.is_dir():

                print(f"Processing {subdir.name} files...")

                # get a list of files and the file paths
                files = [file for file in subdir.glob('*') if file.is_file()]
                file_paths = [str(file) for file in files]

                # run exiftool and store data for files
                subdir_files = extract_exiftool_data(files, file_paths)
                # create file objects for database
                file_objects = create_database_objects(subdir, subdir_files, image_id, table)
                # create the hashes and write the files to the persistent volume
                hash_and_store(subdir, file_objects, image_id, files_path)

                session = connect_database()
                if session is None:
                    raise Exception("Could not connect to the database")

                # store the files in the database
                if insert_files(file_objects, session) < 0:
                    # this means, something went wrong with the database transaction
                    # stop now, image is corrupt
                    return False

            else: continue

        return True
    except Exception as e:
        print(f"Something went wrong while parsing files: {e}")
        return False