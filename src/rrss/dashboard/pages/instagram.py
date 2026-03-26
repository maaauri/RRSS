"""Página de análisis detallado de Instagram."""

import streamlit as st

from rrss.analytics.metrics import CalculadorMetricas
from rrss.collectors.instagram import InstagramCollector
from rrss.dashboard.components.charts import (
    grafica_hashtags,
    grafica_rendimiento_por_tipo,
)
from rrss.dashboard.components.metrics_cards import tarjeta_perfil, tarjetas_metricas


def renderizar():
    """Renderizar la página de Instagram."""
    st.title("📸 Instagram")
    st.markdown("Análisis detallado de perfiles de Instagram.")

    with st.form("form_instagram"):
        usuario = st.text_input("Nombre de usuario", placeholder="ej: mi_marca")
        limite = st.slider("Publicaciones a analizar", 10, 100, 50)
        analizar = st.form_submit_button("Analizar", type="primary")

    if not analizar or not usuario:
        st.info("Ingresa un nombre de usuario para comenzar el análisis.")
        return

    collector = InstagramCollector()
    calculador = CalculadorMetricas()

    with st.spinner("Obteniendo perfil de Instagram..."):
        perfil = collector.obtener_perfil(usuario)

    if not perfil:
        st.error(f"No se pudo obtener el perfil de @{usuario}")
        return

    tarjeta_perfil(perfil)

    with st.spinner("Obteniendo publicaciones..."):
        publicaciones = collector.obtener_publicaciones(usuario, limite)

    if not publicaciones:
        st.warning("No se encontraron publicaciones.")
        return

    st.success(f"Se analizaron {len(publicaciones)} publicaciones.")

    metricas = calculador.calcular(perfil, publicaciones)

    st.markdown("---")
    st.subheader("Métricas Principales")
    tarjetas_metricas(metricas)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Rendimiento por Tipo")
        st.plotly_chart(
            grafica_rendimiento_por_tipo(metricas), use_container_width=True
        )

    with col2:
        st.subheader("Hashtags")
        st.plotly_chart(grafica_hashtags(metricas), use_container_width=True)

    # Top publicaciones
    st.markdown("---")
    st.subheader("Top Publicaciones por Engagement")

    top_pubs = sorted(
        publicaciones,
        key=lambda p: p.engagement_rate(perfil.seguidores),
        reverse=True,
    )[:10]

    for i, pub in enumerate(top_pubs, 1):
        rate = pub.engagement_rate(perfil.seguidores)
        with st.expander(
            f"#{i} - Engagement: {rate:.2f}% | "
            f"❤️ {pub.likes:,} 💬 {pub.comentarios:,}"
        ):
            st.write(pub.texto[:200] if pub.texto else "Sin descripción")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Likes", f"{pub.likes:,}")
            c2.metric("Comentarios", f"{pub.comentarios:,}")
            c3.metric("Compartidos", f"{pub.compartidos:,}")
            c4.metric("Tipo", pub.tipo.value)
            if pub.url:
                st.markdown(f"[Ver publicación]({pub.url})")
