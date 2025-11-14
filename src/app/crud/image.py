"""
image.py (CRUD)

Provides functions to insert, update, delete and read Image records in the database
as well as to update per-image file statistics.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import sys

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.image import Image
from app.models.duplicate import DuplicateGroup, DuplicateMember

########################################################################
###################### WRITE ###########################################
########################################################################

# store image row
# (WARN: make sure session is not none when calling)
def insert_image(image: Image, session: Session) -> int:
    """
    Stores a single Image record in the database.

    Args:
        image (Image): The Image object to store.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int: The ID of the inserted Image or -1 if a database error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session rolled back on failure.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        session.add(image)
        session.commit()
        return image.id
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1
    except ValueError as e:
        session.rollback()
        print("Something went wrong while storing image. Rolling back.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return -1

# delete image
# (WARN: make sure session is not none when calling)
def delete_image(image_id: int, session: Session) -> int:
    """
    Deletes an Image along with its associated Files and Duplicate entries via CASCADE.

    Args:
        image_id (int): The ID of the Image object to delete.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        int: 1 if successful or -1 if a database error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr and session rolled back on failure.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        image = session.get(Image, image_id)
        if image is None:
            print(f"No image found with id {image_id}", file=sys.stderr)
            return -1
        # files and duplicates are automatically deleted through relationships and cascade
        session.delete(image)

        # delete empty duplicate groups
        empty_groups = session.query(DuplicateGroup) \
            .outerjoin(DuplicateMember) \
            .filter(DuplicateMember.file_id == None) \
            .all()

        for group in empty_groups:
            session.delete(group)

        session.commit()
        return 1

    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while deleting image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1
    except ValueError as e:
        session.rollback()
        print("Something went wrong while deleting image. Rolling back.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return -1

########################################################################
###################### READ ############################################
########################################################################

# get the image by ID
# (WARN: make sure session is not none when calling)
def read_image(image_id: int, session: Session) -> Optional[Image]:
    """
    Reads a single Image by its ID.

    Args:
        image_id (int): ID of the Image.
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        Optional[Image]: Image object if found, None if not found or a DB error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        return session.query(Image).filter(Image.id == image_id).first()
    except SQLAlchemyError as e:
        print("Something went wrong while reading image.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None
    except ValueError as e:
        print("Something went wrong while reading image.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return None

# read all images
# (WARN: make sure session is not none when calling)
def read_images(session: Session) -> Optional[List[Image]]:
    """
    Reads all Images from the database.

    Args:
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        Optional[List[Image]]: List of Image objects or None if a DB error occurred.

    Raises:
        ValueError: If session is None.
        SQLAlchemyError: Logged to stderr if query fails.
    """
    try:
        if session is None:
            raise ValueError("session cannot be None!")

        return session.query(Image).all() #type: ignore
    except SQLAlchemyError as e:
        print("Something went wrong while reading images.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None
    except ValueError as e:
        print("Something went wrong while reading images.", file=sys.stderr)
        print(f"Detailed Value error: {e}", file=sys.stderr)
        return None