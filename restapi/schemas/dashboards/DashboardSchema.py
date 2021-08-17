from pydantic import BaseModel
from typing import List

class DashboardSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class DashboardTotalData(DashboardSchema):
    total_institutions: str
    total_location_services: str
    total_guardians: str
    total_doctors: str
    total_male: str
    total_female: str

class DashboardDoneWaitingData(DashboardSchema):
    date: str
    done: str
    waiting: str

class DashboardPositiveNegativeData(DashboardSchema):
    date: str
    positive: str
    negative: str

class DasboardChartData(DashboardSchema):
    done_waiting: List[DashboardDoneWaitingData]
    antigen_p_n: List[DashboardPositiveNegativeData]
    genose_p_n: List[DashboardPositiveNegativeData]
    pcr_p_n: List[DashboardPositiveNegativeData]
