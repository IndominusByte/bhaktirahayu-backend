from phonenumbers import (
    NumberParseException,
    PhoneNumberType,
    PhoneNumberFormat,
    format_number,
    number_type,
    is_valid_number,
    parse as parse_phone_number
)
from pydantic import BaseModel, constr, EmailStr, validator
from libs.NikExtraction import NikExtraction
from typing import List, Literal, Optional
from datetime import datetime
from pytz import timezone
from config import settings
from schemas import errors

nik_extraction = NikExtraction()

tz = timezone(settings.timezone)
tf = '%d-%m-%Y'

class ClientSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class ClientDataImageOcr(ClientSchema):
    nik: Optional[str]
    name: Optional[str]
    birth_date: Optional[datetime]
    birth_place: Optional[str]
    gender: Optional[Literal['LAKI-LAKI','PEREMPUAN']]
    address: Optional[str]

    @validator('birth_date', pre=True)
    def parse_birth_date(cls, v):
        if v: return datetime.strptime(v, tf)

class ClientCrud(ClientSchema):
    nik: constr(strict=True, min_length=3, max_length=100, regex=r'^[0-9]*$')
    name: constr(strict=True, min_length=3, max_length=100)
    birth_place: constr(strict=True, min_length=3, max_length=100)
    birth_date: datetime
    gender: Literal['LAKI-LAKI','PEREMPUAN']
    phone: constr(strict=True, max_length=20)
    address: constr(strict=True, min_length=5)

    @validator('phone')
    def validate_phone(cls, v):
        try:
            n = parse_phone_number(v, "ID")
        except NumberParseException:
            raise errors.PhoneNumberError()

        MOBILE_NUMBER_TYPES = PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE

        if not is_valid_number(n) or number_type(n) not in MOBILE_NUMBER_TYPES:
            raise errors.PhoneNumberError()

        return format_number(n, PhoneNumberFormat.INTERNATIONAL)

    @validator('nik')
    def check_valid_nik(cls, v):
        if nik_extraction.nik_extract(v)['valid'] is False:
            raise ValueError('invalid nik format')
        return v

    @validator('birth_date', pre=True)
    def parse_discount_format(cls, v):
        try:
            return tz.localize(datetime.strptime(v,tf))
        except ValueError:
            raise errors.DatetimeFormatValueError(input_user=v,tf=tf)
        except TypeError:
            raise errors.DatetimeFormatTypeError(type_data=type(v).__name__)

class ClientCreate(ClientCrud):
    checking_type: Literal['antigen','genose','pcr']
    institution_id: constr(strict=True, regex=r'^[0-9]*$')

    class Config:
        schema_extra = {
            "example": {
                "nik": "5103051905990006",
                "name": "NYOMAN PRADIPTA DEWANTARA",
                "birth_place": "BALIKPAPAN",
                "birth_date": format(datetime.now(tz), tf),
                "gender": "LAKI-LAKI",
                "phone": "+62 87862265363",
                "address": "PURIGADING",
                "checking_type": "antigen",
                "institution_id": "1"
            }
        }

    @validator('institution_id')
    def parse_str_to_int(cls, v):
        return int(v) if v else None

class ClientUpdate(ClientCrud):
    class Config:
        schema_extra = {
            "example": {
                "nik": "5103051905990006",
                "name": "NYOMAN PRADIPTA DEWANTARA",
                "birth_place": "BALIKPAPAN",
                "birth_date": format(datetime.now(tz), tf),
                "gender": "LAKI-LAKI",
                "phone": "+62 87862265363",
                "address": "PURIGADING"
            }
        }

class ClientGetDataByNik(ClientSchema):
    nik: str
    name: str
    phone: str
    birth_place: str
    birth_date: datetime
    gender: Literal['LAKI-LAKI','PEREMPUAN']
    address: str

class ClientGetInfoByNik(ClientSchema):
    nik: str
    valid: bool
    area_code: Optional[str]
    location_valid: bool
    province: Optional[str]
    district: Optional[str]
    subdistrict: Optional[str]
    gender: Optional[Literal['LAKI-LAKI','PEREMPUAN']]
    birth_date: Optional[datetime]

class ClientCovidCheckupData(ClientSchema):
    covid_checkups_id: str
    covid_checkups_checking_type: Literal['antigen','genose','pcr']
    covid_checkups_check_date: Optional[datetime]
    covid_checkups_check_result: Optional[Literal['positive','negative']]
    covid_checkups_doctor_id: Optional[str]
    covid_checkups_doctor_username: Optional[str]
    covid_checkups_doctor_email: Optional[EmailStr]
    covid_checkups_guardian_id: Optional[str]
    covid_checkups_guardian_name: Optional[str]
    covid_checkups_location_service_id: Optional[str]
    covid_checkups_location_service_name: Optional[str]
    covid_checkups_institution_id: str
    covid_checkups_institution_name: str
    covid_checkups_created_at: datetime
    covid_checkups_updated_at: datetime

class ClientData(ClientSchema):
    clients_id: str
    clients_nik: str
    clients_name: str
    clients_phone: str
    clients_birth_place: str
    clients_birth_date: datetime
    clients_gender: Literal['LAKI-LAKI','PEREMPUAN']
    clients_address: str
    clients_created_at: datetime
    clients_updated_at: datetime
    covid_checkups: List[ClientCovidCheckupData]

class ClientExportData(ClientSchema):
    clients_no: str
    clients_nik: str
    clients_name: str
    clients_phone: str
    clients_birth_place: str
    clients_birth_date: datetime
    clients_gender: Literal['LAKI-LAKI','PEREMPUAN']
    clients_address: str
    covid_checkups_checking_type: Literal['antigen','genose','pcr']
    covid_checkups_check_date: Optional[datetime]
    covid_checkups_check_result: Optional[Literal['positive','negative']]
    covid_checkups_doctor_username: Optional[str]
    covid_checkups_doctor_email: Optional[EmailStr]
    covid_checkups_guardian_name: Optional[str]
    covid_checkups_location_service_name: Optional[str]
    covid_checkups_institution_name: str

class ClientPaginate(ClientSchema):
    data: List[ClientData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
