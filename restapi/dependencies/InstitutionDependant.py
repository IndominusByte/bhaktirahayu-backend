from fastapi import Query, Form, File, UploadFile, Depends, HTTPException
from libs.MagicImage import validate_single_upload_image
from libs.Parser import parse_str_list
from typing import Optional, Literal

def upload_image_stamp_required(stamp: UploadFile = File(...)):
    return validate_single_upload_image(
        image=stamp,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=5
    )

def upload_image_stamp_optional(stamp: Optional[UploadFile] = File(None)):
    if not stamp: return

    return validate_single_upload_image(
        image=stamp,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=5
    )

def upload_image_antigen_optional(antigen: Optional[UploadFile] = File(None)):
    if not antigen: return

    return validate_single_upload_image(
        image=antigen,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=5
    )

def upload_image_genose_optional(genose: Optional[UploadFile] = File(None)):
    if not genose: return

    return validate_single_upload_image(
        image=genose,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=5
    )

def create_form_institution(
    name: str = Form(...,min_length=3,max_length=100),
    stamp: upload_image_stamp_required = Depends(),
    antigen: upload_image_antigen_optional = Depends(),
    genose: upload_image_genose_optional = Depends()
):
    if antigen is None and genose is None:
        raise HTTPException(status_code=422,detail="Upps, at least upload one of antigen or genose.")

    return {
        'name': name,
        'stamp': stamp,
        'antigen': antigen,
        'genose': genose
    }

def update_form_institution(
    name: str = Form(...,min_length=3,max_length=100),
    image_delete: str = Form(None,min_length=2,description="Example 1.jpg,2.png,3.jpeg"),
    stamp: upload_image_stamp_optional = Depends(),
    antigen: upload_image_antigen_optional = Depends(),
    genose: upload_image_genose_optional = Depends()
):
    image_delete = parse_str_list(image_delete,",")
    if image_delete and False in [img.endswith(('.jpg','.png','.jpeg')) for img in image_delete]:
        raise HTTPException(status_code=422,detail="Invalid image format on image_delete")

    return {
        'name': name,
        'image_delete': image_delete,
        'stamp': stamp,
        'antigen': antigen,
        'genose': genose
    }

def get_all_query_institution(
    page: int = Query(...,gt=0),
    per_page: int = Query(...,gt=0),
    q: str = Query(None,min_length=1),
    checking_type: Literal['genose','antigen'] = Query(None)
):
    return {
        "page": page,
        "per_page": per_page,
        "q": q,
        "checking_type": checking_type
    }
