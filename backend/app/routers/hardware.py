from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.telemetria import AlertaMantenimiento, RegistroFallo
from app.schemas.telemetria import (
    ControlHardwareResponse,
    EstadoActualResponse,
)

from app.ws_manager import manager

router = APIRouter(prefix="/api", tags=["Hardware"])


def _vib_total(vx: float, vy: float, vz: float) -> float:
    return (vx**2 + vy**2 + vz**2) ** 0.5


async def _estado_para_torno(
    db: AsyncSession, torno_id: int
) -> EstadoActualResponse:
    cache = manager.get_ultimo_estado(torno_id)
    if cache:
        return EstadoActualResponse(
            torno_id=cache["torno_id"],
            temperatura=cache["temperatura"],
            vibracion_total=cache["vibracion_total"],
            alerta_activa=cache.get("alerta_activa"),
            paro_emergencia=cache["paro_emergencia"],
        )

    result = await db.execute(
        select(RegistroFallo)
        .where(RegistroFallo.torno_id == torno_id)
        .order_by(RegistroFallo.timestamp.desc())
        .limit(1)
    )
    ultimo = result.scalar_one_or_none()

    if not ultimo:
        return EstadoActualResponse(
            torno_id=torno_id,
            temperatura=0,
            vibracion_total=0,
            alerta_activa=None,
            paro_emergencia=False,
        )

    vib_total = _vib_total(
        ultimo.vibracion_x, ultimo.vibracion_y, ultimo.vibracion_z
    )

    alerta_result = await db.execute(
        select(AlertaMantenimiento)
        .where(
            AlertaMantenimiento.atendida == 0,
            AlertaMantenimiento.torno_id == ultimo.torno_id,
        )
        .order_by(AlertaMantenimiento.timestamp.desc())
        .limit(1)
    )
    alerta = alerta_result.scalar_one_or_none()

    paro = (
        ultimo.temperatura >= settings.temp_emergencia_roja
        or vib_total >= settings.vibracion_emergencia_roja
    )

    return EstadoActualResponse(
        torno_id=ultimo.torno_id,
        temperatura=ultimo.temperatura,
        vibracion_total=round(vib_total, 3),
        alerta_activa=alerta.tipo_alerta if alerta else None,
        paro_emergencia=paro,
    )


@router.get("/estado-actual", response_model=EstadoActualResponse)
async def estado_actual(
    torno_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if torno_id is not None:
        return await _estado_para_torno(db, torno_id)

    result = await db.execute(
        select(RegistroFallo)
        .order_by(RegistroFallo.timestamp.desc())
        .limit(1)
    )
    ultimo = result.scalar_one_or_none()

    if not ultimo:
        return EstadoActualResponse(
            torno_id=1,
            temperatura=0,
            vibracion_total=0,
            alerta_activa=None,
            paro_emergencia=False,
        )

    return await _estado_para_torno(db, ultimo.torno_id)


@router.get(
    "/estado-actual/todos", response_model=list[EstadoActualResponse]
)
async def estado_todos_tornos(db: AsyncSession = Depends(get_db)):
    resultados = []
    ids_vistos: set[int] = set()
    for estado_dict in manager.get_todos_estados():
        tid = estado_dict["torno_id"]
        ids_vistos.add(tid)
        resultados.append(EstadoActualResponse(
            torno_id=tid,
            temperatura=estado_dict["temperatura"],
            vibracion_total=estado_dict["vibracion_total"],
            alerta_activa=estado_dict.get("alerta_activa"),
            paro_emergencia=estado_dict["paro_emergencia"],
        ))

    try:
        ids_result = await db.execute(
            select(RegistroFallo.torno_id)
            .distinct()
            .order_by(RegistroFallo.torno_id)
        )
        for row in ids_result.all():
            tid = row[0]
            if tid not in ids_vistos:
                estado = await _estado_para_torno(db, tid)
                resultados.append(estado)
    except Exception:
        pass

    resultados.sort(key=lambda r: r.torno_id)
    return resultados


@router.get("/control-hardware", response_model=ControlHardwareResponse)
async def control_hardware(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RegistroFallo)
        .order_by(RegistroFallo.timestamp.desc())
        .limit(1)
    )
    ultimo = result.scalar_one_or_none()

    if not ultimo:
        return ControlHardwareResponse(paro_emergencia=False)

    vib_total = _vib_total(
        ultimo.vibracion_x, ultimo.vibracion_y, ultimo.vibracion_z
    )

    paro = (
        ultimo.temperatura >= settings.temp_emergencia_roja
        or vib_total >= settings.vibracion_emergencia_roja
    )

    return ControlHardwareResponse(paro_emergencia=paro)
