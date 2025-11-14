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
import shutil

from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone

from app.db import create_database, connect_database
from app.crud.image import delete_image

from app.parser.audit_file import parse_audit
from app.parser.indv_files import parse_files
from app.parser.duplicates import detect_duplicates
from app.report.report_data import generate_report_data

# abort when error
def abort(error):
    """
    Logs errors and exceptions and aborts the program.
    """
    print(error, file=sys.stderr)
    sys.exit(1)

# clean up data when aborting
def cleanup(image_id: int, image_name: str, output_path: Path):
    """
    Deletes potential database entries and output directory for a failed image parsing.

    Args:
        image_id (int): ID of the Image record in the database (if created).
        image_name (str): Name of the image, used to locate the output folder.
        output_path (Path): Base path where image output folders are stored.
    """
    print(f"Cleaning up after failed import of image...", file=sys.stderr)
    try:
        session = connect_database()
        if session is None:
            raise Exception("Could not connect to the database")

        if image_id > 0:
            # deletes image + associated files + duplicates
            delete_image(image_id, session)

        # delete the image directory in the output folder
        if image_name and output_path:
            dir_to_delete = output_path / image_name
            if dir_to_delete.exists():
                shutil.rmtree(dir_to_delete, ignore_errors=True)

    except Exception as e:
        print(f"File cleanup failed: {e}", file=sys.stderr)

# entrypoint
def main():
    """
    Main entry function for Foremost-Parser.

    Loads environment variables, connects to the database,
    parses the Foremost output (audit and files),
    checks for duplicates and generates the final report.
    """

    # TODO check if audit file numbers and actual parsing numbers can be different safely
    # TODO change file_path for image files to adapt to report structure -> make file_path and report_path relative
    # TODO update roadmap + wiki + generate docs
    # TODO clean cleanup
    # TODO mismatch extension + name -> statistics/overview
    # TODO duplicates/unique files per extension/total, top 10 duplicate groups

    # starting foremost-parser
    PARSING_START = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # first, read in the environment variables
    # if there is no valid path, set default path
    load_dotenv()

    INPUT_PATH = "/data"
    HOST_INPUT_PATH = os.getenv('INPUT_PATH', 'UNKNOWN')
    OUTPUT_PATH = "/output"
    HOST_OUTPUT_PATH = os.getenv('OUTPUT_PATH', 'UNKNOWN')
    REPORT = os.getenv('REPORT', 'html')
    IMAGES = os.getenv('IMAGES', 'false').lower() == 'true'
    CROSS_IMAGE = False

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
            image_id, audit_table, image_name = parse_audit(INPUT_PATH)

            if image_id > 0 and audit_table is not None:
                print("Parsing files...")
                if parse_files(INPUT_PATH, OUTPUT_PATH, image_id, audit_table, image_name, IMAGES):
                    # search for duplicates and reference them
                    print("Starting duplicate detection...")
                    detect_duplicates(session,image_id, CROSS_IMAGE)
                    # generate the HTML report for this image
                    print("Generating report data...")
                    generate_report_data(INPUT_PATH, HOST_INPUT_PATH, OUTPUT_PATH, HOST_OUTPUT_PATH, REPORT, IMAGES, CROSS_IMAGE, PARSING_START, image_id)
                else:
                    # something went wrong while parsing files, so clean up and exit
                    cleanup(image_id, image_name, OUTPUT_PATH)
                    abort("Something went wrong while parsing files. Cleaning up and aborting.\n"
                          "Could not parse directory. Image discarded.")
            else:
                # there is no parseable audit file, so we exit (no need to clean up)
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