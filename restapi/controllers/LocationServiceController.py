from config import database
from sqlalchemy.sql import select, func
from libs.Pagination import Pagination
from models.LocationServiceModel import location_service

class LocationServiceLogic:
    pass

class LocationServiceCrud:
    @staticmethod
    async def create_location_service(name: str) -> int:
        return await database.execute(query=location_service.insert(),values={'name': name})

    @staticmethod
    async def update_location_service(id_: str, **kwargs) -> None:
        await database.execute(query=location_service.update().where(location_service.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_location_service(id_: int) -> None:
        await database.execute(query=location_service.delete().where(location_service.c.id == id_))

class LocationServiceFetch:
    @staticmethod
    async def get_multiple_location_services(list_id: list) -> list:
        query = select([location_service.c.id, location_service.c.name]).where(location_service.c.id.in_(list_id)) \
            .order_by(location_service.c.id.desc()).apply_labels()

        location_service_db = await database.fetch_all(query=query)
        return [{index:value for index,value in item.items()} for item in location_service_db]

    @staticmethod
    async def get_all_location_services_paginate(**kwargs) -> dict:
        query = select([location_service]).order_by(location_service.c.id.desc()).apply_labels()
        if q := kwargs['q']: query = query.where(location_service.c.name.ilike(f"%{q}%"))

        total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
        query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
        location_service_db = await database.fetch_all(query=query)

        paginate = Pagination(kwargs['page'], kwargs['per_page'], total, location_service_db)
        return {
            "data": [{index:value for index,value in item.items()} for item in paginate.items],
            "total": paginate.total,
            "next_num": paginate.next_num,
            "prev_num": paginate.prev_num,
            "page": paginate.page,
            "iter_pages": [x for x in paginate.iter_pages()]
        }

    @staticmethod
    async def filter_by_name(name: str) -> location_service:
        query = select([location_service]).where(location_service.c.name == name)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_id(id_: int) -> location_service:
        query = select([location_service]).where(location_service.c.id == id_)
        return await database.fetch_one(query=query)
