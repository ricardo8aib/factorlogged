from contextlib import contextmanager, nullcontext
from typing import Protocol

from sqlalchemy.orm import sessionmaker
import pydantic
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.ext.declarative import declarative_base

from ..database_interface import DatabaseGateway

Base = declarative_base()


class PostgresSettings(Protocol):
    DATABASE_NAME: str
    DATABASE_USERNAME: str
    DATABASE_SCHEMA: str | None
    DATABASE_PASSWORD: pydantic.SecretStr
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_TABLE: str
    DATABASE_SCHEMA: str
    REMOTE_SSH_USER: str | None
    REMOTE_SSH_HOST: str | None
    PEM_PATH: str | None


class PostgresDatabaseGateway(DatabaseGateway):
    """A gateway for interacting with a PostgreSQL database.

    This class extends the DatabaseGateway class, specializing in
    PostgreSQL database interactions. It includes methods for
    managing database connections.

    Attributes:
        name (str): A class attribute that specifies the type of the database gateway.
        postgres_settings (PostgresSettings): An instance of PostgresSettings containing
            the configuration for the PostgreSQL database.

    Args:
        postgres_settings (PostgresSettings): Configuration settings for the PostgreSQL database.
    """

    name = "postgres"

    def __init__(self, postgres_settings: PostgresSettings) -> None:
        """Initialize the PostgresDatabaseGateway instance.

        Stores the provided PostgreSQL settings and initializes the parent class.

        Args:
            postgres_settings (PostgresSettings): Configuration settings for the
                PostgreSQL database.
        """
        self.postgres_settings = postgres_settings
        print(f"Postgres Settings: {postgres_settings}")
        super().__init__()

    @staticmethod
    @contextmanager
    def connection_handler(params: PostgresSettings) -> None:
        """A context manager to handle database connections.

        This static method manages the connection to the PostgreSQL database,
        optionally through an SSH tunnel.

        Args:
            params (PostgresSettings): The settings for connecting to the PostgreSQL database.

        Yields:
            ContextManager[psycopg2.extensions.cursor]: A context manager providing a
                database cursor.
        """
        with SSHTunnelForwarder(
            ssh_address_or_host=(params.REMOTE_SSH_HOST, 22),
            ssh_private_key=params.PEM_PATH,
            ssh_username=params.REMOTE_SSH_USER,
            remote_bind_address=(params.DATABASE_HOST, params.DATABASE_PORT),
        ) if params.PEM_PATH is not None else nullcontext() as server:

            if server is not None:
                server.start()
                print("SSH server connected")
                host = "localhost"
                port = server.local_bind_port
            else:
                print("Not using SSH tunnel")
                host = params.DATABASE_HOST
                port = params.DATABASE_PORT

            user = params.DATABASE_USERNAME
            password = params.DATABASE_PASSWORD
            database = params.DATABASE_NAME

            db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

            engine = create_engine(db_url)
            Base.metadata.create_all(bind=engine)
            session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            try:
                yield session()

            except Exception as exp:
                print(exp)
            finally:
                server.stop()
