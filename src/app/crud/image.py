"""
image.py (CRUD)

Provides functions to insert, update, delete and read Image records in the database
as well as to update per-image file statistics.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import sys

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.image import Image

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

    Raises:
        ValueError: If session is None.

    Returns:
        int: The ID of the inserted Image or -1 if a database error occurred.

    Notes:
        Commits immediately after adding the Image. Rolls back in case of errors.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        session.add(image)
        session.commit()
        return image.id
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while storing image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return -1

# set the individual files for this image
# (WARN: make sure session is not none when calling)
def update_image_files_individual(image_id: int, result: dict, session: Session) -> int:
    """
    Updates the 'foremost_files_individual' JSON field for a given Image.

    Args:
        image_id (int): ID of the Image to update.
        result (dict): Dictionary containing per-extension file counts.
        session (Session): SQLAlchemy session, must not be None.

    Raises:
        ValueError: If session is None.

    Returns:
        int: 1 if successful, -1 if the Image does not exist or a DB error occurred.

    Notes:
        Commits after updating. Rolls back in case of errors.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        image = session.query(Image).filter(Image.id == image_id).first()
        if image is not None:
            image.foremost_files_individual = result
            session.commit()
            return 1
        else:
            return -1
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while overwriting image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
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

    Notes:
        Commits after deletion. Rolls back in case of errors.
    """
    if session is None:
        raise ValueError("session cannot be None!")

    try:
        image = session.get(Image, image_id)
        if image is None:
            print(f"No image found with id {image_id}", file=sys.stderr)
            return -1
        # files and duplicates are automatically deleted through relationships and cascade
        session.delete(image)
        session.commit()
        return 1

    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while deleting image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
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

    Raises:
        ValueError: If session is None.

    Returns:
        Image | None: Image object if found, None if not found or a DB error occurred.
    """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(Image).filter(Image.id == image_id).first()
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while reading image. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None

# read all images
# (WARN: make sure session is not none when calling)
def read_images(session: Session):
    """
   Reads all Images from the database.

   Args:
       session (Session): SQLAlchemy session, must not be None.

   Raises:
       ValueError: If session is None.

   Returns:
       list[Image] | None: List of Image objects or None if a DB error occurred.
   """
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(Image).all()
    except SQLAlchemyError as e:
        session.rollback()
        print("Something went wrong while reading images. Rolling back.", file=sys.stderr)
        print(f"Detailed DB error: {e}", file=sys.stderr)
        return None