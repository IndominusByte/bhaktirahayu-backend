from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT
from schemas.utils.UtilSchema import UtilEncodingImageBase64
from libs.MagicImage import MagicImage

router = APIRouter()

@router.post('/encoding-image-base64',response_model=bytes)
async def encoding_image_base64(util_data: UtilEncodingImageBase64, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return MagicImage.convert_image_as_base64(util_data.path_file)
