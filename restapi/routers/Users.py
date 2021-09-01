from fastapi import APIRouter, Request, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.UserController import UserFetch, UserCrud, UserLogic
from dependencies.UserDependant import create_form_doctor, update_form_doctor, get_all_query_doctor
from schemas.users.UserSchema import (
    UserData, UserLogin,
    UserUpdatePassword, UserDoctorPaginate,
    UserConfirmPassword, UserDoctorMultiple,
    UserDoctorData
)
from libs.MagicImage import MagicImage
from config import settings
from typing import List

router = APIRouter()

@router.post('/login',
    responses={
        200: {
            "description":"Successful Response",
            "content": {"application/json":{"example": {"detail":"Successfully login."}}}
        }
    }
)
async def login(user_data: UserLogin, authorize: AuthJWT = Depends()):
    if user := await UserFetch.filter_by_email(user_data.email):
        if user['password'] and UserLogic.password_is_same_as_hash(user_data.password,user['password']):
            access_token = authorize.create_access_token(
                subject=str(user['id']),
                fresh=True,
                expires_time=settings.access_expires
            )
            refresh_token = authorize.create_refresh_token(subject=str(user['id']))
            # set jwt in cookies
            authorize.set_access_cookies(access_token)
            authorize.set_refresh_cookies(refresh_token)
            return {"detail":"Successfully login."}
        raise HTTPException(status_code=422,detail="Invalid credential.")
    raise HTTPException(status_code=422,detail="Invalid credential.")

@router.post('/fresh-token',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"example": {"detail": "Successfully make a fresh token."}}}
        }
    }
)
async def fresh_token(user_data: UserConfirmPassword, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        if not UserLogic.password_is_same_as_hash(user_data.password,user['password']):
            raise HTTPException(status_code=422,detail="Password does not match with our records.")

        # set fresh access token in cookie
        access_token = authorize.create_access_token(
            subject=str(user['id']),
            fresh=True,
            expires_time=settings.access_expires
        )
        authorize.set_access_cookies(access_token)
        return {"detail": "Successfully make a fresh token."}

@router.post('/refresh-token',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "The token has been refreshed."}}}
        }
    }
)
async def refresh_token(authorize: AuthJWT = Depends()):
    authorize.jwt_refresh_token_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        new_token = authorize.create_access_token(subject=str(user['id']),expires_time=settings.access_expires)
        authorize.set_access_cookies(new_token)
        return {"detail": "The token has been refreshed."}

@router.delete('/access-revoke',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "An access token has revoked."}}}
        }
    }
)
def access_revoke(request: Request, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    jti = authorize.get_raw_jwt()['jti']
    request.app.state.redis.set(jti,'true',settings.access_expires)
    return {"detail": "An access token has revoked."}

@router.delete('/refresh-revoke',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "An refresh token has revoked."}}}
        }
    }
)
def refresh_revoke(request: Request, authorize: AuthJWT = Depends()):
    authorize.jwt_refresh_token_required()

    jti = authorize.get_raw_jwt()['jti']
    request.app.state.redis.set(jti,'true',settings.refresh_expires)
    return {"detail": "An refresh token has revoked."}

@router.delete('/delete-cookies',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "All cookies have been deleted."}}}
        }
    }
)
def delete_cookies(authorize: AuthJWT = Depends()):
    authorize.unset_jwt_cookies()

    return {"detail": "All cookies have been deleted."}

@router.put('/update-password',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"example": {"detail": "Success update your password."}}}
        },
    }
)
async def update_password(user_data: UserUpdatePassword, authorize: AuthJWT = Depends()):
    authorize.fresh_jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        if not UserLogic.password_is_same_as_hash(user_data.old_password,user['password']):
            raise HTTPException(status_code=422,detail="Password does not match with our records.")

        await UserCrud.update_password_user(user['id'],user_data.password)  # update password
        return {"detail": "Success update your password."}

