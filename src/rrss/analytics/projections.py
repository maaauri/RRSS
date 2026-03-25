"""Motor de proyecciones y tendencias para métricas de redes sociales."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from rrss.models.base import Perfil, Publicacion


@dataclass
class Proyeccion:
    """Resultado de una proyección."""

    metrica: str
    valor_actual: float
    valores_proyectados: list[float] = field(default_factory=list)
    fechas_proyectadas: list[str] = field(default_factory=list)
    tendencia: str = ""  # "crecimiento", "estable", "decrecimiento"
    tasa_cambio_semanal: float = 0.0
    confianza: float = 0.0  # 0-1


@dataclass
class AnalisisTendencia:
    """Análisis de tendencia de una serie temporal."""

    direccion: str  # "crecimiento", "estable", "decrecimiento"
    tasa_cambio: float  # porcentaje por período
    r_cuadrado: float  # bondad del ajuste (0-1)
    pendiente: float
    intercepto: float


class MotorProyecciones:
    """Motor de proyecciones basado en regresión y análisis de tendencias."""

    def proyectar_seguidores(
        self,
        historial_perfiles: list[Perfil],
        dias_futuro: int = 30,
    ) -> Proyeccion:
        """Proyectar el crecimiento de seguidores.

        Args:
            historial_perfiles: Perfiles históricos ordenados por fecha.
            dias_futuro: Número de días a proyectar.

        Returns:
            Proyeccion con valores estimados.
        """
        if len(historial_perfiles) < 2:
            valor_actual = historial_perfiles[0].seguidores if historial_perfiles else 0
            return Proyeccion(
                metrica="seguidores",
                valor_actual=valor_actual,
                tendencia="sin datos suficientes",
            )

        # Extraer serie temporal
        fechas = [p.fecha_recoleccion for p in historial_perfiles]
        valores = [float(p.seguidores) for p in historial_perfiles]

        return self._proyectar_serie(
            fechas=fechas,
            valores=valores,
            metrica="seguidores",
            dias_futuro=dias_futuro,
        )

    def proyectar_engagement(
        self,
        publicaciones: list[Publicacion],
        seguidores: int,
        dias_futuro: int = 30,
    ) -> Proyeccion:
        """Proyectar la tendencia de engagement.

        Args:
            publicaciones: Lista de publicaciones con fechas.
            seguidores: Número actual de seguidores.
            dias_futuro: Días a proyectar.

        Returns:
            Proyeccion con engagement estimado.
        """
        pubs_con_fecha = [p for p in publicaciones if p.fecha_publicacion]
        if len(pubs_con_fecha) < 3 or seguidores == 0:
            return Proyeccion(
                metrica="engagement_rate",
                valor_actual=0.0,
                tendencia="sin datos suficientes",
            )

        # Calcular engagement rate por publicación
        pubs_ordenadas = sorted(pubs_con_fecha, key=lambda p: p.fecha_publicacion)
        fechas = [p.fecha_publicacion for p in pubs_ordenadas]
        valores = [p.engagement_rate(seguidores) for p in pubs_ordenadas]

        return self._proyectar_serie(
            fechas=fechas,
            valores=valores,
            metrica="engagement_rate",
            dias_futuro=dias_futuro,
        )

    def analizar_frecuencia_optima(
        self, publicaciones: list[Publicacion], seguidores: int
    ) -> dict:
        """Analizar la frecuencia óptima de publicación.

        Busca correlación entre frecuencia de publicación y engagement.

        Returns:
            Diccionario con recomendaciones de frecuencia.
        """
        pubs_con_fecha = sorted(
            [p for p in publicaciones if p.fecha_publicacion],
            key=lambda p: p.fecha_publicacion,
        )

        if len(pubs_con_fecha) < 5 or seguidores == 0:
            return {
                "frecuencia_actual": 0,
                "frecuencia_recomendada": "3-5 por semana",
                "nota": "Datos insuficientes para análisis detallado.",
            }

        df = pd.DataFrame(
            [
                {
                    "fecha": p.fecha_publicacion,
                    "engagement": p.engagement_rate(seguidores),
                }
                for p in pubs_con_fecha
            ]
        )
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["semana"] = df["fecha"].dt.isocalendar().week

        # Agrupar por semana
        por_semana = df.groupby("semana").agg(
            publicaciones=("engagement", "count"),
            engagement_promedio=("engagement", "mean"),
        )

        freq_actual = round(float(por_semana["publicaciones"].mean()), 1)

        # Encontrar la frecuencia con mejor engagement
        if len(por_semana) >= 3:
            correlacion = por_semana["publicaciones"].corr(
                por_semana["engagement_promedio"]
            )
            mejor_semana = por_semana.loc[
                por_semana["engagement_promedio"].idxmax()
            ]
            freq_optima = int(mejor_semana["publicaciones"])
        else:
            correlacion = 0.0
            freq_optima = max(3, int(freq_actual))

        # Análisis por día de la semana
        df["dia"] = df["fecha"].dt.day_name()
        engagement_por_dia = df.groupby("dia")["engagement"].mean().sort_values(
            ascending=False
        )
        mejores_dias = engagement_por_dia.head(3).index.tolist()

        # Análisis por hora
        df["hora"] = df["fecha"].dt.hour
        engagement_por_hora = df.groupby("hora")["engagement"].mean().sort_values(
            ascending=False
        )
        mejores_horas = [f"{int(h):02d}:00" for h in engagement_por_hora.head(3).index]

        return {
            "frecuencia_actual": freq_actual,
            "frecuencia_recomendada": f"{freq_optima} por semana",
            "correlacion_frecuencia_engagement": round(float(correlacion), 3)
            if not np.isnan(correlacion)
            else 0.0,
            "mejores_dias": mejores_dias,
            "mejores_horas": mejores_horas,
        }

    def _proyectar_serie(
        self,
        fechas: list[datetime],
        valores: list[float],
        metrica: str,
        dias_futuro: int = 30,
    ) -> Proyeccion:
        """Proyectar una serie temporal usando regresión lineal."""
        # Convertir fechas a días numéricos
        fecha_base = min(fechas)
        x = np.array([(f - fecha_base).total_seconds() / 86400 for f in fechas])
        y = np.array(valores)

        # Regresión lineal
        tendencia = self._analizar_tendencia(x, y)

        # Generar proyecciones
        ultima_fecha = max(fechas)
        ultimo_x = (ultima_fecha - fecha_base).total_seconds() / 86400

        fechas_proy = []
        valores_proy = []
        for dia in range(1, dias_futuro + 1):
            x_futuro = ultimo_x + dia
            valor = tendencia.pendiente * x_futuro + tendencia.intercepto
            valor = max(0, valor)  # No permitir valores negativos

            fecha_futura = ultima_fecha + timedelta(days=dia)
            fechas_proy.append(fecha_futura.strftime("%Y-%m-%d"))
            valores_proy.append(round(valor, 2))

        # Tasa de cambio semanal
        if len(valores) >= 2 and valores[0] > 0:
            cambio_total = (valores[-1] - valores[0]) / valores[0] * 100
            semanas = max(1, (max(fechas) - min(fechas)).days / 7)
            tasa_semanal = cambio_total / semanas
        else:
            tasa_semanal = 0.0

        return Proyeccion(
            metrica=metrica,
            valor_actual=valores[-1] if valores else 0,
            valores_proyectados=valores_proy,
            fechas_proyectadas=fechas_proy,
            tendencia=tendencia.direccion,
            tasa_cambio_semanal=round(tasa_semanal, 3),
            confianza=round(tendencia.r_cuadrado, 3),
        )

    def _analizar_tendencia(self, x: np.ndarray, y: np.ndarray) -> AnalisisTendencia:
        """Analizar la tendencia de una serie con regresión lineal."""
        if len(x) < 2:
            return AnalisisTendencia(
                direccion="sin datos",
                tasa_cambio=0.0,
                r_cuadrado=0.0,
                pendiente=0.0,
                intercepto=float(y[0]) if len(y) > 0 else 0.0,
            )

        # Ajuste lineal
        coefs = np.polyfit(x, y, 1)
        pendiente = float(coefs[0])
        intercepto = float(coefs[1])

        # R² (coeficiente de determinación)
        y_pred = pendiente * x + intercepto
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_cuadrado = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r_cuadrado = max(0, min(1, r_cuadrado))

        # Determinar dirección
        umbral = 0.001 * abs(np.mean(y)) if np.mean(y) != 0 else 0.001
        if pendiente > umbral:
            direccion = "crecimiento"
        elif pendiente < -umbral:
            direccion = "decrecimiento"
        else:
            direccion = "estable"

        # Tasa de cambio
        if np.mean(y) != 0:
            tasa = (pendiente / np.mean(y)) * 100
        else:
            tasa = 0.0

        return AnalisisTendencia(
            direccion=direccion,
            tasa_cambio=round(float(tasa), 4),
            r_cuadrado=r_cuadrado,
            pendiente=pendiente,
            intercepto=intercepto,
        )
