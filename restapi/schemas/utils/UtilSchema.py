import re
from pydantic import BaseModel, FilePath, PathError, validator

class UtilSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class UtilEncodingImageBase64(UtilSchema):
    path_file: FilePath

    @validator('path_file')
    def check_valid_path(cls, v):
        if v and re.match("^.*static.*$", str(v)) is None:
            raise PathError()
        return v
