from sqlalchemy import Table, Column, BigInteger, String
from config import metadata

location_service = Table('location_services', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(100), unique=True, index=True, nullable=False),
)
