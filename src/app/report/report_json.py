"""
report_json.py

Provides functionality to generate a JSON report for Foremost outputs.

This module takes structured image overview and per-extension data and writes
them into JSON files. Each image has an 'image.json' and each file extension
has a separate JSON file named after the extension.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import os
import json
import sys

from typing import List
from pathlib import Path

from app.report.image_extensions_data import ImageExtensionsData
from app.report.image_overview_data import ImageOverviewData


def generate_json_report(image_overview_data: ImageOverviewData, image_extensions_data: List[ImageExtensionsData], report_path: Path):
    """
    Generates JSON report files for a Foremost scan.

    This function creates a directory at `report_path` (if it doesn't exist)
    and writes:
      1. `image.json` containing the overview data
      2. One JSON file per extension with detailed file information

    Args:
        image_overview_data (ImageOverviewData): Aggregated overview data
            for the image, including metadata, statistics, duplicates and logs.
        image_extensions_data (List[ImageExtensionsData]): List of per-extension
            detailed data, including files and metadata.
        report_path (Path): Directory where JSON files will be created.

    Raises:
        Exception: Any exception raised during file creation or JSON dumping
            is caught and logged to stderr.
    """
    try:

        report_path.mkdir(parents=True, exist_ok=True)

        # image.json file
        file_path = os.path.join(report_path, "image.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(image_overview_data.to_dict(), f, indent=4)

        # per extension, one JSON file
        for image_extension in image_extensions_data:
            ext_dir = os.path.join(report_path, image_extension.extension)
            os.makedirs(ext_dir, exist_ok=True)
            file_path = os.path.join(ext_dir, f"{image_extension.extension}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(image_extension.to_dict(), f, indent=4)

        print(f"Report generated at {report_path}")

    except Exception as ex:
        print(f"Something went wrong while generating JSON report: {ex}", file=sys.stderr)

