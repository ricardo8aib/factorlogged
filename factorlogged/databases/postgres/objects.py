from sqlalchemy import Column, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
import json

import datetime

Base = declarative_base()

def create_request_time_object(table_name: str, table_schema: str, data: json):
    class RequestTime(Base):
        """SQLAlchemy model for storing request times in the database.

        Attributes:
            id (int): Primary key for the request time record.
            path (str): The URL path of the request.
            execution_time (float): The execution time of the request.
            timestamp (datetime.datetime): The timestamp of the record creation.
        """

        __tablename__ = table_name
        __table_args__ = {
            "schema": table_schema,
            "extend_existing": True
        }

        id = Column(Integer, primary_key=True, index=True)
        data = Column(JSON)
        timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    return RequestTime(data=data)