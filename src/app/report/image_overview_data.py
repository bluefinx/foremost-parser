"""
image_overview_data.py

Defines data structures for storing image analysis results to be rendered
into a report. Includes overview metadata, file-level details and
file-extension-level aggregations.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from typing import List, Dict, Union
from dataclasses import dataclass

@dataclass
class FileEntry:
    """
    Represents a single file entry within an image or duplicate group.

    Attributes:
        file_name (str): The name of the file.
        file_extension (str): The file extension (e.g., 'jpg', 'txt').
        report_path (str): The report path for the file (detail page).
    """
    file_name: str
    file_extension: str
    file_size: int
    report_path: str

    def to_dict(self):
        """
        Convert the FileEntry object into a JSON-serializable dict.

        Returns:
            Dict[str, str]: A dictionary containing file metadata.
        """
        return {
            "file_name": self.file_name,
            "file_extension": self.file_extension,
            "file_size": self.file_size,
            "report_path": self.report_path
        }

@dataclass
class ImageEntry:
    """
    Represents an image and its associated files within a duplicate group.

    Attributes:
        image_name (str): The name of the image.
        image_files (List[FileEntry]): List of files belonging to this image.
    """
    image_name: str
    image_files: List[FileEntry]

    def to_dict(self):
        """
        Convert the ImageEntry object into a JSON-serializable dict.

        Returns:
            Dict[str, Union[str, List[Dict]]]: Serialized image entry.
        """
        return {
            "image_name": self.image_name,
            "image_files": [f.to_dict() for f in self.image_files]
        }

@dataclass
class DuplicateGroupData:
    """
    Represents a group of duplicate files across one or more images.

    Attributes:
        duplicate_hash (str): The hash of the duplicates.
        file_count (int): Total number of files in this duplicate group.
        linked_images (List[ImageEntry]): List of images with their associated duplicate files.
    """
    duplicate_hash: str
    file_count: int
    linked_images: List[ImageEntry]

    def to_dict(self):
        """
        Convert the duplicate group into a JSON-serializable dict.

        Returns:
            Dict[str, Union[str, int, List[Dict]]]: Serialized duplicate group data.
        """
        return {
            "duplicate_hash": self.duplicate_hash,
            "file_count": self.file_count,
            "linked_images": [img.to_dict() for img in self.linked_images]
        }

class ImageOverviewData:
    """
    Aggregated overview data for a forensic image analysis report.

    Stores metadata, statistics, duplicate information, and logs for a single image.

    Attributes:
        parser_start (str): Start timestamp of the parser execution.
        parser_end (str): End timestamp of the parser execution.
        parser_parameters (Dict[str, Union[str, bool]]): Python parameters passed to the parser.
        foremost_invocation (str): Foremost invocation command.
        foremost_start (str): Start timestamp of the Foremost scan.
        foremost_end (str): End timestamp of the Foremost scan.
        foremost_version (str): Version of Foremost used.
        exiftool_version (str): Version of ExifTool used.
        hash_algorithm (str): Hash algorithm used for duplicate detection (e.g., SHA-256).
        original_output_dir (str): Original Foremost output directory.
        image_name (str): Name of the forensic image.
        image_size (int): Size of the image in bytes.
        total_number_files_parsed (int): Total number of files parsed from the image.
        total_number_files_foremost (int): Total number of files found by Foremost.
        total_size_files (int): Total size of all parsed files in bytes.
        number_extensions_parsed (int): Number of unique file extensions parsed.
        extension_distribution (Dict[str, int]): Mapping of file extensions to file counts.
        top_ten_files (List[FileEntry]): List of the top 10 largest files.
        number_duplicate_groups (int): Total number of duplicate groups detected.
        duplicate_groups (List[DuplicateGroupData]): List of duplicate groups with linked images and files.
        logs (List[str]): List of error or warning messages encountered during processing.
    """
    def __init__(
        self,
        parser_start: str,
        parser_end: str,
        parser_parameters: Dict[str, Union[str, bool]],
        foremost_invocation: str,
        foremost_start: str,
        foremost_end: str,
        foremost_version: str,
        exiftool_version: str,
        hash_algorithm: str,
        original_output_dir: str,
        image_name: str,
        image_size: int,
        total_number_files_parsed: int,
        total_number_files_foremost: int,
        total_size_files: int,
        number_extensions_parsed: int,
        extension_distribution: Dict[str, int],
        top_ten_files: List[FileEntry],
        number_duplicate_groups: int,
        duplicate_groups: List[DuplicateGroupData],
        logs: List[str]
    ):
        self.parser_start = parser_start
        self.parser_end = parser_end
        self.parser_parameters = parser_parameters
        self.foremost_invocation = foremost_invocation
        self.foremost_start = foremost_start
        self.foremost_end = foremost_end
        self.foremost_version = foremost_version
        self.exiftool_version = exiftool_version
        self.hash_algorithm = hash_algorithm
        self.original_output_dir = original_output_dir
        self.image_name = image_name
        self.image_size = image_size
        self.total_number_files_parsed = total_number_files_parsed
        self.total_number_files_foremost = total_number_files_foremost
        self.total_size_files = total_size_files
        self.number_extensions_parsed = number_extensions_parsed
        self.extension_distribution = extension_distribution
        self.top_ten_files = top_ten_files
        self.number_duplicate_groups = number_duplicate_groups
        self.duplicate_groups = duplicate_groups
        self.logs = logs

    def to_dict(self):
        """
        Convert the entire ImageOverviewData structure into a JSON-serializable form.

        Returns:
            Dict: Nested dictionary containing all overview metadata,
                  file statistics, duplicate group data, and log entries.
        """
        return {
            "parser_start": self.parser_start,
            "parser_end": self.parser_end,
            "parser_parameters": self.parser_parameters,
            "foremost_invocation": self.foremost_invocation,
            "foremost_start": self.foremost_start,
            "foremost_end": self.foremost_end,
            "foremost_version": self.foremost_version,
            "exiftool_version": self.exiftool_version,
            "hash_algorithm": self.hash_algorithm,
            "original_output_dir": self.original_output_dir,
            "image_name": self.image_name,
            "image_size": self.image_size,
            "total_number_files_parsed": self.total_number_files_parsed,
            "total_number_files_foremost": self.total_number_files_foremost,
            "total_size_files": self.total_size_files,
            "number_extensions_parsed": self.number_extensions_parsed,
            "extension_distribution": self.extension_distribution,
            "top_ten_files": [
                f.to_dict() for f in self.top_ten_files
            ] if self.top_ten_files else [],
            "number_duplicate_groups": self.number_duplicate_groups,
            "duplicate_groups": [
                g.to_dict() for g in self.duplicate_groups
            ] if self.duplicate_groups else [],
            "logs": self.logs,
        }
