import json
from uuid import uuid4

import pytest


async def test_create_user(client, get_user_from_database):
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