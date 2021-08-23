import pytest, bcrypt, os
from copy import deepcopy
from sqlalchemy.sql import select
from config import database
from models.UserModel import user
from models.GuardianModel import guardian
from models.LocationServiceModel import location_service
from models.InstitutionModel import institution
from models.ClientModel import client
from models.CovidCheckupModel import covid_checkup

class OperationTest:
    name = 'testtesttttttt'
    name2 = 'testtesttttttt2'
    account_admin = {'email':'admin@testing.com','username':'admintesting','password': 'testtesting'}
    account_1 = {'email':'testtesting@gmail.com','username':'testtesting','password':'testtesting'}
    account_2 = {'email':'testtesting2@gmail.com','username':'testtesting2','password':'testtesting2'}
    base_dir = os.path.join(os.path.dirname(__file__),'../static/')
    test_image_dir = base_dir + 'test_image/'
    signature_dir = base_dir + 'signature/'
    institution_dir = base_dir + 'institution/'
    qrcode_dir = base_dir + 'qrcode/'

    # ================ USER SECTION ================

    @pytest.mark.asyncio
    async def create_user(self, **kwargs):
        kwargs = deepcopy(kwargs)
        hashed_pass = bcrypt.hashpw(kwargs['password'].encode(), bcrypt.gensalt())
        kwargs.update({'password': hashed_pass.decode('utf-8')})
        await database.execute(query=user.insert(),values=kwargs)

    @pytest.mark.asyncio
    async def get_user_id(self,email: str):
        user_data = await database.fetch_one(query=select([user]).where(user.c.email == email))
        return user_data['id']

    @pytest.mark.asyncio
    async def get_user_signature(self,email: str):
        user_data = await database.fetch_one(query=select([user]).where(user.c.email == email))
        return user_data['signature']

    @pytest.mark.asyncio
    async def delete_user_from_db(self):
        # delete user admin
        query = user.delete().where(user.c.email == self.account_admin['email'])
        await database.execute(query=query)
        # delete user 1
        query = user.delete().where(user.c.email == self.account_1['email'])
        await database.execute(query=query)
        # delete user 2
        query = user.delete().where(user.c.email == self.account_2['email'])
        await database.execute(query=query)

    # ================ GUARDIAN SECTION ================

    @pytest.mark.asyncio
    async def get_guardian_id(self,name: str):
        guardian_data = await database.fetch_one(query=select([guardian]).where(guardian.c.name == name))
        return guardian_data['id']

    # ================ LOCATION-SERVICE SECTION ================

    @pytest.mark.asyncio
    async def get_location_service_id(self,name: str):
        location_service_data = await database.fetch_one(
            query=select([location_service]).where(location_service.c.name == name)
        )
        return location_service_data['id']

    # ================ INSTITUTION SECTION ================

    @pytest.mark.asyncio
    async def get_institution_id(self,name: str):
        institution_data = await database.fetch_one(query=select([institution]).where(institution.c.name == name))
        return institution_data['id']

    @pytest.mark.asyncio
    async def get_institution_image(self,name: str):
        institution_data = await database.fetch_one(query=select([institution]).where(institution.c.name == name))
        return {
            'stamp': institution_data['stamp'],
            'antigen': institution_data['antigen'],
            'genose': institution_data['genose'],
            'pcr': institution_data['pcr']
        }

    # ================ CLIENT SECTION ================

    @pytest.mark.asyncio
    async def get_client_data(self,nik: str):
        client_data = await database.fetch_one(query=select([client]).where(client.c.nik == nik))
        return {k:v for k,v in client_data.items()}

    @pytest.mark.asyncio
    async def get_client_id(self,nik: str):
        client_data = await database.fetch_one(query=select([client]).where(client.c.nik == nik))
        return client_data['id']

    # ================ COVID-CHECKUP SECTION ================

    @pytest.mark.asyncio
    async def get_covid_checkup_data(self,client_id: int):
        covid_checkup_data = await database.fetch_one(query=select([covid_checkup])
            .where(covid_checkup.c.client_id == client_id)
        )
        return {k:v for k,v in covid_checkup_data.items()}

    @pytest.mark.asyncio
    async def get_covid_checkup_id(self,client_id: int):
        covid_checkup_data = await database.fetch_one(query=select([covid_checkup])
            .where(covid_checkup.c.client_id == client_id)
        )
        return covid_checkup_data['id']

    @pytest.mark.asyncio
    async def update_covid_checkup(self,id_: int, **kwargs):
        await database.execute(query=covid_checkup.update().where(covid_checkup.c.id == id_),values=kwargs)
