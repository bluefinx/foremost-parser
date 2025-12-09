"""
db.py

Handles database initialisation and connections for Foremost-Parser.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import os
import time
import sys

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.base import Base

# Path to the database password file in Docker secrets
PASSWORD_FILE_PATH = "/run/secrets/db-password"

# create database URL for connection
def create_database_url(db_password) -> URL:
    """
    Creates a SQLAlchemy database URL for connecting to the PostgreSQL database.

    Args:
        db_password (str): The database password.

    Returns:
        sqlalchemy.engine.URL: Configured SQLAlchemy URL object for the database.
    """
    return URL.create(
        drivername="postgresql+psycopg2",
        username="foremostparser",
        password=db_password,
        host="db",
        port=5432,
        database="foremostparser-db",
    )

#################################################
# create/delete database
#################################################

# connect to the database and create tables
def create_database() -> bool:
    """
    Connects to the PostgreSQL database and creates the required tables.

    Reads the database password from the password file specified in the
    environment variable POSTGRES_PASSWORD_FILE or the default PASSWORD_FILE_PATH.
    Attempts to connect repeatedly until the database is ready, then creates all tables.

    Returns:
        bool: True if the database was successfully created and tables were initialised,
              False if the password was not found or the connection failed.
    """
    try:
        # read the password from the password file
        with open(os.getenv("POSTGRES_PASSWORD_FILE", PASSWORD_FILE_PATH)) as file:
            DB_PASSWORD = file.read().strip()
        # check if the password is existing
        if DB_PASSWORD:
            # connect to database and create tables if not already existing

            DATABASE_URL = create_database_url(DB_PASSWORD)

            ## TODO maybe find a more elegant fix
            # wait for database to be ready
            # this is a dirty solution but via compose.yaml was not working
            # without the database complaining about not finding a user or database
            while True:
                try:
                    print("Waiting for database...")
                    engine = create_engine(DATABASE_URL)
                    with engine.connect():
                        Base.metadata.create_all(engine)
                        print(f"Database created.")
                        return True
                except SQLAlchemyError as e:
                    print(f"Database connection failed: {e} ", file=sys.stderr)
                    time.sleep(3)
        else:
            print("Password for database not found - could not connect.", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Database connection failed: {e} ", file=sys.stderr)
        return False

#################################################
# connect to database
#################################################

# establish connection to database
def connect_database() -> Optional[Session]:
    """
    Establishes a connection to the PostgreSQL database and returns a session.

    Reads the database password from the password file specified in the
    environment variable POSTGRES_PASSWORD_FILE or the default PASSWORD_FILE_PATH.
    If the password is found, attempts to connect to the database and create a session.

    Returns:
        sqlalchemy.orm.session.Session | None: A SQLAlchemy session object if the connection
        was successful or None if the password was missing or the connection failed.
    """
    try:
        # read the password from the password file
        with open(os.getenv("POSTGRES_PASSWORD_FILE", PASSWORD_FILE_PATH)) as file:
            DB_PASSWORD = file.read().strip()
        # check if the password is existing
        if DB_PASSWORD:
            # connect to database
            DATABASE_URL = create_database_url(DB_PASSWORD)
            # create database connection
            engine = create_engine(DATABASE_URL)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            return session
        else:
            print("Password for database not found - could not connect.", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Database connection failed: {e} ", file=sys.stderr)
        return None