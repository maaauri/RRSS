"""Tests para los modelos base."""

from datetime import datetime

from rrss.models.base import (
    Comentario,
    MetricasPerfil,
    Perfil,
    Plataforma,
    Publicacion,
    TipoContenido,
)


class TestPerfil:
    def test_crear_perfil(self):
        perfil = Perfil(
            nombre_usuario="test_user",
            plataforma=Plataforma.INSTAGRAM,
            seguidores=1000,
            siguiendo=500,
        )
        assert perfil.nombre_usuario == "test_user"
        assert perfil.plataforma == Plataforma.INSTAGRAM
        assert perfil.seguidores == 1000

    def test_ratio_seguidores(self):
        perfil = Perfil(
            nombre_usuario="test",
            plataforma=Plataforma.INSTAGRAM,
            seguidores=1000,
            siguiendo=500,
        )
        assert perfil.ratio_seguidores == 2.0

    def test_ratio_seguidores_sin_siguiendo(self):
        perfil = Perfil(
            nombre_usuario="test",
            plataforma=Plataforma.INSTAGRAM,
            seguidores=1000,
            siguiendo=0,
        )
        assert perfil.ratio_seguidores == 0.0


class TestPublicacion:
    def test_engagement_total(self):
        pub = Publicacion(
            perfil_usuario="test",
            plataforma=Plataforma.INSTAGRAM,
            tipo=TipoContenido.IMAGEN,
            likes=100,
            comentarios=20,
            compartidos=10,
            guardados=5,
        )
        assert pub.engagement_total == 135

    def test_engagement_rate(self):
        pub = Publicacion(
            perfil_usuario="test",
            plataforma=Plataforma.INSTAGRAM,
            tipo=TipoContenido.IMAGEN,
            likes=100,
            comentarios=0,
            compartidos=0,
            guardados=0,
        )
        assert pub.engagement_rate(1000) == 10.0

    def test_engagement_rate_sin_seguidores(self):
        pub = Publicacion(
            perfil_usuario="test",
            plataforma=Plataforma.INSTAGRAM,
            tipo=TipoContenido.IMAGEN,
            likes=100,
        )
        assert pub.engagement_rate(0) == 0.0

    def test_hashtags(self):
        pub = Publicacion(
            perfil_usuario="test",
            plataforma=Plataforma.TIKTOK,
            tipo=TipoContenido.VIDEO,
            hashtags=["viral", "fyp", "trending"],
        )
        assert len(pub.hashtags) == 3
        assert "viral" in pub.hashtags


class TestComentario:
    def test_relevancia(self):
        comentario = Comentario(
            publicacion_id="123",
            plataforma=Plataforma.INSTAGRAM,
            likes=10,
            respuestas=5,
        )
        # relevancia = likes + (respuestas * 2)
        assert comentario.relevancia == 20

    def test_relevancia_sin_interacciones(self):
        comentario = Comentario(
            publicacion_id="123",
            plataforma=Plataforma.FACEBOOK,
        )
        assert comentario.relevancia == 0


class TestMetricasPerfil:
    def test_crear_metricas(self):
        metricas = MetricasPerfil(
            nombre_usuario="test",
            plataforma=Plataforma.INSTAGRAM,
            periodo_inicio=datetime(2026, 1, 1),
            periodo_fin=datetime(2026, 3, 1),
            engagement_rate_promedio=3.5,
            seguidores_fin=10000,
        )
        assert metricas.engagement_rate_promedio == 3.5
        assert metricas.seguidores_fin == 10000
