# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

import os

from dotenv import load_dotenv
from pathlib import Path

from app.db import create_database, connect_database
from app.crud.image import delete_image, update_image_files_individual
from app.crud.file import read_files_per_extension_for_image

from app.parser.image import parse_audit
from app.parser.indv_files import parse_files, delete_files_in_image
from app.parser.duplicates import detect_duplicates
from app.report.report import generate_report

# entrypoint
def main():

    # starting foremost-parser

    # first, read in the environment variables
    # if there is no valid path, set default path
    load_dotenv()

    INPUT_PATH = os.getenv('INPUT_PATH', '/data')
    OUTPUT_PATH = os.getenv('OUTPUT_PATH', '/output')
    FILES_PATH = os.getenv('FILES_PATH', '/files')
    OVERWRITE = os.getenv('OVERWRITE', 'false').lower() in 'true'
    REGENERATE = os.getenv('REGENERATE', 'false').lower() in 'true'

    # check if input path is valid path
    INPUT_PATH = Path(INPUT_PATH)
    if not os.path.isdir(INPUT_PATH):
        print(f"Input path {INPUT_PATH} is not a directory.")
        exit(1)

    # check if output path is valid path
    OUTPUT_PATH = Path(OUTPUT_PATH)
    if not os.path.isdir(OUTPUT_PATH) or not os.access(OUTPUT_PATH, os.W_OK):
        print(f"Output path {OUTPUT_PATH} is not a directory or not writable.")
        exit(1)

    # check if files path is valid path
    FILES_PATH = Path(FILES_PATH)
    if not os.path.isdir(FILES_PATH) or not os.access(FILES_PATH, os.W_OK):
        print(f"Could not access persistent volume.")
        exit(1)

    # connect to database, creating database if not initialised
    if not (create_database()):
        print(f"Aborting!")
        exit(1)
    else:
        try:
            session = connect_database()
            if session is None:
                raise Exception("Could not connect to the database")

            # if OVERWRITE, pass to parse_audit()
            print(f"Parsing audit file...")
            image_id, table = parse_audit(OVERWRITE, INPUT_PATH, FILES_PATH)

            if image_id > 0 and table is not None:
                print(f"Parsing files...")
                if parse_files(INPUT_PATH, image_id, table, FILES_PATH):
                    # per file extension, count the number of files for overview in report
                    result = dict(read_files_per_extension_for_image(image_id, session))
                    update_image_files_individual(image_id, result, session)
                    # search for duplicates and reference them
                    print(f"Starting duplicate detection...")
                    detect_duplicates(session)
                    # generate the HTML report for this image
                    print(f"Generating report...")
                    generate_report(image_id, REGENERATE, OUTPUT_PATH, FILES_PATH)
                else:
                    # something went wrong while parsing files, so clean up and exit
                    print(f"Something went wrong with parsing files. Cleaning up and aborting.")
                    print(f"Could not parse directory. Image discarded.")
                    delete_files_in_image(image_id, FILES_PATH)
                    delete_image(image_id, session)
                    exit(1)
            else:
                # there is no audit file, so we exit
                exit(1)

        except Exception as e:
            print(f"Something went wrong while parsing files: {e}")
            return False


if __name__ == "__main__":
    main()