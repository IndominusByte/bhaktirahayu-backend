from pydantic import BaseModel, constr, conlist, validator
from typing import List, Optional

class InstitutionSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class InstitutionMultiple(InstitutionSchema):
    list_id: conlist(constr(strict=True, regex=r'^[0-9]*$'), min_items=1)

    @validator('list_id', each_item=True)
    def parse_str_to_int(cls, v):
        return int(v) if v else None

class InstitutionData(InstitutionSchema):
    institutions_id: str
    institutions_name: str

class InstitutionAllData(InstitutionData):
    institutions_stamp: str
    institutions_antigen: Optional[str]
    institutions_genose: Optional[str]

class InstitutionDataPaginate(InstitutionSchema):
    data: List[InstitutionAllData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
