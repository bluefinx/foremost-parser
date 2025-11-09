"""
duplicates.py

Provides functions to detect duplicate files based on their hashes and store
duplicate pairs in the database.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from sqlalchemy.orm import Session

from app.crud.file import read_files_with_hash
from app.crud.duplicate import insert_duplicates

# after storing the files, compare the hashes to find duplicate files
def detect_duplicates(session: Session):
    """
    Detects duplicate files by comparing hashes of all stored files and
    inserts the duplicate pairs into the database.

    Args:
        session (Session): SQLAlchemy session, must not be None.

    Notes:
        - Reads all files with a non-null hash using `read_files_with_hash`.
        - Compares each file hash against all others (O(n^2) complexity).
        - Only stores one version of each duplicate pair (order-independent).
        - Uses `insert_duplicates` to write duplicates to the database.
        - Prints progress every 500 files.
        - If no files with hashes exist, duplicate detection is skipped.

    Returns:
        None
    """
    # read in all files
    # TODO improve performance for many duplicates
    files = read_files_with_hash(session)
    if files is not None:
        pairs = set()       # list of compared file pairs
        duplicates = set()  # list of duplicate pairs
        # go through the files
        for i in range(len(files)-1):
            if i % 500 == 0:
                print(f"Searching for duplicates: {i}/{len(files)}")
            # for every file, go through files again but exclude the current file
            for y in range(i+1, len(files)):
                file_id, file_hash = files[i]
                duplicate_id, duplicate_hash = files[y]
                # compare the hashes
                if file_hash == duplicate_hash and tuple(sorted([file_id, duplicate_id])) not in pairs:
                    # we only want to store one version of each pair, so instead of (1,2) and (2,1), we only store (1,2)
                    pairs.add(tuple(sorted([file_id, duplicate_id])))
                    duplicates.add(tuple(sorted([file_id, duplicate_id])))
        insert_duplicates(duplicates, session)
    else:
        print("No file hashes found, skipping duplicate detection.")