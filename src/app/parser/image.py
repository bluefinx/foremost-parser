# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

import os
import re
import exiftool

from datetime import datetime

from app.db import connect_database
from app.models.image import Image
from app.crud.image import read_images, delete_image, insert_image

from app.parser.indv_files import delete_files_in_image

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
# search for "File: johndoe.dd"
image_name_regex = r"File:\s+(\S+)"
# search for "Length: 5 GB (5762727936 bytes)"
image_size_regex = r"Length:\s+\d+\s*\w+\s*\((\d+)\s*bytes\)"
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
# reads in the audit.txt file and extracts
# relevant data
#################################################

# table flag for table parsing
table_started = False

# run exiftool to extract version
def get_exiftool_version(file):
    # run exiftool to get the version
    ## based on https://sylikc.github.io/pyexiftool/examples.html
    with exiftool.ExifToolHelper() as ex:
        file_metadata = ex.get_metadata(file.name)
        if not file_metadata:
            print(f"Could not establish exiftool version.")
            return None
        else:
            return str(file_metadata[0].get('ExifTool:ExifToolVersion'))

# search audit file for specific information
def parse_individual_lines(file, image, table):
    for line in file:
        # remove white spaces
        line = line.strip()
        # skip empty lines
        if not line: continue
        # search for specific lines to extract information
        image_size_match = re.search(image_size_regex, line)
        foremost_version_match = re.search(foremost_version_regex, line)
        foremost_scan_start_match = re.search(foremost_scan_start_regex, line)
        foremost_scan_end_match = re.search(foremost_scan_end_regex, line)
        foremost_files_total_match = re.search(foremost_files_total_regex, line)
        image_name_match = re.search(image_name_regex, line)
        # store information
        if image_name_match:
            image.image_name = image_name_match.group(1)
        if image_size_match:
            image.image_size = image_size_match.group(1)
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

        parse_audit_table(line, table)

# audit file has table with extra information about files
def parse_audit_table(line, table):
    # use the global variable
    global table_started

    # split the line into columns when at least 2 whitespaces or a tab (cause whatever they really use)
    columns = re.split(r'\s{2,}|\t+', line)

    # look for start of table in audit.txt
    if line.startswith('Num') and "Comment" in line:
        table_started = True
        return

    # table is finished
    if line.startswith('Finish:'):
        table_started = False

    # start reading in the table rows
    # check if the line starts with a number and a ":"
    if table_started and re.match(r'^\d+:', columns[0].strip()):

        # get name, size, offset and comment
        if len(columns) > 1:
            name = columns[1]
        else:
            name = None
        if len(columns) > 2:
            size = columns[2]
        else:
            size = None
        if len(columns) > 3:
            offset = columns[3]
        else:
            offset = None
        if len(columns) > 4:
            comment = columns[4]
        else:
            comment = None

        table[name] = {
            'Size': size,
            'File Offset': offset,
            'Comment': comment
        }

# if OVERWRITE, try to overwrite the image
# if no audit file, stop, this is not a foremost directory
# TODO add parsing files for dirs without audit file
def parse_audit(overwrite, input_path, files_path):
    # image object to write to database
    image = Image()

    # audit table with additional file information
    table = {}

    # set image creation date
    image.create_date = datetime.now()

    # just your casual paranoid try-except
    try:
        # get audit file as read-only
        path = os.path.join(input_path, filename)
        if os.path.isfile(path):
            with (open(path, 'r', encoding='utf-8') as file):

                # get exiftool version
                image.exiftool_version = get_exiftool_version(file)

                # get individual line information
                # while also parsing table
                parse_individual_lines(file, image, table)

                session = connect_database()
                if session is None:
                    raise Exception("Could not connect to the database")

                # if OVERWRITE, see if image already exists in database
                if overwrite:
                    images_list = read_images(session)
                    for old_image in images_list:
                        if old_image.image_name == image.image_name:
                            print("Deleting previous image.")
                            # first, delete any files in the persistent volume
                            delete_files_in_image(old_image.id, files_path)
                            # then, delete the rows from the database
                            delete_image(old_image, session)

                return insert_image(image, session), table
        else:
            print(f"Could not find audit file.")
            return -1, None
    except Exception as e:
        print(f"Something went wrong parsing audit file: {e}")
        return -1, None
