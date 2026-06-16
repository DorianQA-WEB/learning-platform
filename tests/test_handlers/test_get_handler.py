import json
from uuid import uuid4

import pytest



async def test_get_user(client, create_user_in_database, get_user_from_db):
    """
    Тестирует получение пользователя по ID через GET-запрос.

    Проверяет:
        - статус код 200,
        - возвращённые поля совпадают с исходными.

    ⚠️ ВНИМАНИЕ: в запросе используется `/user/user_id?user_id={...}`,
        что, скорее всего, является ошибкой — правильный путь: `/user/{user_id}`.

    Args:
        client: Тестовый клиент FastAPI.
        create_user_in_database: Fixture для предварительного создания пользователя.
        get_user_from_db: Fixture для получения пользователя из БД.
    """
    user_data = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@ivanov.com",
        "is_active": True
    }
    await create_user_in_database(**user_data)
    resp = client.get(f'/user/user_id?user_id={user_data["user_id"]}')
    assert resp.status_code == 200
    user_from_response = resp.json()
    assert user_from_response['user_id'] == str(user_data["user_id"])
    assert user_from_response['is_active'] is True
    assert user_from_response['email'] == user_data['email']
    assert user_from_response['name'] == user_data['name']
    assert user_from_response['surname'] == user_data['surname']