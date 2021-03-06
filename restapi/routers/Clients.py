from fastapi import APIRouter, Request, Response, Path, Query, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.CovidCheckupController import CovidCheckupCrud, CovidCheckupLogic
from controllers.ClientController import ClientCrud, ClientFetch
from controllers.InstitutionController import InstitutionFetch
from controllers.LocationServiceController import LocationServiceFetch
from dependencies.ClientDependant import (
    identity_card_ocr_form, get_all_query_client_paginate,
    get_all_query_client_export
)
from schemas.clients.ClientSchema import (
    ClientDataImageOcr, ClientCreate,
    ClientUpdate, ClientPaginate,
    ClientExportData, ClientGetDataByNik,
    ClientGetInfoByNik
)
from libs.MagicImage import MagicImage
from typing import List

router = APIRouter()

@router.post('/identity-card-ocr',response_model=ClientDataImageOcr,
    responses={
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def identity_card_ocr(request: Request, form_data: identity_card_ocr_form = Depends()):
    image_ocr = MagicImage.save_image_to_storage(
        file=form_data['image'].file,
        path_upload='identity_ocr/{}'.format(form_data['kind'])
    )
    if form_data['kind'] == 'kis':
        result = request.app.state.ocr_kis.extract_image_to_text(image_ocr)
        MagicImage.delete_image(image_ocr,path_delete='identity_ocr/kis/')
    if form_data['kind'] == 'ktp':
        result = request.app.state.ocr_ktp.extract_image_to_text(image_ocr)
        MagicImage.delete_image(image_ocr,path_delete='identity_ocr/ktp/')

    return result

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully registration."}}}
        },
        400: {
            "description": "Cannot register many times",
            "content": {"application/json":{"example": {"detail": "You cannot register many times at the same institute, please try again after 1 hour."}}}
        },
        404: {
            "description": "Institution not found or Institution does not have antigen/genose",
            "content": {"application/json": {"example": {"detail": "string"}}}
        }
    }
)
async def create_client(client_data: ClientCreate, response: Response):
    # check institution have antigen, genose, or pcr
    if institution := await InstitutionFetch.filter_by_id(client_data.institution_id):
        for kind in ['antigen','genose','pcr']:
            if institution[kind] is None and client_data.checking_type == kind:
                raise HTTPException(status_code=404,detail=f"The institution does not have {kind} checking.")
    else: raise HTTPException(status_code=404,detail="Institution not found!")

    # check location service if exists
    if client_data.location_service_id and not await LocationServiceFetch.filter_by_id(client_data.location_service_id):
        raise HTTPException(status_code=404,detail="Location-service not found!")

    client_data.birth_date = client_data.birth_date.replace(tzinfo=None)
    # make client identity to uppercase
    client_identity = {
        **{k:v.upper() for k,v in client_data.dict(exclude={'birth_date','checking_type','institution_id','location_service_id'}).items()},
        **{'birth_date': client_data.birth_date}
    }

    covid_checkup_data = client_data.dict(include={'checking_type','institution_id','location_service_id'})

    # update client when nik exists in db
    if client := await ClientFetch.filter_by_nik(client_identity['nik']):
        # cannot register many times in same institute on same day
        if await CovidCheckupLogic.covid_checkup_on_same_date_and_institution(
            covid_checkup_data['checking_type'],
            covid_checkup_data['institution_id'],
            client['id']
        ):
            raise HTTPException(
                status_code=400,
                detail="You cannot register many times at the same institute, please try again after 1 hour."
            )

        await ClientCrud.update_client(client['id'],**client_identity)
        await CovidCheckupCrud.create_covid_checkup(client_id=client['id'],**covid_checkup_data)
        response.status_code = 200
    else:
        client_id = await ClientCrud.create_client(**client_identity)
        await CovidCheckupCrud.create_covid_checkup(client_id=client_id,**covid_checkup_data)

    return {"detail": "Successfully registration."}

@router.get('/get-data-by-nik',response_model=ClientGetDataByNik)
async def get_client_data_by_nik(nik: str = Query(...,min_length=1,regex=r'^[A-Z0-9]*$')):
    return await ClientFetch.filter_by_nik(nik)

@router.get('/get-info-by-nik',response_model=ClientGetInfoByNik)
async def get_client_info_by_nik(request: Request, nik: str = Query(...,min_length=1,regex=r'^[0-9]*$')):
    return request.app.state.nik_extraction.nik_extract(nik)

@router.get('/all-clients',response_model=ClientPaginate)
async def get_all_clients(query_string: get_all_query_client_paginate = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await ClientFetch.get_all_clients_paginate(with_paginate=True,**query_string)

@router.get('/all-clients-export',response_model=List[ClientExportData])
async def get_all_clients_export(query_string: get_all_query_client_export = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await ClientFetch.get_all_clients_paginate(with_paginate=False,**query_string)

@router.put('/update/{client_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the client."}}}
        },
        400: {
            "description": "Nik already taken",
            "content": {"application/json":{"example": {"detail": "The nik has already been taken."}}}
        },
        404: {
            "description": "Client not found",
            "content": {"application/json": {"example": {"detail": "Client not found!"}}}
        }
    }
)
async def update_client(
    client_data: ClientUpdate,
    client_id: int = Path(...,gt=0),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    if client := await ClientFetch.filter_by_id(client_id):
        client_data.birth_date = client_data.birth_date.replace(tzinfo=None)
        # make client identity to uppercase
        client_identity = {
            **{k:v.upper() for k,v in client_data.dict(exclude={'birth_date'}).items()},
            **{'birth_date': client_data.birth_date}
        }

        if client['nik'] != client_identity['nik'] and await ClientFetch.filter_by_nik(client_identity['nik']):
            raise HTTPException(status_code=400,detail="The nik has already been taken.")

        await ClientCrud.update_client(client['id'],**client_identity)

        return {"detail": "Successfully update the client."}
    raise HTTPException(status_code=404,detail="Client not found!")

@router.delete('/delete/{client_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the client."}}}
        },
        404: {
            "description": "Client not found",
            "content": {"application/json": {"example": {"detail": "Client not found!"}}}
        }
    }
)
async def delete_client(client_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    if client := await ClientFetch.filter_by_id(client_id):
        await ClientCrud.delete_client(client['id'])
        return {"detail": "Successfully delete the client."}
    raise HTTPException(status_code=404,detail="Client not found!")
