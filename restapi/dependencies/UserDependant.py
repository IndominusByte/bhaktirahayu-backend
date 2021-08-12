from fastapi import UploadFile, File, Form, Query, Depends
from libs.MagicImage import validate_single_upload_image
from pydantic import EmailStr
from typing import Optional

def upload_image_required(image: UploadFile = File(...)):
    return validate_single_upload_image(
        image=image,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=5
    )

def upload_image_optional(image: Optional[UploadFile] = File(None)):
    if not image: return

    return validate_single_upload_image(
        image=image,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=5
    )

def create_form_doctor(
    email: EmailStr = Form(...),
    username: str = Form(...,min_length=3,max_length=100),
    signature: upload_image_required = Depends()
):
    return {
        'email': email,
        'username': username,
        'signature': signature
    }

def update_form_user(
    email: EmailStr = Form(...),
    username: str = Form(...,min_length=3,max_length=100),
    signature: upload_image_optional = Depends()
):
    return {
        'email': email,
        'username': username,
        'signature': signature
    }

def get_all_query_doctor(
    page: int = Query(...,gt=0),
    per_page: int = Query(...,gt=0),
    q: str = Query(None,min_length=1),
):
    return {
        "page": page,
        "per_page": per_page,
        "q": q,
    }
