"""
image_extensions_data.py

Defines the data structure for storing aggregated information about files
grouped by their file extension. This is used to generate extension-level
pages in the report, showing statistics and file listings per extension.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from typing import List, Optional

from app.report.image_files_data import ImageFilesData

class ImageExtensionsData:
    """
    Stores aggregated information about files of a specific file extension.

    This class represents the summary and detailed listing of all files
    with the same extension, used in the report to show statistics and
    optionally render previews for image files.

    Attributes:
        number_files (int): Total number of files with this extension.
        total_size_files (int): Combined size of all files with this extension, in bytes.
        percentage_extraction (float): Percentage of all files that this extension represents.
        files (List[ImageFilesData]): List of ImageFilesData objects for each file
            with this extension, including metadata, duplicates, and optional image previews.
    """
    def __init__(
        self,
        number_files: int,
        total_size_files: int,
        percentage_extraction: float,
        files: Optional[List[ImageFilesData]] = None,
    ):
        self.number_files = number_files
        self.total_size_files = total_size_files
        self.percentage_extraction = percentage_extraction
        self.files = files