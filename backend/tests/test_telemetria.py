import pytest
from httpx import AsyncClient


class TestTelemetria:
    @pytest.mark.asyncio
    async def test_enviar_telemetria(self, client: AsyncClient):
        payload = {
            "torno_id": 1,
            "temperatura": 65.0,
            "vibracion_x": 1.2,
            "vibracion_y": 1.0,
            "vibracion_z": 0.9,
        }
        response = await client.post("/api/telemetria", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["torno_id"] == 1
        assert data["temperatura"] == 65.0
        assert "id" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_enviar_telemetria_valores_extremos(self, client: AsyncClient):
        payload = {
            "torno_id": 1,
            "temperatura": 150.0,
            "vibracion_x": 20.0,
            "vibracion_y": 20.0,
            "vibracion_z": 20.0,
        }
        response = await client.post("/api/telemetria", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_enviar_telemetria_invalida(self, client: AsyncClient):
        payload = {
            "torno_id": 0,
            "temperatura": -1,
            "vibracion_x": 1.0,
            "vibracion_y": 1.0,
            "vibracion_z": 1.0,
        }
        response = await client.post("/api/telemetria", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_listar_telemetria(self, client: AsyncClient):
        for i in range(3):
            await client.post(
                "/api/telemetria",
                json={
                    "torno_id": 1,
                    "temperatura": 82.0 + i,
                    "vibracion_x": 2.6,
                    "vibracion_y": 2.5,
                    "vibracion_z": 2.4,
                },
            )

        response = await client.get("/api/telemetria")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_listar_telemetria_limite(self, client: AsyncClient):
        for i in range(5):
            await client.post(
                "/api/telemetria",
                json={
                    "torno_id": 1,
                    "temperatura": 85.0,
                    "vibracion_x": 2.6,
                    "vibracion_y": 2.5,
                    "vibracion_z": 2.4,
                },
            )

        response = await client.get("/api/telemetria?limite=3")
        data = response.json()
        assert len(data) <= 3
