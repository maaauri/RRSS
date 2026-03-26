"""Cálculo de métricas de rendimiento por perfil y plataforma."""

from collections import Counter
from datetime import datetime

import numpy as np
import pandas as pd

from rrss.models.base import MetricasPerfil, Perfil, Plataforma, Publicacion


class CalculadorMetricas:
    """Calcula métricas de rendimiento a partir de los datos recolectados."""

    def calcular(
        self,
        perfil: Perfil,
        publicaciones: list[Publicacion],
        periodo_inicio: datetime | None = None,
        periodo_fin: datetime | None = None,
    ) -> MetricasPerfil:
        """Calcular todas las métricas para un perfil dado.

        Args:
            perfil: Datos del perfil.
            publicaciones: Lista de publicaciones del perfil.
            periodo_inicio: Inicio del período de análisis.
            periodo_fin: Fin del período de análisis.

        Returns:
            MetricasPerfil con todas las métricas calculadas.
        """
        ahora = datetime.now()
        periodo_fin = periodo_fin or ahora
        periodo_inicio = periodo_inicio or (
            min(
                (p.fecha_publicacion for p in publicaciones if p.fecha_publicacion),
                default=ahora,
            )
        )

        # Filtrar publicaciones dentro del período
        pubs_periodo = [
            p
            for p in publicaciones
            if p.fecha_publicacion
            and periodo_inicio <= p.fecha_publicacion <= periodo_fin
        ]

        if not pubs_periodo:
            return MetricasPerfil(
                nombre_usuario=perfil.nombre_usuario,
                plataforma=perfil.plataforma,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
            )

        # DataFrame para análisis
        df = self._publicaciones_a_dataframe(pubs_periodo)

        # Calcular métricas
        engagement = self._calcular_engagement(df, perfil.seguidores)
        frecuencia = self._calcular_frecuencia(df, periodo_inicio, periodo_fin)
        rendimiento_tipo = self._calcular_rendimiento_por_tipo(df, perfil.seguidores)
        hashtags = self._analizar_hashtags(pubs_periodo)
        top_pubs = self._obtener_top_publicaciones(pubs_periodo, perfil.seguidores)

        return MetricasPerfil(
            nombre_usuario=perfil.nombre_usuario,
            plataforma=perfil.plataforma,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            # Engagement
            engagement_rate_promedio=engagement["rate_promedio"],
            likes_promedio=engagement["likes_promedio"],
            comentarios_promedio=engagement["comentarios_promedio"],
            compartidos_promedio=engagement["compartidos_promedio"],
            # Crecimiento
            seguidores_fin=perfil.seguidores,
            total_publicaciones=len(pubs_periodo),
            # Frecuencia
            publicaciones_por_semana=frecuencia["por_semana"],
            mejor_dia=frecuencia["mejor_dia"],
            mejor_hora=frecuencia["mejor_hora"],
            # Rendimiento por tipo
            mejor_tipo_contenido=rendimiento_tipo.get("mejor_tipo", ""),
            rendimiento_por_tipo=rendimiento_tipo.get("por_tipo", {}),
            # Top publicaciones
            top_publicaciones_ids=[p.id for p in top_pubs if p.id],
            # Hashtags
            hashtags_frecuentes=hashtags["frecuentes"],
            hashtags_mejor_rendimiento=hashtags["mejor_rendimiento"],
        )

    def _publicaciones_a_dataframe(
        self, publicaciones: list[Publicacion]
    ) -> pd.DataFrame:
        """Convertir publicaciones a un DataFrame de pandas."""
        datos = []
        for p in publicaciones:
            datos.append(
                {
                    "id": p.id,
                    "tipo": p.tipo.value,
                    "likes": p.likes,
                    "comentarios": p.comentarios,
                    "compartidos": p.compartidos,
                    "guardados": p.guardados,
                    "vistas": p.vistas,
                    "engagement_total": p.engagement_total,
                    "fecha": p.fecha_publicacion,
                    "hashtags": p.hashtags,
                }
            )
        df = pd.DataFrame(datos)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"])
            df["dia_semana"] = df["fecha"].dt.day_name()
            df["hora"] = df["fecha"].dt.hour
        return df

    def _calcular_engagement(self, df: pd.DataFrame, seguidores: int) -> dict:
        """Calcular métricas de engagement."""
        if df.empty or seguidores == 0:
            return {
                "rate_promedio": 0.0,
                "likes_promedio": 0.0,
                "comentarios_promedio": 0.0,
                "compartidos_promedio": 0.0,
            }

        rates = (df["engagement_total"] / seguidores) * 100
        return {
            "rate_promedio": round(float(rates.mean()), 4),
            "likes_promedio": round(float(df["likes"].mean()), 2),
            "comentarios_promedio": round(float(df["comentarios"].mean()), 2),
            "compartidos_promedio": round(float(df["compartidos"].mean()), 2),
        }

    def _calcular_frecuencia(
        self,
        df: pd.DataFrame,
        inicio: datetime,
        fin: datetime,
    ) -> dict:
        """Calcular frecuencia de publicación y mejores momentos."""
        if df.empty:
            return {"por_semana": 0.0, "mejor_dia": "", "mejor_hora": ""}

        semanas = max(1, (fin - inicio).days / 7)
        por_semana = round(len(df) / semanas, 2)

        # Mejor día
        mejor_dia = ""
        if "dia_semana" in df.columns:
            conteo_dias = df["dia_semana"].value_counts()
            if not conteo_dias.empty:
                mejor_dia = conteo_dias.index[0]

        # Mejor hora
        mejor_hora = ""
        if "hora" in df.columns:
            conteo_horas = df["hora"].value_counts()
            if not conteo_horas.empty:
                mejor_hora = f"{int(conteo_horas.index[0]):02d}:00"

        return {
            "por_semana": por_semana,
            "mejor_dia": mejor_dia,
            "mejor_hora": mejor_hora,
        }

    def _calcular_rendimiento_por_tipo(
        self, df: pd.DataFrame, seguidores: int
    ) -> dict:
        """Calcular rendimiento promedio por tipo de contenido."""
        if df.empty or seguidores == 0:
            return {"mejor_tipo": "", "por_tipo": {}}

        por_tipo = {}
        for tipo, grupo in df.groupby("tipo"):
            rate = float((grupo["engagement_total"] / seguidores * 100).mean())
            por_tipo[str(tipo)] = round(rate, 4)

        mejor_tipo = max(por_tipo, key=por_tipo.get) if por_tipo else ""
        return {"mejor_tipo": mejor_tipo, "por_tipo": por_tipo}

    def _analizar_hashtags(self, publicaciones: list[Publicacion]) -> dict:
        """Analizar hashtags: frecuencia y rendimiento."""
        conteo = Counter()
        rendimiento: dict[str, list[int]] = {}

        for pub in publicaciones:
            for tag in pub.hashtags:
                tag_lower = tag.lower()
                conteo[tag_lower] += 1
                if tag_lower not in rendimiento:
                    rendimiento[tag_lower] = []
                rendimiento[tag_lower].append(pub.engagement_total)

        # Top 20 más frecuentes
        frecuentes = dict(conteo.most_common(20))

        # Promedio de engagement por hashtag (solo los que aparecen 2+ veces)
        mejor_rendimiento = {}
        for tag, engagements in rendimiento.items():
            if len(engagements) >= 2:
                mejor_rendimiento[tag] = round(float(np.mean(engagements)), 2)

        # Ordenar por rendimiento
        mejor_rendimiento = dict(
            sorted(mejor_rendimiento.items(), key=lambda x: x[1], reverse=True)[:15]
        )

        return {
            "frecuentes": frecuentes,
            "mejor_rendimiento": mejor_rendimiento,
        }

    def _obtener_top_publicaciones(
        self,
        publicaciones: list[Publicacion],
        seguidores: int,
        limite: int = 10,
    ) -> list[Publicacion]:
        """Obtener las publicaciones con mejor engagement."""
        return sorted(
            publicaciones,
            key=lambda p: p.engagement_rate(seguidores),
            reverse=True,
        )[:limite]
