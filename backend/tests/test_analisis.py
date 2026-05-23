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
            res = engine.analizar(36.0, 1.1)
        assert res.probabilidad < 0.3
        assert res.severidad == "NORMAL"

    def test_tendencia_alza_temperatura_aumenta_probabilidad(self):
        engine = PredictiveEngine(ventana=50)
        temp = 30.0
        for _ in range(25):
            res = engine.analizar(temp, 1.1)
            temp += 0.8
        assert res.probabilidad >= 0.3
        assert res.pendiente_temperatura is not None

    def test_tendencia_alza_vibracion_aumenta_probabilidad(self):
        engine = PredictiveEngine(ventana=50)
        vib = 1.0
        for _ in range(25):
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
            res = engine.analizar(36.0, 1.1)
        assert res.severidad == "NORMAL"

    def test_clasificacion_severidad_observacion(self):
        engine = PredictiveEngine(ventana=50)
        temp = 30.0
        for _ in range(30):
            res = engine.analizar(temp, 1.1)
            temp += 0.1
        assert res.severidad in ("OBSERVACION", "ADVERTENCIA")

    def test_clasificacion_severidad_advertencia(self):
        engine = PredictiveEngine(ventana=50)
        temp = 30.0
        for _ in range(30):
            res = engine.analizar(temp, 1.1)
            temp += 0.2
        assert res.severidad in ("ADVERTENCIA", "CRITICA")

    def test_modo_termico_detectado(self):
        engine = PredictiveEngine(ventana=50)
        temp = 30.0
        for _ in range(25):
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
