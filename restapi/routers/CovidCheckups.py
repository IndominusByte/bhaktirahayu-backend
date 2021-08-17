from fastapi import APIRouter, Query, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.CovidCheckupController import CovidCheckupFetch, CovidCheckupCrud
from controllers.UserController import UserFetch
from controllers.GuardianController import GuardianFetch
from controllers.LocationServiceController import LocationServiceFetch
from controllers.InstitutionController import InstitutionFetch
from schemas.clients.ClientSchema import ClientCovidCheckupData
from schemas.covid_checkups.CovidCheckupSchema import (
    CovidCheckupUpdate, CovidCheckupDocumentData, CovidCheckupDocumentPdfData
)
from libs.MagicImage import MagicImage
from libs.MakeQRCode import generate_qr_code
from libs.Parser import int_to_roman
from datetime import datetime
from pytz import timezone
from config import settings
from uuid import uuid4
from typing import Literal

tz = timezone(settings.timezone)

router = APIRouter()

@router.put('/update/{covid_checkup_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the covid-checkup."}}}
        },
        401: {
            "description": "User without role doctor",
            "content": {"application/json": {"example": {"detail": "Only users with doctor privileges can do this action."}}}
        },
        404: {
            "description": "Covid-checkup, Doctor, Guardian, Location-Service, Institution not found",
            "content": {"application/json": {"example": {"detail": "string"}}}
        }
    }
)
async def update_covid_checkup(
    covid_checkup_data: CovidCheckupUpdate,
    covid_checkup_id: int = Path(...,gt=0),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_role(user_id,role='doctor')

    if covid_checkup := await CovidCheckupFetch.filter_by_id(covid_checkup_id):

        if doctor := await UserFetch.filter_by_id(covid_checkup_data.doctor_id):
            if doctor['role'] != 'doctor': raise HTTPException(status_code=404,detail="Doctor not found!")
        else: raise HTTPException(status_code=404,detail="Doctor not found!")

        if not await InstitutionFetch.filter_by_id(covid_checkup_data.institution_id):
            raise HTTPException(status_code=404,detail="Institution not found!")
        if (
            covid_checkup_data.guardian_id and
            not await GuardianFetch.filter_by_id(covid_checkup_data.guardian_id)
        ):
            raise HTTPException(status_code=404,detail="Guardian not found!")
        if (
            covid_checkup_data.location_service_id and
            not await LocationServiceFetch.filter_by_id(covid_checkup_data.location_service_id)
        ):
            raise HTTPException(status_code=404,detail="Location-service not found!")

        covid_checkup_data.check_date = covid_checkup_data.check_date.replace(tzinfo=None)
        additional_data = dict()

        # save qrcode if check_hash is None or qrcode has deleted
        if (
            covid_checkup['check_hash'] is None or
            (
                covid_checkup['check_hash'] is not None and
                MagicImage.check_file_exist('qrcode/{}.png'.format(covid_checkup['check_hash'])) is False
            )
        ):
            qrcode_hash = uuid4().hex
            additional_data.update({'check_hash': qrcode_hash})
            generate_qr_code(
                data=f"{settings.frontend_uri}/covid_checkups/validate-document/{qrcode_hash}",
                filename=f"{qrcode_hash}.png"
            )

        await CovidCheckupCrud.update_covid_checkup(covid_checkup['id'],**covid_checkup_data.dict(),**additional_data)
        return {"detail": "Successfully update the covid-checkup."}
    raise HTTPException(status_code=404,detail="Covid-checkup not found!")

@router.get('/get-covid-checkup/{covid_checkup_id}',response_model=ClientCovidCheckupData,
    responses={
        404: {
            "description": "Covid-checkup not found",
            "content": {"application/json": {"example": {"detail": "Covid-checkup not found!"}}}
        }
    }
)
async def get_covid_checkup_by_id(covid_checkup_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    if covid_checkup := await CovidCheckupFetch.get_covid_checkup_by_id(covid_checkup_id):
        return covid_checkup
    raise HTTPException(status_code=404,detail="Covid-checkup not found!")

@router.get('/preview-document/{institution_id}',response_model=CovidCheckupDocumentPdfData,
    responses={
        400: {
            "description": "Institution doesn't have letterhead",
            "content": {"application/json":{
                "example": {"detail": "The institution doesn't have letterhead please fill the image letterhead {type}."}}
            }
        },
        404: {
            "description": "Institution not found",
            "content": {"application/json": {"example": {"detail": "Institution not found!"}}}
        }
    }
)
async def preview_document_covid_checkup(
    institution_id: int = Path(...,gt=0),
    checking_type: Literal['antigen','genose'] = Query(...),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    if institution := await InstitutionFetch.filter_by_id(institution_id):
        # check letterhead in institution exists in db
        institution_letterhead = None
        if checking_type == 'antigen': institution_letterhead = institution['antigen']
        if checking_type == 'genose': institution_letterhead = institution['genose']

        if institution_letterhead is None:
            raise HTTPException(
                status_code=400,
                detail="The institution doesn't have letterhead please fill the image letterhead {}."
                .format(checking_type)
            )

        time_now = datetime.now(tz)

        # get format report number
        check_month = time_now.strftime("%m")
        check_year = time_now.strftime("%Y")
        report_number = "{}/{}/{}/{}".format(
            0, checking_type.upper(),
            int_to_roman(int(check_month)).upper(), check_year
        )

        return {
            'clients_nik': '5103051905990006',
            'clients_name': 'NYOMAN PRADIPTA DEWANTARA',
            'clients_phone': '+62 878-6226-5363',
            'clients_birth_place': 'BALIKPAPAN',
            'clients_birth_date': time_now,
            'clients_gender': 'LAKI-LAKI',
            'clients_address': 'DENPASAR',
            'clients_age': 0,
            'covid_checkups_report_number': report_number,
            'covid_checkups_checking_type': checking_type,
            'covid_checkups_check_date': time_now,
            'covid_checkups_check_result': 'negative',
            'covid_checkups_doctor_username': 'Boyke Dian Nugraha',
            'covid_checkups_doctor_email': 'boyke@gmail.com',
            'covid_checkups_institution_name': institution['name'],
            'covid_checkups_institution_letterhead': institution_letterhead,
            'covid_checkups_institution_stamp': institution['stamp'],
            'covid_checkups_doctor_signature': 'signature.png',
            'covid_checkups_check_qrcode': 'qrcode.png'
        }
    raise HTTPException(status_code=404,detail="Institution not found!")

@router.get('/see-document/{covid_checkup_id}',response_model=CovidCheckupDocumentPdfData,
    responses={
        400: {
            "description": "Institution doesn't have letterhead or Covid-checkup doesn't have required data",
            "content": {"application/json":{"example": {"detail": "string"}}}
        }
    }
)
async def see_document_covid_checkup(covid_checkup_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    if covid_checkup := await CovidCheckupFetch.get_covid_checkup_document(covid_checkup_id):
        # check letterhead in institution exists in db
        covid_checkups_institution_letterhead = None
        if covid_checkup['covid_checkups_checking_type'] == 'antigen':
            covid_checkups_institution_letterhead = covid_checkup['covid_checkups_institution_antigen']
        if covid_checkup['covid_checkups_checking_type'] == 'genose':
            covid_checkups_institution_letterhead = covid_checkup['covid_checkups_institution_genose']

        if covid_checkups_institution_letterhead is None:
            raise HTTPException(
                status_code=400,
                detail="The institution doesn't have letterhead please fill the image letterhead {}."
                .format(covid_checkup['covid_checkups_checking_type'])
            )

        # get format report number
        check_month = covid_checkup['covid_checkups_check_date'].strftime("%m")
        check_year = covid_checkup['covid_checkups_check_date'].strftime("%Y")
        report_number = "{}/{}/{}/{}".format(
            covid_checkup['covid_checkups_id'], covid_checkup['covid_checkups_checking_type'].upper(),
            int_to_roman(int(check_month)).upper(), check_year
        )

        # get age client
        client_year = covid_checkup['clients_birth_date'].strftime("%Y")
        now_year = datetime.now(tz).strftime("%Y")
        client_age = int(now_year) - int(client_year)

        # get qrcode
        if MagicImage.check_file_exist('qrcode/{}.png'.format(covid_checkup['covid_checkups_check_hash'])) is True:
            qrcode_png = covid_checkup['covid_checkups_check_hash'] + '.png'
        else: qrcode_png = 'qrcode.png'

        # get data required
        institution_data = {
            **{
                k:v for k,v in covid_checkup.items()
                if k in ['covid_checkups_institution_name', 'covid_checkups_institution_stamp']
            },
            **{'covid_checkups_institution_letterhead': covid_checkups_institution_letterhead}
        }
        doctor_data = {
            k:v for k,v in covid_checkup.items()
            if k in ['covid_checkups_doctor_username', 'covid_checkups_doctor_email', 'covid_checkups_doctor_signature']
        }
        covid_checkup_data = {
            **{
                k:v for k,v in covid_checkup.items()
                if k in ['covid_checkups_check_result', 'covid_checkups_check_date', 'covid_checkups_checking_type']
            },
            **{
                'covid_checkups_check_qrcode': qrcode_png,
                'covid_checkups_report_number': report_number
            }
        }
        client_data = {
            **{
                k:v for k,v in covid_checkup.items()
                if k in [
                    'clients_nik', 'clients_name', 'clients_phone',
                    'clients_birth_place', 'clients_birth_date',
                    'clients_gender', 'clients_address'
                ]
            },
            **{'clients_age': client_age}
        }

        return {**institution_data, **doctor_data, **covid_checkup_data, **client_data}
    raise HTTPException(status_code=400,detail="The covid-checkup doesn't have all the required data.")

@router.get('/validate-document/{check_hash}',response_model=CovidCheckupDocumentData)
async def validate_document_covid_checkup(check_hash: str = Path(...,min_length=1)):
    return await CovidCheckupFetch.get_covid_checkup_by_hash(check_hash)

@router.delete('/delete/{covid_checkup_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the covid-checkup."}}}
        },
        404: {
            "description": "Covid-checkup not found",
            "content": {"application/json": {"example": {"detail": "Covid-checkup not found!"}}}
        }
    }
)
async def delete_covid_checkup(covid_checkup_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    if covid_checkup := await CovidCheckupFetch.filter_by_id(covid_checkup_id):
        MagicImage.delete_image(file=f"{covid_checkup['check_hash']}.png",path_delete='qrcode/')
        await CovidCheckupCrud.delete_covid_checkup(covid_checkup['id'])
        return {"detail": "Successfully delete the covid-checkup."}
    raise HTTPException(status_code=404,detail="Covid-checkup not found!")
