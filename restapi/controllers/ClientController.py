from config import database
from sqlalchemy.sql import select, func
from models.ClientModel import client
from models.CovidCheckupModel import covid_checkup
from models.InstitutionModel import institution
from models.LocationServiceModel import location_service
from models.GuardianModel import guardian
from models.UserModel import user
from libs.Pagination import Pagination
from typing import Union

class ClientLogic:
    @staticmethod
    def export_client_covid_checkup(client_data: list) -> list:
        index, result = 1, []
        exclude_client_data = ['clients_id','clients_created_at','clients_updated_at','covid_checkups']
        include_covid_checkup_data = [
            'covid_checkups_checking_type', 'covid_checkups_check_date', 'covid_checkups_check_result',
            'covid_checkups_doctor_username', 'covid_checkups_doctor_email', 'covid_checkups_guardian_name',
            'covid_checkups_location_service_name', 'covid_checkups_institution_name'
        ]

        for data in client_data:
            for covid_checkup_data in data['covid_checkups']:
                result.append({
                    'clients_no': index,
                    **{k:v for k,v in data.items() if k not in exclude_client_data},
                    **{k:v for k,v in covid_checkup_data.items() if k in include_covid_checkup_data}
                })
                index += 1

        return result

class ClientCrud:
    @staticmethod
    async def create_client(**kwargs) -> int:
        return await database.execute(query=client.insert(),values=kwargs)

    @staticmethod
    async def update_client(id_: int, **kwargs) -> None:
        kwargs.update({"updated_at": func.now()})
        await database.execute(query=client.update().where(client.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_client(id_: int) -> None:
        await database.execute(query=client.delete().where(client.c.id == id_))

class ClientFetch:
    @staticmethod
    async def get_covid_checkup_client(client_data: dict, **kwargs) -> list:
        institution_alias = select([institution.c.id, institution.c.name]) \
            .alias('covid_checkups_institution')
        location_service_alias = select([location_service.c.id, location_service.c.name]) \
            .alias('covid_checkups_location_service')
        guardian_alias = select([guardian.c.id, guardian.c.name]) \
            .alias('covid_checkups_guardian')
        doctor_alias = select([user.c.id, user.c.username, user.c.email]) \
            .alias('covid_checkups_doctor')

        joined_table = covid_checkup.outerjoin(institution_alias) \
            .outerjoin(location_service_alias) \
            .outerjoin(guardian_alias) \
            .outerjoin(doctor_alias)

        query = select([joined_table]).where(covid_checkup.c.client_id == client_data['clients_id']) \
            .order_by(covid_checkup.c.id.desc()).apply_labels()

        if checking_type := kwargs['checking_type']:
            query = query.where(covid_checkup.c.checking_type == checking_type)
        if kwargs['check_result'] in ['positive','negative']:
            query = query.where(covid_checkup.c.check_result == kwargs['check_result'])
        if kwargs['check_result'] == 'empty':
            query = query.where(covid_checkup.c.check_result.is_(None))
        if doctor_id := kwargs['doctor_id']:
            query = query.where(covid_checkup.c.doctor_id.in_(doctor_id))
        if guardian_id := kwargs['guardian_id']:
            query = query.where(covid_checkup.c.guardian_id.in_(guardian_id))
        if location_service_id := kwargs['location_service_id']:
            query = query.where(covid_checkup.c.location_service_id.in_(location_service_id))
        if institution_id := kwargs['institution_id']:
            query = query.where(covid_checkup.c.institution_id.in_(institution_id))
        if kwargs['register_start_date'] and kwargs['register_end_date']:
            query = query.where(
                (func.date(covid_checkup.c.created_at) >= kwargs['register_start_date'].replace(tzinfo=None)) &
                (func.date(covid_checkup.c.created_at) <= kwargs['register_end_date'].replace(tzinfo=None))
            )
        if kwargs['check_start_date'] and kwargs['check_end_date']:
            query = query.where(
                (covid_checkup.c.check_date >= kwargs['check_start_date'].replace(tzinfo=None)) &
                (covid_checkup.c.check_date <= kwargs['check_end_date'].replace(tzinfo=None))
            )

        covid_checkup_db = await database.fetch_all(query)
        return [{index:value for index,value in item.items()} for item in covid_checkup_db]

    @staticmethod
    async def get_all_clients_paginate(with_paginate: bool = True, **kwargs) -> Union[dict,list]:
        client_alias = select([client]).alias('clients')
        covid_checkup_alias = select([covid_checkup]).alias('covid_checkups')

        query = select([client_alias.join(covid_checkup_alias)]).apply_labels()

        if q := kwargs['q']:
            query = query.where((client_alias.c.nik.ilike(f"%{q}%")) | (client_alias.c.name.ilike(f"%{q}%")))
        if gender := kwargs['gender']:
            query = query.where(client_alias.c.gender == gender)
        if checking_type := kwargs['checking_type']:
            query = query.where(covid_checkup_alias.c.checking_type == checking_type)
        if kwargs['check_result'] in ['positive','negative']:
            query = query.where(covid_checkup_alias.c.check_result == kwargs['check_result'])
        if kwargs['check_result'] == 'empty':
            query = query.where(covid_checkup_alias.c.check_result.is_(None))
        if doctor_id := kwargs['doctor_id']:
            query = query.where(covid_checkup_alias.c.doctor_id.in_(doctor_id))
        if guardian_id := kwargs['guardian_id']:
            query = query.where(covid_checkup_alias.c.guardian_id.in_(guardian_id))
        if location_service_id := kwargs['location_service_id']:
            query = query.where(covid_checkup_alias.c.location_service_id.in_(location_service_id))
        if institution_id := kwargs['institution_id']:
            query = query.where(covid_checkup_alias.c.institution_id.in_(institution_id))
        if kwargs['register_start_date'] and kwargs['register_end_date']:
            query = query.where(
                (func.date(covid_checkup_alias.c.created_at) >= kwargs['register_start_date'].replace(tzinfo=None)) &
                (func.date(covid_checkup_alias.c.created_at) <= kwargs['register_end_date'].replace(tzinfo=None))
            )
        if kwargs['check_start_date'] and kwargs['check_end_date']:
            query = query.where(
                (covid_checkup_alias.c.check_date >= kwargs['check_start_date'].replace(tzinfo=None)) &
                (covid_checkup_alias.c.check_date <= kwargs['check_end_date'].replace(tzinfo=None))
            )

        query = query.distinct(client_alias.c.id).order_by(client_alias.c.id.desc())

        if with_paginate is True:
            total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
            query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
            client_db = await database.fetch_all(query=query)

            paginate = Pagination(kwargs['page'], kwargs['per_page'], total, client_db)
            client_data = [{k:v for k,v in item.items() if k.startswith('clients_')} for item in paginate.items]
        else:
            client_db = await database.fetch_all(query=query)
            client_data = [{k:v for k,v in item.items() if k.startswith('clients_')} for item in client_db]

        [
            data.__setitem__('covid_checkups', await ClientFetch.get_covid_checkup_client(data,
                **{k:v for k,v in kwargs.items() if k not in ['page','per_page','q','gender']}
            )) for data in client_data
        ]

        if with_paginate is True:
            return {
                "data": client_data,
                "total": paginate.total,
                "next_num": paginate.next_num,
                "prev_num": paginate.prev_num,
                "page": paginate.page,
                "iter_pages": [x for x in paginate.iter_pages()]
            }
        else:
            return ClientLogic.export_client_covid_checkup(client_data)

    @staticmethod
    async def filter_by_phone(phone: int) -> client:
        query = select([client]).where(client.c.phone == phone)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_id(id_: int) -> client:
        query = select([client]).where(client.c.id == id_)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_nik(nik: str) -> client:
        query = select([client]).where(client.c.nik == nik)
        return await database.fetch_one(query=query)