@router.put('/update-account',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"example": {"detail": "Success updated your account."}}}
        },
        400: {
            "description": "Email already taken & Only doctor can upload signature",
            "content": {"application/json":{"example": {"detail": "string"}}}
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def update_account(form_data: update_form_doctor = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        # only doctor can upload signature
        if user['role'] != 'doctor' and form_data['signature'] is not None:
            raise HTTPException(status_code=400,detail="The only a doctor can change signature.")
        # check email duplicate
        if user['email'] != form_data['email'] and await UserFetch.filter_by_email(form_data['email']):
            raise HTTPException(status_code=400,detail="The email has already been taken.")

        if signature := form_data['signature']:
            MagicImage.delete_image(file=user['signature'],path_delete='signature/')
            image_magic = MagicImage(
                file=signature.file,
                width=500,
                height=500,
                path_upload='signature/',
                square=True
            )
            image_magic.save_image()
            form_data['signature'] = image_magic.file_name

        if form_data['signature'] is None: del form_data['signature']

        await UserCrud.update_user(user['id'], **form_data)
        return {"detail": "Success updated your account."}

@router.get('/my-user', response_model=UserData)
async def my_user(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return {index:value for index,value in user.items()}

@router.post('/create-doctor',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new doctor."}}}
        },
        400: {
            "description": "Email already taken",
            "content": {"application/json":{"example": {"detail": "The email has already been taken."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def create_doctor(form_data: create_form_doctor = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if await UserFetch.filter_by_email(form_data['email']):
        raise HTTPException(status_code=400,detail="The email has already been taken.")

    image_magic = MagicImage(
        file=form_data['signature'].file,
        width=500,
        height=500,
        path_upload='signature/',
        square=True
    )
    image_magic.save_image()
    form_data['signature'] = image_magic.file_name

    await UserCrud.create_user(**form_data,role='doctor',password='bhaktirahayu')
    return {"detail": "Successfully add a new doctor."}

@router.get('/all-doctors',response_model=UserDoctorPaginate)
async def get_all_doctors(query_string: get_all_query_doctor = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await UserFetch.get_all_doctors_paginate(**query_string)

@router.post('/get-multiple-doctors',response_model=List[UserDoctorData])
async def get_multiple_doctors(doctor_data: UserDoctorMultiple, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await UserFetch.get_multiple_users(doctor_data.list_id)

@router.put('/reset-password-doctor/{doctor_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully reset the password of the doctor."}}}
        },
        400: {
            "description": "Can only reset password doctor account",
            "content": {"application/json":{"example": {"detail": "You can only reset the password of a doctor account."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Doctor not found",
            "content": {"application/json": {"example": {"detail": "Doctor not found!"}}}
        },

    }
)
async def reset_password_doctor(doctor_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if user := await UserFetch.filter_by_id(doctor_id):
        if user['role'] == 'doctor':
            await UserCrud.update_password_user(user['id'],'bhaktirahayu')  # update password
            return {"detail": "Successfully reset the password of the doctor."}
        raise HTTPException(status_code=400,detail="You can only reset the password of a doctor account.")
    raise HTTPException(status_code=404,detail="Doctor not found!")

@router.put('/update-doctor/{doctor_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the doctor."}}}
        },
        400: {
            "description": "Email already taken & Can only edit doctor account",
            "content": {"application/json":{"example": {"detail": "string"}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Doctor not found",
            "content": {"application/json": {"example": {"detail": "Doctor not found!"}}}
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def update_doctor(
    doctor_id: int = Path(...,gt=0),
    form_data: update_form_doctor = Depends(),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if user := await UserFetch.filter_by_id(doctor_id):
        # check account is doctor
        if user['role'] != 'doctor':
            raise HTTPException(status_code=400,detail="You can only edit a doctor account.")
        # check email duplicate
        if user['email'] != form_data['email'] and await UserFetch.filter_by_email(form_data['email']):
            raise HTTPException(status_code=400,detail="The email has already been taken.")

        if signature := form_data['signature']:
            MagicImage.delete_image(file=user['signature'],path_delete='signature/')
            image_magic = MagicImage(
                file=signature.file,
                width=500,
                height=500,
                path_upload='signature/',
                square=True
            )
            image_magic.save_image()
            form_data['signature'] = image_magic.file_name

        if form_data['signature'] is None: del form_data['signature']

        await UserCrud.update_user(user['id'], **form_data)
        return {"detail": "Successfully update the doctor."}
    raise HTTPException(status_code=404,detail="Doctor not found!")

@router.delete('/delete-doctor/{doctor_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the doctor."}}}
        },
        400: {
            "description": "Cannot delete an admin account",
            "content": {"application/json":{"example": {"detail": "You can't delete an admin account."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Doctor not found",
            "content": {"application/json": {"example": {"detail": "Doctor not found!"}}}
        },
    }
)
async def delete_doctor(doctor_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if user := await UserFetch.filter_by_id(doctor_id):
        if user['role'] == 'doctor':
            MagicImage.delete_image(file=user['signature'],path_delete='signature/')
            await UserCrud.delete_user(user['id'])
            return {"detail": "Successfully delete the doctor."}
        raise HTTPException(status_code=400,detail="You can't delete an admin account.")
    raise HTTPException(status_code=404,detail="Doctor not found!")
