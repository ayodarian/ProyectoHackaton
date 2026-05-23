from collections import deque
from dataclasses import dataclass, field
import math

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from app.config import settings


@dataclass
class AnalisisResult:
    probabilidad: float = 0.0
    severidad: str = "NORMAL"
    modo_fallo: str | None = None
    rul_estimado: float | None = None
    pendiente_temperatura: float | None = None
    pendiente_vibracion: float | None = None
    aceleracion_temperatura: float | None = None
    aceleracion_vibracion: float | None = None
    correlacion: float | None = None
    inactividad: float = 0.0


class PredictiveEngine:
    def __init__(self, ventana: int | None = None):
        self.ventana = ventana or settings.ventana_analisis
        self._buffer: deque[dict] = deque(maxlen=self.ventana)
        self._ultimo_resultado: AnalisisResult = AnalisisResult()

    def agregar_lectura(self, temperatura: float, vibracion_total: float) -> None:
        self._buffer.append({"temp": temperatura, "vib": vibracion_total})

    def analizar(self, temperatura: float, vibracion_total: float, tiempo_inactividad: float = 0.0) -> AnalisisResult:
        self.agregar_lectura(temperatura, vibracion_total)

        if len(self._buffer) < 3:
            self._ultimo_resultado = AnalisisResult()
            return self._ultimo_resultado

        pend_temp = self._calcular_pendiente("temp")
        pend_vib = self._calcular_pendiente("vib")
        ace_temp = self._calcular_aceleracion("temp")
        ace_vib = self._calcular_aceleracion("vib")
        corr = self._calcular_correlacion()

        prob_umbral_temp = self._sigmoid(temperatura, k=0.8, x0=settings.temp_alerta_amarilla)
        prob_umbral_vib = self._sigmoid(vibracion_total, k=3, x0=settings.vibracion_alerta_amarilla)
        prob_inactividad = self._escala_lineal(tiempo_inactividad, 30)

        prob_temp = self._escala_lineal(abs(pend_temp or 0), 0.3) * prob_umbral_temp
        prob_vib = self._escala_lineal(abs(pend_vib or 0), 0.05) * prob_umbral_vib
        prob_corr = self._escala_lineal(abs(corr or 0), 0.6) * 0.6 * max(prob_umbral_temp, prob_umbral_vib, prob_inactividad)
        prob_ace_temp = self._escala_lineal(max(0, ace_temp or 0), 0.03) * 0.7 * prob_umbral_temp
        prob_ace_vib = self._escala_lineal(max(0, ace_vib or 0), 0.008) * 0.7 * prob_umbral_vib

        probabilidad = min(1.0, max(
            prob_temp, prob_vib, prob_corr,
            prob_ace_temp, prob_ace_vib,
            prob_umbral_temp, prob_umbral_vib,
            prob_inactividad,
        ))

        rul = self._estimar_rul(temperatura, vibracion_total, pend_temp, pend_vib)
        severidad = self._clasificar_severidad(probabilidad)
        modo = self._clasificar_modo(
            probabilidad, pend_temp, pend_vib,
            corr, temperatura, vibracion_total,
            ace_temp, ace_vib
        )

        self._ultimo_resultado = AnalisisResult(
            probabilidad=round(probabilidad, 4),
            severidad=severidad,
            modo_fallo=modo,
            rul_estimado=rul,
            pendiente_temperatura=round(pend_temp, 6) if pend_temp is not None else None,
            pendiente_vibracion=round(pend_vib, 6) if pend_vib is not None else None,
            aceleracion_temperatura=round(ace_temp, 6) if ace_temp is not None else None,
            aceleracion_vibracion=round(ace_vib, 6) if ace_vib is not None else None,
            correlacion=round(corr, 4) if corr is not None else None,
            inactividad=round(tiempo_inactividad, 1),
        )
        return self._ultimo_resultado

    def pendiente_temperatura(self) -> float | None:
        return self._ultimo_resultado.pendiente_temperatura

    def pendiente_vibracion(self) -> float | None:
        return self._ultimo_resultado.pendiente_vibracion

    def es_anomalia_predictiva(self) -> bool:
        return self._ultimo_resultado.probabilidad >= 0.5

    def reset(self) -> None:
        self._buffer.clear()
        self._ultimo_resultado = AnalisisResult()

    def resultado_con_inactividad(self, tiempo_inactividad: float) -> AnalisisResult:
        prob_inactividad = self._escala_lineal(tiempo_inactividad, 30)
        prob = max(self._ultimo_resultado.probabilidad, prob_inactividad)
        return AnalisisResult(
            probabilidad=round(prob, 4),
            severidad=self._clasificar_severidad(prob),
            modo_fallo=self._ultimo_resultado.modo_fallo,
            rul_estimado=self._ultimo_resultado.rul_estimado,
            pendiente_temperatura=self._ultimo_resultado.pendiente_temperatura,
            pendiente_vibracion=self._ultimo_resultado.pendiente_vibracion,
            aceleracion_temperatura=self._ultimo_resultado.aceleracion_temperatura,
            aceleracion_vibracion=self._ultimo_resultado.aceleracion_vibracion,
            correlacion=self._ultimo_resultado.correlacion,
            inactividad=round(tiempo_inactividad, 1),
        )

    def _calcular_pendiente(self, clave: str) -> float | None:
        if len(self._buffer) < 2:
            return None
        X = np.arange(len(self._buffer)).reshape(-1, 1)
        y = np.array([r[clave] for r in self._buffer])
        modelo = LinearRegression()
        modelo.fit(X, y)
        return float(modelo.coef_[0])

    def _calcular_aceleracion(self, clave: str) -> float | None:
        if len(self._buffer) < 5:
            return None
        X = np.arange(len(self._buffer)).reshape(-1, 1)
        y = np.array([r[clave] for r in self._buffer])
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)
        modelo = LinearRegression()
        modelo.fit(X_poly, y)
        coefs = modelo.coef_
        if len(coefs) >= 2:
            return float(coefs[1]) * 2
        return None

    def _calcular_correlacion(self) -> float | None:
        if len(self._buffer) < 5:
            return None
        temps = np.array([r["temp"] for r in self._buffer])
        vibs = np.array([r["vib"] for r in self._buffer])
        if np.std(temps) < 0.01 or np.std(vibs) < 0.01:
            return 0.0
        corr = np.corrcoef(temps, vibs)[0, 1]
        return float(corr)

    def _estimar_rul(
        self,
        temp: float,
        vib: float,
        pend_temp: float | None,
        pend_vib: float | None,
    ) -> float | None:
        rul_temp = None
        rul_vib = None
        if pend_temp and pend_temp > 0.001:
            faltante = settings.temp_emergencia_roja - temp
            if faltante > 0:
                rul_temp = faltante / pend_temp
        if pend_vib and pend_vib > 0.001:
            faltante = settings.vibracion_emergencia_roja - vib
            if faltante > 0:
                rul_vib = faltante / pend_vib
        if rul_temp is None and rul_vib is None:
            return None
        rul = min(r for r in [rul_temp, rul_vib] if r is not None)
        return round(rul * 2, 1)

    def _clasificar_severidad(self, prob: float) -> str:
        if prob >= 0.8:
            return "CRITICA"
        if prob >= 0.6:
            return "ADVERTENCIA"
        if prob >= 0.3:
            return "OBSERVACION"
        return "NORMAL"

    def _clasificar_modo(
        self,
        prob: float,
        pend_temp: float | None,
        pend_vib: float | None,
        corr: float | None,
        temp: float,
        vib: float,
        ace_temp: float | None,
        ace_vib: float | None,
    ) -> str | None:
        if prob < 0.3:
            return None
        temp_dominante = (pend_temp or 0) > 0.1 or temp >= settings.temp_alerta_amarilla
        vib_dominante = (pend_vib or 0) > 0.02 or vib >= settings.vibracion_alerta_amarilla
        hay_correlacion = abs(corr or 0) > 0.5
        hay_aceleracion = (ace_temp or 0) > 0.02 or (ace_vib or 0) > 0.005

        if temp_dominante and vib_dominante and (hay_correlacion or hay_aceleracion):
            return "COMBINADO"
        if temp_dominante and vib_dominante:
            return "COMBINADO"
        if temp_dominante:
            return "TERMICO"
        if vib_dominante:
            return "MECANICO"
        return None

    @staticmethod
    def _sigmoid(x: float, k: float = 1.0, x0: float = 0.5) -> float:
        return 1.0 / (1.0 + math.exp(-k * (x - x0)))

    @staticmethod
    def _escala_lineal(x: float, umbral: float) -> float:
        if x <= 0:
            return 0.0
        return min(1.0, x / umbral)


analizador = PredictiveEngine()
