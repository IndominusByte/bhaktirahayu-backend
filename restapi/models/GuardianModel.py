from sqlalchemy import Table, Column, BigInteger, String
from config import metadata

guardian = Table('guardians', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(100), unique=True, index=True, nullable=False),
)
