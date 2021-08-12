from fastapi import APIRouter, Path, Depends, HTTPException
from controllers.LocationServiceController import LocationServiceCrud, LocationServiceFetch
from controllers.UserController import UserFetch
from dependencies.LocationServiceDependant import get_all_query_location_service
from schemas.location_services.LocationServiceSchema import (
    LocationServiceCreateUpdate, LocationServiceDataPaginate,
    LocationServiceData, LocationServiceMultiple
)
from fastapi_jwt_auth import AuthJWT
from typing import List

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new location-service."}}}
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
async def create_location_service(location_service_data: LocationServiceCreateUpdate, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if await LocationServiceFetch.filter_by_name(location_service_data.name):
        raise HTTPException(status_code=400,detail="The name has already been taken.")

    await LocationServiceCrud.create_location_service(location_service_data.name)
    return {"detail": "Successfully add a new location-service."}

@router.get('/all-location-services',response_model=LocationServiceDataPaginate)
async def get_all_location_services(query_string: get_all_query_location_service = Depends()):
    return await LocationServiceFetch.get_all_location_services_paginate(**query_string)

@router.post('/get-multiple-location-services',response_model=List[LocationServiceData])
async def get_multiple_location_services(location_service_data: LocationServiceMultiple, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await LocationServiceFetch.get_multiple_location_services(location_service_data.list_id)

@router.put('/update/{location_service_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the location-service."}}}
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
            "description": "Location-service not found",
            "content": {"application/json": {"example": {"detail": "Location-service not found!"}}}
        }
    }
)
async def update_location_service(
    location_service_data: LocationServiceCreateUpdate,
    location_service_id: int = Path(...,gt=0),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if location_service := await LocationServiceFetch.filter_by_id(location_service_id):
        if (
            location_service['name'] != location_service_data.name and
            await LocationServiceFetch.filter_by_name(location_service_data.name)
        ):
            raise HTTPException(status_code=400,detail="The name has already been taken.")

        await LocationServiceCrud.update_location_service(location_service['id'],name=location_service_data.name)
        return {"detail": "Successfully update the location-service."}
    raise HTTPException(status_code=404,detail="Location-service not found!")

@router.delete('/delete/{location_service_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the location-service."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Location-service not found",
            "content": {"application/json": {"example": {"detail": "Location-service not found!"}}}
        }
    }
)
async def delete_location_service(location_service_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if location_service := await LocationServiceFetch.filter_by_id(location_service_id):
        await LocationServiceCrud.delete_location_service(location_service['id'])
        return {"detail": "Successfully delete the location-service."}
    raise HTTPException(status_code=404,detail="Location-service not found!")
