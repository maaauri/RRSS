"""Modelos específicos para Facebook."""

from pydantic import BaseModel, Field


class FacebookPageInsights(BaseModel):
    """Insights de una página de Facebook."""

    me_gusta_pagina: int = 0
    seguidores_pagina: int = 0
    alcance_pagina: int = 0
    impresiones_pagina: int = 0
    interacciones_pagina: int = 0
    visitas_pagina: int = 0
    clics_pagina: int = 0

    # Reacciones desglosadas
    reacciones: dict[str, int] = Field(default_factory=dict)
    # Ej: {"me_gusta": 100, "me_encanta": 50, "jaja": 20, ...}

    # Datos demográficos (solo páginas)
    fans_por_ciudad: dict[str, int] = Field(default_factory=dict)
    fans_por_pais: dict[str, int] = Field(default_factory=dict)
    fans_por_genero_edad: dict[str, int] = Field(default_factory=dict)


class FacebookReaccion(BaseModel):
    """Desglose de reacciones de Facebook."""

    me_gusta: int = 0
    me_encanta: int = 0
    me_importa: int = 0
    me_divierte: int = 0
    me_asombra: int = 0
    me_entristece: int = 0
    me_enoja: int = 0

    @property
    def total(self) -> int:
        return (
            self.me_gusta
            + self.me_encanta
            + self.me_importa
            + self.me_divierte
            + self.me_asombra
            + self.me_entristece
            + self.me_enoja
        )
