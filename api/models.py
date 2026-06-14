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
    """Базовая модель Pydantic с включённой поддержкой ORM (orm_mode)."""
    class Config:

        orm_mode = True


class ShowUser(TunedModel):
    """Модель для возврата информации о пользователе (GET-запросы)."""
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class UserCreate(BaseModel):
    """Модель для валидации данных при создании нового пользователя (POST /user/)."""
    name: str
    surname: str
    email: EmailStr

    @classmethod
    @field_validator("name")
    def validate_name(cls, name):
        """
        Валидирует, что имя состоит только из букв (русских/английских) и дефиса.

        Returns:
            str: Валидное имя.

        Raises:
            HTTPException: Если имя содержит недопустимые символы (status_code=422).
        """
        if not LETTER_MATCH_PATTERN.match(name):
            raise HTTPException(status_code=422, detail="Name should contains only letters")
        return name

    @classmethod
    @field_validator("surname")
    def validate_surname(cls, surname):
        """
        Валидирует, что фамилия состоит только из букв (русских/английских) и дефиса.

        Returns:
            str: Валидная фамилия.

        Raises:
            HTTPException: Если фамилия содержит недопустимые символы (status_code=422).
        """
        if not LETTER_MATCH_PATTERN.match(surname):
            raise HTTPException(status_code=422, detail="Surname should contains only letters")
        return surname


class DeleteUserResponse(BaseModel):
    """Модель ответа на запрос удаления пользователя (DELETE /user/)."""
    deleted_user_id: uuid.UUID


class UpdateUserRequest(BaseModel):
    """Модель для валидации данных при частичном обновлении пользователя (PATCH /user/)."""
    name: Optional[constr(min_length=1)]
    surname: Optional[constr(min_length=1)]
    email: Optional[EmailStr]

    @classmethod
    @field_validator("name")
    def validate_name(cls, name):
        """
        Валидирует, что имя (если указано) состоит только из букв и дефиса.

        Args:
            name: Имя пользователя или None.

        Returns:
            Optional[str]: Валидное имя или None.

        Raises:
            HTTPException: Если имя содержит недопустимые символы (status_code=422).
        """
        if not LETTER_MATCH_PATTERN.match(name):
            raise HTTPException(status_code=422, detail="Name should contains only letters")
        return name

    @classmethod
    @field_validator("surname")
    def validate_surname(cls, surname):
        """
        Валидирует, что фамилия (если указана) состоит только из букв и дефиса.

        Args:
            surname: Фамилия пользователя или None.

        Returns:
            Optional[str]: Валидная фамилия или None.

        Raises:
            HTTPException: Если фамилия содержит недопустимые символы (status_code=422).
        """
        if not LETTER_MATCH_PATTERN.match(surname):
            raise HTTPException(status_code=422, detail="Surname should contains only letters")
        return surname


class UpdateUserResponse(BaseModel):
    """Модель ответа на запрос обновления пользователя (PATCH /user/)."""
    update_user_id: uuid.UUID

