import json
from uuid import uuid4

import pytest



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

async def test_update_user_check_one_is_updated(client, create_user_in_database, get_user_from_db):
    user_data_1 = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@ivanov.com",
        "is_active": True
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Vasiliy",
        "surname": "Vasilyev",
        "email": "vas@vas.com",
        "is_active": True
    }
    user_data_3 = {
        "user_id": uuid4(),
        "name": "Dima",
        "surname": "Dimaev",
        "email": "dim@dim.com",
        "is_active": True
    }
    user_data_updated = {
        'name': 'Petr',
        'surname': 'Petrov',
        'email': 'petr@petrov.com'
    }
    for user_data in [user_data_1, user_data_2, user_data_3]:
        await create_user_in_database(**user_data)
    resp = client.patch(f"/user/?user_id={user_data_1['user_id']}", data=json.dumps(user_data_updated))
    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data["updated_user_id"] == str(user_data_1['user_id'])
    users_from_db = await get_user_from_db(user_data_1["user_id"])
    user_from_db = dict(users_from_db[0])
    assert user_from_db['name'] == user_data_updated['name']
    assert user_from_db['surname'] == user_data_updated['surname']
    assert user_from_db['email'] == user_data_updated['email']
    assert user_from_db['is_active'] == user_data_1['is_active']
    assert user_from_db['user_id'] == user_data_1['user_id']

    # check that other users are not updated
    users_from_db = await get_user_from_db(user_data_2["user_id"])
    user_from_db = dict(users_from_db[0])
    assert user_from_db['name'] == user_data_2['name']
    assert user_from_db['surname'] == user_data_2['surname']
    assert user_from_db['email'] == user_data_2['email']
    assert user_from_db['is_active'] == user_data_2['is_active']
    assert user_from_db['user_id'] == user_data_2['user_id']

    users_from_db = await get_user_from_db(user_data_3["user_id"])
    user_from_db = dict(users_from_db[0])
    assert user_from_db['name'] == user_data_3['name']
    assert user_from_db['surname'] == user_data_3['surname']
    assert user_from_db['email'] == user_data_3['email']
    assert user_from_db['is_active'] == user_data_3['is_active']
    assert user_from_db['user_id'] == user_data_3['user_id']


async def test_update_user_id_validation_error(client, create_user_in_database, get_user_from_db):
    user_data_updated = {
        'name': 'Petr',
        'surname': 'Petrov',
        'email': 'petr@petrov.com'
    }
    response = client.patch(f"/user/?user_id=123", data=json.dumps(user_data_updated))
    assert response.status_code == 422
    data_from_response = response.json()
    assert data_from_response == {'detail': [{'loc': ['query', 'user_id'], 'msg': 'value is not a valid uuid',
                                              'type': 'type_error.uuid'}]}

async def test_update_user_not_found(client, create_user_in_database, get_user_from_db):
    user_data_updated = {
        'name': 'Petr',
        'surname': 'Petrov',
        'email': 'petr@petrov.com'
    }
    user_id = uuid4()
    response = client.patch(f"/user/?user_id={user_id}", data=json.dumps(user_data_updated))
    assert response.status_code == 404
    data_from_response = response.json()
    assert data_from_response == {'detail': f"User with id {user_id} not found"}

async def test_update_user_duplicate_email_error(client, create_user_in_database, get_user_from_db):
    user_data_1 = {
        "user_id": uuid4(),
        "name": "Vasiliy",
        "surname": "Vasilyev",
        "email": "vas@vas.com",
        "is_active": True
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Dima",
        "surname": "Dimaev",
        "email": "dim@dim.com",
        "is_active": True
    }
    user_data_updated = {
        'email': user_data_2['email']
    }
    for user_data in [user_data_1, user_data_2]:
        await create_user_in_database(**user_data)
    resp = client.patch(f"/user/?user_id={user_data_1['user_id']}", data=json.dumps(user_data_updated))
    assert resp.status_code == 503
    assert 'duplicate key value violates unique constraint "users_email_key"' in resp.json()['detail']
