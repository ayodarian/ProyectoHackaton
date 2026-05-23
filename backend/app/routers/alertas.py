import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.telemetria import AlertaMantenimiento
from app.schemas.telemetria import AlertaResponse, AtenderAlertaRequest
from app.ws_manager import manager

router = APIRouter(prefix="/api", tags=["Alertas"])


@router.get("/alertas", response_model=list[AlertaResponse])
async def listar_alertas(
    no_atendidas: bool = False, db: AsyncSession = Depends(get_db)
):
    query = select(AlertaMantenimiento).order_by(
        AlertaMantenimiento.timestamp.desc()
    )
    if no_atendidas:
        query = query.where(AlertaMantenimiento.atendida == 0)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/alertas/atender", response_model=AlertaResponse)
async def atender_alerta(
    data: AtenderAlertaRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AlertaMantenimiento).where(
            AlertaMantenimiento.id == data.alerta_id
        )
    )
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    await db.execute(
        update(AlertaMantenimiento)
        .where(AlertaMantenimiento.id == data.alerta_id)
        .values(atendida=1)
    )
    await db.commit()
    await db.refresh(alerta)

    await manager.broadcast_alerta(
        alerta.torno_id,
        {
            "id": alerta.id,
            "torno_id": alerta.torno_id,
            "tipo_alerta": alerta.tipo_alerta,
            "descripcion": alerta.descripcion,
            "atendida": 1,
            "timestamp": (
                alerta.timestamp.isoformat()
                if alerta.timestamp
                else None
            ),
        },
    )

    return alerta


@router.get("/alertas/exportar-csv")
async def exportar_alertas_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AlertaMantenimiento).order_by(AlertaMantenimiento.timestamp.desc())
    )
    alertas = result.scalars().all()

    f = StringIO()
    writer = csv.writer(f)
    writer.writerow(["id", "torno_id", "tipo_alerta", "descripcion", "atendida", "timestamp"])

    for a in alertas:
        writer.writerow([
            a.id,
            a.torno_id,
            a.tipo_alerta,
            a.descripcion or "",
            "Sí" if a.atendida else "No",
            a.timestamp.isoformat() if a.timestamp else "",
        ])

    f.seek(0)
    return StreamingResponse(
        iter([f.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alertas_mantenimiento.csv"},
    )
