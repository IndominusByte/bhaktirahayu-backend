from pydantic import BaseModel, constr, conlist, validator
from typing import List, Optional

class GuardianSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class GuardianCreateUpdate(GuardianSchema):
    name: constr(strict=True, min_length=3, max_length=100)

class GuardianMultiple(GuardianSchema):
    list_id: conlist(constr(strict=True, regex=r'^[0-9]*$'), min_items=1)

    @validator('list_id', each_item=True)
    def parse_str_to_int(cls, v):
        return int(v) if v else None

class GuardianData(GuardianSchema):
    guardians_id: str
    guardians_name: str

class GuardianDataPaginate(GuardianSchema):
    data: List[GuardianData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
