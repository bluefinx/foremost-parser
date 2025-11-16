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

from typing import Optional, List

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
        int: 1 if insertion succeeded, -1 if an error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session is rolled back if insertion fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        session.add(duplicate_group)
        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing duplicate group. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1
    except ValueError as e:
        print("Something went wrong while storing duplicate group.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return -1

# create an association table entry for the duplicate group and image
def link_duplicate_group_to_image(file_hash: str, image_id: int, session: Session) -> int:
    """
    Links an existing DuplicateGroup to a specific Image.

    Args:
        file_hash (str): The hash identifying the DuplicateGroup.
        image_id (int): The ID of the Image to link.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int: 1 if linking succeeded, 0 if the group or image is invalid, -1 on DB error.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session is rolled back on failure.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

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
        print("Something went wrong while connecting image to duplicate group. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1
    except ValueError as e:
        print("Something went wrong while connecting image to duplicate group.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return -1

# create duplicate member
def insert_duplicate_member(file_hash: str, image_id: int, file_id: int, session: Session) -> int:
    """
    Inserts a DuplicateMember linking a File to a DuplicateGroup.

    Args:
        file_hash (str): Hash identifying the DuplicateGroup.
        image_id (int): ID of the Image the file belongs to.
        file_id (int): ID of the File to link.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int: 1 if insertion succeeded, 0 if input invalid or group not found, -1 on DB error.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session is rolled back on failure.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        if file_hash and image_id > 0:
            duplicate_group = read_duplicate_group_for_image_and_hash(session, file_hash, image_id)
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
    except ValueError as e:
        print("Something went wrong while storing duplicate member.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return -1

########################################################################
###################### READ ############################################
########################################################################

# read all duplicate groups
def read_duplicate_groups(session: Session) -> List[DuplicateGroup]:
    """
    Retrieves all DuplicateGroups from the database.

    Args:
       session (Session): SQLAlchemy session, must not be None.

    Returns:
       list[DuplicateGroup]: List of DuplicateGroup objects; empty list if error occurs.

    Raises:
       ValueError: If session is None.
       SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        return session.query(DuplicateGroup).all() #type: ignore
    except SQLAlchemyError as e:
        print("Something went wrong while reading duplicate groups.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return []
    except ValueError as e:
        print("Something went wrong while reading duplicate groups.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return []

# read duplicate group for image and specific hash
def read_duplicate_group_for_image_and_hash(session: Session, file_hash: str, image_id: int) -> Optional[DuplicateGroup]:
    """
    Retrieves the DuplicateGroup for a file hash linked to a specific image.

    Args:
        session (Session): SQLAlchemy session, must not be None.
        file_hash (str): SHA-256 hash of the file.
        image_id (int): ID of the image the group should be linked to.

    Returns:
        Optional[DuplicateGroup]: The DuplicateGroup if found; None otherwise.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

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
    except ValueError as e:
        print("Something went wrong while reading duplicate group for image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return None

# read duplicate groups for image
def read_duplicate_groups_for_image(session: Session, image_id: int) -> List[DuplicateGroup]:
    """
    Retrieves the DuplicateGroups for a specific image.

    Args:
        session (Session): SQLAlchemy session, must not be None.
        image_id (int): ID of the image the group should be linked to.

    Returns:
        Optional[List[DuplicateGroup]]: The DuplicateGroups if found; None otherwise.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        return (
            session.query(DuplicateGroup)
            .join(duplicate_group_image_association,
                  DuplicateGroup.id == duplicate_group_image_association.c.duplicate_group_id)
            .filter(
                duplicate_group_image_association.c.image_id == image_id #type: ignore
            ).all()
        )
    except SQLAlchemyError as e:
        print("Something went wrong while reading duplicate group for image.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return []
    except ValueError as e:
        print("Something went wrong while reading duplicate group for image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return []

# is there already a duplicate group for this hash that is connected to this image
def check_duplicate_group_for_image(session: Session, image_id: int, file_hash: str) -> tuple[bool, bool]:
    """
    Checks if a DuplicateGroup exists for a hash and whether it is linked to an image.

    Args:
        session (Session): SQLAlchemy session, must not be None.
        image_id (int): ID of the image.
        file_hash (str): Hash to check.

    Returns:
        tuple[bool, bool]:
            - exists: True if DuplicateGroup exists.
            - linked_to_image: True if group is linked to the image.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session rolled back on error.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

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
    except ValueError as e:
        print("SSomething went wrong while checking duplicate groups for image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return False, False

# get duplicate group for a file
def read_duplicate_group_by_file_id(file_id: int, session: Session) -> Optional[DuplicateGroup]:
    """
    Retrieves the DuplicateGroup for a given file ID.

    Args:
        file_id (int): ID of the file to check.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        Optional[DuplicateGroup]: The DuplicateGroup if found; None otherwise.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        duplicate_member = session.query(DuplicateMember).filter(DuplicateMember.file_id == file_id).first()
        if duplicate_member:
            return session.query(DuplicateGroup).filter(DuplicateGroup.id == duplicate_member.group_id).first()
        else: return None

    except SQLAlchemyError as e:
        print("Something went wrong while reading duplicate group for file.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None
    except ValueError as e:
        print("SSomething went wrong while checking duplicate groups for image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return None
