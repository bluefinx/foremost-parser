# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

# this file creates the Image table

from sqlalchemy import Column, Integer, String, TIMESTAMP, BigInteger, JSON
from sqlalchemy.orm import validates

from app.models.base import Base

# database table image
class Image(Base):
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