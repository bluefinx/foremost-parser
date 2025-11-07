# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

# this file creates the File table

from sqlalchemy import Column, Integer, String, TIMESTAMP, BigInteger, JSON, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import validates

from app.models.base import Base

# database table file
class File(Base):
    __tablename__ = 'table_file'

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('table_image.id'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(255))
    file_extension = Column(String(10))
    file_mime = Column(String(50))
    file_size = Column(BigInteger)
    file_offset = Column(BigInteger)
    file_path = Column(String(255))
    file_hash = Column(String(64))
    timestamp_mod = Column(TIMESTAMP(timezone=True))
    timestamp_acc = Column(TIMESTAMP(timezone=True))
    timestamp_cre = Column(TIMESTAMP(timezone=True))
    timestamp_ino = Column(TIMESTAMP(timezone=True))
    is_exiftool = Column(Boolean, default=True)
    is_duplicate = Column(Boolean, default=False)
    foremost_comment = Column(String(255))
    more_metadata = Column(JSON)

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

    @validates('foremost_comment')
    def validate_foremost_comment(self, key, value):
        if value and len(value) > 255:
            return value[:255]
        return value