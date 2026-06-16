import json
from uuid import uuid4

import pytest


async def test_delete_user(client, create_user_in_database, get_user_from_database):
    """
    Тестирует удаление пользователя через DELETE-запрос.

    Проверяет:
        - статус код 200 (успешное удаление),
        - формат ответа: `{"deleted_user_id": "..."}`
        - что пользователь помечен как `is_active=False` в базе (soft delete),
        - все поля пользователя сохранены.

    Args:
        client: Тестовый клиент FastAPI.
        create_user_in_database: Fixture для предварительного создания пользователя.
        get_user_from_database: Fixture для получения пользователя из БД.
    """
    user_data = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@ivanov.com",
        'is_active': True
    }

    await create_user_in_database(**user_data)
    response = client.delete(f"/users/?user_id={user_data['user_id']}")
    assert response.status_code == 200
    assert response.json() == {"deleted_user_id": str(user_data["user_id"])}
    users_from_db = await get_user_from_database(user_data["user_id"])
    user_from_db = dict(users_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is False
    assert user_from_db["user_id"] == user_data["user_id"]