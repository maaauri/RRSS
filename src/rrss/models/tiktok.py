"""Modelos específicos para TikTok."""

from pydantic import BaseModel, Field


class TikTokVideoMetricas(BaseModel):
    """Métricas específicas de un video de TikTok."""

    reproducciones: int = 0
    tiempo_reproduccion_total: int = 0  # segundos
    tiempo_reproduccion_promedio: float = 0.0  # segundos
    tasa_reproduccion_completa: float = 0.0  # porcentaje
    compartidos: int = 0
    duetos: int = 0
    stitches: int = 0
    sonido_original: bool = False
    nombre_sonido: str = ""

    # Fuentes de tráfico
    trafico_para_ti: float = 0.0  # porcentaje desde For You
    trafico_perfil: float = 0.0
    trafico_busqueda: float = 0.0
    trafico_sonido: float = 0.0
    trafico_hashtag: float = 0.0


class TikTokPerfilExtra(BaseModel):
    """Datos adicionales del perfil de TikTok."""

    total_likes_recibidos: int = 0
    videos_totales: int = 0
    promedio_vistas_por_video: float = 0.0
    temas_frecuentes: list[str] = Field(default_factory=list)
    sonidos_populares: list[str] = Field(default_factory=list)
