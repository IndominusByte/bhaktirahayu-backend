import pytest, bcrypt, os
from copy import deepcopy
from sqlalchemy.sql import select
from config import database
from models.UserModel import user

class OperationTest:
    name = 'testtesttttttt'
    name2 = 'testtesttttttt2'
    account_admin = {'email':'admin@testing.com','username':'admintesting','password': 'testtesting'}
    account_1 = {'email':'testtesting@gmail.com','username':'testtesting','password':'testtesting'}
    account_2 = {'email':'testtesting2@gmail.com','username':'testtesting2','password':'testtesting2'}
    base_dir = os.path.join(os.path.dirname(__file__),'../static/')
    test_image_dir = base_dir + 'test_image/'
    signature_dir = base_dir + 'signature/'

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
