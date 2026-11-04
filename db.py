"""Shared database configuration for the Accra Transport Engine.

Credentials come from environment variables (see .env.example) so that no
secrets are hardcoded in the repository. Locally, docker-compose reads the
same POSTGRES_* variables from a .env file at the project root.
"""
import os


def db_config():
    return {
        "host": os.environ.get("PGHOST", "127.0.0.1"),
        "port": os.environ.get("PGPORT", "5432"),
        "dbname": os.environ.get("POSTGRES_DB", "informal_transport"),
        "user": os.environ.get("POSTGRES_USER", "transit_admin"),
        "password": os.environ["POSTGRES_PASSWORD"],  # fail loudly if unset
    }
