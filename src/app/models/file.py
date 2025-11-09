"""
file.py

Defines the ORM model for storing individual files extracted by Foremost.

Each file is associated with a forensic image and contains metadata such as size,
hash, timestamps, MIME type and additional JSON metadata. Validation
ensures that string fields do not exceed their maximum length.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from sqlalchemy import Column, Integer, String, BigInteger, JSON, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import validates, relationship

from app.models.base import Base
from app.models.duplicate import Duplicate

# database table file
class File(Base):
    """
    Represents a single carved file in the database.

    Attributes:
        id (int): Primary key.
        image_id (int): Foreign key linking to the parent image.
        file_name (str): Name of the file.
        file_type (str | None): Type of the file.
        file_extension (str | None): File extension.
        file_mime (str | None): MIME type.
        file_size (int | None): Size of the file in bytes.
        file_offset (int | None): Offset within the source image.
        file_path (str | None): File path in output directory.
        file_hash (str | None): Hash of the file contents.
        is_exiftool (bool): Whether EXIFTool or Python was run on this file.
        is_duplicate (bool): Whether this file is marked as duplicate.
        foremost_comment (str | None): Optional comment from Foremost.
        more_metadata (dict | None): Additional JSON metadata.

    Notes:
        String fields are validated to ensure they do not exceed the
        database column length. Excess characters are truncated automatically.
    """
    __tablename__ = 'table_file'

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('table_image.id', ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(255))
    file_extension = Column(String(10))
    file_mime = Column(String(50))
    file_size = Column(BigInteger)
    file_offset = Column(BigInteger)
    file_path = Column(String(255))
    file_hash = Column(String(64))
    is_exiftool = Column(Boolean, default=True)
    is_duplicate = Column(Boolean, default=False)
    foremost_comment = Column(String(255))
    more_metadata = Column(JSON)

    image = relationship("Image", back_populates="files")

    duplicates = relationship(
        "Duplicate",
        foreign_keys=lambda: [Duplicate.file_id],
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="file"
    )

    duplicate_of = relationship(
        "Duplicate",
        foreign_keys=lambda: [Duplicate.duplicate_id],
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="duplicate"
    )

    # make sure to cut too long data before storing
    @validates('file_name')
    def validate_file_name(self, key, value):
        if value and len(value) > 255:
            return value[:255]
        return value

    @validates('file_type')
    def validate_file_type(self, key, value):
        if value and len(value) > 255:
            return value[:255]
        return value

    @validates('file_extension')
    def validate_file_extension(self, key, value):
        if value and len(value) > 10:
            return value[:10]
        return value

    @validates('file_mime')
    def validate_file_mime(self, key, value):
        if value and len(value) > 50:
            return value[:50]
        return value

    @validates('file_path')
    def validate_file_path(self, key, value):
        if value and len(value) > 255:
            return value[:255]
        return value

    @validates('file_hash')
    def validate_file_hash(self, key, value):
        if value and len(value) > 64:
            return value[:64]
        return value

    @validates('foremost_comment')
    def validate_foremost_comment(self, key, value):
        if value and len(value) > 255:
            return value[:255]
        return value