from pydantic import BaseModel, constr, conlist, validator
from typing import List, Optional

class LocationServiceSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class LocationServiceCreateUpdate(LocationServiceSchema):
    name: constr(strict=True, min_length=3, max_length=100)

class LocationServiceMultiple(LocationServiceSchema):
    list_id: conlist(constr(strict=True, regex=r'^[0-9]*$'), min_items=1)

    @validator('list_id', each_item=True)
    def parse_str_to_int(cls, v):
        return int(v) if v else None

class LocationServiceData(LocationServiceSchema):
    location_services_id: str
    location_services_name: str

class LocationServiceDataPaginate(LocationServiceSchema):
    data: List[LocationServiceData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
