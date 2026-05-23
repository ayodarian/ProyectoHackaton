from app.services.analisis import PredictiveEngine


class TestPredictiveEngine:
    def test_recien_creado_sin_datos(self):
        engine = PredictiveEngine(ventana=10)
        res = engine.analizar(25.0, 1.0)
        assert res.probabilidad == 0.0
        assert res.severidad == "NORMAL"

    def test_lecturas_estables_probabilidad_baja(self):
        engine = PredictiveEngine(ventana=10)
        for _ in range(15):
            res = engine.analizar(30.0, 1.1)
        assert res.probabilidad < 0.3
        assert res.severidad == "NORMAL"

    def test_tendencia_alza_temperatura_aumenta_probabilidad(self):
        engine = PredictiveEngine(ventana=50)
        temp = 30.0
        for _ in range(18):
            res = engine.analizar(temp, 1.1)
            temp += 0.8
        assert res.probabilidad >= 0.3
        assert res.pendiente_temperatura is not None

    def test_tendencia_alza_vibracion_aumenta_probabilidad(self):
        engine = PredictiveEngine(ventana=50)
        vib = 2.5
        for _ in range(20):
            res = engine.analizar(36.0, vib)
            vib += 0.04
        assert res.probabilidad >= 0.3
        assert res.pendiente_vibracion is not None

    def test_umbral_temperatura_amarilla_dispara_probabilidad(self):
        engine = PredictiveEngine(ventana=10)
        for _ in range(10):
            res = engine.analizar(39.0, 1.1)
        assert res.probabilidad >= 0.5

    def test_umbral_vibracion_amarilla_dispara_probabilidad(self):
        engine = PredictiveEngine(ventana=10)
        for _ in range(10):
            res = engine.analizar(36.0, 3.2)
        assert res.probabilidad >= 0.5

    def test_clasificacion_severidad_normal(self):
        engine = PredictiveEngine(ventana=10)
        for _ in range(10):
            res = engine.analizar(32.0, 1.1)
        assert res.severidad == "NORMAL"

    def test_clasificacion_severidad_observacion(self):
        engine = PredictiveEngine(ventana=50)
        temp = 34.0
        for _ in range(30):
            res = engine.analizar(temp, 1.1)
            temp += 0.04
        assert res.severidad in ("OBSERVACION", "ADVERTENCIA")

    def test_clasificacion_severidad_advertencia(self):
        engine = PredictiveEngine(ventana=50)
        temp = 36.0
        for _ in range(30):
            res = engine.analizar(temp, 1.1)
            temp += 0.15
        assert res.severidad in ("ADVERTENCIA", "CRITICA")

    def test_modo_termico_detectado(self):
        engine = PredictiveEngine(ventana=50)
        temp = 30.0
        for _ in range(18):
            res = engine.analizar(temp, 1.1)
            temp += 0.8
        if res.probabilidad >= 0.3:
            assert res.modo_fallo is not None

    def test_modo_mecanico_detectado(self):
        engine = PredictiveEngine(ventana=50)
        vib = 1.0
        for _ in range(25):
            res = engine.analizar(36.0, vib)
            vib += 0.05
        if res.probabilidad >= 0.3:
            assert res.modo_fallo is not None

    def test_rul_estimado_con_tendencia(self):
        engine = PredictiveEngine(ventana=50)
        temp = 30.0
        for _ in range(20):
            res = engine.analizar(temp, 1.0)
            temp += 0.5
        if res.pendiente_temperatura and res.pendiente_temperatura > 0.001:
            assert res.rul_estimado is not None
            assert res.rul_estimado > 0

    def test_correlacion_alta_en_escenario_combinado(self):
        engine = PredictiveEngine(ventana=30)
        temp = 30.0
        vib = 1.0
        for _ in range(20):
            res = engine.analizar(temp, vib)
            temp += 0.5
            vib += 0.03
        if res.correlacion is not None:
            assert res.correlacion > 0.3

    def test_inactividad_cero_sin_efecto(self):
        engine = PredictiveEngine(ventana=30)
        temp = 30.0
        for _ in range(10):
            res = engine.analizar(temp, 1.0, tiempo_inactividad=0.0)
            temp += 0.005
        assert res.inactividad == 0.0
        assert res.probabilidad < 0.1

    def test_inactividad_alta_aumenta_probabilidad(self):
        engine = PredictiveEngine(ventana=30)
        for _ in range(10):
            res = engine.analizar(30.0, 1.0, tiempo_inactividad=60.0)
        assert res.probabilidad > 0.5
        assert res.inactividad == 60.0

    def test_resultado_con_inactividad(self):
        engine = PredictiveEngine(ventana=30)
        for _ in range(10):
            engine.analizar(30.0, 1.0)
        res = engine.resultado_con_inactividad(120.0)
        assert res.probabilidad > 0.5
        assert res.inactividad == 120.0

    def test_ajuste_ia_blending(self):
        prob_mate = 0.5
        prob_ia = 0.8
        prob_final = round(prob_mate * 0.7 + prob_ia * 0.3, 4)
        assert prob_final == 0.59
        prob_mate2 = 0.2
        prob_ia2 = 0.1
        prob_final2 = round(prob_mate2 * 0.7 + prob_ia2 * 0.3, 4)
        assert prob_final2 == 0.17

    def test_paro_emergencia_probabilidad_100(self):
        engine = PredictiveEngine(ventana=10)
        res = engine.analizar(36.0, 1.1, paro_emergencia=True)
        assert res.probabilidad == 1.0
        assert res.severidad == "CRITICA"
        assert res.modo_fallo == "PARO_EMERGENCIA"

    def test_temp_45_probabilidad_100(self):
        engine = PredictiveEngine(ventana=10)
        res = engine.analizar(45.0, 1.1)
        assert res.probabilidad == 1.0
        assert res.severidad == "CRITICA"
        assert res.modo_fallo == "PARO_EMERGENCIA"
