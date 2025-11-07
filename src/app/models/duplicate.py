# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

# this file creates the Duplicate table
from sqlalchemy import Column, Integer, CheckConstraint, ForeignKey

from app.models.base import Base

# database table duplicate
class Duplicate(Base):
    __tablename__ = 'table_duplicate'
    # make the pairs symmetric and prevent double entries, so only one entry per pair
    __table_args__ = (
        CheckConstraint('file_id < duplicate_id'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('table_file.id', ondelete='CASCADE'))
    duplicate_id = Column(Integer, ForeignKey('table_file.id', ondelete='CASCADE'))