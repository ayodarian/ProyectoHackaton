from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.telemetria import PrediccionFallo
from app.schemas.telemetria import PrediccionActualResponse, PrediccionResponse
from app.services.analisis import analizador
from app.ws_manager import manager

router = APIRouter(prefix="/api/predicciones", tags=["Predicciones"])


@router.get("/actual", response_model=PrediccionActualResponse)
async def prediccion_actual():
    resultado = analizador._ultimo_resultado
    estado = manager.get_ultimo_estado(1)
    return PrediccionActualResponse(
        torno_id=1,
        prediccion=PrediccionResponse(
            probabilidad=resultado.probabilidad,
            severidad=resultado.severidad,
            modo_fallo=resultado.modo_fallo,
            rul_estimado=resultado.rul_estimado,
            pendiente_temperatura=resultado.pendiente_temperatura,
            pendiente_vibracion=resultado.pendiente_vibracion,
            aceleracion_temperatura=resultado.aceleracion_temperatura,
            aceleracion_vibracion=resultado.aceleracion_vibracion,
            correlacion=resultado.correlacion,
        ),
        estado_actual=estado,
    )


@router.get("", response_model=list[PrediccionResponse])
async def listar_predicciones(
    limite: int = 50,
    severidad: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PrediccionFallo).order_by(desc(PrediccionFallo.timestamp))
    if severidad:
        query = query.where(PrediccionFallo.severidad == severidad)
    result = await db.execute(query.limit(limite))
    rows = result.scalars().all()
    return [
        PrediccionResponse(
            probabilidad=r.probabilidad,
            severidad=r.severidad,
            modo_fallo=r.modo_fallo,
            rul_estimado=r.rul_estimado,
            pendiente_temperatura=r.pendiente_temperatura,
            pendiente_vibracion=r.pendiente_vibracion,
            correlacion=r.correlacion,
            timestamp=r.timestamp,
        )
        for r in rows
    ]
