"""
duplicates.py

Provides functions to detect duplicate files based on their hashes and store
duplicate pairs in the database.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import sys

from sqlalchemy.orm import Session

from app.crud.file import read_files_with_hash
from app.crud.duplicate import insert_duplicates

# after storing the files, compare the hashes to find duplicate files
def detect_duplicates(session: Session):
    """
    Detects duplicate files by comparing SHA-256 hashes of all stored files
    and inserts the duplicate pairs into the database.

    Args:
        session (Session): SQLAlchemy session, must not be None.

    Returns:
        None

    Notes:
        - Reads all files with non-null hash using `read_files_with_hash()`.
        - Compares each file hash against others with same hash (improves performance).
        - Only stores one version of each duplicate pair (order-independent).
        - Uses `insert_duplicates()` to write duplicates to the database.
    """

    try:
        if session is None:
            raise Exception("Could not connect to the database")

        # read in all files
        files = read_files_with_hash(session)   # tuple[file_id, file_hash]
        if not files:
            print("No file hashes found, skipping duplicate detection.")
            return

        # group files by hash to avoid O(n^2) comparison
        hash_groups = {}    # key: file_hash
        for file_id, file_hash in files:
            # check if key already exists, add file to hash
            hash_groups.setdefault(file_hash, []).append(file_id)

        duplicates = set()  # list of duplicate pairs
        for file_hash, file_ids in hash_groups.items():
            # no duplicates for this hash
            if len(file_ids) < 2:
                continue
            # go through the duplicate hashes
            for i in range(len(file_ids) -1):
                for j in range(i + 1, len(file_ids)):
                    pair = tuple(sorted([file_ids[i], file_ids[j]]))
                    duplicates.add(pair)

        if duplicates:
            print(f"Found {len(duplicates)} duplicate pairs, inserting into DB...")
            insert_duplicates(duplicates, session)
        else:
            print("No duplicates found.")

    except Exception as e:
        print(f"Something went wrong searching for duplicates: {e}", file=sys.stderr)
