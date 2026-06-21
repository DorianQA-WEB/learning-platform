from logging import getLogger
from typing import Union
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_session
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import DeleteUserResponse
from api.models import ShowUser
from api.models import UpdateUserRequest
from api.models import UpdateUserResponse
from api.models import UserCreate
from db.dals import UserDAL
from db.session import get_db

"""
Модуль обработчиков (handlers) для API-роутов пользователя.

Определяет:
- CRUD-операции (создание, чтение, обновление, удаление) для пользователя.
- Обработку ошибок (IntegrityError → 503, not found → 404).
- Валидацию входящих данных через Pydantic-модели.
- Интеграцию с SQLAlchemy и FastAPI через dependency injection.

"""

logger = getLogger(__name__)

# create router for user
user_router = APIRouter()


async def _create_new_user(body: UserCreate) -> ShowUser:
    """
    Создаёт нового пользователя в БД.

    ⚠️ НЕ ИСПОЛЬЗУЕТ `db`, передаваемую из хендлера — в текущем виде принимает только `body`,
    но вызывается из create_user() с `db` как второй аргумент — это приведёт к TypeError.

    Args:
        body: Pydantic-модель с данными для создания пользователя (name, surname, email).

    Returns:
        ShowUser: Возвращает созданный пользователь с user_id.

    Raises:
        IntegrityError: При дублировании email (но не перехватывается здесь).
    """
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.create_user(
                name=body.name, surname=body.surname, email=body.email
            )

            return ShowUser(
                user_id=user.user_id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                is_active=user.is_active,
            )


async def _delete_user(user_id, db) -> Union[UUID, None]:
    """
    Создаёт нового пользователя в БД.

    ⚠️ НЕ ИСПОЛЬЗУЕТ `db`, передаваемую из хендлера — в текущем виде принимает только `body`,
    но вызывается из create_user() с `db` как второй аргумент — это приведёт к TypeError.

    Args:
        body: Pydantic-модель с данными для создания пользователя (name, surname, email).

    Returns:
        ShowUser: Возвращает созданный пользователь с user_id.

    Raises:
        IntegrityError: При дублировании email (но не перехватывается здесь).
    """
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            deleted_user = await user_dal.delete_user(user_id)
            return deleted_user


async def _get_user_by_id(user_id, db) -> Union[ShowUser, None]:
    """
    Получает пользователя по ID.

    Args:
        user_id: UUID пользователя.
        db: AsyncSession.

    Returns:
        ShowUser или None: Данные пользователя или None, если не найден.
    """
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.get_user_by_id(user_id=user_id)
            if user is not None:
                return ShowUser(
                    user_id=user.user_id,
                    name=user.name,
                    surname=user.surname,
                    email=user.email,
                    is_active=user.is_active,
                )


async def _update_user(
    updated_user_params: dict, user_id: UUID, db
) -> Union[UUID, None]:
    """
    Обновляет данные пользователя.

    Args:
        updated_user_params: Словарь с полями для обновления (name, surname, email).
        user_id: UUID пользователя для обновления.
        db: AsyncSession (но используется `async with db as session` — избыточно).

    Returns:
        UUID или None: ID обновлённого пользователя или None, если не найден.

    Raises:
        IntegrityError: При дублировании email.
    """
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            update_user_id = await user_dal.update_user(
                user_id=user_id, **updated_user_params
            )
            return update_user_id


@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)) -> ShowUser:
    """
    Эндпоинт для создания нового пользователя.

    Args:
        body: Данные для создания пользователя (валидируются UserCreate).
        db: AsyncSession от get_db().

    Returns:
        ShowUser: Созданный пользователь.

    Raises:
        HTTPException(status_code=503): При ошибке уникальности email (IntegrityError).
    """
    try:
        return _create_new_user(body, db)
    except IntegrityError as e:
        logger.error(e)
        raise HTTPException(status_code=503, detail=f"Database error: {e}")


@user_router.delete("/", response_model=DeleteUserResponse)
async def delete_user(
    user_id: UUID, db: AsyncSession = Depends(get_db)
) -> DeleteUserResponse:
    """
    Эндпоинт для удаления пользователя (soft delete).

    Args:
        user_id: UUID пользователя для удаления (передаётся как query-параметр ?user_id=...).
        db: AsyncSession от get_db().

    Returns:
        DeleteUserResponse: UUID удалённого пользователя.

    Raises:
        HTTPException(status_code=404): Если пользователь не найден.
    """
    deleted_user_id = await _delete_user(user_id, db)
    if deleted_user_id is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return DeleteUserResponse(user_id=deleted_user_id)


@user_router.get("/", response_model=ShowUser)
async def get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)) -> ShowUser:
    """
    Эндпоинт для получения пользователя по ID.

    ⚠️ НЕПРАВИЛЬНО: использует query-параметр `?user_id=...`, но должен использовать path-параметр `/{user_id}`.

    Args:
        user_id: UUID пользователя (передаётся как query-параметр).
        db: AsyncSession от get_db().

    Returns:
        ShowUser: Данные пользователя.

    Raises:
        HTTPException(status_code=404): Если пользователь не найден.
    """
    user = await _get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return user


@user_router.patch("/", response_model=UpdateUserResponse)
async def update_user_by_id(
    user_id: UUID, body: UpdateUserRequest, db: AsyncSession = Depends(get_db)
) -> UpdateUserResponse:
    """
    Эндпоинт для частичного обновления пользователя.

    ⚠️ НЕПРАВИЛЬНО: использует query-параметр `?user_id=...`, но должен использовать `/{user_id}`.

    Args:
        user_id: UUID пользователя (передаётся как query-параметр).
        body: Данные для обновления (валидируются UpdateUserRequest).
        db: AsyncSession от get_db().

    Returns:
        UpdateUserResponse: UUID обновлённого пользователя.

    Raises:
        HTTPException(status_code=400): Если тело запроса пустое.
        HTTPException(status_code=404): Если пользователь не найден.
        HTTPException(status_code=503): При ошибке уникальности email (IntegrityError).
    """
    updated_user_params = body.model_dump(exclude_none=True)
    if updated_user_params == {}:
        raise HTTPException(
            status_code=400,
            detail="At least one parameter for user update info should be provided",
        )
    user = await _get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    try:
        updated_user_id = await _update_user(
            updated_user_params=updated_user_params, db=db, user_id=user_id
        )
    except IntegrityError as e:
        logger.error(e)
        raise HTTPException(status_code=503, detail=f"Database error: {e}")
    return UpdateUserResponse(updated_user_id=updated_user_id)
