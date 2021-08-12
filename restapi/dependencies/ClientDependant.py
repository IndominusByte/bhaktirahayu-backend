from fastapi import UploadFile, Query, File, Form, Depends, HTTPException
from libs.MagicImage import validate_single_upload_image
from libs.Parser import parse_int_list, parse_str_date, get_date_now
from typing import Literal

def upload_image_required(image: UploadFile = File(...)):
    return validate_single_upload_image(
        image=image,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=5
    )

def identity_card_ocr_form(
    kind: Literal['ktp','kis'] = Form(...),
    image: upload_image_required = Depends()
):
    return {
        'kind': kind,
        'image': image
    }

def get_all_query_client(
    q: str = Query(None,min_length=1),
    gender: Literal['LAKI-LAKI','PEREMPUAN'] = Query(None),
    checking_type: Literal['antigen','genose'] = Query(None),
    check_result: Literal['positive','negative','empty'] = Query(None),
    doctor_id: str = Query(None,min_length=1,description="Example 1,2,3"),
    guardian_id: str = Query(None,min_length=1,description="Example 1,2,3"),
    location_service_id: str = Query(None,min_length=1,description="Example 1,2,3"),
    institution_id: str = Query(None,min_length=1,description="Example 1,2,3"),
    register_start_date: str = Query(None,min_length=1,regex=r'(\d{2}-\d{2}-\d{4})',example=get_date_now('%d-%m-%Y')),
    register_end_date: str = Query(None,min_length=1,regex=r'(\d{2}-\d{2}-\d{4})',example=get_date_now('%d-%m-%Y')),
    check_start_date: str = Query(
        None,min_length=1,regex=r'(\d{2}-\d{2}-\d{4} \d{2}:\d{2})',example=get_date_now('%d-%m-%Y %H:%M')
    ),
    check_end_date: str = Query(
        None,min_length=1,regex=r'(\d{2}-\d{2}-\d{4} \d{2}:\d{2})',example=get_date_now('%d-%m-%Y %H:%M')
    ),
):
    register_start_date = parse_str_date(register_start_date,'%d-%m-%Y') if register_start_date else None
    register_end_date = parse_str_date(register_end_date,'%d-%m-%Y') if register_end_date else None

    check_start_date = parse_str_date(check_start_date,'%d-%m-%Y %H:%M') if check_start_date else None
    check_end_date = parse_str_date(check_end_date,'%d-%m-%Y %H:%M') if check_end_date else None

    if register_start_date is not None and register_end_date is None:
        raise HTTPException(status_code=422,detail="register_end_date is required")
    if register_end_date is not None and register_start_date is None:
        raise HTTPException(status_code=422,detail="register_start_date is required")
    if register_start_date is not None and register_end_date is not None:
        if register_start_date > register_end_date:
            raise HTTPException(status_code=422,detail="the start time must be after the end time")

    if check_start_date is not None and check_end_date is None:
        raise HTTPException(status_code=422,detail="check_end_date is required")
    if check_end_date is not None and check_start_date is None:
        raise HTTPException(status_code=422,detail="check_start_date is required")
    if check_start_date is not None and check_end_date is not None:
        if check_start_date > check_end_date:
            raise HTTPException(status_code=422,detail="the start time must be after the end time")

    return {
        'q': q,
        'gender': gender,
        'checking_type': checking_type,
        'check_result': check_result,
        'doctor_id': parse_int_list(doctor_id,','),
        'guardian_id': parse_int_list(guardian_id,','),
        'location_service_id': parse_int_list(location_service_id,','),
        'institution_id': parse_int_list(institution_id,','),
        'register_start_date': register_start_date,
        'register_end_date': register_end_date,
        'check_start_date': check_start_date,
        'check_end_date': check_end_date
    }

def get_all_query_client_paginate(
    page: int = Query(...,gt=0),
    per_page: int = Query(...,gt=0),
    query_search: get_all_query_client = Depends()
):
    return {'page': page, 'per_page': per_page, **query_search}

def get_all_query_client_export(query_search: get_all_query_client = Depends()):
    return query_search
