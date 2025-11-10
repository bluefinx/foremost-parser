"""
duplicate.py (CRUD)

Provides CRUD functions to manage duplicate files in the database.

This module includes functions to:
- Detect and insert duplicate groups based on file hashes.
- Link duplicate groups to images via an association table.
- Insert and read duplicate members linking individual files to their groups.
- Query existing duplicate groups for specific images or globally.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import sys

from typing import Optional

from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.duplicate import DuplicateGroup, DuplicateMember, duplicate_group_image_association

from app.crud.image import read_image

########################################################################
###################### WRITE ###########################################
########################################################################

# create duplicate group
def insert_duplicate_group(duplicate_group: DuplicateGroup, session: Session) -> int:
    """
    Inserts a new DuplicateGroup into the database.

    Args:
        duplicate_group (DuplicateGroup): The DuplicateGroup object to store.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int: 1 if the group was successfully inserted, -1 if a database error occurred.

    Notes:
        - Rolls back the session automatically if a SQLAlchemyError occurs.
        - Does not check for existing groups; attempting to insert a duplicate
          primary key or unique file_hash will raise an exception that is handled with an error message.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        session.add(duplicate_group)
        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing duplicate group. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1

def link_duplicate_group_to_image(file_hash: str, image_id: int, session: Session) -> int:
    """
    Links an existing DuplicateGroup to a specific Image by creating an entry
    in the association table.

    Args:
        file_hash (str): The hash identifying the DuplicateGroup.
        image_id (int): The ID of the Image to link.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int:
            1 if the DuplicateGroup was successfully linked to the Image.
            0 if the DuplicateGroup does not exist or the image ID is invalid.
            -1 if a database error occurred during the operation.

    Notes:
        - Rolls back the session automatically if a SQLAlchemyError occurs.
        - If the DuplicateGroup is already linked to the Image, no duplicate
          entry is created.
        - Logs errors to stderr when the group does not exist or the image ID
          is invalid.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        if image_id > 0 and file_hash:
            image = read_image(image_id, session)
            duplicate_group = session.query(DuplicateGroup).filter(DuplicateGroup.file_hash == file_hash).first()
            if not duplicate_group:
                print(f"Error in duplicate check for hash: {file_hash} (duplicate group not found)", file=sys.stderr)
                return 0
            if image and image not in duplicate_group.images:
                duplicate_group.images.append(image)
            session.commit()
            return 1
        else:
            print(f"Error in duplicate check for hash: {file_hash} (invalid image id)", file=sys.stderr)
            return 0
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while connection image to duplicate group. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1

# create duplicate member
def insert_duplicate_member(file_hash: str, image_id: int, file_id: int, session: Session) -> int:
    """
    Inserts a DuplicateMember entry linking a File to its DuplicateGroup.

    Args:
        file_hash (str): Hash identifying the DuplicateGroup.
        image_id (int): ID of the Image the file belongs to.
        file_id (int): ID of the File to link to the DuplicateGroup.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int:
            1 if the DuplicateMember was successfully created.
            0 if the DuplicateGroup does not exist or input parameters are invalid.
            -1 if a database error occurred during the operation.

    Notes:
        - Looks up the DuplicateGroup for the given file_hash and image_id.
        - Commits the session after adding the DuplicateMember.
        - Rolls back the session automatically if a SQLAlchemyError occurs.
        - Logs errors to stderr if the group does not exist or parameters are invalid.
        - Each file is linked to exactly one DuplicateGroup.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        if file_hash and image_id > 0:
            duplicate_group = read_duplicate_group_for_image(session, file_hash, image_id)
            if duplicate_group:
                session.add(DuplicateMember(group_id=duplicate_group.id, file_id=file_id))
                session.commit()
                return 1
            print(f"Error while storing duplicate member. Skipping file {file_id}", file=sys.stderr)
            return 0
        else:
            print(f"Error while storing duplicate member. Skipping file {file_id}", file=sys.stderr)
            return 0
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing duplicate member. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1

########################################################################
###################### READ ############################################
########################################################################

# read all duplicate groups
def read_duplicate_groups(session: Session) -> list[DuplicateGroup]:
    """
    Retrieves all DuplicateGroup entries from the database.

    Args:
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        list[DuplicateGroup]: A list of all DuplicateGroup objects.
            Returns an empty list if a database error occurs.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(DuplicateGroup).all() #type: ignore
    except SQLAlchemyError as e:
        print("Something went wrong while reading duplicate groups.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return []

# read duplicate groups for image
def read_duplicate_group_for_image(session: Session, file_hash: str, image_id: int) -> Optional[DuplicateGroup]:
    """
    Retrieves the DuplicateGroup for a specific file hash that is linked to a given image.

    Args:
        session (Session): SQLAlchemy session, must not be None.
        file_hash (str): SHA-256 hash of the file to search for.
        image_id (int): ID of the image to which the duplicate group should be linked.

    Returns:
        Optional[DuplicateGroup]: The DuplicateGroup object if found and linked to the image.
            Returns None if no such group exists or in case of a database error.

    Notes:
        - Uses a join on the association table between DuplicateGroup and Image.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return (
            session.query(DuplicateGroup)
            .join(duplicate_group_image_association,
                  DuplicateGroup.id == duplicate_group_image_association.c.duplicate_group_id)
            .filter(
                DuplicateGroup.file_hash == file_hash,
                duplicate_group_image_association.c.image_id == image_id #type: ignore
            ).first()
        )
    except SQLAlchemyError as e:
        print("Something went wrong while reading duplicate group for image.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None

# is there already a duplicate group for this hash that is connected to this image
def check_duplicate_group_for_image(session: Session, image_id: int, file_hash: str) -> tuple[bool, bool]:
    """
    Checks if a duplicate group exists for a given hash and if it is linked
    to a specific image.

    Args:
        session (Session): SQLAlchemy session.
        image_id (int): ID of the image.
        file_hash (str): Hash to check.

    Returns:
        tuple:
            exists (bool): True if a DuplicateGroup with the hash exists.
            linked_to_image (bool): True if the group is already linked to the image.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        # check if the group exists
        if session.query(exists().where(DuplicateGroup.file_hash == file_hash)).scalar():
            # check if the group is linked to this image
            if session.query(
                exists()
                .where(DuplicateGroup.file_hash == file_hash)
                .where(duplicate_group_image_association.c.image_id == image_id) #type: ignore
                .join(duplicate_group_image_association,
                      DuplicateGroup.id == duplicate_group_image_association.c.duplicate_group_id)
            ).scalar(): return True, True
            else: return True, False
        else:
            return False, False
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while checking duplicate groups for image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return False, False