from sqlalchemy import Table, Column, BigInteger, String
from config import metadata

institution = Table('institutions', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(100), unique=True, index=True, nullable=False),
    Column('stamp', String(100), nullable=False),
    Column('antigen', String(100), nullable=True),
    Column('genose', String(100), nullable=True),
)
