"""
duplicate.py (CRUD)

Provides functions to insert and read duplicate file pairs in the database.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import sys

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
    """
    Stores duplicate file pairs in the database and updates each file's
    'is_duplicate' flag.

    Args:
        duplicates (set of tuple[int, int]): Set of tuples containing (file_id, duplicate_id)
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        int: -1 if a database error occurred, otherwise 1.

    Notes:
        Commits after each duplicate insertion. Rolls back in case of errors.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        # store the tuple as duplicate
        # update every file's is_duplicate
        for idx, (file_id, duplicate_id) in enumerate(duplicates, 1):
            duplicate_obj = Duplicate(file_id=file_id, duplicate_id=duplicate_id)
            session.add(duplicate_obj)

            # update flags
            file = session.query(File).get(file_id)
            if file:
                file.is_duplicate = True
            duplicate = session.query(File).get(duplicate_id)
            if duplicate:
                duplicate.is_duplicate = True

            # batch commit
            if idx % 1000 == 0:
                session.commit()

        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while overwriting image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1

########################################################################
###################### READ ############################################
########################################################################

# read all files that are stored in duplicate table
# (WARN: make sure session is not none when calling)
def read_duplicates(file_ids: list, session: Session):
    """
    Reads all duplicate file pairs for the given file IDs from the database.

    Args:
        file_ids (list[int]): List of file IDs to check for duplicates.
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        set[tuple[File, File]] | None: Set of tuples containing duplicate File objects,
        or None if a database error occurred.

    Notes:
        Each pair is stored only once in the returned set, regardless of order.
    """
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
        print("Something went wrong while reading duplicates. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None