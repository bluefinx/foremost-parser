# fmparser - Copyright (c) 2025 bluefinx
# Licensed under the GNU General Public License v3.0

# this file handles the database connections and initialising

import os
import time

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.models.base import Base

PASSWORD_FILE_PATH = "/run/secrets/db-password"

def create_database_url(db_password):
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
    # read the password from the password file
    with open(os.getenv("POSTGRES_PASSWORD_FILE", PASSWORD_FILE_PATH)) as file:
        DB_PASSWORD = file.read().strip()
    # check if the password is existing
    if DB_PASSWORD is not None:
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
                print(f"Database connection failed: {e} ")
                time.sleep(3)
    else:
        print(f"Password for database not found - could not connect.")
        return False

#################################################
# connect to database
#################################################

# establish connection to database
def connect_database():
    # read the password from the password file
    with open(os.getenv("POSTGRES_PASSWORD_FILE", PASSWORD_FILE_PATH)) as file:
        DB_PASSWORD = file.read().strip()
    # check if the password is existing
    if DB_PASSWORD is not None:
        # connect to database
        try:
            DATABASE_URL = create_database_url(DB_PASSWORD)
            # create database connection
            engine = create_engine(DATABASE_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            return session
        except SQLAlchemyError:
            return None
    else:
        print(f"Password for database not found - could not connect.")
        return None