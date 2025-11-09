"""
duplicate.py

Defines the ORM model for storing duplicate file pairs in the database.
Ensures that each duplicate pair is stored only once by enforcing
a symmetric constraint.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

from sqlalchemy import Column, Integer, CheckConstraint, ForeignKey

from app.models.base import Base

# database table duplicate
class Duplicate(Base):
    """
    Represents a pair of duplicate files in the database.

    Attributes:
        id (int): Primary key.
        file_id (int): Foreign key to the first file.
        duplicate_id (int): Foreign key to the duplicate file.

    Notes:
        The CheckConstraint ensures that only one entry per duplicate pair exists
        by requiring file_id < duplicate_id, making the relationship symmetric.
    """
    __tablename__ = 'table_duplicate'
    # make the pairs symmetric and prevent double entries, so only one entry per pair
    __table_args__ = (
        CheckConstraint('file_id < duplicate_id'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('table_file.id', ondelete='CASCADE'))
    duplicate_id = Column(Integer, ForeignKey('table_file.id', ondelete='CASCADE'))