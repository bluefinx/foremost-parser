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

class ImageOverviewData:
    """
    Represents the aggregated overview data for a forensic image analysis report.

    This class is used to store all relevant metadata, statistics, duplicate
    information and logs for a single image, which can then be rendered into
    a report.

    Attributes:
        parser_start (str): Start timestamp of the parser execution.
        parser_end (str): End timestamp of the parser execution.
        parser_parameters (Dict[str, Union[str, bool]]): Parameters passed to the parser.
        foremost_start (str): Start timestamp of the Foremost scan.
        foremost_end (str): End timestamp of the Foremost scan.
        foremost_version (str): Version of Foremost used.
        exiftool_version (str): Version of ExifTool used.
        hash_algorithm (str): Hash algorithm used for duplicate detection (e.g., SHA-256).
        input_path (str): Absolute path to the input image directory.
        image_name (str): Name of the forensic image.
        image_size (int): Size of the image in bytes.
        image_creation_date (str): Creation date of the image.
        total_number_files (int): Total number of files extracted from the image.
        total_size_files (int): Total size of all extracted files in bytes.
        number_extensions (int): Number of unique file extensions detected.
        extension_distribution (Dict[str, int]): Mapping of file extensions to file counts.
        top_ten_files (List[Dict[str, str]]): List of the top 10 largest files with their attributes.
        number_duplicate_groups (int): Total number of duplicate groups detected.
        duplicate_groups (List[Dict[str, str]]): List of duplicates, including hash, file count, and linked images.
        logs (List[str]): List of error or warning messages encountered during processing.
    """
    def __init__(
        self,
        parser_start: str,
        parser_end: str,
        parser_parameters: Dict[str, Union[str, bool]],
        foremost_start: str,
        foremost_end: str,
        foremost_version: str,
        exiftool_version: str,
        hash_algorithm: str,
        input_path: str,
        image_name: str,
        image_size: int,
        image_creation_date: str,
        total_number_files: int,
        total_size_files: int,
        number_extensions: int,
        extension_distribution: Dict[str, int],
        top_ten_files: List[Dict[str, str]],
        number_duplicate_groups: int,
        duplicate_groups: List[Dict[str, str]],
        logs: List[str]
    ):
        self.parser_start = parser_start
        self.parser_end = parser_end
        self.parser_parameters = parser_parameters
        self.foremost_start = foremost_start
        self.foremost_end = foremost_end
        self.foremost_version = foremost_version
        self.exiftool_version = exiftool_version
        self.hash_algorithm = hash_algorithm
        self.input_path = input_path
        self.image_name = image_name
        self.image_size = image_size
        self.image_creation_date = image_creation_date
        self.total_number_files = total_number_files
        self.total_size_files = total_size_files
        self.number_extensions = number_extensions
        self.extension_distribution = extension_distribution
        self.top_ten_files = top_ten_files
        self.number_duplicate_groups = number_duplicate_groups
        self.duplicate_groups = duplicate_groups
        self.logs = logs