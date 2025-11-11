"""
image_files_data.py

Defines the data structure for storing detailed information about individual files
extracted from a forensic image. This data is used to generate file-level pages in
the report, including metadata, duplicates, and optional image previews.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from typing import List, Union, Dict, Any

from app.report.image_overview_data import FileEntry

AdditionalMetadata = Union[Dict[str, Any], List[Any]]

class ImageFilesData:
    """
    Stores detailed information for a single file extracted from a forensic image.

    This class contains all relevant metadata, duplicate information, and optionally
    extracted metadata (e.g., from ExifTool or Python analysis). It is used to
    generate file-level report pages.

    Attributes:
        file_name (str): Name of the file.
        file_size (int): Size of the file in bytes.
        file_extension (str): File extension (e.g., 'jpg', 'txt').
        file_path (str): Absolute path for image files; can be empty for non-image files.
        file_report_path (str): Relative link to the file's HTML report page.
        file_hash (str): Hash value of the file.
        file_hash_algorithm (str): Hash algorithm used for this file (e.g., SHA-256).
        file_type (str): Detected type of the file.
        file_mime (str): MIME type of the file.
        file_offset (int): Offset within the image where the file was found (according to Foremost).
        foremost_comment (str): Foremost parser comment for the file.
        is_exiftool (bool): True if metadata was extracted using ExifTool, false for Python extraction.
        duplicate_group_hash (str): Hash of the duplicate group this file belongs to.
        duplicate_files (List[FileEntry]): List of duplicate files with report paths.
        additional_metadata (Union[Dict[str, Any], List[Any]]): Any extra metadata extracted from the file.
    """
    def __init__(
        self,
        file_name: str,
        file_size: int,
        file_extension: str,
        file_path: str,                  # for image files
        file_report_path: str,           # link within HTML report
        file_hash: str,
        file_hash_algorithm: str,
        file_type: str,
        file_mime: str,
        file_offset: int,
        foremost_comment: str,
        is_exiftool: bool,
        duplicate_group_hash: str,
        duplicate_files: List[FileEntry],      # file_report_paths
        additional_metadata: AdditionalMetadata
    ):
        self.file_name = file_name
        self.file_size = file_size
        self.file_extension = file_extension
        self.file_path = file_path
        self.file_report_path = file_report_path
        self.file_hash = file_hash
        self.file_hash_algorithm = file_hash_algorithm
        self.file_type = file_type
        self.file_mime = file_mime
        self.file_offset = file_offset
        self.foremost_comment = foremost_comment
        self.is_exiftool = is_exiftool
        self.duplicate_group_hash = duplicate_group_hash
        self.duplicate_files = duplicate_files
        self.additional_metadata = additional_metadata