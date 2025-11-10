"""
image_files_data.py

Defines the data structure for storing detailed information about individual files
extracted from a forensic image. This data is used to generate file-level pages in
the report, including metadata, duplicates and optional image previews.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from typing import Optional, List

class ImageFilesData:
    """
    Stores detailed information for a single file extracted from a forensic image.

    This includes file metadata, duplicate information and optionally
    extracted metadata (e.g., from ExifTool or Python analysis).

    Attributes:
        file_name (str): Name of the file.
        file_size (int): Size of the file in bytes.
        file_extension (str): File extension (e.g., 'jpg', 'txt').
        file_path (Optional[str]): Absolute path for image files; None for non-image files.
        file_report_path (str): Relative link to the file's HTML report page.
        file_hash (str): Hash value of the file.
        file_hash_algorithm (str): Hash algorithm used for this file (e.g., SHA-256).
        file_type (str): Detected type of the file.
        file_mime (str): MIME type of the file.
        file_offset (int): Offset within the image where the file was found.
        foremost_comment (Optional[str]): Foremost parser comment for the file.
        is_exiftool (bool): True if metadata was extracted using ExifTool or Python.
        duplicate_group_hash (Optional[str]): Hash of the duplicate group this file belongs to.
        duplicate_files (Optional[List[str]]): List of file_report_paths of duplicate files, if any.
        additional_metadata (Optional[List[str]]): Any extra metadata extracted from the file.
    """
    def __init__(
        self,
        file_name: str,
        file_size: int,
        file_extension: str,
        file_path: Optional[str],        # for image files
        file_report_path: str,           # link within HTML report
        file_hash: str,
        file_hash_algorithm: str,
        file_type: str,
        file_mime: str,
        file_offset: int,
        foremost_comment: Optional[str],
        is_exiftool: bool,
        duplicate_group_hash: Optional[str],
        duplicate_files: Optional[List[str]],   # file_report_paths
        additional_metadata: Optional[List[str]]
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