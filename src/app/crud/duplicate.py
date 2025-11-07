# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

# this file contains the database interactions for duplicates

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.duplicate import Duplicate
from app.models.file import File

########################################################################
###################### WRITE ###########################################
########################################################################

# store the duplicates
# (WARN: make sure session is not none when calling)
def insert_duplicates(duplicates: set, session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        # store the tuple as duplicate
        # update every file's is_duplicate
        for file_id, duplicate_id in duplicates:
            duplicate_obj = Duplicate()
            duplicate_obj.file_id = file_id
            duplicate_obj.duplicate_id = duplicate_id

            session.add(duplicate_obj)

            file = session.query(File).get(file_id)
            if file is not None:
                file.is_duplicate = True
            duplicate = session.query(File).get(duplicate_id)
            if duplicate is not None:
                duplicate.is_duplicate = True

            session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while overwriting image. Rolling back.")
        print(f"Detailed DB error: {e}")
        return -1

########################################################################
###################### READ ############################################
########################################################################

# read all files that are stored in duplicate table
# (WARN: make sure session is not none when calling)
def read_duplicates(file_ids: list, session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        duplicate_files = set()
        for duplicate in session.query(Duplicate).filter(
                or_(
                    Duplicate.file_id.in_(file_ids),
                    Duplicate.duplicate_id.in_(file_ids),
                )
        ).all():
            file_one = session.query(File).filter(File.id == duplicate.file_id).first()
            file_two = session.query(File).filter(File.id == duplicate.duplicate_id).first()
            file_tuple = (file_one, file_two)
            if file_tuple not in duplicate_files:
                duplicate_files.add(file_tuple)
        return duplicate_files
    except SQLAlchemyError as e:
        print(f"Something went wrong while reading duplicates. Rolling back.")
        print(f"Detailed DB error: {e}")
        return None