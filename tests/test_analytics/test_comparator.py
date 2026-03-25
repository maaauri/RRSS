"""Tests para el comparador de métricas."""

from datetime import datetime

from rrss.analytics.comparator import Comparador
from rrss.models.base import MetricasPerfil, Plataforma


def _crear_metricas(usuario, plataforma, engagement=3.0, seguidores=10000, freq=5.0):
    return MetricasPerfil(
        nombre_usuario=usuario,
        plataforma=plataforma,
        periodo_inicio=datetime(2026, 1, 1),
        periodo_fin=datetime(2026, 3, 1),
        engagement_rate_promedio=engagement,
        seguidores_fin=seguidores,
        publicaciones_por_semana=freq,
        mejor_tipo_contenido="video",
        rendimiento_por_tipo={"video": engagement, "imagen": engagement * 0.5},
        mejor_dia="Monday",
        mejor_hora="10:00",
    )


class TestComparador:
    def test_comparar_dos_perfiles(self):
        comparador = Comparador()
        metricas = [
            _crear_metricas("marca_a", Plataforma.INSTAGRAM, engagement=5.0),
            _crear_metricas("marca_a", Plataforma.TIKTOK, engagement=3.0),
        ]

        resultado = comparador.comparar(metricas)

        assert len(resultado.perfiles_comparados) >= 1
        assert len(resultado.plataformas) == 2
        assert "marca_a@instagram" in resultado.mejor_engagement

    def test_comparar_sin_datos(self):
        comparador = Comparador()
        resultado = comparador.comparar([])

        assert resultado.perfiles_comparados == []
        assert resultado.mejor_engagement == ""

    def test_recomendaciones(self):
        comparador = Comparador()
        metricas = [
            _crear_metricas("marca", Plataforma.INSTAGRAM, engagement=5.0, freq=7.0),
            _crear_metricas("marca", Plataforma.TIKTOK, engagement=1.0, freq=1.0),
        ]

        resultado = comparador.comparar(metricas)

        assert len(resultado.recomendaciones) > 0

    def test_resumen(self):
        comparador = Comparador()
        metricas = [
            _crear_metricas("marca", Plataforma.INSTAGRAM),
            _crear_metricas("marca", Plataforma.FACEBOOK),
        ]

        resultado = comparador.comparar(metricas)

        assert resultado.resumen != ""
        assert "engagement" in resultado.resumen.lower() or "Mayor" in resultado.resumen
