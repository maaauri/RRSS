"""Página de vista general del dashboard."""

import streamlit as st

from rrss.analytics.metrics import CalculadorMetricas
from rrss.collectors.facebook import FacebookCollector
from rrss.collectors.instagram import InstagramCollector
from rrss.collectors.tiktok import TikTokCollector
from rrss.dashboard.components.charts import (
    grafica_engagement_comparativo,
    grafica_seguidores_comparativo,
)
from rrss.dashboard.components.metrics_cards import tarjeta_perfil, tarjetas_metricas
from rrss.models.base import Plataforma

COLLECTORS = {
    "Instagram": (Plataforma.INSTAGRAM, InstagramCollector),
    "Facebook": (Plataforma.FACEBOOK, FacebookCollector),
    "TikTok": (Plataforma.TIKTOK, TikTokCollector),
}


def renderizar():
    """Renderizar la página de vista general."""
    st.title("Vista General")
    st.markdown("Analiza perfiles de redes sociales en un solo lugar.")

    # Formulario de entrada
    with st.form("form_overview"):
        col1, col2 = st.columns([3, 1])
        usuario = col1.text_input(
            "Nombre de usuario",
            placeholder="ej: mi_marca",
        )
        plataformas = col2.multiselect(
            "Plataformas",
            ["Instagram", "Facebook", "TikTok"],
            default=["Instagram"],
        )
        limite = st.slider("Publicaciones a analizar", 10, 100, 50)
        analizar = st.form_submit_button("Analizar", type="primary")

    if not analizar or not usuario:
        st.info("Ingresa un nombre de usuario y selecciona las plataformas para comenzar.")
        return

    calculador = CalculadorMetricas()
    todas_metricas = []

    for plat_nombre in plataformas:
        plat_enum, collector_clase = COLLECTORS[plat_nombre]
        collector = collector_clase()

        with st.spinner(f"Analizando {plat_nombre}..."):
            perfil = collector.obtener_perfil(usuario)
            if not perfil:
                st.warning(f"No se pudo obtener el perfil en {plat_nombre}")
                continue

            publicaciones = collector.obtener_publicaciones(usuario, limite)

        st.markdown("---")
        tarjeta_perfil(perfil)

        if publicaciones:
            metricas = calculador.calcular(perfil, publicaciones)
            tarjetas_metricas(metricas)
            todas_metricas.append(metricas)
        else:
            st.warning(f"Sin publicaciones en {plat_nombre}")

    # Gráficas comparativas si hay múltiples plataformas
    if len(todas_metricas) >= 2:
        st.markdown("---")
        st.subheader("Comparación Rápida")

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
