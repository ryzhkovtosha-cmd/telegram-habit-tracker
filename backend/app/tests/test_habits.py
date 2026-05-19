import pytest
from datetime import date

@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/auth/register", json={"telegram_id": 111})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_create_habit(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = await client.post("/habits/", json={"name": "Чтение"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Чтение"
    assert data["completion_count"] == 0

@pytest.mark.asyncio
async def test_list_habits(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Создаём одну привычку
    await client.post("/habits/", json={"name": "Спорт"}, headers=headers)
    resp = await client.get("/habits/", headers=headers)
    assert resp.status_code == 200
    habits = resp.json()
    assert len(habits) == 1

@pytest.mark.asyncio
async def test_daily_habits(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Создаём привычку
    await client.post("/habits/", json={"name": "Медитация"}, headers=headers)
    target = date.today().isoformat()
    resp = await client.get("/habits/daily", params={"target_date": target}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["completed"] == False

@pytest.mark.asyncio
async def test_complete_habit(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    create_resp = await client.post("/habits/", json={"name": "Бег"}, headers=headers)
    habit_id = create_resp.json()["id"]
    today = date.today().isoformat()
    resp = await client.post(f"/habits/daily/{habit_id}/complete",
                             json={"date": today}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed"] == True
    # Проверяем, что счётчик увеличился
    get_resp = await client.get("/habits/", headers=headers)
    habits = get_resp.json()
    assert habits[0]["completion_count"] == 1