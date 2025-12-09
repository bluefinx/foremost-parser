"""
duplicates.py

Provides functions to detect duplicate files based on their SHA-256 hashes
and store the duplicate relationships in the database.

The module handles:
    - Intra-image duplicate detection: compares files within the same image.
    - Cross-image duplicate detection (planned): compares files across all images.
    - Creation of DuplicateGroup entries for each hash shared by multiple files.
    - Linking DuplicateGroups to images via an association table.
    - Creation of DuplicateMember entries for each file in a group.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import sys

from sqlalchemy.orm import Session

from app.crud.file import read_files_with_hash, read_file_hashes_for_image
from app.crud.duplicate import check_duplicate_group_for_image, insert_duplicate_group, link_duplicate_group_to_image, insert_duplicate_member
from app.models.duplicate import DuplicateGroup

# after storing the files, compare the hashes to find duplicate files
def detect_duplicates(session: Session, image_id: int, cross_image: bool):
    """
    Detects duplicate files based on their hashes and stores them in the database.

    Compares file hashes to identify duplicates within a single image
    or, optionally, across multiple images. It creates duplicate groups and links
    files to these groups in the database.

    Args:
        session (Session): SQLAlchemy database session used to query and update records.
        image_id (int): ID of the image whose files should be checked for duplicates.
        cross_image (bool): If True, duplicates will be checked across all images;
                            if False, only within the given image.

    Returns:
        None

    Raises:
        Exception: If the database session is None or if an error occurs during duplicate detection.
    """
    try:
        if session is None:
            raise Exception("Could not connect to the database")

        # get the file hashes for this image
        image_hashes = read_file_hashes_for_image(image_id, session)
        # get hashes for all files stored
        all_hashes = read_files_with_hash(session)

        if not image_hashes or not all_hashes:
            print("No file hashes found, skipping duplicate detection.")
            return

        intra_image_counter = 0
        cross_image_counter = 0

        # if cross_image = False, only compare the hashes of this image
        if not cross_image:

            # group files by hash to avoid O(n^2) comparison
            hash_groups = {}  # key: file_hash
            for file_hash in image_hashes:
                # check if key already exists, add file to hash
                hash_groups.setdefault(file_hash.file_hash, []).append(file_hash.file_id)

            for file_hash, file_ids in hash_groups.items():
                # no duplicates for this hash
                if len(file_ids) >= 2:
                    # check duplicate group already exists and is connected to image
                    exists, linked_to_image = check_duplicate_group_for_image(session, image_id, file_hash)

                    # create duplicate group and connect to image
                    if not exists:
                        insert_duplicate_group(DuplicateGroup(file_hash=file_hash), session)
                        link_duplicate_group_to_image(file_hash, image_id, session)
                    if exists and not linked_to_image:
                        link_duplicate_group_to_image(file_hash, image_id, session)

                    for file_id in file_ids:
                        insert_duplicate_member(file_hash, image_id, file_id, session)
                        intra_image_counter += 1

        # if cross_image = True, compare all files stored
        # else:
            # TODO implement cross-image duplicate detection

        print(f"Found {intra_image_counter} duplicate files for this image.")

    except Exception as e:
        print(f"Something went wrong searching for duplicates: {e}", file=sys.stderr)
