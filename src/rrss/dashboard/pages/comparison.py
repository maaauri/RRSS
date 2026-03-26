"""Página de comparación entre perfiles y plataformas."""

import streamlit as st

from rrss.analytics.comparator import Comparador
from rrss.analytics.metrics import CalculadorMetricas
from rrss.collectors.facebook import FacebookCollector
from rrss.collectors.instagram import InstagramCollector
from rrss.collectors.tiktok import TikTokCollector
from rrss.dashboard.components.charts import (
    grafica_engagement_comparativo,
    grafica_radar_comparativo,
    grafica_seguidores_comparativo,
)
from rrss.dashboard.components.metrics_cards import tarjetas_comparacion
from rrss.models.base import Plataforma

COLLECTORS = {
    "Instagram": (Plataforma.INSTAGRAM, InstagramCollector),
    "Facebook": (Plataforma.FACEBOOK, FacebookCollector),
    "TikTok": (Plataforma.TIKTOK, TikTokCollector),
}


def renderizar():
    """Renderizar la página de comparación."""
    st.title("Comparativa")
    st.markdown("Compara perfiles entre plataformas y detecta oportunidades.")

    with st.form("form_comparacion"):
        usuarios_texto = st.text_area(
            "Usuarios a comparar (uno por línea)",
            placeholder="mi_marca\ncompetidor1\ncompetidor2",
            height=100,
        )
        plataformas = st.multiselect(
            "Plataformas",
            ["Instagram", "Facebook", "TikTok"],
            default=["Instagram", "TikTok"],
        )
        limite = st.slider("Publicaciones por perfil", 10, 100, 30)
        comparar = st.form_submit_button("Comparar", type="primary")

    if not comparar or not usuarios_texto.strip():
        st.info("Ingresa al menos 2 usuarios y selecciona las plataformas.")
        return

    usuarios = [u.strip() for u in usuarios_texto.strip().split("\n") if u.strip()]

    if len(usuarios) < 1 or len(plataformas) < 1:
        st.warning("Necesitas al menos 1 usuario y 1 plataforma.")
        return

    if len(usuarios) * len(plataformas) < 2:
        st.warning("Se necesitan al menos 2 combinaciones usuario/plataforma.")
        return

    calculador = CalculadorMetricas()
    todas_metricas = []

    barra = st.progress(0)
    total = len(usuarios) * len(plataformas)
    actual = 0

    for usuario in usuarios:
        for plat_nombre in plataformas:
            actual += 1
            barra.progress(actual / total)

            plat_enum, collector_clase = COLLECTORS[plat_nombre]
            collector = collector_clase()

            with st.spinner(f"Analizando @{usuario} en {plat_nombre}..."):
                perfil = collector.obtener_perfil(usuario)
                if not perfil:
                    continue
                publicaciones = collector.obtener_publicaciones(usuario, limite)
                if publicaciones:
                    metricas = calculador.calcular(perfil, publicaciones)
                    todas_metricas.append(metricas)

    barra.empty()

    if len(todas_metricas) < 2:
        st.error("No se obtuvieron suficientes datos para comparar.")
        return

    # Realizar comparación
    comparador = Comparador()
    resultado = comparador.comparar(todas_metricas)

    # Mostrar resultados
    st.markdown("---")
    st.subheader("Resumen")
    st.info(resultado.resumen)

    # Tarjetas de ranking
    tarjetas_comparacion(
        resultado.engagement_por_perfil,
        resultado.seguidores_por_perfil,
        resultado.frecuencia_por_perfil,
        resultado.mejor_engagement,
    )

    # Gráficas
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            grafica_engagement_comparativo(todas_metricas),
            use_container_width=True,
        )

    with col2:
        st.plotly_chart(
            grafica_seguidores_comparativo(todas_metricas),
            use_container_width=True,
        )

    # Radar
    st.plotly_chart(
        grafica_radar_comparativo(resultado),
        use_container_width=True,
    )

    # Recomendaciones
    if resultado.recomendaciones:
        st.markdown("---")
        st.subheader("Recomendaciones")
        for rec in resultado.recomendaciones:
            st.markdown(f"- {rec}")

    # Insight con IA (opcional)
    st.markdown("---")
    if st.button("Generar Análisis con IA (requiere OpenAI API Key)"):
        try:
            from rrss.ai.insights import GeneradorInsights

            generador = GeneradorInsights()
            with st.spinner("Generando análisis con IA..."):
                analisis = generador.analisis_comparativo(resultado)
            st.markdown("### Análisis con IA")
            st.markdown(analisis)
        except Exception as e:
            st.error(f"Error al generar insight: {e}")
