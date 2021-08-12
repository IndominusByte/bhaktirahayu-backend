import csv
from redis import Redis
from sqlalchemy import MetaData
from databases import Database
from datetime import timedelta
from fastapi_jwt_auth import AuthJWT
from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings, PostgresDsn, validator
from typing import Optional, Literal

with open("public_key.txt") as f:
    public_key = f.read().strip()

with open("private_key.txt") as f:
    private_key = f.read().strip()

with open('migration_data/nik_area_code.csv', 'r') as f:
    my_reader = csv.reader(f, delimiter=',')
    nik_area_code_list = [
        {'kodewilayah': row[0], 'provinsi': row[1], 'kabupatenkota': row[2], 'kecamatan': row[3]}
        for row in my_reader
    ]

class Settings(BaseSettings):
    authjwt_token_location: set = {"cookies"}
    authjwt_secret_key: str
    authjwt_algorithm: str = "RS512"
    authjwt_public_key: str = public_key
    authjwt_private_key: str = private_key
    authjwt_denylist_enabled: bool = True
    authjwt_cookie_domain: Optional[str] = None
    authjwt_cookie_secure: bool
    authjwt_cookie_samesite: str = "lax"

    frontend_uri: str
    database_uri: PostgresDsn
    redis_db_host: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_tls: bool

    timezone: str
    stage_app: Literal['production','development']
    nik_area_code_data: list = nik_area_code_list

    access_expires: Optional[int] = None
    refresh_expires: Optional[int] = None

    @validator('database_uri')
    def validate_database_uri(cls, v):
        assert v.path and len(v.path) > 1, 'database must be provided'
        return v

    @validator('access_expires',always=True)
    def parse_access_expires(cls, v):
        return int(timedelta(hours=8).total_seconds())

    @validator('refresh_expires',always=True)
    def parse_refresh_expires(cls, v):
        return int(timedelta(days=30).total_seconds())

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


metadata = MetaData()
settings = Settings()
database = Database(settings.database_uri)
templates = Jinja2Templates(directory="templates")
redis_conn = Redis(host=settings.redis_db_host, port=6379, db=0, decode_responses=True)

@AuthJWT.load_config
def get_config():
    return settings

@AuthJWT.token_in_denylist_loader
def check_if_token_in_denylist(decrypted_token):
    jti = decrypted_token['jti']
    entry = redis_conn.get(jti)
    return entry and entry == 'true'
