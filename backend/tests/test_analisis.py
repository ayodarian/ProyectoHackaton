from app.services.analisis import AnalizadorTendencias


class TestAnalizadorTendencias:
    def test_analizador_recien_creado_sin_datos(self):
        analizador = AnalizadorTendencias(ventana=10)
        assert analizador.pendiente_temperatura() is None
        assert analizador.pendiente_vibracion() is None
        assert analizador.es_anomalia_predictiva() is False

    def test_lecturas_estables_no_generan_anomalia(self):
        analizador = AnalizadorTendencias(ventana=10)
        for _ in range(15):
            analizador.agregar_lectura(36.0, 1.1)
        assert analizador.es_anomalia_predictiva() is False

    def test_tendencia_alza_temperatura_detecta_anomalia(self):
        analizador = AnalizadorTendencias(ventana=50)
        temp = 60.0
        for _ in range(20):
            analizador.agregar_lectura(temp, 1.1)
            temp += 1.5
        assert analizador.pendiente_temperatura() is not None
        assert analizador.pendiente_temperatura() > 0.5

    def test_tendencia_alza_vibracion_detecta_anomalia(self):
        analizador = AnalizadorTendencias(ventana=50)
        vib = 1.0
        for _ in range(20):
            analizador.agregar_lectura(62.0, vib)
            vib += 0.08
        assert analizador.pendiente_vibracion() is not None
        assert analizador.pendiente_vibracion() > 0.05

    def test_umbral_temperatura_amarilla_genera_anomalia(self):
        analizador = AnalizadorTendencias(ventana=50)
        for _ in range(12):
            analizador.agregar_lectura(82.0, 1.1)
        assert analizador.es_anomalia_predictiva() is True

    def test_umbral_vibracion_amarilla_genera_anomalia(self):
        analizador = AnalizadorTendencias(ventana=50)
        for _ in range(12):
            analizador.agregar_lectura(36.0, 3.2)
        assert analizador.es_anomalia_predictiva() is True
