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
from app.report.report_data import generate_report_data, REPORT_FORMAT_JSON

# abort when error
def abort(error: str):
    """
    Logs errors and exceptions and aborts the program.

    Args:
        error (str): Exception raised if an error occurred.
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
            image_deleted = delete_image(image_id, session)
            if image_deleted != 1:
                print("Deleting image in database failed.", file=sys.stderr)
            else: print("Image deleted from database.", file=sys.stderr)

        # delete the image directory in the output folder
        if image_name and output_path:
            dir_to_delete = Path(os.path.join(output_path, image_name))
            if dir_to_delete.exists():
                shutil.rmtree(dir_to_delete, ignore_errors=True)
                print("Deleted image data in output directory.", file=sys.stderr)

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
    image_id = -1
    image_name = ""
    OUTPUT_PATH = ""

    try:

        # starting foremost-parser
        PARSING_START = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # first, read in the environment variables
        # if there is no valid path, set default path
        load_dotenv()

        INPUT_PATH = "/data"
        HOST_INPUT_PATH = os.getenv('INPUT_PATH', 'UNKNOWN')
        OUTPUT_PATH = "/output"
        HOST_OUTPUT_PATH = os.getenv('OUTPUT_PATH', 'UNKNOWN')
        REPORT = os.getenv('REPORT', REPORT_FORMAT_JSON)
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
                    parsed, audit_table = parse_files(INPUT_PATH, OUTPUT_PATH, image_id, audit_table, image_name, IMAGES)
                    if parsed:
                        # search for duplicates and reference them
                        print("Starting duplicate detection...")
                        detect_duplicates(session,image_id, CROSS_IMAGE)
                        # generate the HTML report for this image
                        print("Generating report data...")
                        generate_report_data(INPUT_PATH, HOST_INPUT_PATH, OUTPUT_PATH, HOST_OUTPUT_PATH, REPORT, IMAGES, CROSS_IMAGE, PARSING_START, image_id, audit_table)
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
    except KeyboardInterrupt:
        print("Shutdown requested. Exiting gracefully.")
        cleanup(image_id, image_name, OUTPUT_PATH)
        sys.exit(0)

if __name__ == "__main__":
    main()