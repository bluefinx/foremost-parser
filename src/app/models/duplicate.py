"""
duplicate.py

Defines the ORM models for storing duplicate file groups in the database.

This module provides two main classes:
1. DuplicateGroup: Represents a group of files that share the same hash,
   effectively capturing all duplicates across one or multiple images.
2. DuplicateMember: Association table linking files to their duplicate group,
   implementing a many-to-many relationship between File and DuplicateGroup.

The design avoids storing redundant pairwise duplicates, instead
grouping duplicates together, which simplifies queries and reporting.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.models.base import Base

# Association table linking DuplicateGroups to Images.
# Each entry represents that an Image contains one or more files
# belonging to a particular DuplicateGroup. Enables many-to-many
# cross-image duplicate tracking.
duplicate_group_image_association = Table(
    "duplicate_group_image_association",
    Base.metadata,
    Column("duplicate_group_id", Integer, ForeignKey("table_duplicate_group.id", ondelete="CASCADE"), primary_key=True),
    Column('image_id', Integer, ForeignKey('table_image.id', ondelete="CASCADE"), primary_key=True)
)

# database table duplicate group
class DuplicateGroup(Base):
    """
    ORM model for a group of duplicate files.

    Each DuplicateGroup represents a set of files that share the same hash.
    A DuplicateGroup can be linked to multiple images via a Many-to-Many
    relationship, allowing cross-image duplicate tracking.

    Attributes:
        id (int): Primary key of the duplicate group.
        file_hash (str): Hash value shared by all files in this group.
        members (List[DuplicateMember]): Association entries linking files to this group.
        members_files (List[File]): All File objects in this group, accessible
            via the DuplicateMember association. viewonly=True ensures changes
            are managed via DuplicateMember.
        images (List[Image]): All Image objects containing files in this group.
            Managed via the Many-to-Many association table `duplicate_group_image_association`.
    """

    __tablename__ = 'table_duplicate_group'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String(64), unique=True, nullable=False)

    members = relationship("DuplicateMember", back_populates="group")
    members_files = relationship(
        "File",
        secondary="table_duplicate_member",
        back_populates="duplicate_groups",
        viewonly=True
    )

    images = relationship(
        "Image",
        secondary=duplicate_group_image_association,
        back_populates="duplicate_groups"
    )

# database table duplicate member
class DuplicateMember(Base):
    """
    Association table linking files to duplicate groups.

    Each entry represents one file being a member of a duplicate group.

    Attributes:
        group_id (int): Foreign key to DuplicateGroup.id.
        file_id (int): Foreign key to File.id.
        group (DuplicateGroup): Relationship back to the duplicate group.
        file (File): Relationship back to the File object.
    """

    __tablename__ = 'table_duplicate_member'

    group_id = Column(Integer, ForeignKey("table_duplicate_group.id", ondelete="CASCADE"), primary_key=True)
    file_id = Column(Integer, ForeignKey("table_file.id", ondelete="CASCADE"), primary_key=True, unique=True)

    group = relationship("DuplicateGroup", back_populates="members")
    file = relationship("File", back_populates="duplicate_memberships")