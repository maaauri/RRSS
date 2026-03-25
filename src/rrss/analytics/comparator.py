"""Comparador de métricas entre plataformas y perfiles."""

from dataclasses import dataclass, field

from rrss.models.base import MetricasPerfil, Plataforma


@dataclass
class ResultadoComparacion:
    """Resultado de una comparación entre perfiles/plataformas."""

    perfiles_comparados: list[str]
    plataformas: list[str]

    # Rankings
    mejor_engagement: str = ""
    mejor_crecimiento: str = ""
    mayor_frecuencia: str = ""
    mejor_tipo_contenido_global: str = ""

    # Datos por perfil (clave: "usuario@plataforma")
    engagement_por_perfil: dict[str, float] = field(default_factory=dict)
    crecimiento_por_perfil: dict[str, float] = field(default_factory=dict)
    frecuencia_por_perfil: dict[str, float] = field(default_factory=dict)
    seguidores_por_perfil: dict[str, int] = field(default_factory=dict)

    # Recomendaciones
    resumen: str = ""
    recomendaciones: list[str] = field(default_factory=list)


class Comparador:
    """Compara métricas entre diferentes perfiles y plataformas."""

    def comparar(self, metricas: list[MetricasPerfil]) -> ResultadoComparacion:
        """Comparar múltiples perfiles/plataformas.

        Args:
            metricas: Lista de métricas de diferentes perfiles.

        Returns:
            ResultadoComparacion con rankings y recomendaciones.
        """
        if not metricas:
            return ResultadoComparacion(
                perfiles_comparados=[], plataformas=[]
            )

        perfiles = list({m.nombre_usuario for m in metricas})
        plataformas = list({m.plataforma.value for m in metricas})

        # Construir datos por perfil
        engagement_por_perfil = {}
        crecimiento_por_perfil = {}
        frecuencia_por_perfil = {}
        seguidores_por_perfil = {}

        for m in metricas:
            clave = f"{m.nombre_usuario}@{m.plataforma.value}"
            engagement_por_perfil[clave] = m.engagement_rate_promedio
            crecimiento_por_perfil[clave] = m.tasa_crecimiento
            frecuencia_por_perfil[clave] = m.publicaciones_por_semana
            seguidores_por_perfil[clave] = m.seguidores_fin

        # Rankings
        mejor_engagement = (
            max(engagement_por_perfil, key=engagement_por_perfil.get)
            if engagement_por_perfil
            else ""
        )
        mejor_crecimiento = (
            max(crecimiento_por_perfil, key=crecimiento_por_perfil.get)
            if crecimiento_por_perfil
            else ""
        )
        mayor_frecuencia = (
            max(frecuencia_por_perfil, key=frecuencia_por_perfil.get)
            if frecuencia_por_perfil
            else ""
        )

        # Mejor tipo de contenido global
        tipos_rendimiento: dict[str, list[float]] = {}
        for m in metricas:
            for tipo, rate in m.rendimiento_por_tipo.items():
                if tipo not in tipos_rendimiento:
                    tipos_rendimiento[tipo] = []
                tipos_rendimiento[tipo].append(rate)

        mejor_tipo_global = ""
        if tipos_rendimiento:
            promedios_tipo = {
                t: sum(rates) / len(rates) for t, rates in tipos_rendimiento.items()
            }
            mejor_tipo_global = max(promedios_tipo, key=promedios_tipo.get)

        # Generar recomendaciones
        recomendaciones = self._generar_recomendaciones(
            metricas, engagement_por_perfil, frecuencia_por_perfil
        )

        resumen = self._generar_resumen(
            mejor_engagement,
            mejor_crecimiento,
            mejor_tipo_global,
            engagement_por_perfil,
        )

        return ResultadoComparacion(
            perfiles_comparados=perfiles,
            plataformas=plataformas,
            mejor_engagement=mejor_engagement,
            mejor_crecimiento=mejor_crecimiento,
            mayor_frecuencia=mayor_frecuencia,
            mejor_tipo_contenido_global=mejor_tipo_global,
            engagement_por_perfil=engagement_por_perfil,
            crecimiento_por_perfil=crecimiento_por_perfil,
            frecuencia_por_perfil=frecuencia_por_perfil,
            seguidores_por_perfil=seguidores_por_perfil,
            resumen=resumen,
            recomendaciones=recomendaciones,
        )

    def comparar_plataformas_de_usuario(
        self, metricas: list[MetricasPerfil], nombre_usuario: str
    ) -> ResultadoComparacion:
        """Comparar las métricas de un mismo usuario en diferentes plataformas."""
        metricas_usuario = [
            m for m in metricas if m.nombre_usuario == nombre_usuario
        ]
        return self.comparar(metricas_usuario)

    def _generar_recomendaciones(
        self,
        metricas: list[MetricasPerfil],
        engagement: dict[str, float],
        frecuencia: dict[str, float],
    ) -> list[str]:
        """Generar recomendaciones basadas en los datos."""
        recs = []

        # Encontrar plataformas con bajo engagement
        if engagement:
            promedio_eng = sum(engagement.values()) / len(engagement)
            bajos = [k for k, v in engagement.items() if v < promedio_eng * 0.7]
            for perfil in bajos:
                recs.append(
                    f"El engagement en {perfil} está por debajo del promedio. "
                    "Considerar ajustar el tipo de contenido o la frecuencia."
                )

        # Comparar frecuencias
        for m in metricas:
            if m.publicaciones_por_semana < 2:
                recs.append(
                    f"{m.nombre_usuario}@{m.plataforma.value}: La frecuencia de "
                    f"publicación es baja ({m.publicaciones_por_semana}/semana). "
                    "Se recomienda al menos 3-5 publicaciones por semana."
                )

        # Recomendar mejor tipo de contenido
        for m in metricas:
            if m.mejor_tipo_contenido and m.rendimiento_por_tipo:
                recs.append(
                    f"{m.nombre_usuario}@{m.plataforma.value}: El contenido tipo "
                    f"'{m.mejor_tipo_contenido}' tiene el mejor rendimiento. "
                    "Priorizar este formato."
                )

        # Mejores horarios
        for m in metricas:
            if m.mejor_dia and m.mejor_hora:
                recs.append(
                    f"{m.nombre_usuario}@{m.plataforma.value}: Mejor momento para "
                    f"publicar: {m.mejor_dia} a las {m.mejor_hora}."
                )

        return recs

    def _generar_resumen(
        self,
        mejor_eng: str,
        mejor_crec: str,
        mejor_tipo: str,
        engagement: dict[str, float],
    ) -> str:
        """Generar un resumen textual de la comparación."""
        partes = []

        if mejor_eng:
            partes.append(
                f"Mayor engagement: {mejor_eng} ({engagement.get(mejor_eng, 0):.2f}%)"
            )
        if mejor_crec:
            partes.append(f"Mayor crecimiento: {mejor_crec}")
        if mejor_tipo:
            partes.append(f"Mejor tipo de contenido global: {mejor_tipo}")

        return " | ".join(partes) if partes else "Sin datos suficientes para comparar."
