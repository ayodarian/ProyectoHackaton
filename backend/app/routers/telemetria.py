from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.telemetria import (
    AlertaMantenimiento,
    PrediccionFallo,
    RegistroFallo,
    TelemetriaTorno,
)
from app.schemas.telemetria import TelemetriaRequest, TelemetriaResponse
from app.services.analisis import analizador
from app.services.ollama_client import (
    ajustar_probabilidad_ollama,
    clasificar_fallo_ollama,
    generar_reporte_tecnico,
)
from app.ws_manager import manager

router = APIRouter(prefix="/api", tags=["Telemetria"])

_ultimo_guardado: dict[int, float] = {}
_ultima_alerta: dict[int, dict[str, float]] = {}
_ultimo_telemetria: dict[int, float] = {}
_ultima_consulta_ia: dict[int, float] = {}


def _puede_crear_alerta(torno_id: int, tipo: str) -> bool:
    ahora = datetime.now().timestamp()
    por_torno = _ultima_alerta.get(torno_id, {})
    ultima = por_torno.get(tipo, 0)
    if ahora - ultima < settings.intervalo_guardado_amarillo:
        return False
    por_torno[tipo] = ahora
    _ultima_alerta[torno_id] = por_torno
    return True


def _calcular_vib_total(vx: float, vy: float, vz: float) -> float:
    return (vx**2 + vy**2 + vz**2) ** 0.5


def _puede_guardar(torno_id: int) -> bool:
    ahora = datetime.now().timestamp()
    ultimo = _ultimo_guardado.get(torno_id, 0)
    if ahora - ultimo >= settings.intervalo_guardado_amarillo:
        _ultimo_guardado[torno_id] = ahora
        return True
    return False


async def _broadcast_estado(
    db: AsyncSession, torno_id: int, temp: float, vib_total: float, alerta_activa: str | None, paro: bool
) -> None:
    await manager.broadcast_estado(
        torno_id,
        {
            "torno_id": torno_id,
            "temperatura": temp,
            "vibracion_total": round(vib_total, 3),
            "alerta_activa": alerta_activa,
            "paro_emergencia": paro,
        },
    )


async def _verificar_alertas(
    db: AsyncSession,
    torno_id: int,
    temp: float,
    vib_total: float,
    vx: float,
    vy: float,
    vz: float,
    tiempo_inactividad: float = 0.0,
) -> str | None:
    es_rojo = (
        temp >= settings.temp_emergencia_roja
        or vib_total >= settings.vibracion_emergencia_roja
    )
    es_amarillo = (
        temp >= settings.temp_alerta_amarilla
        or vib_total >= settings.vibracion_alerta_amarilla
    )

    if es_rojo:
        if _puede_guardar(torno_id):
            db.add(
                RegistroFallo(
                    torno_id=torno_id,
                    temperatura=temp,
                    vibracion_x=vx,
                    vibracion_y=vy,
                    vibracion_z=vz,
                    tipo_alerta="EMERGENCIA_ROJA",
                )
            )
            await db.commit()

        if _puede_crear_alerta(torno_id, "EMERGENCIA_ROJA"):
            alerta = AlertaMantenimiento(
                torno_id=torno_id,
                tipo_alerta="EMERGENCIA_ROJA",
                descripcion=(
                    f"PARO DE EMERGENCIA - Temperatura: {temp:.1f}°C, "
                    f"Vibración: {vib_total:.2f}G"
                ),
            )
            db.add(alerta)
            await db.commit()
            await db.refresh(alerta)
            await manager.broadcast_alerta(
                torno_id, _alerta_to_dict(alerta)
            )
        _ultimo_guardado[torno_id] = datetime.now().timestamp()
        return "EMERGENCIA_ROJA"

    resultado = analizador.analizar(temp, vib_total, tiempo_inactividad)
    es_predictivo = resultado.probabilidad >= 0.5

    if es_amarillo or es_predictivo:
        if _puede_guardar(torno_id):
            db.add(
                RegistroFallo(
                    torno_id=torno_id,
                    temperatura=temp,
                    vibracion_x=vx,
                    vibracion_y=vy,
                    vibracion_z=vz,
                    tipo_alerta="PREDICTIVA_AMARILLA",
                )
            )
            await db.commit()

        if es_amarillo and _puede_crear_alerta(torno_id, "ALERTA_AMARILLA"):
            alerta = AlertaMantenimiento(
                torno_id=torno_id,
                tipo_alerta="ALERTA_AMARILLA",
                descripcion=(
                    f"Alerta Amarilla - Temperatura: {temp:.1f}°C, "
                    f"Vibración: {vib_total:.2f}G"
                ),
            )
            db.add(alerta)
            await db.commit()
            await db.refresh(alerta)
            await manager.broadcast_alerta(
                torno_id, _alerta_to_dict(alerta)
            )

        if es_predictivo and not es_amarillo and _puede_crear_alerta(torno_id, "PREDICTIVA_AMARILLA"):
            pend_vib = analizador.pendiente_vibracion() or 0
            incremento = pend_vib * 50 * 100
            reporte = await generar_reporte_tecnico(
                torno_id=torno_id,
                incremento_vibracion=min(incremento, 100),
                temperatura=temp,
            )
            alerta = AlertaMantenimiento(
                torno_id=torno_id,
                tipo_alerta="PREDICTIVA_AMARILLA",
                descripcion=reporte,
            )
            db.add(alerta)
            await db.commit()
            await db.refresh(alerta)
            await manager.broadcast_alerta(
                torno_id, _alerta_to_dict(alerta)
            )

        return "PREDICTIVA_AMARILLA" if es_predictivo else "ALERTA_AMARILLA"

    return None


