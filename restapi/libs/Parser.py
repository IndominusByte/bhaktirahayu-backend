from fastapi import HTTPException
from typing import List
from pytz import timezone
from config import settings
from datetime import datetime

tz = timezone(settings.timezone)

def parse_int_list(items: str, seperator: str) -> List[int]:
    try:
        return [int(float(item)) for item in items.split(seperator)]
    except Exception:
        return None

def parse_str_list(items: str, seperator: str) -> List[str]:
    try:
        return list(filter(None,[item for item in items.split(seperator)]))
    except Exception:
        return None

def parse_str_date(string: str, tf: str) -> datetime:
    try:
        return tz.localize(datetime.strptime(string,tf))
    except ValueError:
        raise HTTPException(status_code=422,detail=f"time data '{string}' does not match format '{tf}'")
    except TypeError:
        raise HTTPException(status_code=422,detail=f'strptime() argument 1 must be str, not {type(string).__name__}')

def get_date_now(tf: str) -> datetime:
    return format(datetime.now(tz), tf)

def int_to_roman(data: int) -> str:
    try:
        if not 0 < data < 4000:
            return None

        ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
        nums = ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
        result = []
        for i in range(len(ints)):
            count = int(data / ints[i])
            result.append(nums[i] * count)
            data -= ints[i] * count
        return ''.join(result)
    except Exception:
        return None
