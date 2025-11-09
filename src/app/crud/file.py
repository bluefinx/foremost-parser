"""
file.py (CRUD)

Provides functions to insert and read File records in the database.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""
import sys

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
def insert_file(file: File, session: Session) -> int:
    """
    Stores a single File record in the database.

    Args:
        file (File): File object to store.
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        int: The ID of the inserted file or -1 if a database error occurred.

    Notes:
        Commits immediately after adding the file. Rolls back in case of errors.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        session.add(file)
        session.commit()
        return file.id
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing file. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1

# store a bulk of files
# (WARN: make sure session is not none when calling)
def insert_files(files: list[File], session: Session) -> int:
    """
    Stores multiple File records in bulk.

    Args:
        files (list[File]): List of File objects to store.
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        int: 1 if successful or -1 if a database error occurred.

    Notes:
        Commits once after adding all files. Rolls back in case of errors.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        session.add_all(files)
        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing files. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1

########################################################################
###################### READ ############################################
########################################################################

# read files for image
# (WARN: make sure session is not none when calling)
def read_files_for_image(image_id: int, session: Session) -> Optional[List[File]]:
    """
    Reads all File records associated with a given image ID.

    Args:
        image_id (int): ID of the image.
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        list[File] | None: List of File objects or None if an error occurred.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(File).filter(File.image_id == image_id).all() # type: ignore
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while reading files for image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None

# read the numbers of file per file_extension per image
# (WARN: make sure session is not none when calling)
def read_files_per_extension_for_image(image_id: int, session: Session):
    """
    Reads the number of files per file extension for a given image.

    Args:
        image_id (int): ID of the image.
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        list[tuple[str, int]] | None: List of tuples (file_extension, count) or None if an error occurred.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(File.file_extension, func.count(File.id).label('file_count')) \
            .filter(File.image_id == image_id) \
            .group_by(File.file_extension) \
            .all()
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while reading files per extension for image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None

# read all files with existing hashes
# (WARN: make sure session is not none when calling)
# (ATTENTION: gives back list of tuples with (id, hash))
def read_files_with_hash(session: Session) -> Optional[List[Tuple[int, str]]]:
    """
    Reads all files that have a non-null hash.

    Args:
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        list[tuple[int, str]] | None: List of tuples (file_id, file_hash) or None if an error occurred.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        rows = session.query(File.id, File.file_hash).filter(File.file_hash != None).all()
        return [(row.id, row.file_hash) for row in rows]
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while reading images with hashes. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None