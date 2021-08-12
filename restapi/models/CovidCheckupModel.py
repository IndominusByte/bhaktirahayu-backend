from sqlalchemy import Table, Column, BigInteger, String, ForeignKey, DateTime, func
from config import metadata

covid_checkup = Table('covid_checkups', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('checking_type', String(20), nullable=False),
    Column('check_hash', String(100), unique=True, index=True, nullable=True),
    Column('check_date', DateTime, nullable=True),
    Column('check_result', String(20), nullable=True),
    Column('doctor_id', BigInteger,
        ForeignKey('users.id',onupdate='cascade',ondelete='set null'), nullable=True),
    Column('guardian_id', BigInteger,
        ForeignKey('guardians.id',onupdate='cascade',ondelete='set null'), nullable=True),
    Column('location_service_id', BigInteger,
        ForeignKey('location_services.id',onupdate='cascade',ondelete='set null'), nullable=True),
    Column('institution_id', BigInteger,
        ForeignKey('institutions.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('client_id', BigInteger,
        ForeignKey('clients.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
    Column('updated_at', DateTime, default=func.now()),
)
