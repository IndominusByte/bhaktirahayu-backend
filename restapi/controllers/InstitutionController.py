from config import database
from sqlalchemy.sql import select, func
from models.InstitutionModel import institution
from libs.Pagination import Pagination

class InstitutionLogic:
    pass

class InstitutionCrud:
    @staticmethod
    async def create_institution(**kwargs) -> int:
        return await database.execute(query=institution.insert(),values=kwargs)

    @staticmethod
    async def update_institution(id_: int, **kwargs) -> None:
        await database.execute(query=institution.update().where(institution.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_institution(id_: int) -> None:
        await database.execute(query=institution.delete().where(institution.c.id == id_))

class InstitutionFetch:
    @staticmethod
    async def get_multiple_institutions(list_id: list) -> list:
        query = select([institution.c.id, institution.c.name]).where(institution.c.id.in_(list_id)) \
            .order_by(institution.c.id.desc()).apply_labels()

        institution_db = await database.fetch_all(query=query)
        return [{index:value for index,value in item.items()} for item in institution_db]

    @staticmethod
    async def get_all_institutions_paginate(**kwargs) -> dict:
        query = select([institution]).order_by(institution.c.id.desc()).apply_labels()
        if q := kwargs['q']: query = query.where(institution.c.name.ilike(f"%{q}%"))
        if kwargs['checking_type'] == 'antigen': query = query.where(institution.c.antigen.isnot(None))
        if kwargs['checking_type'] == 'genose': query = query.where(institution.c.genose.isnot(None))
        if kwargs['checking_type'] == 'pcr': query = query.where(institution.c.pcr.isnot(None))

        total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
        query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
        institution_db = await database.fetch_all(query=query)

        paginate = Pagination(kwargs['page'], kwargs['per_page'], total, institution_db)
        return {
            "data": [{index:value for index,value in item.items()} for item in paginate.items],
            "total": paginate.total,
            "next_num": paginate.next_num,
            "prev_num": paginate.prev_num,
            "page": paginate.page,
            "iter_pages": [x for x in paginate.iter_pages()]
        }

    @staticmethod
    async def filter_by_id(id_: int) -> institution:
        query = select([institution]).where(institution.c.id == id_)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_name(name: str) -> institution:
        query = select([institution]).where(institution.c.name == name)
        return await database.fetch_one(query=query)
