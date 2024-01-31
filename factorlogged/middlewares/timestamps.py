from ..databases.postgres.objects import create_request_time_object
from ..databases.postgres.db import PostgresDatabaseGateway, PostgresSettings
import time
import json
from fastapi import Request
from fastapi import FastAPI


class ExecutionTimesMiddleware:
    """Middleware for FastAPI to log request execution times and store them in a database.

    Attributes:
        app (FastAPI): The FastAPI application instance.
        SessionLocal (sqlalchemy.orm.session.Session): SQLAlchemy session for the database.
    """
    # TODO: params should work for other databases
    def __init__(
        self,
        app: FastAPI,
        params: PostgresSettings
    ):
        """Initializes the LoggerMiddleware.

        Args:
            app (FastAPI): The FastAPI application instance.
            params (PostgresSettings): Instance of PostgresSettings with db params.
        """
        self.app = app
        self.params = params

        # The next line of code registers the middleware method as a middleware
        # function for handling HTTP requests.
        # This means that the middleware method will be invoked automatically
        # by FastAPI for each HTTP request, but not during the __init__ method.
        app.middleware("http")(self.middleware)

    async def middleware(
        self,
        request: Request,
        call_next: callable
    ):
        """Middleware method to log request execution times and store them in the database.

        Args:
            request (Request): The FastAPI request object.
            call_next (Callable): The next callable in the FastAPI middleware chain.

        Returns:
            Any: The FastAPI response object.
        """
        # Get process time
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Load data to db
        with PostgresDatabaseGateway.connection_handler(params=self.params) as SessionLocal:
            # Create a dictionary with the data to be stored in the JSON column
            data_dict = {
                "execution_time": process_time,
                "request.url": request.url,
                "request.headers": request.headers,
                "request.session": request.session
            }

            # Convert the dictionary to a JSON string
            data_json = json.dumps(data_dict)

            # Create the RequestTime instance with the JSON data
            request_time_record = create_request_time_object(
                table_name=self.params.DATABASE_TABLE,
                table_schema=self.params.DATABASE_SCHEMA,
                data=data_json
            )
            SessionLocal.add(request_time_record)
            SessionLocal.commit()
            SessionLocal.close()

        return response
