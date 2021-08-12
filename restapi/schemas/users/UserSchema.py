from pydantic import BaseModel, EmailStr, constr, conlist, validator
from typing import List, Literal, Optional
from datetime import datetime
from schemas import errors

class UserSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class UserLogin(UserSchema):
    email: EmailStr
    password: constr(strict=True, min_length=6, max_length=100)

class UserUpdatePassword(UserSchema):
    old_password: constr(strict=True, min_length=6, max_length=100)
    confirm_password: constr(strict=True, min_length=6, max_length=100)
    password: constr(strict=True, min_length=6, max_length=100)

    @validator('password')
    def validate_password(cls, v, values, **kwargs):
        if 'confirm_password' in values and values['confirm_password'] != v:
            raise errors.PasswordConfirmError()
        return v

class UserConfirmPassword(UserSchema):
    password: constr(strict=True, min_length=6, max_length=100)

class UserDoctorMultiple(UserSchema):
    list_id: conlist(constr(strict=True, regex=r'^[0-9]*$'), min_items=1)

    @validator('list_id', each_item=True)
    def parse_str_to_int(cls, v):
        return int(v) if v else None

class UserData(UserSchema):
    id: str
    username: str
    email: EmailStr
    role: Literal['admin','doctor']
    signature: Optional[str]
    created_at: datetime
    updated_at: datetime

class UserDoctorData(UserSchema):
    users_id: str
    users_username: str

class UserDoctorAllData(UserDoctorData):
    users_email: EmailStr
    users_signature: str

class UserDoctorPaginate(UserSchema):
    data: List[UserDoctorAllData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
