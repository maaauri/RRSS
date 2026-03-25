"""Modelos específicos para Instagram."""

from typing import Optional

from pydantic import BaseModel, Field


class InstagramInsights(BaseModel):
    """Insights disponibles a través de la API de Instagram."""

    alcance: int = 0
    impresiones: int = 0
    visitas_perfil: int = 0
    clics_sitio_web: int = 0
    clics_email: int = 0
    guardados: int = 0

    # Datos de audiencia (solo cuentas Business/Creator)
    audiencia_por_ciudad: dict[str, int] = Field(default_factory=dict)
    audiencia_por_pais: dict[str, int] = Field(default_factory=dict)
    audiencia_por_genero_edad: dict[str, int] = Field(default_factory=dict)


class InstagramStory(BaseModel):
    """Datos específicos de una Story de Instagram."""

    id: Optional[str] = None
    tipo: str = "imagen"  # imagen, video
    impresiones: int = 0
    alcance: int = 0
    respuestas: int = 0
    salidas: int = 0
    toques_adelante: int = 0
    toques_atras: int = 0
