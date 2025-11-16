"""
report_data.py

Contains functions to generate structured data for Foremost outputs.
Includes overview data, file-extension-level aggregation and file-level
details for reporting.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

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
#      • image name
#      • image size
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

import os
import ssl
import sys

from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Set
from enum import Enum
from collections import defaultdict, Counter

from sqlalchemy.orm import Session

from app.db import connect_database
from app.models.image import Image
from app.models.file import File
from app.crud.image import read_image
from app.crud.file import read_files_with_extension_mismatch_for_image
from app.crud.duplicate import read_duplicate_group_by_file_id, read_duplicate_groups_for_image

from app.report.image_extensions_data import ImageExtensionsData
from app.report.image_files_data import ImageFilesData
from app.report.image_overview_data import ImageOverviewData, FileEntry, ImageEntry, DuplicateGroupData, ExtensionEntry
from app.report.report_json import generate_json_report

REPORT_FORMAT_JSON = "json"
REPORT_FORMAT_HTML = "html"

class ReportFormat(Enum):
    """
    Enumeration of supported report formats.

    Attributes:
        HTML (str): Standard HTML report.
        JSON (str): JSON formatted report.
    """
    HTML = REPORT_FORMAT_HTML
    JSON = REPORT_FORMAT_JSON

# generate the file path in the report
def generate_file_report_path(output_path: Path, image_name: str, file_extension: str, file_name: str, report: str) -> str:
    """
    Generate a relative file path for inclusion in the HTML report.

    Args:
        output_path (Path): Base output directory of the report.
        image_name (str): Name of the forensic image.
        file_extension (str): Extension of the file.
        file_name (str): Name of the file.
        report (str): Report format.

    Returns:
        str: Relative path to the file in the report or empty string if
             any argument is invalid.
    """
    if report == REPORT_FORMAT_JSON:
        return ""
    elif output_path is not None and image_name is not None and file_extension is not None and file_name is not None:
        return str(os.path.join(output_path, image_name, file_extension, file_name))
    else:
        print("Could not create file report path. Invalid arguments.", file=sys.stderr)
        return ""

# generate the image overview data for the report
def generate_image_overview_data(
        input_path: Path,
        host_input_path: str,
        output_path: Path,
        host_output_path: str,
        report: str,
        with_images: bool,
        cross_image: bool,
        parsing_start: str,
        image: Image,
        audit_table: dict,
        session: Session
) -> ImageOverviewData:
    """
    Generate an aggregated overview of a forensic image for report rendering.

    This includes parser execution info, image metadata, file statistics,
    extension distributions, duplicate groups and placeholder for logs.

    Args:
        input_path (Path): Path to input image files.
        host_input_path (str): Path to host input Foremost directory.
        output_path (Path): Output directory for the report.
        host_output_path (str): Output directory for the host output report directory.
        report (str): Report format.
        with_images (bool): Whether to include image previews.
        cross_image (bool): Whether cross-image duplicate detection is enabled.
        parsing_start (str): Timestamp when parsing started.
        image (Image): SQLAlchemy Image object with files and metadata.
        audit_table (dict): the audit_table dict after all parsed files were dropped.
        session (Session): SQLAlchemy session for queries.

    Returns:
        ImageOverviewData: Structured overview data for the image.
    """

    # set the parsing end time
    PARSING_END = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # hash algorithm is always SHA256
    hash_algorithm = f"SHA-256 (Python hashlib ({ssl.OPENSSL_VERSION}))"

    # set the fmparser parameters
    parameters = {
        "input_path": host_input_path,
        "output_path": host_output_path,
        "report": report,
        "with_images": with_images,
        #"cross_image": cross_image
    }

    # calculate total file size
    total_file_size = sum(file.file_size for file in image.files)

    # top ten files regarding size
    top_ten_files_objects = sorted(
        image.files, key=lambda f: f.file_size, reverse=True
    )[:10]
    top_ten_files = []
    for file in top_ten_files_objects:
        top_ten_files.append(FileEntry(file.file_name, file.file_extension, file.file_size, generate_file_report_path(output_path, image.image_name, file.file_extension, file.file_name, report)))

    files_ext_mismatch = read_files_with_extension_mismatch_for_image(image.id, session)
    files_extension_mismatch = []
    for file in files_ext_mismatch:
        files_extension_mismatch.append(FileEntry(file.file_name, file.file_extension, file.file_size, generate_file_report_path(output_path, image.image_name, file.file_extension, file.file_name, report)))

    # duplicate groups data
    duplicate_groups = read_duplicate_groups_for_image(session, image.id)
    number_duplicate_files = 0
    for group in duplicate_groups:
        number_duplicate_files += len(group.members)

    top_ten_duplicate_groups = sorted(
        duplicate_groups,
        key=lambda g: len(g.members),
        reverse=True
    )[:10]

    duplicate_groups_data = []
    for group in top_ten_duplicate_groups:
        file_count = 0
        duplicate_images = []
        # read the duplicate images
        if group.images:
            for group_image in group.images:
                # read the duplicate files data
                duplicate_files = []
                if group_image.files:
                    duplicate_files_set = set(group.members_files)
                    for file in group_image.files:
                        if file in duplicate_files_set:
                            duplicate_files.append(FileEntry(file.file_name, file.file_extension, file.file_size,
                                                             generate_file_report_path(output_path, group_image.image_name,
                                                                                       file.file_extension,
                                                                                       file.file_name, report)))
                            file_count += 1
                duplicate_images.append(ImageEntry(group_image.image_name, duplicate_files))
        duplicate_groups_data.append(DuplicateGroupData(group.file_hash, file_count, duplicate_images))

    # extension distribution
    extensions = [file.file_extension for file in image.files if file.file_extension] # list of all extensions
    extension_counts: dict[str, int] = dict(Counter(extensions)) # {ext: count, ...}

    # go through all duplicate group members
    extension_to_files: Dict[str, Set[File]] = {} # {ext: list[File]}
    extension_to_groups: Dict[str, Set[int]] = {} # {ext: list[group_id]}

    for group in duplicate_groups:
        for file in group.members_files:
            extension = file.file_extension
            if not extension:
                continue
            extension_to_files.setdefault(extension, set()).add(file)
            extension_to_groups.setdefault(extension, set()).add(group.id)

    extension_distribution: Dict[str, ExtensionEntry] = {}
    for ext, count in sorted(extension_counts.items()):
        duplicate_files = extension_to_files.get(ext, set())
        duplicate_groups = extension_to_groups.get(ext, set())

        extension_distribution[ext] = ExtensionEntry(ext, count, len(duplicate_groups), len(duplicate_files))

    return ImageOverviewData(
        parser_start=parsing_start,
        parser_end=PARSING_END,
        parser_parameters=parameters,
        foremost_invocation=image.foremost_invocation,
        foremost_start=image.foremost_scan_start.strftime("%Y-%m-%d %H:%M:%S") if image.foremost_scan_start else "",
        foremost_end=image.foremost_scan_end.strftime("%Y-%m-%d %H:%M:%S") if image.foremost_scan_end else "",
        foremost_version=image.foremost_version,
        exiftool_version=image.exiftool_version,
        hash_algorithm=hash_algorithm,
        original_output_dir=str(image.original_output_dir) if image.original_output_dir else "",
        image_name=image.image_name,
        image_size=image.image_size,
        total_number_files_parsed=len(image.files) if image.files else 0,
        total_number_files_foremost=image.foremost_files_total,
        foremost_parsed_extra=audit_table,
        total_size_files=total_file_size,
        number_extensions_parsed=len(extension_counts) if extension_counts else 0,
        extension_distribution=extension_distribution,
        top_ten_files=top_ten_files,
        files_extension_mismatch_count=len(files_extension_mismatch),
        files_extension_mismatch=files_extension_mismatch,
        number_duplicate_groups=len(image.duplicate_groups) if image.duplicate_groups else 0,
        number_duplicate_files=number_duplicate_files,
        top_ten_duplicate_groups=duplicate_groups_data,
        logs=[]     # TODO implement logs
    )

def generate_image_extensions_data(image_overview_data: ImageOverviewData, image: Image, output_path: Path, report: str, session: Session) -> List[ImageExtensionsData]:
    """
    Generate a list of file-extension-level data for an image report.

    Each entry contains aggregated statistics and detailed file listings
    for one extension.

    Args:
        image_overview_data (ImageOverviewData): Previously generated overview data.
        image (Image): SQLAlchemy Image object with files.
        output_path (Path): Base output path for report file links.
        report (str): Report format.
        session (Session): SQLAlchemy session for queries.

    Returns:
        List[ImageExtensionsData]: Aggregated per-extension report data.
    """
    image_extensions_data_list = []

    # sort all files by extension
    files_by_extension = defaultdict(list)
    for file in image.files:
        files_by_extension[file.file_extension].append(file)

    # go through files per extension
    for ext, files in files_by_extension.items():
        # files per extension
        number_files = len(files)
        # total file size per extension
        total_file_size = sum(file.file_size for file in files)
        # percentage of extensions
        percentage_extraction = image_overview_data.extension_distribution.get(ext, 0)

        # files per extension data
        files_per_extension = []

        # go through files per extension to generate file data
        for file in files:

            # creat duplicate files data
            duplicate_group = read_duplicate_group_by_file_id(file.id, session)
            duplicate_files = []
            if duplicate_group:
                files = duplicate_group.members_files
                for f in files:
                    if file.id == f.id:
                        continue
                    file_path = generate_file_report_path(output_path, f.image.image_name, ext, f.file_name, report)
                    duplicate_files.append(FileEntry(f.file_name, f.file_extension, f.file_size, file_path))

            files_per_extension.append(
                ImageFilesData(
                    file_name=file.file_name,
                    file_size=file.file_size,
                    file_extension=file.file_extension,
                    file_extension_mismatch=file.file_extension_mismatch,
                    file_path=str(file.file_path) if file.file_path else "",
                    file_report_path=generate_file_report_path(output_path, image.image_name, file.file_extension, file.file_name, report),
                    file_hash=file.file_hash,
                    file_hash_algorithm=image_overview_data.hash_algorithm,
                    file_type=file.file_type,
                    file_mime=file.file_mime,
                    file_offset=file.file_offset,
                    foremost_comment=file.foremost_comment,
                    is_exiftool=file.is_exiftool,
                    duplicate_group_hash=duplicate_group.file_hash if duplicate_group else None,
                    duplicate_files=duplicate_files,
                    additional_metadata=file.more_metadata
                )
            )

        # create extensions data object
        image_extensions_data_list.append(
            ImageExtensionsData(
                extension=ext,
                number_files=number_files,
                total_size_files=total_file_size,
                files=files_per_extension
            )
        )

    return image_extensions_data_list

def generate_report_data(
        input_path: Path,
        host_input_path: str,
        output_path: Path,
        host_output_path: str,
        report: str,
        with_images: bool,
        cross_image: bool,
        parsing_start: str,
        image_id: int,
        audit_table: dict
):
    """
    Orchestrates the generation of image overview and extension-level report data.

    Connects to the database, retrieves image data and computes all
    structured data needed to render the HTML report.

    Args:
        input_path (Path): Input image directory.
        host_input_path (str): Path to host input Foremost directory.
        output_path (Path): Output report directory.
        host_output_path (str): Output directory for the host output report directory.
        report (str): Report type (HTML, JSON).
        with_images (bool): Include image previews if True.
        cross_image (bool): Enable cross-image duplicate detection if True.
        parsing_start (str): Timestamp when parsing started.
        image_id (int): ID of the image to generate the report for.
        audit_table (dict): the audit_table dict after all parsed files were dropped.

    Returns:
        None

    Raises:
        Exception: If database connection fails or image cannot be read.
    """
    try:
        session = connect_database()
        if session is None:
            raise Exception("Could not connect to the database")

        # read the database data
        image = read_image(image_id, session)
        if image is None:
            raise Exception("Could not read the image. Aborting report!")

        ######################## calculate and gather data #################

        image_overview_data = generate_image_overview_data(input_path, host_input_path, output_path, host_output_path, report, with_images, cross_image, parsing_start, image, audit_table, session)
        image_extensions_data = generate_image_extensions_data(image_overview_data, image, output_path, report, session)

        report_path = Path(os.path.join(output_path, image.image_name))

        try:
            report_enum = ReportFormat(report.lower())

            if report_enum == ReportFormat.JSON:
                print("Generating JSON report...")
                generate_json_report(image_overview_data, image_extensions_data, report_path)
            else:
                print(f"Invalid report format: {report}", file=sys.stderr)
        except ValueError:
            print(f"Invalid report format: {report}.", file=sys.stderr)

    except Exception as e:
        print(f"Something went wrong while generating report data: {e}", file=sys.stderr)