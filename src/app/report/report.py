# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0
import hashlib
import os
import ssl

from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader

from app.db import connect_database
from app.crud.image import read_image
from app.report.image_extensions_data import ImageExtensionsData
from app.report.image_files_data import ImageFilesData
from app.report.image_overview_data import ImageOverviewData


# -----------------------------------------------------------------------------
# REPORT CONTENT STRUCTURE
# -----------------------------------------------------------------------------
#
# 1. IMAGE OVERVIEW PAGE
#    - General metadata about the analysis
#      • fmparser start and end time + parameters
#      • foremost scan start and end time
#      • foremost version
#      • exiftool version
#      • hash algorithm used (e.g. SHA-256)
#    - Image information
#      • input path
#      • image name
#      • image size
#      • image creation date
#    - Statistics
#      • total number of extracted files
#      • total size of all files
#      • number of unique file extensions
#      • distribution of file extensions (graph)
#      • top 10 largest files
#      • number of duplicate groups detected
#    - Duplicate summary
#      • per group: hash, number of files, linked images (if cross-image mode active)
#    - Logs
#      • error and warning messages
#
# 2. EXTENSION PAGES (ONE PER FILE TYPE)
#    - File statistics per extension
#      • number of files per extension
#      • total size of all files
#      • percentage of total extracted files
#    - File list (sortable)
#      • file name
#      • file size
#      • icons for:
#         🧩 duplicate indicator
#         🧠 metadata extracted (exiftool/python)
#      • for images: embedded preview
#      • size shown in human-readable format
#
# 3. FILE DETAIL PAGE
#    - Basic file info
#      • file name
#      • file size
#      • hash + algorithm
#      • type and MIME type
#      • offset (from foremost)
#      • foremost comment
#    - Metadata
#      • extracted with exiftool/python
#    - Duplicate info
#      • duplicate group hash
#      • list of duplicate files (names, images if applicable)
#    - For images
#      • embedded image preview
#      • additional ExifTool metadata
#
# -----------------------------------------------------------------------------

def generate_report_data(
        input_path: Path,
        output_path: Path,
        images: bool,
        cross_image: bool,
        parsing_start: str,
        image_id: int
):
    try:
        session = connect_database()
        if session is None:
            raise Exception("Could not connect to the database")

        # read the database data
        image = read_image(image_id, session)
        if image is None:
            raise Exception("Could not read the image. Aborting report!")

        ######################## calculate and gather data #################

        # set the parsing end time
        PARSING_END = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # set the fmparser parameters
        parameters = {
            "input_path": input_path,
            "output_path": output_path,
            "images": images,
            "cross_image": cross_image
        }

        # hash algorithm is always SHA256
        hash_algorithm = f"SHA-256 (Python hashlib ({ssl.OPENSSL_VERSION}))"

        # calculate total file size
        total_file_size = sum(file.file_size for file in image.files)
        top_ten_files = sorted(
            image.files, key=lambda f: f.file_size, reverse=True
        )[:10]

        # calculate extension distribution
        total_files = sum(image.foremost_files_individual.values())
        extension_distribution = {
            ext: round((count / total_files) * 100)
            for ext, count in image.foremost_files_individual.items()
        }

        image_extensions_data_list = []

        files_by_extension = defaultdict(list)
        # sort all files by extension
        for file in image.files:
            files_by_extension[file.file_extension].append(file)
        # go through files per extension
        for ext, files in files_by_extension.items():
            number_files = len(files)
            total_file_size = sum(file.file_size for file in files)
            percentage_extraction = extension_distribution.get(ext, 0)

            image_extensions_data = ImageExtensionsData(
                number_files=number_files,
                total_size_files=total_file_size,
                percentage_extraction=percentage_extraction,
                files=None
            )

            for file in files:

                report_path = os.path.join(output_path, image.image_name, ext, file.file_name)

                image_file_data = ImageFilesData(
                    file_name=file.file_name,
                    file_size=file.file_size,
                    file_extension=file.file_extension,
                    file_path=file.file_path,
                    file_report_path=report_path,
                    file_hash=file.file_hash,
                    file_hash_algorithm=hash_algorithm,
                    file_type=file.file_type,
                    file_mime=file.file_mime,
                    file_offset=file.file_offset,
                    foremost_comment=file.foremost_comment,
                    is_exiftool=file.is_exiftool,
                )






















        image_overview_data = ImageOverviewData(
            parser_start=parsing_start,
            parser_end=PARSING_END,
            parser_parameters=parameters,
            foremost_start=image.foremost_scan_start,
            foremost_end=image.foremost_scan_end,
            foremost_version=image.foremost_version,
            exiftool_version=image.exiftool_version,
            hash_algorithm=hash_algorithm,
            input_path=input_path,
            image_name=image.image_name,
            image_size=image.image_size,
            image_creation_date=image.create_date,
            total_number_files=image.foremost_files_total,
            total_size_files=total_file_size,
            number_extensions=len(image.foremost_files_individual),
            extension_distribution=extension_distribution,
        )


    except Exception as e:
        print("Ohoh fehler.")