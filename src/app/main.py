"""
main.py

Entry point for Foremost-Parser.

This tool parses Foremost output folders and generates a detailed report.

Features:
    - Loads and verifies environment variables
    - Creates or connects to the database
    - Parses the Foremost audit file
    - Parses individual recovered files
    - Detects duplicates
    - Generates a comprehensive report

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
Version: 1.0.0
"""

import os
import sys

from dotenv import load_dotenv
from pathlib import Path

from app.db import create_database, connect_database
from app.crud.image import delete_image, update_image_files_individual
from app.crud.file import read_files_per_extension_for_image

from app.parser.audit_file import parse_audit
from app.parser.indv_files import parse_files, delete_files_in_image
from app.parser.duplicates import detect_duplicates
from app.report.report import generate_report

def abort(error):
    """
    Logs errors and exceptions and aborts the program.
    """
    print(error, file=sys.stderr)
    sys.exit(1)

# entrypoint
def main():
    """
    Main entry function for Foremost-Parser.

    Loads environment variables, connects to the database,
    parses the Foremost output (audit and files),
    checks for duplicates and generates the final report.
    """

    # starting foremost-parser

    # first, read in the environment variables
    # if there is no valid path, set default path
    load_dotenv()

    INPUT_PATH = os.getenv('INPUT_PATH', '/data')
    OUTPUT_PATH = os.getenv('OUTPUT_PATH', '/output')
    IMAGES = os.getenv('IMAGES', 'false').lower() == 'true'

    # check if input path is valid path
    INPUT_PATH = Path(INPUT_PATH)
    if not os.path.isdir(INPUT_PATH):
        abort(f"Input path {INPUT_PATH} is not a directory.")

    # check if output path is valid path
    OUTPUT_PATH = Path(OUTPUT_PATH)
    if not os.path.isdir(OUTPUT_PATH) or not os.access(OUTPUT_PATH, os.W_OK):
        abort(f"Output path {OUTPUT_PATH} is not a directory or not writable.")

    # connect to database, creating database if not initialised
    if not (create_database()):
        abort("Aborting!")
    else:
        try:
            session = connect_database()
            if session is None:
                raise Exception("Could not connect to the database")

            # first, parse audit file
            # TODO add parsing for folders with no audit file
            print("Parsing audit file...")
            image_id, table = parse_audit(INPUT_PATH)

            if image_id > 0 and table is not None:
                print("Parsing files...")
                if parse_files(INPUT_PATH, image_id, table, FILES_PATH):
                    # per file extension, count the number of files for overview in report
                    result = dict(read_files_per_extension_for_image(image_id, session))
                    update_image_files_individual(image_id, result, session)
                    # search for duplicates and reference them
                    print("Starting duplicate detection...")
                    detect_duplicates(session)
                    # generate the HTML report for this image
                    print("Generating report...")
                    generate_report(image_id, REGENERATE, OUTPUT_PATH, FILES_PATH)
                else:
                    # something went wrong while parsing files, so clean up and exit
                    delete_files_in_image(image_id, FILES_PATH)
                    delete_image(image_id, session)
                    abort("Something went wrong while parsing files. Cleaning up and aborting.\n"
                          "Could not parse directory. Image discarded.")
            else:
                # there is no parseable audit file, so we exit
                sys.exit(1)

        except Exception as e:
            abort(f"Something went wrong while parsing files: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Shutdown requested. Exiting gracefully.")
        # TODO implement cleanup
        sys.exit(0)