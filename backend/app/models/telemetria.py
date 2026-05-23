from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelemetriaTorno(Base):
    __tablename__ = "telemetria_torno"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    torno_id: Mapped[int] = mapped_column(Integer, nullable=False)
    temperatura: Mapped[float] = mapped_column(Float, nullable=False)
    vibracion_x: Mapped[float] = mapped_column(Float, nullable=False)
    vibracion_y: Mapped[float] = mapped_column(Float, nullable=False)
    vibracion_z: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime('now', 'localtime')
    )


class RegistroFallo(Base):
    __tablename__ = "registros_fallo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    torno_id: Mapped[int] = mapped_column(Integer, nullable=False)
    temperatura: Mapped[float] = mapped_column(Float, nullable=False)
    vibracion_x: Mapped[float] = mapped_column(Float, nullable=False)
    vibracion_y: Mapped[float] = mapped_column(Float, nullable=False)
    vibracion_z: Mapped[float] = mapped_column(Float, nullable=False)
    tipo_alerta: Mapped[str] = mapped_column(
        String(20), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime('now', 'localtime')
    )


class AlertaMantenimiento(Base):
    __tablename__ = "alertas_mantenimiento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    torno_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo_alerta: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=True)
    atendida: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime('now', 'localtime')
    )


class PrediccionFallo(Base):
    __tablename__ = "predicciones_fallo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    torno_id: Mapped[int] = mapped_column(Integer, nullable=False)
    probabilidad: Mapped[float] = mapped_column(Float, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False)
    modo_fallo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rul_estimado: Mapped[float | None] = mapped_column(Float, nullable=True)
    pendiente_temperatura: Mapped[float | None] = mapped_column(Float, nullable=True)
    pendiente_vibracion: Mapped[float | None] = mapped_column(Float, nullable=True)
    correlacion: Mapped[float | None] = mapped_column(Float, nullable=True)
    inactividad: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime('now', 'localtime')
    )
