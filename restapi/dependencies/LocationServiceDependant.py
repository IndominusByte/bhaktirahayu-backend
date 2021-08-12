from fastapi import Query

def get_all_query_location_service(
    page: int = Query(...,gt=0),
    per_page: int = Query(...,gt=0),
    q: str = Query(None,min_length=1),
):
    return {
        "page": page,
        "per_page": per_page,
        "q": q,
    }
