from pydantic import BaseModel, constr, EmailStr, validator
from typing import Literal, Optional
from datetime import datetime
from pytz import timezone
from config import settings
from schemas import errors

tz = timezone(settings.timezone)
tf = '%d-%m-%Y %H:%M'

class CovidCheckupSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class CovidCheckupUpdate(CovidCheckupSchema):
    check_date: datetime
    check_result: Literal['positive','negative']
    doctor_id: constr(strict=True, regex=r'^[0-9]*$')
    guardian_id: Optional[constr(strict=True, regex=r'^[0-9]*$')]
    location_service_id: Optional[constr(strict=True, regex=r'^[0-9]*$')]
    institution_id: constr(strict=True, regex=r'^[0-9]*$')

    class Config:
        schema_extra = {
            "example": {
                "check_date": format(datetime.now(tz), tf),
                "check_result": "positive",
                "doctor_id": "1",
                "guardian_id": "1",
                "location_service_id": "1",
                "institution_id": "1"
            }
        }

    @validator('doctor_id','guardian_id','location_service_id','institution_id')
    def parse_str_to_int(cls, v):
        return int(v) if v else None

    @validator('check_date', pre=True)
    def parse_discount_format(cls, v):
        try:
            return tz.localize(datetime.strptime(v,tf))
        except ValueError:
            raise errors.DatetimeFormatValueError(input_user=v,tf=tf)
        except TypeError:
            raise errors.DatetimeFormatTypeError(type_data=type(v).__name__)

class CovidCheckupDocumentData(CovidCheckupSchema):
    clients_nik: str
    clients_name: str
    clients_phone: str
    clients_birth_place: str
    clients_birth_date: datetime
    clients_gender: Literal['LAKI-LAKI','PEREMPUAN']
    clients_address: str
    covid_checkups_checking_type: Literal['antigen','genose','pcr']
    covid_checkups_check_hash: str
    covid_checkups_check_date: datetime
    covid_checkups_check_result: Literal['positive','negative']
    covid_checkups_institution_name: str

class CovidCheckupDocumentPdfData(CovidCheckupSchema):
    clients_nik: str
    clients_name: str
    clients_phone: str
    clients_birth_place: str
    clients_birth_date: datetime
    clients_gender: Literal['LAKI-LAKI','PEREMPUAN']
    clients_address: str
    clients_age: int
    covid_checkups_report_number: str
    covid_checkups_checking_type: Literal['antigen','genose','pcr']
    covid_checkups_check_date: datetime
    covid_checkups_check_result: Literal['positive','negative']
    covid_checkups_doctor_username: str
    covid_checkups_doctor_email: EmailStr
    covid_checkups_institution_name: str
    covid_checkups_institution_letterhead: str
    covid_checkups_institution_stamp: str
    covid_checkups_doctor_signature: str
    covid_checkups_check_qrcode: str
