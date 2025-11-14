"""
image_extensions_data.py

Defines the data structure for storing aggregated information about files
grouped by their file extension. This is used to generate extension-level
pages in the report, showing statistics and file listings per extension.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from typing import List, Dict, Any

from app.report.image_files_data import ImageFilesData

class ImageExtensionsData:
    """
    Stores aggregated information about files of a specific file extension.

    This class represents the summary and detailed listing of all files
    with the same extension. It is used in the report to show statistics,
    percentages, and optionally render previews for image files.

    Attributes:
        extension (str): The file extension of the files.
        number_files (int): Total number of files with this extension.
        total_size_files (int): Combined size of all files with this extension, in bytes.
        files (List[ImageFilesData]): List of ImageFilesData objects for each file
            with this extension, including metadata, duplicates and optional image previews.
    """
    def __init__(
        self,
        extension: str,
        number_files: int,
        total_size_files: int,
        files: List[ImageFilesData],
    ):
        self.extension = extension
        self.number_files = number_files
        self.total_size_files = total_size_files
        self.files = files

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this ImageExtensionsData instance into a JSON-serializable dictionary.

        This method serializes all high-level extension statistics as well as the full
        list of underlying ImageFilesData objects. Each file entry is converted using
        its own to_dict() method to ensure complete JSON compatibility.

        Returns:
            Dict[str, Any]: A JSON-safe representation of this extension group,
            including aggregated statistics and detailed per-file information.
        """
        return {
            "extension": self.extension,
            "number_files": self.number_files,
            "total_size_files": self.total_size_files,
            "files": [file.to_dict() for file in self.files],
        }
