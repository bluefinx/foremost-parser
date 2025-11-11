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

from app.models.file import File, FileHash

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

    Returns:
        int: The ID of the inserted file, or -1 if a database error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session rolled back on failure.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        session.add(file)
        session.commit()
        return file.id
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing file. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1
    except ValueError as e:
        session.rollback()
        print("Something went wrong while storing file. Rolling back.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return -1

# store a bulk of files
# (WARN: make sure session is not none when calling)
def insert_files(files: list[File], session: Session) -> int:
    """
    Stores multiple File records in bulk and creates corresponding FileHash entries.

    Args:
        files (list[File]): List of File objects to store.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int: 1 if successful, or -1 if a database error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session rolled back on failure.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        session.add_all(files)
        session.flush()

        # create FileHash entries
        file_hashes = [
            FileHash(file_id=f.id, file_hash=f.file_hash, image_id=f.image_id)
            for f in files if f.file_hash
        ]
        if file_hashes:
            session.add_all(file_hashes)

        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing files. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1
    except ValueError as e:
        session.rollback()
        print("Something went wrong while storing files. Rolling back.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return -1

########################################################################
###################### READ ############################################
########################################################################

# read files for image
# (WARN: make sure session is not none when calling)
def read_files_for_image(image_id: int, session: Session) -> Optional[List[File]]:
    """
    Retrieves all File records associated with a given image ID.

    Args:
        image_id (int): ID of the image.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        Optional[List[File]]: List of File objects, or None if an error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        return session.query(File).filter(File.image_id == image_id).all() # type: ignore
    except SQLAlchemyError as e:
        print("Something went wrong while reading files for image.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None
    except ValueError as e:
        print("Something went wrong while reading files for image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return None

# read the numbers of file per file_extension per image
# (WARN: make sure session is not none when calling)
def read_files_per_extension_for_image(image_id: int, session: Session) -> Optional[List[Tuple[int, str]]]:
    """
    Retrieves the number of files per file extension for a given image.

    Args:
        image_id (int): ID of the image.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        Optional[List[Tuple[str, int]]]: List of tuples (file_extension, count), or None if an error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        results = session.query(File.file_extension, func.count(File.id).label('file_count')) \
            .filter(File.image_id == image_id) \
            .group_by(File.file_extension) \
            .all()
        return [(row.file_extension, row.file_count) for row in results]
    except SQLAlchemyError as e:
        print("Something went wrong while reading files per extension for image.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None
    except ValueError as e:
        print("Something went wrong while reading files per extension for image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return None

# read all files with existing hashes
# (WARN: make sure session is not none when calling)
# (ATTENTION: gives back list of tuples with (id, hash))
def read_files_with_hash(session: Session) -> Optional[List[Tuple[int, str]]]:
    """
    Retrieves all files that have a non-null hash.

    Args:
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        Optional[List[Tuple[int, str]]]: List of tuples (file_id, file_hash), or None if an error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        rows = session.query(File.id, File.file_hash).filter(File.file_hash != None).all()
        return [(row.id, row.file_hash) for row in rows]
    except SQLAlchemyError as e:
        print("Something went wrong while reading images with hashes.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None
    except ValueError as e:
        print("Something went wrong while reading images with hashes.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return None

# read the file hashes for a specific image
def read_file_hashes_for_image(image_id: int, session: Session) -> List[FileHash]:
    """
    Retrieves all FileHash entries associated with a specific image.

    Args:
        image_id (int): ID of the image.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        List[FileHash]: List of FileHash objects, or empty list if an error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        hashes = session.query(FileHash).filter(FileHash.image_id == image_id).all()
        return hashes # type: ignore
    except SQLAlchemyError as e:
        print("Something went wrong while reading hashes for image.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return []
    except ValueError as e:
        print("Something went wrong while reading hashes for image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return []

# read all file hashes
def read_file_hashes(session: Session) -> List[FileHash]:
    """
    Retrieves all FileHash entries from the database.

    Args:
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        List[FileHash]: List of all FileHash objects, or empty list if an error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        return session.query(FileHash).all() # type: ignore
    except SQLAlchemyError as e:
        print("Something went wrong while reading hashes.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return []
    except ValueError as e:
        print("Something went wrong while reading hashes.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return []