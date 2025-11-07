# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

# this file contains the database interactions for images

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.image import Image
from app.models.file import File
from app.models.duplicate import Duplicate

########################################################################
###################### WRITE ###########################################
########################################################################

# store image row
# (WARN: make sure session is not none when calling)
def insert_image(image: Image, session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        session.add(image)
        session.commit()
        return image.id
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while storing image. Rolling back.")
        print(f"Detailed DB error: {e}")
        return -1

# set the individual files for this image
# (WARN: make sure session is not none when calling)
def update_image_files_individual(image_id: int, result: dict, session: Session):
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
        print(f"Something went wrong while overwriting image. Rolling back.")
        print(f"Detailed DB error: {e}")
        return -1

# delete image
# (WARN: make sure session is not none when calling)
def delete_image(image: Image, session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        # first, delete existing duplicate entries
        files = session.query(File).filter(File.image_id == image.id).all()
        for file in files:
            session.query(Duplicate).filter(
                or_(
                    Duplicate.file_id == file.id,
                    Duplicate.duplicate_id == file.id
                )
            ).delete(synchronize_session='fetch')
        session.query(File).filter(File.image_id == image.id).delete(synchronize_session='fetch')
        session.delete(image)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while deleting image. Rolling back.")
        print(f"Detailed DB error: {e}")
        return -1

########################################################################
###################### READ ############################################
########################################################################

# get the image by ID
# (WARN: make sure session is not none when calling)
def read_image(image_id: int, session: Session) -> Optional[Image]:
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(Image).filter(Image.id == image_id).first()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while reading image by ID. Rolling back.")
        print(f"Detailed DB error: {e}")
        return None

# read all images
# (WARN: make sure session is not none when calling)
def read_images(session: Session):
    if session is None:
        raise ValueError("session cannot be None!")
    try:
        return session.query(Image).all()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Something went wrong while reading images. Rolling back.")
        print(f"Detailed DB error: {e}")
        return None