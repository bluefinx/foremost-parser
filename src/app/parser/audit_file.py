"""
audit_file.py

Parses a Foremost `audit.txt` file to extract image metadata and detailed
file-level information. The extracted data is stored in the database and
returned as a structured dictionary for further processing.

This module handles:
- Reading the audit.txt from a Foremost output directory.
- Extracting metadata (image name, size, timestamps, versions, etc.).
- Parsing the internal audit table for per-file details.
- Storing the parsed image entry in the database.

Requirements:
- The audit file must exist and be named exactly `audit.txt`.

Functions:
    get_exiftool_version(file): Reads ExifTool version metadata.
    parse_individual_lines(file, image, audit_table): Extracts line-based metadata.
    parse_audit_table(line, audit_table): Parses audit table rows.
    parse_audit(input_path): Entry point to parse the audit file and store results.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import os
import re
import sys
import exiftool

from datetime import datetime
from typing import Optional
from pathlib import Path

from app.db import connect_database
from app.models.image import Image
from app.crud.image import insert_image

# Need the following for the database:
# - image_name
# - image_size
# - create_date
# - exiftool_version
# - foremost_version
# - foremost_scan_start
# - foremost_scan_end
# - foremost_files_total

# read information from foremost's audit.txt file
filename = "audit.txt"

#################################################
# set regex for extraction
#################################################

# create raw strings to store the regex
# search for "File: example.dd"
image_name_regex = r"File:\s+(.+)"
# search for "Length: 5 GB (5762727936 bytes)"
image_size_regex = r"Length:\s+\d+\s*\w+\s*\((\d+)\s*bytes\)"
# original Foremost output directory
original_output_dir_regex = r"Output directory:\s+(.+)"
# foremost invocation
foremost_invocation_regex = r"Invocation:\s+(.+)"
# search for "Foremost version 1.5.7 by Jesse Kornblum, Kris Kendall, and Nick Mikus"
foremost_version_regex = r"Foremost version\s+([\d.]+)\s+by"
# search for "Start: Fri Nov 29 16:24:35 2024"
foremost_scan_start_regex = r"Start:\s+(.+)"
# search for "Finish: Fri Nov 29 16:25:57 2024"
foremost_scan_end_regex = r"Finish:\s+(.+)"
# search for "9838 FILES EXTRACTED"
foremost_files_total_regex = r"(\d+)\s+FILES EXTRACTED"

#################################################
# parse audit.txt
#################################################

# table flag for table parsing
table_started = False

# run exiftool to extract version
## based on https://sylikc.github.io/pyexiftool/examples.html
def get_exiftool_version(file) -> Optional[str]:
    """
    Extracts the ExifTool version for the given open file.

    This function uses `pyexiftool.ExifToolHelper` to read metadata from
    the file's path (via `file.name`) and extract the ExifTool version.
    It returns the version string if found, otherwise `None`.

    Args:
        file: An open file object (e.g., from `open(path, 'r', encoding='utf-8')`).

    Returns:
        Optional[str]: The ExifTool version string, or None if unavailable.
    """
    if not file or not hasattr(file, "name"):
        print("Invalid file object passed to get_exiftool_version().", file=sys.stderr)
        return None

    try:
        with exiftool.ExifToolHelper() as ex:
            metadata = ex.get_metadata(file.name)
            if not metadata:
                print("Could not establish ExifTool version.", file=sys.stderr)
                return None
            return str(metadata[0].get("ExifTool:ExifToolVersion"))
    except Exception as e:
        print(f"Error while extracting ExifTool version: {e}", file=sys.stderr)
        return None

# search audit file for specific information
def parse_individual_lines(file, image, audit_table: dict) -> None:
    """
    Parses the audit.txt line by line to extract image-level metadata
    and populate the audit table with file-specific data.

    Args:
        file: Opened audit.txt file object (text mode).
        image: Image model instance where metadata (name, size, etc.) is stored.
        audit_table (dict): Dictionary to store parsed file table entries.
    """
    for line in file:
        # remove white spaces and skip empty lines
        line = line.strip()
        if not line:
            continue

        # search for specific lines to extract information
        image_size_match = re.search(image_size_regex, line)
        original_output_dir_match = re.search(original_output_dir_regex, line)
        foremost_invocation_match = re.search(foremost_invocation_regex, line)
        foremost_version_match = re.search(foremost_version_regex, line)
        foremost_scan_start_match = re.search(foremost_scan_start_regex, line)
        foremost_scan_end_match = re.search(foremost_scan_end_regex, line)
        foremost_files_total_match = re.search(foremost_files_total_regex, line)
        image_name_match = re.search(image_name_regex, line)

        # assign matched values to the image object
        if image_name_match:
            image.image_name = image_name_match.group(1)
        if image_size_match:
            image.image_size = image_size_match.group(1)
        if original_output_dir_match:
            image.original_output_dir = original_output_dir_match.group(1)
        if foremost_invocation_match:
            image.foremost_invocation = foremost_invocation_match.group(1)
        if foremost_version_match:
            image.foremost_version = foremost_version_match.group(1)
        if foremost_scan_start_match:
            timestamp_start = foremost_scan_start_match.group(1)
            image.foremost_scan_start = datetime.strptime(timestamp_start, "%a %b %d %H:%M:%S %Y")
        if foremost_scan_end_match:
            timestamp_end = foremost_scan_end_match.group(1)
            image.foremost_scan_end = datetime.strptime(timestamp_end, "%a %b %d %H:%M:%S %Y")
        if foremost_files_total_match:
            image.foremost_files_total = foremost_files_total_match.group(1)

        # pass each line to the audit table parser
        parse_audit_table(line, audit_table)

# audit file has table with extra information about files
def parse_audit_table(line: str, audit_table: dict) -> None:
    """
    Parses a line from the audit.txt file to detect and extract rows from
    the Foremost audit table (containing Num, Size, Offset, Comment, etc.).

    Args:
        line (str): A single line from the audit.txt file.
        audit_table (dict): Dictionary where parsed table rows are stored.
    """
    # use the global variable
    global table_started

    # detect table start
    if line.startswith('Num') and "Comment" in line:
        table_started = True
        return

    # detect table end
    if line.startswith('Finish:'):
        table_started = False

    # only parse if we are inside the table
    if not table_started:
        return

    # split line into columns (Num, Name, Size, Offset, Comment)
    columns = re.split(r'\s{2,}|\t+', line)

    # check if valid row (starts with a number and colon)
    if not columns or not re.match(r"^\d+:", columns[0].strip()):
        return

    # safely extract columns
    name = columns[1] if len(columns) > 1 else None
    size = columns[2] if len(columns) > 2 else None
    offset = columns[3] if len(columns) > 3 else None
    comment = columns[4] if len(columns) > 4 else None

    # store entry
    if name:
        audit_table[name] = {
            "Size": size,
            "File Offset": offset,
            "Comment": comment,
        }

# if no audit file, stop, this is not a foremost directory
def parse_audit(input_path: Path) -> tuple[int, Optional[dict], Optional[str]]:
    """
    Parses the Foremost audit file (`audit.txt`) in the given input directory.

    This function does the following:
      1. Looks for a file named `audit.txt` in `input_path`.
      2. Extracts ExifTool version metadata using `get_exiftool_version()`.
      3. Parses individual metadata lines and the audit table using `parse_individual_lines()`.
      4. Stores the parsed image record in the database via `insert_image()`.
      5. Returns the new image ID, the populated audit table dictionary, and the image name.

    Args:
        input_path (Path): Path to the Foremost output directory containing `audit.txt`.

    Returns:
        tuple[int, dict | None, str | None]: A tuple containing:
            image_id: int, the new image ID, or -1 if the file is missing or an error occurred.
            audit_table: dict | None, the parsed audit table, or None if failed.
            image_name: str | None, the image name, or None if failed.

    Raises:
        ValueError: If the database session could not be established.
    """

    # image object to write to database
    image = Image()

    # audit table with additional file information
    audit_table = {}

    try:
        # get audit file as read-only
        path = os.path.join(input_path, filename)
        if os.path.isfile(path):
            with (open(path, 'r', encoding='utf-8') as file):

                # get exiftool version
                image.exiftool_version = get_exiftool_version(file)

                # get individual line information
                # and parse table
                parse_individual_lines(file, image, audit_table)

                session = connect_database()
                if session is None:
                    raise Exception("Could not connect to the database")

                return insert_image(image, session), audit_table, image.image_name
        else:
            print("Could not find audit file.", file=sys.stderr)
            return -1, None, None
    except Exception as e:
        print(f"Something went wrong parsing audit file: {e}", file=sys.stderr)
        return -1, None, None
