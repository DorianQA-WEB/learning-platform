import re
import uuid
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, field_validator, constr

#########################
# BLOCK WITH API MODELS #
#########################


LETTER_MATCH_PATTERN = re.compile(r'^[a-яА-Яa-zA-Z\-]+$')

class TunedModel(BaseModel):
    class Config:

        orm_mode = True


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr

    @classmethod
    @field_validator("name")
    def validate_name(cls, name):
        if not LETTER_MATCH_PATTERN.match(name):
            raise HTTPException(status_code=422, detail="Name should contains only letters")
        return name

    @classmethod
    @field_validator("surname")
    def validate_surname(cls, surname):
        if not LETTER_MATCH_PATTERN.match(surname):
            raise HTTPException(status_code=422, detail="Surname should contains only letters")
        return surname


class DeleteUserResponse(BaseModel):
    deleted_user_id: uuid.UUID


class UserUpdateRequest(BaseModel):
    name: Optional[constr(min_length=1)]
    surname: Optional[constr(min_length=1)]
    email: Optional[EmailStr]

    @classmethod
    @field_validator("name")
    def validate_name(cls, name):
        if not LETTER_MATCH_PATTERN.match(name):
            raise HTTPException(status_code=422, detail="Name should contains only letters")
        return name

    @classmethod
    @field_validator("surname")
    def validate_surname(cls, surname):
        if not LETTER_MATCH_PATTERN.match(surname):
            raise HTTPException(status_code=422, detail="Surname should contains only letters")
        return surname


class UserUpdateResponse(BaseModel):
    update_user_id: uuid.UUID

