import pytest
from httpx import AsyncClient


class TestHardware:
    @pytest.mark.asyncio
    async def test_estado_actual_sin_datos(self, client: AsyncClient):
        response = await client.get("/api/estado-actual")
        assert response.status_code == 200
        data = response.json()
        assert data["temperatura"] == 0
        assert data["paro_emergencia"] is False

    @pytest.mark.asyncio
    async def test_estado_actual_con_datos(self, client: AsyncClient):
        await client.post(
            "/api/telemetria",
            json={
                "torno_id": 1,
                "temperatura": 85.0,
                "vibracion_x": 1.5,
                "vibracion_y": 1.2,
                "vibracion_z": 1.1,
            },
        )

        response = await client.get("/api/estado-actual")
        assert response.status_code == 200
        data = response.json()
        assert data["temperatura"] == 85.0
        assert data["vibracion_total"] > 0

    @pytest.mark.asyncio
    async def test_control_hardware_normal(self, client: AsyncClient):
        await client.post(
            "/api/telemetria",
            json={
                "torno_id": 1,
                "temperatura": 36.0,
                "vibracion_x": 1.0,
                "vibracion_y": 1.0,
                "vibracion_z": 1.0,
            },
        )

        response = await client.get("/api/control-hardware")
        assert response.status_code == 200
        assert response.json()["paro_emergencia"] is False

    @pytest.mark.asyncio
    async def test_control_hardware_emergencia(self, client: AsyncClient):
        await client.post(
            "/api/telemetria",
            json={
                "torno_id": 1,
                "temperatura": 95.0,
                "vibracion_x": 1.0,
                "vibracion_y": 1.0,
                "vibracion_z": 1.0,
            },
        )

        response = await client.get("/api/control-hardware")
        assert response.status_code == 200
        assert response.json()["paro_emergencia"] is True
