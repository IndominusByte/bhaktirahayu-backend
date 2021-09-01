from config import database
from sqlalchemy.sql import select, func
from libs.Pagination import Pagination
from models.GuardianModel import guardian

class GuardianLogic:
    @staticmethod
    async def get_max_id() -> int:
        return await database.execute(query=select([func.max(guardian.c.id)])) or 0

class GuardianCrud:
    @staticmethod
    async def create_guardian(name: str) -> int:
        kwargs = {'id': await GuardianLogic.get_max_id() + 1,'name': name}
        return await database.execute(query=guardian.insert(),values=kwargs) or kwargs['id']

    @staticmethod
    async def update_guardian(id_: str, **kwargs) -> None:
        await database.execute(query=guardian.update().where(guardian.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_guardian(id_: int) -> None:
        await database.execute(query=guardian.delete().where(guardian.c.id == id_))

class GuardianFetch:
    @staticmethod
    async def get_multiple_guardians(list_id: list) -> list:
        query = select([guardian.c.id, guardian.c.name]).where(guardian.c.id.in_(list_id)) \
            .order_by(guardian.c.id.desc()).apply_labels()

        guardian_db = await database.fetch_all(query=query)
        return [{index:value for index,value in item.items()} for item in guardian_db]

    @staticmethod
    async def get_all_guardians_paginate(**kwargs) -> dict:
        query = select([guardian]).order_by(guardian.c.id.desc()).apply_labels()
        if q := kwargs['q']: query = query.where(guardian.c.name.ilike(f"%{q}%"))

        total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
        query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
        guardian_db = await database.fetch_all(query=query)

        paginate = Pagination(kwargs['page'], kwargs['per_page'], total, guardian_db)
        return {
            "data": [{index:value for index,value in item.items()} for item in paginate.items],
            "total": paginate.total,
            "next_num": paginate.next_num,
            "prev_num": paginate.prev_num,
            "page": paginate.page,
            "iter_pages": [x for x in paginate.iter_pages()]
        }

    @staticmethod
    async def filter_by_name(name: str) -> guardian:
        query = select([guardian]).where(guardian.c.name == name)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_id(id_: int) -> guardian:
        query = select([guardian]).where(guardian.c.id == id_)
        return await database.fetch_one(query=query)
