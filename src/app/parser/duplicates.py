# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

from sqlalchemy.orm import Session

from app.crud.file import read_files_with_hash
from app.crud.duplicate import insert_duplicates

# after storing the files, compare the hashes to find duplicate files
def detect_duplicates(session: Session):
    # read in all files
    files = read_files_with_hash(session)
    if files is not None:
        # list of compared file pairs
        pairs = set()
        # list of duplicate pairs
        duplicates = set()
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
        print(f"No file hashes found, skipping duplicate detection.")