from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.telemetria import RegistroFallo
from app.schemas.telemetria import RegistroFalloResponse

router = APIRouter(prefix="/api", tags=["Registros"])


@router.get(
    "/registros-fallo", response_model=list[RegistroFalloResponse]
)
async def listar_registros(
    torno_id: int | None = Query(None, description="Filtrar por torno"),
    estado: str | None = Query(
        None, description="PREDICTIVA_AMARILLA, EMERGENCIA_ROJA, NORMAL"
    ),
    desde: datetime | None = Query(None, description="ISO datetime"),
    hasta: datetime | None = Query(None, description="ISO datetime"),
    limite: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(RegistroFallo).order_by(
        RegistroFallo.timestamp.desc()
    )

    if torno_id is not None:
        query = query.where(RegistroFallo.torno_id == torno_id)
    if estado:
        if estado == "NORMAL":
            query = query.where(RegistroFallo.tipo_alerta.is_(None))
        else:
            query = query.where(RegistroFallo.tipo_alerta == estado)
    if desde:
        query = query.where(RegistroFallo.timestamp >= desde)
    if hasta:
        query = query.where(RegistroFallo.timestamp <= hasta)

    try:
        result = await db.execute(query.limit(limite))
        return result.scalars().all()
    except Exception:
        return []


@router.get(
    "/registros-fallo/ultimos",
    response_model=list[RegistroFalloResponse],
)
async def ultimos_registros(
    minutos: int = Query(60, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
):
    desde = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    query = (
        select(RegistroFallo)
        .where(RegistroFallo.timestamp >= desde)
        .order_by(RegistroFallo.timestamp.desc())
        .limit(100)
    )
    try:
        result = await db.execute(query)
        return result.scalars().all()
    except Exception:
        return []


@router.get(
    "/registros-fallo/tornos-activos",
    response_model=list[dict],
)
async def tornos_activos(db: AsyncSession = Depends(get_db)):
    desde = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    query = (
        select(RegistroFallo.torno_id, RegistroFallo.tipo_alerta)
        .where(RegistroFallo.timestamp >= desde)
        .distinct()
        .order_by(RegistroFallo.torno_id)
    )
    try:
        result = await db.execute(query)
        rows = result.all()
        tornos: dict[int, str] = {}
        for r in rows:
            if r.torno_id not in tornos:
                tornos[r.torno_id] = r.tipo_alerta or "NORMAL"
        return [
            {"torno_id": tid, "estado": est}
            for tid, est in tornos.items()
        ]
    except Exception:
        return []
