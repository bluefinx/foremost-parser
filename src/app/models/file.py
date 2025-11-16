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
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import validates, relationship

from app.models.base import Base

# database table file
class File(Base):
    """
    Represents a single carved file in the database.

    This class stores all metadata related to a file extracted by Foremost,
    including hash, size, offsets, MIME type and optional Foremost comments.
    It also links the file to its parent Image and to any duplicate groups
    it belongs to.

    Attributes:
        id (int): Primary key.
        image_id (int): Foreign key linking to the parent Image.
        file_name (str): Name of the file.
        file_type (str | None): Type of the file.
        file_extension (str | None): File extension.
        file_extension_mismatch (bool | None): Whether the file extension found by Foremost
            and that by Exiftool are the same.
        file_mime (str | None): MIME type.
        file_size (int | None): Size of the file in bytes.
        file_offset (int | None): Offset within the source image.
        file_path (str | None): File path in output directory.
        file_hash (str | None): Hash of the file contents.
        is_exiftool (bool): Whether EXIFTool or Python fallback was used.
        is_duplicate (bool): Whether this file is marked as duplicate.
        foremost_comment (str | None): Optional comment from Foremost.
        more_metadata (dict | None): Additional JSON metadata.
        image (Image): Relationship to the parent Image.
        hash_entries (List[FileHash]): Minimal hash entries for efficient duplicate detection,
            used for cross-image duplicate lookups.
        duplicate_memberships (List[DuplicateMember]): Association entries linking
            this file to its duplicate groups.
        duplicate_groups (List[DuplicateGroup]): All DuplicateGroup objects this
            file belongs to. viewonly=True ensures membership is managed via
            DuplicateMember.
    """
    __tablename__ = 'table_file'

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('table_image.id', ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(255))
    file_extension = Column(String(10))
    file_extension_mismatch = Column(Boolean, default=False)
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

    hash_entries = relationship("FileHash", back_populates="file", cascade="all, delete-orphan")

    duplicate_memberships = relationship(
        "DuplicateMember",
        back_populates="file",
        cascade="all, delete-orphan"
    )

    duplicate_groups = relationship(
        "DuplicateGroup",
        secondary="table_duplicate_member",
        back_populates="members_files",
        viewonly=True
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

class FileHash(Base):
    """
    Represents a minimal hash entry for a carved file, used for efficient
    duplicate detection across one or multiple images.

    This table stores only the file ID, its hash and the associated image ID,
    allowing fast lookups when checking for duplicates. It is designed to be
    memory-efficient and performant for cross-image duplicate searches.

    Attributes:
        id (int): Primary key.
        file_id (int): Foreign key linking to the File object.
        file_hash (str): Hash of the file contents.
        image_id (int): Foreign key linking to the parent Image.
        file (File): Relationship back to the File object.
        image (Image): Relationship back to the Image object.
    """
    __tablename__ = 'table_file_hash'

    __table_args__ = (
        # index for performative lookup
        Index('ix_file_hash', 'file_hash'),
        # only one file with same hash and ID can be stored
        UniqueConstraint('file_id', 'file_hash'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('table_file.id', ondelete="CASCADE"))
    file_hash = Column(String(64), nullable=False)
    image_id = Column(Integer, ForeignKey('table_image.id', ondelete="CASCADE"))

    file = relationship("File", back_populates="hash_entries")
    image = relationship("Image", back_populates="hash_entries")