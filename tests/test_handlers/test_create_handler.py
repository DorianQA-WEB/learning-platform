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
    resp = client.post("/user/", data=json.dumps(user_data))
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


async def test_create_user_duplicate_email_error(client, get_user_from_db):
    """
    Тестирует ошибку при попытке создать пользователя с уже существующим email.

    Проверяет:
        - статус код 503 (database error, уникальное ограничение),
        - сообщение об ошибке содержит "duplicate key value violates unique constraint".

    ⚠️ ОШИБКА В ПУТИ: использует `/user/`, тогда как в первой части теста — `/users/`.
       Если роутер зарегистрирован только под `/users/`, этот тест будет падать с 404.

    Args:
        client: Тестовый клиент FastAPI.
        get_user_from_db: Fixture для получения пользователя из БД.
    """
    user_data = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@ivanov.com"
    }
    user_data_same_email ={
        'name': 'Peter',
        'surname': 'Petrov',
        'email': 'ivan@ivanov.com'
    }
    response = client.post("/user/", data=json.dumps(user_data))
    data_from_response = response.json()
    assert response.status_code == 200
    assert data_from_response["name"] == user_data["name"]
    assert data_from_response["surname"] == user_data["surname"]
    assert data_from_response["email"] == user_data["email"]
    assert await data_from_response["is_active"] is True
    user_from_db = await get_user_from_db(data_from_response["user_id"])
    assert len(user_from_db) == 1
    user_from_db = dict(user_from_db[0])
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db['is_active'] is True
    assert str(user_from_db["user_id"]) == data_from_response["user_id"]
    response = client.post("/user/", data=json.dumps(user_data_same_email))
    assert response.status_code == 503
    assert 'duplicate key value violates unique constraint "users_email_key"' in response.json()['detail']

@pytest.mark.parametrize("user_data_for_creation, expected_status_code, expected_detail", [
    ({}, 422, {'detail': [{'loc': ['body', 'name'], 'msg': 'field required', 'type': 'value_error.missing'},
                          {'loc': ['body', 'surname'], 'msg': 'field required', 'type': 'value_error.missing'},
                          {'loc': ['body', 'email'], 'msg': 'field required', 'type': 'value_error.missing'}]}),
    ({'name': 123, "surname": 456, "email" : 'lol'}, 422, {'detail': 'Name should contains only letters'}),
    ({'name': 'Ivan', 'surname': 456, 'email': 'lol'}, 422, {'detail': 'Surname should contains only letters'}),
    ({'name': 'Ivan', 'surname': 'Ivanov', 'email': 'lol'},
     422, {'detail': [{'loc': ['body', 'email'],
                       'msg': 'value is not a valid email address', 'type': 'value_error.email'}]}),
])
async def test_create_user_validation_error(client, user_data_for_creation, expected_status_code, expected_detail):
    """
    Тестирует валидацию данных при создании пользователя.

    Проверяет:
        - статус код 422 при передаче некорректных данных,
        - правильные сообщения об ошибках для каждого поля.

    ⚠️ Использует путь `/user/`, что может не совпадать с роутом.

    Args:
        client: Тестовый клиент FastAPI.
        user_data_for_creation: Данные для создания (с ошибкой).
        expected_status_code: Ожидаемый HTTP-статус (422).
        expected_detail: Ожидаемое сообщение об ошибке.
    """
    response = client.post("/user/", data=json.dumps(user_data_for_creation))
    data_from_response = response.json()
    assert response.status_code == expected_status_code
    assert data_from_response == expected_detail