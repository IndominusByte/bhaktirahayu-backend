from config import database
from sqlalchemy.sql import select, func, exists
from models.CovidCheckupModel import covid_checkup
from models.ClientModel import client
from models.InstitutionModel import institution
from models.LocationServiceModel import location_service
from models.GuardianModel import guardian
from models.UserModel import user
from datetime import datetime, timedelta
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

class CovidCheckupLogic:
    @staticmethod
    async def covid_checkup_on_same_date_and_institution(
        checking_type: str,
        institution_id: int,
        client_id: int
    ) -> bool:
        time_now = datetime.now(tz).replace(tzinfo=None)
        one_hours_ago = time_now - timedelta(hours=1)

        query = select([exists().where(
            (covid_checkup.c.checking_type == checking_type) &
            (covid_checkup.c.institution_id == institution_id) &
            (covid_checkup.c.client_id == client_id) &
            ((covid_checkup.c.created_at > one_hours_ago) & (covid_checkup.c.created_at < time_now))
        )]).as_scalar()

        return await database.execute(query=query)

class CovidCheckupCrud:
    @staticmethod
    async def create_covid_checkup(**kwargs) -> int:
        return await database.execute(query=covid_checkup.insert(),values=kwargs)

    @staticmethod
    async def update_covid_checkup(id_: int, **kwargs) -> None:
        kwargs.update({"updated_at": func.now()})
        await database.execute(query=covid_checkup.update().where(covid_checkup.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_covid_checkup(id_: int) -> None:
        await database.execute(query=covid_checkup.delete().where(covid_checkup.c.id == id_))

class CovidCheckupFetch:
    @staticmethod
    async def get_covid_checkup_by_id(id_: int) -> covid_checkup:
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

        query = select([joined_table]).where(covid_checkup.c.id == id_) \
            .order_by(covid_checkup.c.id.desc()).apply_labels()

        return await database.fetch_one(query=query)

    @staticmethod
    async def get_covid_checkup_document(id_: int) -> covid_checkup:
        client_alias = select([client]).alias('clients')
        covid_checkup_alias = select([covid_checkup]).alias('covid_checkups')
        doctor_alias = select([user]).alias('covid_checkups_doctor')
        institution_alias = select([institution]).alias('covid_checkups_institution')

        joined_table = client_alias.join(covid_checkup_alias.join(doctor_alias).join(institution_alias))
        query = select([joined_table]).where(covid_checkup_alias.c.id == id_).apply_labels()

        return await database.fetch_one(query=query)

    @staticmethod
    async def get_covid_checkup_by_hash(check_hash: str) -> covid_checkup:
        client_alias = select([client]).alias('clients')
        covid_checkup_alias = select([covid_checkup]).alias('covid_checkups')
        institution_alias = select([institution.c.id, institution.c.name]).alias('covid_checkups_institution')

        query = select([client_alias.join(covid_checkup_alias.join(institution_alias))]) \
            .where(covid_checkup_alias.c.check_hash == check_hash).apply_labels()

        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_id(id_: int) -> covid_checkup:
        query = select([covid_checkup]).where(covid_checkup.c.id == id_)
        return await database.fetch_one(query=query)
