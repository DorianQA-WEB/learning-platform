"""
Тесты для API-.handlers пользователя в приложении Learning Platform.

Тестируются CRUD-операции над пользователем:
- создание пользователя (POST /users/)
- получение пользователя по ID (GET /user/user_id)
- обновление пользователя (PATCH /user/)
- удаление пользователя (DELETE /users/)

Тесты используют fixture'ы из conftest.py:
- `client`: асинхронный тестовый клиент FastAPI.
- `get_user_from_database`: функция для получения пользователя по ID из БД.
- `create_user_in_database`: функция для создания пользователя в БД.
- `get_user_in_db`: альтернативная функция получения пользователя (возможно, устаревшая).
"""
import json
from uuid import uuid4

import pytest


async def test_create_user(client, get_user_from_database):
    """
    Тестирует создание нового пользователя через POST-запрос.

    Проверяет:
        - статус код 200 (успешное создание),
        - корректность сохранённых данных (name, surname, email),
        - значение `is_active` по умолчанию (True),
        - совпадение данных в базе и в ответе.

    Args:
        client: Тестовый клиент FastAPI.
        get_user_from_database: Fixture для получения пользователя по ID.
    """
    user_data = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@ivanov.com"
    }
    resp = client.post("/users/", data=json.dumps(user_data))
    resp_data = resp.json()
    assert resp.status_code == 200
    assert resp_data["name"] == user_data["name"]
    assert resp_data["surname"] == user_data["surname"]
    assert resp_data["email"] == user_data["email"]
    assert resp_data["is_active"] is True
    user_from_db = await get_user_from_database(resp_data["user_id"])
    assert len(user_from_db) == 1
    user_from_db = dict(user_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert str(user_from_db["user_id"]) == resp_data["user_id"]
    assert user_from_db["is_active"] is True

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


async def test_update_user(client, create_user_in_database, get_user_from_db):
    """
    Тестирует частичное обновление пользователя через PATCH-запрос.

    Проверяет:
        - статус код 200,
        - обновлённые данные в ответе (name, surname, email),
        - ID пользователя не меняется,
        - поле `is_active` сохраняется (не обнуляется при отсутствии в update).

    ⚠️ ВНИМАНИЕ: путь `/user/&user_id={...}` содержит лишний `&` —
        это синтаксическая ошибка, должен быть `/user/{user_id}`.

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
    }
    user_data_updated = {
        "name": "Petr",
        "surname": "Petrov",
        "email": "petr@petrov.com",
    }
    await create_user_in_database(**user_data)
    response = client.patch(f"/user/&user_id={user_data['user_id']}", data=json.dumps(user_data_updated))
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["updated_user_id"] == str(user_data['user_id'])
    users_from_db = await get_user_from_db(user_data["user_id"])
    user_from_db = dict(users_from_db[0])
    assert user_from_db["name"] == user_data_updated["name"]
    assert user_from_db["surname"] == user_data_updated["surname"]
    assert user_from_db["email"] == user_data_updated["email"]
    assert user_from_db["user_id"] == user_data["user_id"]
    assert user_from_db["is_active"] is user_data["is_active"]

@pytest.mark.parametrize("user_data_updated, expected_status_code, expected_detail", [
    (
            {},
            422,
            {'detail': "At least one parameter for user update info should be provided"}
    ),
    (
            {"name": "123"},
            422,
            {'detail': "Name should contains only letters"}
    ),
    (
            {"email": ""},
            422,
            {'detail': [{'loc': ['body', 'email'],
                         'msg': 'value is not a valid email address',
                         'type': 'value_error.email'}]
             }
    ),
    (
            {"surname": ""},
            422,
            {'detail': [{'loc': ['body', 'surname'], 'msg': 'ensure this value has at least 1 characters',
                         'type': 'value_error.any_str.min_length', 'ctx': {'limit_value': 1}}]}
    ),
    (
            {"name": ""},
            422,
            {'detail': [{'loc': ['body', 'name'], 'msg': 'ensure this value has at least 1 characters',
                         'type': 'value_error.any_str.min_length', 'ctx': {'limit_value': 1}}]}
    ),
    (
            {"email": "123"},
            422,
            {'detail': [{'loc': ['body', 'email'], 'msg': 'value is not a valid email address',
                         'type': 'value_error.email'}]}
    )
])
async def tess_update_user_validation_error(client, create_user_in_database, get_user_in_db, user_data_updated,
                                            expected_status_code, expected_detail):
    """
    Тестирует валидацию PATCH-запроса обновления пользователя.

    Проверяет, что при передаче некорректных данных сервер возвращает:
        - статус код 422 (Unprocessable Entity),
        - ожидаемый текст ошибки в `detail`.

    ⚠️ ВНИМАНИЕ: название теста содержит опечатку — `tess_update_user_validation_error`,
        должно быть `test_update_user_validation_error`.
            Args:
        client: Тестовый клиент FastAPI.
        create_user_in_database: Fixture для предварительного создания пользователя.
        get_user_in_db: Fixture для получения пользователя из БД.
        user_data_updated: Данные для обновления (включают ошибку).
        expected_status_code: Ожидаемый HTTP-статус.
        expected_detail: Ожидаемое сообщение об ошибке.

    Тестируемые случаи:
        - Пустое тело запроса → ошибка: "At least one parameter..."
        - Имя с цифрами → ошибка: "Name should contains only letters"
        - Пустой email → ошибка: "value is not a valid email address"
        - Пустой surname/name → ошибка: min_length=1
        - Некорректный email → ошибка: "value is not a valid email address"
    """
    user_data = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@ivanov.com",
        "is_active": True
    }
    await create_user_in_database(**user_data)
    resp = client.patch(f"/user/?user_id={user_data['user_id']}", data=json.dumps(user_data_updated))
    assert resp.status_code == expected_status_code
    resp_data = resp.json()
    assert resp_data == expected_detail