"""
db.py

Handles database initialisation and connections for Foremost-Parser.

Functions:
    create_database(): Creates the database if it does not exist.
    connect_database(): Connects to the database and returns a session object.

Author: bluefinx
Copyright (c) 2025 bluefinx
License: GNU General Public License v3.0
"""

import os
import time
import sys

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.models.base import Base

# Path to the database password file in Docker secrets
PASSWORD_FILE_PATH = "/run/secrets/db-password"

# create database URL for connection
def create_database_url(db_password):
    """
    Creates a SQLAlchemy database URL for connecting to the PostgreSQL database.

    Args:
        db_password (str): The database password.

    Returns:
        sqlalchemy.engine.URL: A SQLAlchemy URL object configured for the Foremost-Parser database.
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
# create database
#################################################

# connect to the database and create tables
def create_database():
    """
    Connects to the PostgreSQL database and creates the required tables.

    Reads the database password from the password file specified in the
    environment variable POSTGRES_PASSWORD_FILE or the default PASSWORD_FILE_PATH.
    Attempts to connect repeatedly until the database is ready, then creates all tables.

    Returns:
        bool: True if the database was successfully created and tables were initialised,
              False if the password was not found or the connection failed.
    """
    # read the password from the password file
    with open(os.getenv("POSTGRES_PASSWORD_FILE", PASSWORD_FILE_PATH)) as file:
        DB_PASSWORD = file.read().strip()
    # check if the password is existing
    if DB_PASSWORD:
        # connect to database and create tables if not already existing

        ## TODO maybe find a more elegant fix
        # wait for database to be ready
        # this is a dirty solution but via compose.yaml was not working
        # without the database complaining about not finding a user or database
        while True:
            print("Waiting for database...")
            try:
                DATABASE_URL = create_database_url(DB_PASSWORD)
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

#################################################
# connect to database
#################################################

# establish connection to database
def connect_database():
    """
    Establishes a connection to the PostgreSQL database and returns a session.

    Reads the database password from the password file specified in the
    environment variable POSTGRES_PASSWORD_FILE or the default PASSWORD_FILE_PATH.
    If the password is found, attempts to connect to the database and create a session.

    Returns:
        sqlalchemy.orm.session.Session | None: A SQLAlchemy session object if the connection
        was successful, or None if the password was missing or the connection failed.
    """
    # read the password from the password file
    with open(os.getenv("POSTGRES_PASSWORD_FILE", PASSWORD_FILE_PATH)) as file:
        DB_PASSWORD = file.read().strip()
    # check if the password is existing
    if DB_PASSWORD:
        # connect to database
        try:
            DATABASE_URL = create_database_url(DB_PASSWORD)
            # create database connection
            engine = create_engine(DATABASE_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            return session
        except SQLAlchemyError as e:
            print(f"Database connection failed: {e} ", file=sys.stderr)
            return None
    else:
        print("Password for database not found - could not connect.", file=sys.stderr)
        return None