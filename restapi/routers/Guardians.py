from fastapi import APIRouter, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.GuardianController import GuardianFetch, GuardianCrud
from controllers.UserController import UserFetch
from dependencies.GuardianDependant import get_all_query_guardian
from schemas.guardians.GuardianSchema import (
    GuardianCreateUpdate, GuardianDataPaginate,
    GuardianData, GuardianMultiple
)
from typing import List

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new guardian."}}}
        },
        400: {
            "description": "Name already taken",
            "content": {"application/json":{"example": {"detail": "The name has already been taken."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        }
    }
)
async def create_guardian(guardian_data: GuardianCreateUpdate, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if await GuardianFetch.filter_by_name(guardian_data.name):
        raise HTTPException(status_code=400,detail="The name has already been taken.")

    await GuardianCrud.create_guardian(guardian_data.name)
    return {"detail": "Successfully add a new guardian."}

@router.get('/all-guardians',response_model=GuardianDataPaginate)
async def get_all_guardians(query_string: get_all_query_guardian = Depends()):
    return await GuardianFetch.get_all_guardians_paginate(**query_string)

@router.post('/get-multiple-guardians',response_model=List[GuardianData])
async def get_multiple_guardians(guardian_data: GuardianMultiple, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await GuardianFetch.get_multiple_guardians(guardian_data.list_id)

@router.put('/update/{guardian_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the guardian."}}}
        },
        400: {
            "description": "Name already taken",
            "content": {"application/json":{"example": {"detail": "The name has already been taken."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Guardian not found",
            "content": {"application/json": {"example": {"detail": "Guardian not found!"}}}
        }
    }
)
async def update_guardian(
    guardian_data: GuardianCreateUpdate,
    guardian_id: int = Path(...,gt=0),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if guardian := await GuardianFetch.filter_by_id(guardian_id):
        if guardian['name'] != guardian_data.name and await GuardianFetch.filter_by_name(guardian_data.name):
            raise HTTPException(status_code=400,detail="The name has already been taken.")

        await GuardianCrud.update_guardian(guardian['id'],name=guardian_data.name)
        return {"detail": "Successfully update the guardian."}
    raise HTTPException(status_code=404,detail="Guardian not found!")

@router.delete('/delete/{guardian_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the guardian."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Guardian not found",
            "content": {"application/json": {"example": {"detail": "Guardian not found!"}}}
        }
    }
)
async def delete_guardian(guardian_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if guardian := await GuardianFetch.filter_by_id(guardian_id):
        await GuardianCrud.delete_guardian(guardian['id'])
        return {"detail": "Successfully delete the guardian."}
    raise HTTPException(status_code=404,detail="Guardian not found!")
