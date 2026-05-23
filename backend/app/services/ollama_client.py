import httpx

from app.config import settings


async def generar_reporte_tecnico(
    torno_id: int,
    incremento_vibracion: float,
    temperatura: float,
    periodo_minutos: int = 15,
) -> str:
    prompt = (
        f"Actúa como un ingeniero de mantenimiento industrial experto en CNC. "
        f"El torno ID {torno_id} muestra un incremento del "
        f"{incremento_vibracion:.0f}% en la vibración del husillo y la temperatura "
        f"subió a {temperatura:.0f}°C en los últimos {periodo_minutos} minutos. "
        f"Genera un reporte técnico de una oración explicando el posible fallo "
        f"físico y la acción inmediata recomendada para el supervisor."
    )

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No se pudo generar el reporte.")
        except Exception:
            return (
                f"⚠ ALERTA PREDICTIVA: Torno {torno_id} - "
                f"Incremento de vibración ({incremento_vibracion:.0f}%) "
                f"y temperatura ({temperatura:.0f}°C). "
                f"Se recomienda inspección inmediata del herramental."
            )
