import bcrypt
from config import database
from sqlalchemy import select, func
from models.UserModel import user
from libs.Pagination import Pagination
from fastapi import HTTPException

class UserLogic:
    @staticmethod
    def password_is_same_as_hash(password: str, password_db: str) -> bool:
        return bcrypt.checkpw(password.encode(),password_db.encode())

class UserCrud:
    @staticmethod
    async def create_user(**kwargs) -> int:
        hashed_pass = bcrypt.hashpw(kwargs['password'].encode(), bcrypt.gensalt())
        kwargs.update({'password': hashed_pass.decode('utf-8')})
        return await database.execute(query=user.insert(),values=kwargs)

    @staticmethod
    async def update_password_user(id_: int, password: str) -> None:
        query = user.update().where(user.c.id == id_)
        hashed_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        await database.execute(query=query,values={
            "password": hashed_pass.decode('utf-8'),
            "updated_at": func.now()
        })

    @staticmethod
    async def update_user(id_: int, **kwargs) -> None:
        kwargs.update({"updated_at": func.now()})
        await database.execute(query=user.update().where(user.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_user(id_: int) -> None:
        await database.execute(query=user.delete().where(user.c.id == id_))

class UserFetch:
    @staticmethod
    async def user_is_role(id_: int, role: str) -> user:
        if user_role := await database.fetch_one(query=select([user]).where(user.c.id == id_)):
            if user_role['role'] == role:
                return user_role
            raise HTTPException(status_code=401,detail=f"Only users with {role} privileges can do this action.")
        raise HTTPException(status_code=404,detail="User not found!")

    @staticmethod
    async def get_multiple_users(list_id: list) -> list:
        query = select([user.c.id, user.c.username]).where((user.c.role == 'doctor') & (user.c.id.in_(list_id))) \
            .order_by(user.c.id.desc()).apply_labels()

        doctor_db = await database.fetch_all(query=query)
        return [{index:value for index,value in item.items()} for item in doctor_db]

    @staticmethod
    async def get_all_doctors_paginate(**kwargs) -> dict:
        query = select([user]).where(user.c.role == 'doctor').order_by(user.c.id.desc()).apply_labels()

        if q := kwargs['q']:
            query = query.where((user.c.username.ilike(f"%{q}%")) | (user.c.email.ilike(f"%{q}%")))

        total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
        query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
        doctor_db = await database.fetch_all(query=query)

        paginate = Pagination(kwargs['page'], kwargs['per_page'], total, doctor_db)
        return {
            "data": [{index:value for index,value in item.items()} for item in paginate.items],
            "total": paginate.total,
            "next_num": paginate.next_num,
            "prev_num": paginate.prev_num,
            "page": paginate.page,
            "iter_pages": [x for x in paginate.iter_pages()]
        }

    @staticmethod
    async def filter_by_email(email: str) -> user:
        query = select([user]).where(user.c.email == email)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_id(id_: int) -> user:
        query = select([user]).where(user.c.id == id_)
        return await database.fetch_one(query=query)
