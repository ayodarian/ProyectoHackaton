from collections import deque

import numpy as np
from sklearn.linear_model import LinearRegression

from app.config import settings


class AnalizadorTendencias:
    def __init__(self, ventana: int | None = None):
        self.ventana = ventana or settings.ventana_analisis
        self._buffer: deque[dict] = deque(maxlen=self.ventana)

    def agregar_lectura(
        self, temperatura: float, vibracion_total: float
    ) -> None:
        self._buffer.append(
            {"temp": temperatura, "vib": vibracion_total}
        )

    def pendiente_temperatura(self) -> float | None:
        return self._calcular_pendiente("temp")

    def pendiente_vibracion(self) -> float | None:
        return self._calcular_pendiente("vib")

    def es_anomalia_predictiva(self) -> bool:
        if len(self._buffer) < 10:
            return False

        pend_temp = self.pendiente_temperatura()
        pend_vib = self.pendiente_vibracion()

        if pend_temp is None or pend_vib is None:
            return False

        return (
            pend_temp > 0.5
            or pend_vib > 0.05
            or (
                self._buffer[-1]["temp"]
                >= settings.temp_alerta_amarilla
            )
            or (
                self._buffer[-1]["vib"]
                >= settings.vibracion_alerta_amarilla
            )
        )

    def _calcular_pendiente(self, clave: str) -> float | None:
        if len(self._buffer) < 2:
            return None

        X = np.arange(len(self._buffer)).reshape(-1, 1)
        y = np.array([r[clave] for r in self._buffer])

        modelo = LinearRegression()
        modelo.fit(X, y)
        return float(modelo.coef_[0])


analizador = AnalizadorTendencias()
