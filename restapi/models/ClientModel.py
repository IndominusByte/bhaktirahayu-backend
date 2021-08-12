from sqlalchemy import Table, Column, BigInteger, String, Text, DateTime, func
from config import metadata

client = Table('clients', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('nik', String(100), unique=True, index=True, nullable=False),
    Column('name', String(100), nullable=False),
    Column('phone', String(20), unique=True, index=True, nullable=False),
    Column('birth_place', String(100), nullable=False),
    Column('birth_date', DateTime, nullable=False),
    Column('gender', String(50), nullable=False),
    Column('address', Text, nullable=False),
    Column('created_at', DateTime, default=func.now()),
    Column('updated_at', DateTime, default=func.now()),
)
