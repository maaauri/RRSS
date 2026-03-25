"""Tests para el calculador de métricas."""

from datetime import datetime, timedelta

from rrss.analytics.metrics import CalculadorMetricas
from rrss.models.base import Perfil, Plataforma, Publicacion, TipoContenido


def _crear_perfil(seguidores=10000):
    return Perfil(
        nombre_usuario="test_user",
        plataforma=Plataforma.INSTAGRAM,
        seguidores=seguidores,
        siguiendo=500,
        total_publicaciones=100,
    )


def _crear_publicaciones(n=10, seguidores=10000):
    pubs = []
    ahora = datetime.now()
    for i in range(n):
        pubs.append(
            Publicacion(
                id=str(i),
                perfil_usuario="test_user",
                plataforma=Plataforma.INSTAGRAM,
                tipo=TipoContenido.IMAGEN if i % 2 == 0 else TipoContenido.VIDEO,
                likes=100 + i * 10,
                comentarios=10 + i,
                compartidos=5 + i,
                guardados=2 + i,
                hashtags=["test", "marca"] if i % 3 == 0 else ["test"],
                fecha_publicacion=ahora - timedelta(days=i * 2),
            )
        )
    return pubs


class TestCalculadorMetricas:
    def test_calcular_metricas_basicas(self):
        calculador = CalculadorMetricas()
        perfil = _crear_perfil()
        pubs = _crear_publicaciones()

        metricas = calculador.calcular(perfil, pubs)

        assert metricas.nombre_usuario == "test_user"
        assert metricas.plataforma == Plataforma.INSTAGRAM
        assert metricas.engagement_rate_promedio > 0
        assert metricas.likes_promedio > 0
        assert metricas.total_publicaciones == 10

    def test_sin_publicaciones(self):
        calculador = CalculadorMetricas()
        perfil = _crear_perfil()

        metricas = calculador.calcular(perfil, [])

        assert metricas.engagement_rate_promedio == 0.0
        assert metricas.total_publicaciones == 0

    def test_rendimiento_por_tipo(self):
        calculador = CalculadorMetricas()
        perfil = _crear_perfil()
        pubs = _crear_publicaciones()

        metricas = calculador.calcular(perfil, pubs)

        assert len(metricas.rendimiento_por_tipo) > 0
        assert metricas.mejor_tipo_contenido != ""

    def test_frecuencia(self):
        calculador = CalculadorMetricas()
        perfil = _crear_perfil()
        pubs = _crear_publicaciones(20)

        metricas = calculador.calcular(perfil, pubs)

        assert metricas.publicaciones_por_semana > 0

    def test_hashtags(self):
        calculador = CalculadorMetricas()
        perfil = _crear_perfil()
        pubs = _crear_publicaciones()

        metricas = calculador.calcular(perfil, pubs)

        assert "test" in metricas.hashtags_frecuentes

    def test_top_publicaciones(self):
        calculador = CalculadorMetricas()
        perfil = _crear_perfil()
        pubs = _crear_publicaciones()

        metricas = calculador.calcular(perfil, pubs)

        assert len(metricas.top_publicaciones_ids) > 0
