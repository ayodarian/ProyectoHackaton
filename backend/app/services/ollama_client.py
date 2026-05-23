import json
import time

import httpx

from app.config import settings

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 60


async def clasificar_fallo_ollama(
    torno_id: int,
    temperatura: float,
    vibracion_total: float,
    pendiente_temp: float | None,
    pendiente_vib: float | None,
    correlacion: float | None,
    probabilidad: float,
) -> dict:
    cache_key = f"{torno_id}"
    ahora = time.time()
    if cache_key in _cache:
        ts, val = _cache[cache_key]
        if ahora - ts < _CACHE_TTL:
            return json.loads(val)

    prompt = (
        f"Eres un ingeniero de mantenimiento industrial experto en tornos CNC. "
        f"Analiza estos datos del Torno ID {torno_id}:\n\n"
        f"Temperatura actual: {temperatura:.1f}°C\n"
        f"Vibración actual: {vibracion_total:.2f}G\n"
        f"Tendencia temperatura: {pendiente_temp or 0:.4f} °C/lectura\n"
        f"Tendencia vibración: {pendiente_vib or 0:.4f} G/lectura\n"
        f"Correlación temp-vib: {correlacion or 0:.2f}\n"
        f"Probabilidad estadística de fallo: {probabilidad:.2f}\n\n"
        f"Clasifica el estado del herramental:\n"
        f"- NORMAL: sin signos de desgaste\n"
        f"- DESGASTE_INICIAL: incremento leve en vibración o temperatura\n"
        f"- DESGASTE_PROGRESIVO: tendencia sostenida al alza en ambas variables\n"
        f"- FALLO_INMINENTE: correlación alta + aceleración positiva\n\n"
        f"Responde SOLO con JSON: "
        f'{{"clasificacion":"...","probabilidad_ia":0.0,"recomendacion":"..."}}'
    )

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            data = response.json()
            texto = data.get("response", "")
            inicio = texto.find("{")
            fin = texto.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                parsed = json.loads(texto[inicio:fin])
                _cache[cache_key] = (ahora, json.dumps(parsed))
                return parsed
        except Exception:
            pass

    fallback = {
        "clasificacion": "DESGASTE_PROGRESIVO" if probabilidad > 0.6 else "DESGASTE_INICIAL",
        "probabilidad_ia": round(probabilidad, 2),
        "recomendacion": (
            f"⚠ Torno {torno_id}: probabilidad de fallo {probabilidad:.0%}. "
            f"Inspeccionar herramental. Temp: {temperatura:.1f}°C, Vib: {vibracion_total:.2f}G."
        ),
    }
    return fallback


async def ajustar_probabilidad_ollama(
    torno_id: int,
    temperatura: float,
    vibracion_total: float,
    pendiente_temp: float | None,
    pendiente_vib: float | None,
    correlacion: float | None,
    prob_matematica: float,
) -> float:
    prompt = (
        f"Eres un afinador de probabilidades de fallo para un torno CNC. "
        f"Analiza si la probabilidad matemática subestima o sobreestima el riesgo real "
        f"considerando correlaciones sutiles y patrones que un modelo lineal no captura.\n\n"
        f"Torno #{torno_id}\n"
        f"Temperatura: {temperatura:.1f}°C\n"
        f"Vibración: {vibracion_total:.2f}G\n"
        f"Tendencia temperatura: {pendiente_temp or 0:.4f} °C/lectura\n"
        f"Tendencia vibración: {pendiente_vib or 0:.4f} G/lectura\n"
        f"Correlación temp-vib: {correlacion or 0:.2f}\n"
        f"Probabilidad matemática: {prob_matematica:.2f}\n\n"
        f"Responde SOLO con JSON: "
        f'{{"probabilidad_ia": 0.X, "justificacion": "una oración"}}'
    )

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            data = response.json()
            texto = data.get("response", "")
            inicio = texto.find("{")
            fin = texto.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                parsed = json.loads(texto[inicio:fin])
                ia = float(parsed.get("probabilidad_ia", prob_matematica))
                return max(0.0, min(1.0, ia))
        except Exception:
            pass

    return prob_matematica


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
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
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
