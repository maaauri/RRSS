"""Generación de insights con IA usando OpenAI API.

Proporciona análisis profundo, resúmenes ejecutivos y recomendaciones
de estrategia basadas en las métricas recolectadas.
"""

import json
import logging
from typing import Optional

from openai import OpenAI

from rrss.analytics.comparator import ResultadoComparacion
from rrss.analytics.projections import Proyeccion
from rrss.config import OPENAI_API_KEY, OPENAI_MODELO
from rrss.models.base import Comentario, MetricasPerfil

logger = logging.getLogger(__name__)


class GeneradorInsights:
    """Genera insights y recomendaciones usando OpenAI."""

    def __init__(self, api_key: str = "", modelo: str = ""):
        self._api_key = api_key or OPENAI_API_KEY
        self._modelo = modelo or OPENAI_MODELO
        self._cliente: Optional[OpenAI] = None

    @property
    def cliente(self) -> OpenAI:
        if self._cliente is None:
            if not self._api_key:
                raise ValueError(
                    "Se requiere OPENAI_API_KEY. Configúrala en .env o pásala como parámetro."
                )
            self._cliente = OpenAI(api_key=self._api_key)
        return self._cliente

    def _consultar(self, sistema: str, mensaje: str) -> str:
        """Hacer una consulta a OpenAI."""
        try:
            respuesta = self.cliente.chat.completions.create(
                model=self._modelo,
                messages=[
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": mensaje},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return respuesta.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error al consultar OpenAI: {e}")
            return f"Error al generar insight: {e}"

    def resumen_ejecutivo(self, metricas: list[MetricasPerfil]) -> str:
        """Generar un resumen ejecutivo de las métricas.

        Args:
            metricas: Lista de métricas de uno o más perfiles.

        Returns:
            Resumen ejecutivo en texto.
        """
        datos = []
        for m in metricas:
            datos.append({
                "perfil": f"{m.nombre_usuario}@{m.plataforma.value}",
                "seguidores": m.seguidores_fin,
                "engagement_rate": f"{m.engagement_rate_promedio:.2f}%",
                "publicaciones_semana": m.publicaciones_por_semana,
                "mejor_tipo_contenido": m.mejor_tipo_contenido,
                "mejor_dia": m.mejor_dia,
                "mejor_hora": m.mejor_hora,
                "tasa_crecimiento": f"{m.tasa_crecimiento:.2f}%",
                "top_hashtags": list(m.hashtags_frecuentes.keys())[:5],
            })

        sistema = (
            "Eres un experto en marketing digital y análisis de redes sociales. "
            "Genera resúmenes ejecutivos claros, accionables y en español. "
            "Usa un tono profesional pero accesible. "
            "Incluye datos concretos y recomendaciones específicas."
        )

        mensaje = (
            "Genera un resumen ejecutivo de las siguientes métricas de redes sociales. "
            "Incluye: estado actual, fortalezas, áreas de mejora y 3 acciones prioritarias.\n\n"
            f"Datos:\n{json.dumps(datos, indent=2, ensure_ascii=False)}"
        )

        return self._consultar(sistema, mensaje)

    def analisis_comparativo(self, comparacion: ResultadoComparacion) -> str:
        """Generar análisis comparativo con IA.

        Args:
            comparacion: Resultado de la comparación entre perfiles.

        Returns:
            Análisis comparativo detallado.
        """
        datos = {
            "perfiles": comparacion.perfiles_comparados,
            "plataformas": comparacion.plataformas,
            "mejor_engagement": comparacion.mejor_engagement,
            "mejor_crecimiento": comparacion.mejor_crecimiento,
            "engagement_por_perfil": comparacion.engagement_por_perfil,
            "seguidores_por_perfil": comparacion.seguidores_por_perfil,
            "frecuencia_por_perfil": comparacion.frecuencia_por_perfil,
            "mejor_tipo_contenido": comparacion.mejor_tipo_contenido_global,
            "recomendaciones_base": comparacion.recomendaciones,
        }

        sistema = (
            "Eres un estratega de marketing digital especializado en redes sociales. "
            "Analiza datos comparativos entre perfiles y plataformas. "
            "Proporciona insights accionables en español. "
            "Identifica patrones, fortalezas relativas y oportunidades."
        )

        mensaje = (
            "Realiza un análisis comparativo profundo de estos perfiles de redes sociales. "
            "Incluye:\n"
            "1. Comparativa de rendimiento entre plataformas\n"
            "2. Fortalezas y debilidades de cada perfil/plataforma\n"
            "3. Oportunidades de crecimiento\n"
            "4. Estrategia recomendada para crecer la marca\n"
            "5. Priorización de acciones\n\n"
            f"Datos:\n{json.dumps(datos, indent=2, ensure_ascii=False)}"
        )

        return self._consultar(sistema, mensaje)

    def analisis_sentimiento_comentarios(
        self, comentarios: list[Comentario]
    ) -> str:
        """Analizar el sentimiento y temas de los comentarios.

        Args:
            comentarios: Lista de comentarios a analizar.

        Returns:
            Análisis de sentimiento y temas destacados.
        """
        if not comentarios:
            return "No hay comentarios para analizar."

        # Limitar a 50 comentarios para no exceder tokens
        muestra = sorted(comentarios, key=lambda c: c.relevancia, reverse=True)[:50]
        textos = [
            {
                "autor": c.autor,
                "texto": c.texto,
                "likes": c.likes,
                "plataforma": c.plataforma.value,
            }
            for c in muestra
        ]

        sistema = (
            "Eres un analista de comunidades digitales. "
            "Analiza comentarios de redes sociales para identificar "
            "sentimiento, temas recurrentes y oportunidades. "
            "Responde en español."
        )

        mensaje = (
            "Analiza estos comentarios de redes sociales y proporciona:\n"
            "1. Sentimiento general (positivo/negativo/neutro con porcentaje estimado)\n"
            "2. Temas recurrentes y preocupaciones\n"
            "3. Comentarios más relevantes y por qué\n"
            "4. Oportunidades de engagement identificadas\n"
            "5. Alertas o riesgos de reputación\n\n"
            f"Comentarios:\n{json.dumps(textos, indent=2, ensure_ascii=False)}"
        )

        return self._consultar(sistema, mensaje)

    def recomendaciones_crecimiento(
        self,
        metricas: list[MetricasPerfil],
        proyecciones: list[Proyeccion],
    ) -> str:
        """Generar recomendaciones de crecimiento basadas en datos y proyecciones.

        Args:
            metricas: Métricas actuales de los perfiles.
            proyecciones: Proyecciones calculadas.

        Returns:
            Recomendaciones detalladas de estrategia.
        """
        datos_metricas = []
        for m in metricas:
            datos_metricas.append({
                "perfil": f"{m.nombre_usuario}@{m.plataforma.value}",
                "seguidores": m.seguidores_fin,
                "engagement_rate": f"{m.engagement_rate_promedio:.2f}%",
                "publicaciones_semana": m.publicaciones_por_semana,
                "mejor_tipo": m.mejor_tipo_contenido,
                "hashtags_top": list(m.hashtags_frecuentes.keys())[:5],
            })

        datos_proyecciones = []
        for p in proyecciones:
            datos_proyecciones.append({
                "metrica": p.metrica,
                "valor_actual": p.valor_actual,
                "tendencia": p.tendencia,
                "tasa_cambio_semanal": f"{p.tasa_cambio_semanal:.2f}%",
                "confianza": f"{p.confianza:.0%}",
                "valor_proyectado_30d": p.valores_proyectados[-1]
                if p.valores_proyectados
                else "N/A",
            })

        sistema = (
            "Eres un consultor de crecimiento en redes sociales con experiencia "
            "en estrategias de marca. Basándote en datos reales y proyecciones, "
            "genera un plan de acción concreto y medible. Responde en español."
        )

        mensaje = (
            "Basándote en estas métricas y proyecciones, genera un plan de crecimiento:\n\n"
            "1. Diagnóstico actual (dónde estamos)\n"
            "2. Objetivos realistas a 30, 60 y 90 días\n"
            "3. Estrategia de contenido por plataforma\n"
            "4. Calendario de publicación recomendado\n"
            "5. Tácticas específicas para aumentar engagement\n"
            "6. KPIs a monitorear\n\n"
            f"Métricas:\n{json.dumps(datos_metricas, indent=2, ensure_ascii=False)}\n\n"
            f"Proyecciones:\n{json.dumps(datos_proyecciones, indent=2, ensure_ascii=False)}"
        )

        return self._consultar(sistema, mensaje)

    def analisis_contenido(
        self, metricas: list[MetricasPerfil]
    ) -> str:
        """Analizar el rendimiento del contenido y sugerir mejoras.

        Args:
            metricas: Métricas con datos de rendimiento por tipo.

        Returns:
            Análisis y recomendaciones de contenido.
        """
        datos = []
        for m in metricas:
            datos.append({
                "perfil": f"{m.nombre_usuario}@{m.plataforma.value}",
                "rendimiento_por_tipo": m.rendimiento_por_tipo,
                "mejor_tipo": m.mejor_tipo_contenido,
                "hashtags_frecuentes": dict(list(m.hashtags_frecuentes.items())[:10]),
                "hashtags_mejor_rendimiento": dict(
                    list(m.hashtags_mejor_rendimiento.items())[:10]
                ),
                "engagement_promedio": f"{m.engagement_rate_promedio:.2f}%",
                "mejor_dia": m.mejor_dia,
                "mejor_hora": m.mejor_hora,
            })

        sistema = (
            "Eres un estratega de contenido digital especializado en redes sociales. "
            "Analiza el rendimiento del contenido y proporciona recomendaciones "
            "creativas y basadas en datos. Responde en español."
        )

        mensaje = (
            "Analiza el rendimiento del contenido y genera recomendaciones:\n\n"
            "1. Qué tipos de contenido funcionan mejor y por qué\n"
            "2. Estrategia de hashtags recomendada\n"
            "3. Ideas de contenido basadas en lo que mejor funciona\n"
            "4. Formatos a probar o potenciar\n"
            "5. Calendario de contenido sugerido (semanal)\n\n"
            f"Datos:\n{json.dumps(datos, indent=2, ensure_ascii=False)}"
        )

        return self._consultar(sistema, mensaje)