def _alerta_to_dict(a: AlertaMantenimiento) -> dict:
    return {
        "id": a.id,
        "torno_id": a.torno_id,
        "tipo_alerta": a.tipo_alerta,
        "descripcion": a.descripcion,
        "atendida": a.atendida,
        "timestamp": a.timestamp.isoformat() if a.timestamp else None,
    }


@router.post("/telemetria", response_model=TelemetriaResponse, status_code=201)
async def recibir_telemetria(
    data: TelemetriaRequest, db: AsyncSession = Depends(get_db)
):
    vib_total = _calcular_vib_total(
        data.vibracion_x, data.vibracion_y, data.vibracion_z
    )

    ahora = datetime.now().timestamp()
    ultimo = _ultimo_telemetria.get(data.torno_id, 0)
    tiempo_inactividad = ahora - ultimo
    if tiempo_inactividad > settings.intervalo_guardado_amarillo:
        analizador.reset()
    _ultimo_telemetria[data.torno_id] = ahora

    alerta_activa = await _verificar_alertas(
        db, data.torno_id, data.temperatura, vib_total,
        data.vibracion_x, data.vibracion_y, data.vibracion_z,
        tiempo_inactividad,
    )

    paro = (
        data.temperatura >= settings.temp_emergencia_roja
        or vib_total >= settings.vibracion_emergencia_roja
    )

    await _broadcast_estado(
        db, data.torno_id, data.temperatura, vib_total, alerta_activa, paro
    )

    resultado = analizador._ultimo_resultado

    if paro:
        prob_final = 1.0
        severidad = "CRITICA"
        modo_fallo = "PARO_EMERGENCIA"
    else:
        prob_matematica = resultado.probabilidad
        prob_final = prob_matematica
        if prob_matematica > 0:
            ahora_ia = datetime.now().timestamp()
            ultima_ia = _ultima_consulta_ia.get(data.torno_id, 0)
            if ahora_ia - ultima_ia >= settings.intervalo_ajuste_ia:
                _ultima_consulta_ia[data.torno_id] = ahora_ia
                probabilidad_ia = await ajustar_probabilidad_ollama(
                    data.torno_id, data.temperatura, vib_total,
                    resultado.pendiente_temperatura,
                    resultado.pendiente_vibracion,
                    resultado.correlacion,
                    prob_matematica,
                )
                prob_final = round(prob_matematica * 0.7 + probabilidad_ia * 0.3, 4)

    if prob_final > 0:
        pred_dict = {
            "probabilidad": prob_final,
            "severidad": "CRITICA" if paro else resultado.severidad,
            "modo_fallo": "PARO_EMERGENCIA" if paro else resultado.modo_fallo,
            "rul_estimado": resultado.rul_estimado,
            "pendiente_temperatura": resultado.pendiente_temperatura,
            "pendiente_vibracion": resultado.pendiente_vibracion,
            "aceleracion_temperatura": resultado.aceleracion_temperatura,
            "aceleracion_vibracion": resultado.aceleracion_vibracion,
            "correlacion": resultado.correlacion,
            "inactividad": resultado.inactividad,
        }
        await manager.broadcast_prediccion(data.torno_id, pred_dict)

        if prob_final >= 0.3:
            db.add(PrediccionFallo(
                torno_id=data.torno_id,
                probabilidad=prob_final,
                severidad=resultado.severidad,
                modo_fallo=resultado.modo_fallo,
                rul_estimado=resultado.rul_estimado,
                pendiente_temperatura=resultado.pendiente_temperatura,
                pendiente_vibracion=resultado.pendiente_vibracion,
                correlacion=resultado.correlacion,
                inactividad=resultado.inactividad,
            ))
            await db.commit()

    return TelemetriaResponse(
        id=0,
        torno_id=data.torno_id,
        temperatura=data.temperatura,
        vibracion_x=data.vibracion_x,
        vibracion_y=data.vibracion_y,
        vibracion_z=data.vibracion_z,
        timestamp=datetime.now(),
    )


@router.get("/telemetria", response_model=list[TelemetriaResponse])
async def listar_telemetria(
    torno_id: int | None = None,
    limite: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(RegistroFallo).order_by(
        RegistroFallo.timestamp.desc()
    )
    if torno_id:
        query = query.where(RegistroFallo.torno_id == torno_id)
    result = await db.execute(query.limit(limite))
    return [
        TelemetriaResponse(
            id=r.id,
            torno_id=r.torno_id,
            temperatura=r.temperatura,
            vibracion_x=r.vibracion_x,
            vibracion_y=r.vibracion_y,
            vibracion_z=r.vibracion_z,
            timestamp=r.timestamp,
        )
        for r in result.scalars().all()
    ]
