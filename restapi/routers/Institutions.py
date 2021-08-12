from fastapi import APIRouter, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.InstitutionController import InstitutionFetch, InstitutionCrud
from controllers.UserController import UserFetch
from dependencies.InstitutionDependant import create_form_institution, update_form_institution, get_all_query_institution
from schemas.institutions.InstitutionSchema import InstitutionDataPaginate, InstitutionMultiple, InstitutionData
from libs.MagicImage import MagicImage
from typing import List

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new institution."}}}
        },
        400: {
            "description": "Name already taken",
            "content": {"application/json":{"example": {"detail": "The name has already been taken."}}}
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
async def create_institution(form_data: create_form_institution = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if await InstitutionFetch.filter_by_name(form_data['name']):
        raise HTTPException(status_code=400,detail="The name has already been taken.")

    image_magic = MagicImage(
        file=form_data['stamp'].file,
        width=500,
        height=500,
        path_upload='institution/',
        square=True
    )
    image_magic.save_image()
    form_data['stamp'] = image_magic.file_name

    if antigen := form_data['antigen']:
        image_magic = MagicImage(
            file=antigen.file,
            width=1000,
            height=200,
            path_upload='institution/'
        )
        image_magic.save_image()
        form_data['antigen'] = image_magic.file_name

    if genose := form_data['genose']:
        image_magic = MagicImage(
            file=genose.file,
            width=1000,
            height=200,
            path_upload='institution/'
        )
        image_magic.save_image()
        form_data['genose'] = image_magic.file_name

    await InstitutionCrud.create_institution(**form_data)
    return {"detail": "Successfully add a new institution."}

@router.get('/all-institutions',response_model=InstitutionDataPaginate)
async def get_all_institutions(query_string: get_all_query_institution = Depends()):
    return await InstitutionFetch.get_all_institutions_paginate(**query_string)

@router.post('/get-multiple-institutions',response_model=List[InstitutionData])
async def get_multiple_institutions(institution_data: InstitutionMultiple, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await InstitutionFetch.get_multiple_institutions(institution_data.list_id)

@router.put('/update/{institution_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the institution."}}}
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
            "description": "Institution not found",
            "content": {"application/json": {"example": {"detail": "Institution not found!"}}}
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def update_institution(
    institution_id: int = Path(...,gt=0),
    form_data: update_form_institution = Depends(),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if institution := await InstitutionFetch.filter_by_id(institution_id):
        if institution['name'] != form_data['name'] and await InstitutionFetch.filter_by_name(form_data['name']):
            raise HTTPException(status_code=400,detail="The name has already been taken.")

        image_in_db = [value for index,value in institution.items() if value and index in ['stamp','antigen','genose']]
        try:
            image_delete = [value for value in form_data['image_delete'] if value in image_in_db]
        except Exception:
            image_delete = []

        if institution['stamp'] in image_delete and form_data['stamp'] is None:
            raise HTTPException(status_code=422,detail="Image is required, make sure the institution has stamp.")

        if (
            len([x for x in image_in_db if x not in institution['stamp'] and x not in image_delete]) == 0 and
            form_data['antigen'] is None and form_data['genose'] is None
        ):
            raise HTTPException(status_code=422,detail="Upps, at least upload one of antigen or genose.")

        if image_delete:
            [MagicImage.delete_image(file=file,path_delete='institution/') for file in image_delete]

        if stamp := form_data['stamp']:
            MagicImage.delete_image(file=institution['stamp'],path_delete='institution/')
            image_magic = MagicImage(
                file=stamp.file,
                width=500,
                height=500,
                path_upload='institution/',
                square=True
            )
            image_magic.save_image()
            form_data['stamp'] = image_magic.file_name

        if antigen := form_data['antigen']:
            MagicImage.delete_image(file=institution['antigen'],path_delete='institution/')
            image_magic = MagicImage(
                file=antigen.file,
                width=1000,
                height=200,
                path_upload='institution/'
            )
            image_magic.save_image()
            form_data['antigen'] = image_magic.file_name

        if genose := form_data['genose']:
            MagicImage.delete_image(file=institution['genose'],path_delete='institution/')
            image_magic = MagicImage(
                file=genose.file,
                width=1000,
                height=200,
                path_upload='institution/'
            )
            image_magic.save_image()
            form_data['genose'] = image_magic.file_name

        # set value in form_data when is value is None and value not in image_delete
        for value in ['stamp', 'antigen', 'genose']:
            if form_data[value] is None and institution[value] not in image_delete: form_data[value] = institution[value]

        await InstitutionCrud.update_institution(
            institution['id'],
            **{index:value for index,value in form_data.items() if index not in ['image_delete']}
        )
        return {"detail": "Successfully update the institution."}
    raise HTTPException(status_code=404,detail="Institution not found!")

@router.delete('/delete/{institution_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the institution."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Institution not found",
            "content": {"application/json": {"example": {"detail": "Institution not found!"}}}
        }
    }
)
async def delete_institution(institution_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='admin')

    if institution := await InstitutionFetch.filter_by_id(institution_id):
        MagicImage.delete_image(file=institution['stamp'],path_delete='institution/')
        MagicImage.delete_image(file=institution['antigen'],path_delete='institution/')
        MagicImage.delete_image(file=institution['genose'],path_delete='institution/')
        await InstitutionCrud.delete_institution(institution['id'])
        return {"detail": "Successfully delete the institution."}
    raise HTTPException(status_code=404,detail="Institution not found!")
