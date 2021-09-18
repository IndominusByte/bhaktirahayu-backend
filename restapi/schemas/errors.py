from pydantic import PydanticValueError, PydanticTypeError
from typing import Any

class DatetimeFormatTypeError(PydanticTypeError):
    code = 'datetime_zone'
    msg_template = 'strptime() argument 1 must be str, not {type_data}'

    def __init__(self, *, type_data: Any) -> None:
        super().__init__(type_data=type_data)

class DatetimeFormatValueError(PydanticValueError):
    code = 'datetime_zone'
    msg_template = "time data '{input_user}' does not match format '{tf}'"

    def __init__(self, *, input_user: str, tf: str) -> None:
        super().__init__(input_user=input_user, tf=tf)

class PhoneNumberError(PydanticValueError):
    code = 'phone_number'
    msg_template = 'value is not a valid mobile phone number'

# ========= USER SECTION =========

class PasswordConfirmError(PydanticValueError):
    code = 'password_confirm'
    msg_template = 'password must match with password confirmation'

# ========= CLIENT SECTION =========

class BirthDateNotGtError(PydanticValueError):
    code = 'birth_date.not_gt'
    msg_template = 'the birth date cannot greater than the current time now'

# ========= CLIENT SECTION =========

class CheckDateNotGtError(PydanticValueError):
    code = 'check_date.not_gt'
    msg_template = 'the check date cannot greater than the current time now'
