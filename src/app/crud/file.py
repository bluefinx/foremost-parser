# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

# this file contains the database interactions for files

from typing import List, Tuple, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.file import File

########################################################################
###################### WRITE ###########################################
########################################################################

# store file row
# (WARN: make sure session is not none when calling)
def insert_file(file: File, session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        session.add(file)
        session.commit()
        return file.id
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while storing file. Rolling back.")
        print(f"Detailed DB error: {e}")
        return -1

# store a bulk of files
# (WARN: make sure session is not none when calling)
def insert_files(files: list[File], session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        session.add_all(files)
        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while storing files. Rolling back.")
        print(f"Detailed DB error: {e}")
        return -1

########################################################################
###################### READ ############################################
########################################################################

# read files for image
# (WARN: make sure session is not none when calling)
def read_files_for_image(image_id: int, session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(File).filter(File.image_id == image_id).all()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while reading files for image. Rolling back.")
        print(f"Detailed DB error: {e}")
        return None

# read the numbers of file per file_extension per image
# (WARN: make sure session is not none when calling)
def read_files_per_extension_for_image(image_id: int, session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(File.file_extension, func.count(File.id).label('file_count')) \
            .filter(File.image_id == image_id) \
            .group_by(File.file_extension) \
            .all()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while reading files per extension for image. Rolling back.")
        print(f"Detailed DB error: {e}")
        return None

# read all files with existing hashes
# (WARN: make sure session is not none when calling)
# (ATTENTION: gives back list of tuples with (id, hash))
def read_files_with_hash(session: Session) -> Optional[List[Tuple[int, str]]]:
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        rows = session.query(File.id, File.file_hash).filter(File.file_hash != None).all()
        return [(row.id, row.file_hash) for row in rows]
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while reading images with hashes. Rolling back.")
        print(f"Detailed DB error: {e}")
        return None