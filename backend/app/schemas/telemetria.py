from datetime import datetime

from pydantic import BaseModel, Field


class TelemetriaRequest(BaseModel):
    torno_id: int = Field(..., ge=1)
    temperatura: float = Field(..., ge=0, le=150)
    vibracion_x: float = Field(..., ge=0, le=20)
    vibracion_y: float = Field(..., ge=0, le=20)
    vibracion_z: float = Field(..., ge=0, le=20)


class TelemetriaResponse(TelemetriaRequest):
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class RegistroFalloResponse(BaseModel):
    id: int
    torno_id: int
    temperatura: float
    vibracion_x: float
    vibracion_y: float
    vibracion_z: float
    tipo_alerta: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class AlertaResponse(BaseModel):
    id: int
    torno_id: int
    tipo_alerta: str
    descripcion: str | None
    atendida: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class AtenderAlertaRequest(BaseModel):
    alerta_id: int


class EstadoActualResponse(BaseModel):
    torno_id: int
    temperatura: float
    vibracion_total: float
    alerta_activa: str | None
    paro_emergencia: bool


class PrediccionResponse(BaseModel):
    probabilidad: float
    severidad: str
    modo_fallo: str | None = None
    rul_estimado: float | None = None
    pendiente_temperatura: float | None = None
    pendiente_vibracion: float | None = None
    aceleracion_temperatura: float | None = None
    aceleracion_vibracion: float | None = None
    correlacion: float | None = None
    inactividad: float | None = None
    timestamp: datetime | None = None

    model_config = {"from_attributes": True}


class PrediccionActualResponse(BaseModel):
    torno_id: int
    prediccion: PrediccionResponse | None = None
    estado_actual: EstadoActualResponse | None = None


class ControlHardwareResponse(BaseModel):
    paro_emergencia: bool
