import json

async def test_create_user(client, get_user_from_database):
    user_data = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@ivanov.com"
    }
    resp = client.post("users/", data=json.dumps(user_data))
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