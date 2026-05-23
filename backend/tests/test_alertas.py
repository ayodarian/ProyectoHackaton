import pytest
from httpx import AsyncClient


class TestAlertas:
    @pytest.mark.asyncio
    async def test_listar_alertas_vacio(self, client: AsyncClient):
        response = await client.get("/api/alertas")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_generar_alerta_predictiva(self, client: AsyncClient):
        for i in range(15):
            await client.post(
                "/api/telemetria",
                json={
                    "torno_id": 1,
                    "temperatura": 60.0 + i * 2,
                    "vibracion_x": 1.0,
                    "vibracion_y": 1.0,
                    "vibracion_z": 1.0,
                },
            )

        response = await client.get("/api/alertas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_generar_emergencia_roja(self, client: AsyncClient):
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

        response = await client.get("/api/alertas?no_atendidas=true")
        data = response.json()
        emergencias = [
            a for a in data if a["tipo_alerta"] == "EMERGENCIA_ROJA"
        ]
        assert len(emergencias) >= 1

    @pytest.mark.asyncio
    async def test_atender_alerta(self, client: AsyncClient):
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

        alertas_resp = await client.get("/api/alertas?no_atendidas=true")
        alerta_id = alertas_resp.json()[0]["id"]

        response = await client.post(
            "/api/alertas/atender", json={"alerta_id": alerta_id}
        )
        assert response.status_code == 200
        assert response.json()["atendida"] == 1

    @pytest.mark.asyncio
    async def test_atender_alerta_inexistente(self, client: AsyncClient):
        response = await client.post(
            "/api/alertas/atender", json={"alerta_id": 9999}
        )
        assert response.status_code == 404
