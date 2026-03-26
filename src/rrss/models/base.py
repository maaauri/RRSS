"""Modelos base compartidos entre todas las plataformas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Plataforma(str, Enum):
    """Plataformas de redes sociales soportadas."""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class TipoContenido(str, Enum):
    """Tipos de contenido publicado."""

    IMAGEN = "imagen"
    VIDEO = "video"
    CARRUSEL = "carrusel"
    REEL = "reel"
    STORY = "story"
    TEXTO = "texto"
    EN_VIVO = "en_vivo"


class Perfil(BaseModel):
    """Perfil de una cuenta de red social."""

    id: Optional[str] = None
    nombre_usuario: str
    nombre_completo: str = ""
    plataforma: Plataforma
    seguidores: int = 0
    siguiendo: int = 0
    total_publicaciones: int = 0
    biografia: str = ""
    url_avatar: str = ""
    es_verificado: bool = False
    fecha_recoleccion: datetime = Field(default_factory=datetime.now)

    @property
    def ratio_seguidores(self) -> float:
        """Ratio seguidores/siguiendo."""
        if self.siguiendo == 0:
            return 0.0
        return self.seguidores / self.siguiendo


class Publicacion(BaseModel):
    """Una publicación en cualquier plataforma."""

    id: Optional[str] = None
    perfil_usuario: str
    plataforma: Plataforma
    tipo: TipoContenido
    texto: str = ""
    hashtags: list[str] = Field(default_factory=list)
    likes: int = 0
    comentarios: int = 0
    compartidos: int = 0
    guardados: int = 0
    vistas: int = 0
    alcance: int = 0
    impresiones: int = 0
    url: str = ""
    fecha_publicacion: Optional[datetime] = None
    fecha_recoleccion: datetime = Field(default_factory=datetime.now)

    @property
    def engagement_total(self) -> int:
        """Total de interacciones."""
        return self.likes + self.comentarios + self.compartidos + self.guardados

    def engagement_rate(self, seguidores: int) -> float:
        """Tasa de engagement basada en seguidores."""
        if seguidores == 0:
            return 0.0
        return (self.engagement_total / seguidores) * 100


class Comentario(BaseModel):
    """Un comentario en una publicación."""

    id: Optional[str] = None
    publicacion_id: str
    plataforma: Plataforma
    autor: str = ""
    texto: str = ""
    likes: int = 0
    respuestas: int = 0
    fecha: Optional[datetime] = None
    sentimiento: Optional[str] = None  # positivo, negativo, neutro

    @property
    def relevancia(self) -> int:
        """Puntuación de relevancia del comentario."""
        return self.likes + (self.respuestas * 2)


class MetricasPerfil(BaseModel):
    """Métricas calculadas para un perfil en un período dado."""

    nombre_usuario: str
    plataforma: Plataforma
    periodo_inicio: datetime
    periodo_fin: datetime

    # Engagement
    engagement_rate_promedio: float = 0.0
    likes_promedio: float = 0.0
    comentarios_promedio: float = 0.0
    compartidos_promedio: float = 0.0

    # Crecimiento
    seguidores_inicio: int = 0
    seguidores_fin: int = 0
    crecimiento_neto: int = 0
    tasa_crecimiento: float = 0.0  # porcentaje

    # Frecuencia
    total_publicaciones: int = 0
    publicaciones_por_semana: float = 0.0
    mejor_dia: str = ""
    mejor_hora: str = ""

    # Rendimiento por tipo
    mejor_tipo_contenido: str = ""
    rendimiento_por_tipo: dict[str, float] = Field(default_factory=dict)

    # Top contenido
    top_publicaciones_ids: list[str] = Field(default_factory=list)

    # Hashtags
    hashtags_frecuentes: dict[str, int] = Field(default_factory=dict)
    hashtags_mejor_rendimiento: dict[str, float] = Field(default_factory=dict)

    fecha_calculo: datetime = Field(default_factory=datetime.now)
