from fastapi import Query
from typing import Literal

def get_all_query_dashboard(
    period: Literal['week','month','year'] = Query(...),
    institution_id: int = Query(None,gt=0),
    location_service_id: int = Query(None,gt=0)
):
    return {
        'period': period,
        'institution_id': institution_id,
        'location_service_id': location_service_id
    }
