"""
image.py

Defines the ORM model for storing forensic images processed by Foremost.

Each image record stores metadata about the image file itself and
information about the Foremost scan, including version, scan timestamps
and the number of files recovered.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from sqlalchemy import Column, Integer, String, TIMESTAMP, BigInteger, JSON
from sqlalchemy.orm import validates, relationship

from app.models.base import Base
from app.models.duplicate import duplicate_group_image_association

# database table image
class Image(Base):
    """
    Represents a forensic image in the database.

    This class stores all metadata related to a source image that was parsed
    by Foremost, including file counts, timestamps, and tool versions. It also
    manages relationships to carved files, their minimal hash entries, and any
    duplicate groups associated with this image.

    Attributes:
        id (int): Primary key.
        image_name (str | None): Name of the image.
        image_size (int | None): Size of the image in bytes.
        create_date (datetime | None): Timestamp when the image was created.
        exiftool_version (str | None): Version of EXIFTool used.
        foremost_version (str | None): Version of Foremost used.
        foremost_scan_start (datetime | None): Start timestamp of the Foremost scan.
        foremost_scan_end (datetime | None): End timestamp of the Foremost scan.
        foremost_files_total (int | None): Total number of files recovered by Foremost.
        foremost_files_individual (dict | None): Number of files per extension.
        files (List[File]): All File objects carved from this image.
            Cascade ensures that deleting an Image deletes its Files and
            related DuplicateMember entries automatically.
        hash_entries (List[FileHash]): Minimal hash entries for all Files,
            used for efficient duplicate detection.
        duplicate_groups (List[DuplicateGroup]): All DuplicateGroups that
            contain files from this image. Managed via the
            Many-to-Many association table `duplicate_group_image_association`.
    """
    __tablename__ = 'table_image'

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String(255))
    image_size = Column(BigInteger)
    create_date = Column(TIMESTAMP)
    exiftool_version = Column(String(50))
    foremost_version = Column(String(50))
    foremost_scan_start = Column(TIMESTAMP)
    foremost_scan_end = Column(TIMESTAMP)
    foremost_files_total = Column(BigInteger)
    foremost_files_individual = Column(JSON)

    files = relationship(
        "File",
        back_populates="image",
        cascade="all, delete, delete-orphan",
        passive_deletes=True)

    hash_entries = relationship("FileHash", back_populates="image", cascade="all, delete-orphan")

    duplicate_groups = relationship(
        "DuplicateGroup",
        secondary=duplicate_group_image_association,
        back_populates="images"
    )

    # make sure to cut too long data before storing
    @validates('image_name')
    def validate_image_name(self, key, value):
        if value and len(value) > 255:
            return value[:255]
        return value

    @validates('exiftool_version')
    def validate_exiftool_version(self, key, value):
        if value and len(value) > 50:
            return value[:50]
        return value

    @validates('foremost_version')
    def validate_foremost_version(self, key, value):
        if value and len(value) > 50:
            return value[:50]
        return value