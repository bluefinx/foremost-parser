# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

import os

from jinja2 import Environment, FileSystemLoader

from app.db import connect_database
from app.crud.image import read_images, read_image
from app.crud.file import read_files_for_image
from app.crud.duplicate import read_duplicates

# create the report file data, contains
# - file_name
# - file_type
# - file_extension
# - file_mime
# - file_size
# - file_offset
# - timestamp_mod
# - timestamp_acc
# - timestamp_cre
# - timestamp_ino
# - is_exiftool
# - duplicates (List of [(file name, image name), ...])
# - foremost_comment
# - more_metadata (Dict key:value)
# - file_hash
# - file_path (only for jpg, png, gif, bmp)
class ReportFile:
    def __init__(self, file_name, file_type, file_extension, file_mime, file_size, file_offset,
                 timestamp_mod, timestamp_acc, timestamp_cre, timestamp_ino, is_exiftool, duplicates,
                 foremost_comment, more_metadata, file_hash, file_path):
        self.file_name = file_name
        self.file_type = file_type
        self.file_extension = file_extension
        self.file_mime = file_mime
        self.file_size = file_size
        self.file_offset = file_offset
        self.timestamp_mod = timestamp_mod
        self.timestamp_acc = timestamp_acc
        self.timestamp_cre = timestamp_cre
        self.timestamp_ino = timestamp_ino
        self.is_exiftool = is_exiftool
        self.duplicates = duplicates
        self.foremost_comment = foremost_comment
        self.more_metadata = more_metadata
        self.file_hash = file_hash
        self.file_path = file_path

# create the report data, contains:
# - report name
# - foremostparser_start
# - foremost_version
# - exiftool_version
# - foremost_scan_start
# - foremost_scan_end
# - image_size
# - foremost_files_total
# - foremost_files_individual (Dict key:value)
# - image_files (List of ReportFile Objects)
class ReportData:
    def __init__(self, report_name, foremostparser_start, foremost_version, exiftool_version, foremost_scan_start,
                 foremost_scan_end, image_size, foremost_files_total, foremost_files_individual, image_files):
        self.report_name = report_name
        self.foremostparser_start = foremostparser_start
        self.foremost_version = foremost_version
        self.exiftool_version = exiftool_version
        self.foremost_scan_start = foremost_scan_start
        self.foremost_scan_end = foremost_scan_end
        self.image_size = image_size
        self.foremost_files_total = foremost_files_total
        self.foremost_files_individual = foremost_files_individual
        self.image_files = image_files

# this is the actual HTML report generation with Jinja2
# reads in the template, creates the Jinja2 engine and renders the report
# the report is then saved to the /files volume as well as the bind-mount provided by the user
def render_report(report_data, image_id, output_path, files_path):
    # read in the Jinja2 template
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../template'))
    env = Environment(loader=FileSystemLoader(dir_path))
    template = env.get_template('template.html')

    # fill in the template
    output = template.render(report=report_data)

    # store the template in /files as copy
    # create, if not existing, report dir
    report_dir = os.path.join(files_path, "report")
    os.makedirs(report_dir, exist_ok=True)
    # create path for image report
    report_path = os.path.join(report_dir, str(image_id) + ".html")
    # if file exists, overwrite content
    with open(os.path.join(dir_path, report_path), 'w') as f:
        f.write(output)

    # store the template in the output folder provided by user
    # create path for image report
    report_path = os.path.join(output_path, "foremostparser" + str(report_data.report_name) + ".html")
    # if file exists, overwrite content
    with open(os.path.join(dir_path, report_path), 'w') as f:
        f.write(output)
        print(f"Report saved to {report_path}.")

# takes in the current image and the regenerate flag
# if regenerate, generate new reports for all images
def generate_report(image_id, regenerate, output_path, files_path):
    try:
        session = connect_database()
        if session is None:
            raise Exception("Could not connect to the database")

        # first, check if flag is set
        all_images = []
        if regenerate:
            all_images = read_images(session)
        else:
            all_images = read_images(session) if regenerate else [read_image(image_id, session)]
        # create a separate report for every image
        for image in all_images:

            # read all files for image
            report_files = read_files_for_image(image.id, session)
            # for every file, get id to query duplicates
            duplicate_files = []
            if report_files is not None and len(report_files) > 0:
                file_ids = [file.id for file in report_files if file.is_duplicate == True]
                # is [(file, file)]
                duplicate_files = []
                if len(file_ids) > 0:
                    duplicate_files = read_duplicates(file_ids, session)

            report_name = image.image_name
            foremostparser_start = image.create_date
            foremost_version = image.foremost_version
            exiftool_version = image.exiftool_version
            foremost_scan_start = image.foremost_scan_start
            foremost_scan_end = image.foremost_scan_end
            image_size = image.image_size
            foremost_files_total = image.foremost_files_total
            foremost_files_individual = image.foremost_files_individual

            image_files = []
            for file in report_files:
                file_name = file.file_name
                file_type = file.file_type
                file_extension = file.file_extension
                file_mime = file.file_mime
                file_size = file.file_size
                file_offset = file.file_offset
                timestamp_mod = file.timestamp_mod
                timestamp_acc = file.timestamp_acc
                timestamp_cre = file.timestamp_cre
                timestamp_ino = file.timestamp_ino
                is_exiftool = file.is_exiftool
                foremost_comment = file.foremost_comment
                more_metadata = file.more_metadata
                file_hash = file.file_hash

                file_path = None
                if file_extension.lower() in {"jpg", "jpeg", "png", "gif", "bmp"}:
                    file_path = file.file_path

                duplicates = []
                # for every duplicate file, get the image name
                # want a list of [(file name, image name), ...]
                if duplicate_files is not None and len(duplicate_files) > 0:
                    for file_one, file_two in duplicate_files:
                        #print(f"Duplicate file {file_one} and {file_two}")
                        # TODO there is a bug here, when there's too many duplicates, the code crashes
                        # TODO is probably a database issue because with less files it works fine
                        if file_one.id == file.id:
                            # file_two is the duplicate, get the image name for the duplicate file
                            image_for_duplicate = read_image(file_two.image_id, session)
                            if image_for_duplicate:
                                duplicates.append((file_one.file_name, image_for_duplicate.image_name))
                        elif file_two.id == file.id:
                            # file_one is the duplicate, get the image name for the duplicate file
                            image_for_duplicate = read_image(file_one.image_id, session)
                            if image_for_duplicate:
                                duplicates.append((file_one.file_name, image_for_duplicate.image_name))

                # create the ReportFile object and store it in image_files
                report_file = ReportFile(file_name,
                                         file_type,
                                         file_extension,
                                         file_mime,
                                         file_size,
                                         file_offset,
                                         timestamp_mod,
                                         timestamp_acc,
                                         timestamp_cre,
                                         timestamp_ino,
                                         is_exiftool,
                                         duplicates,
                                         foremost_comment,
                                         more_metadata,
                                         file_hash,
                                         file_path)
                image_files.append(report_file)

            # create the report object
            report_data = ReportData(report_name,
                                     foremostparser_start,
                                     foremost_version,
                                     exiftool_version,
                                     foremost_scan_start,
                                     foremost_scan_end,
                                     image_size,
                                     foremost_files_total,
                                     foremost_files_individual,
                                     image_files)

            render_report(report_data, image.id, output_path, files_path)
    except Exception as e:
        print(f"Something went wrong while creating report: {e}")
        return False