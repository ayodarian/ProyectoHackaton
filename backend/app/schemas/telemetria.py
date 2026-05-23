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


class ControlHardwareResponse(BaseModel):
    paro_emergencia: bool
