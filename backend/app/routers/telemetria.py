from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.telemetria import (
    AlertaMantenimiento,
    RegistroFallo,
    TelemetriaTorno,
)
from app.schemas.telemetria import TelemetriaRequest, TelemetriaResponse
from app.services.analisis import analizador
from app.services.ollama_client import generar_reporte_tecnico
from app.ws_manager import manager

router = APIRouter(prefix="/api", tags=["Telemetria"])

_ultimo_guardado: dict[int, float] = {}


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

    analizador.agregar_lectura(temp, vib_total)
    es_predictivo = analizador.es_anomalia_predictiva()

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

        if es_predictivo and not es_amarillo:
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

        return "PREDICTIVA_AMARILLA"

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

    alerta_activa = await _verificar_alertas(
        db, data.torno_id, data.temperatura, vib_total,
        data.vibracion_x, data.vibracion_y, data.vibracion_z,
    )

    paro = (
        data.temperatura >= settings.temp_emergencia_roja
        or vib_total >= settings.vibracion_emergencia_roja
    )

    await _broadcast_estado(
        db, data.torno_id, data.temperatura, vib_total, alerta_activa, paro
    )

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
