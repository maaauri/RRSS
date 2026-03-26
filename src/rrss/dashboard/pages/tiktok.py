"""Página de análisis detallado de TikTok."""

import streamlit as st

from rrss.analytics.metrics import CalculadorMetricas
from rrss.collectors.tiktok import TikTokCollector
from rrss.dashboard.components.charts import (
    grafica_hashtags,
    grafica_rendimiento_por_tipo,
)
from rrss.dashboard.components.metrics_cards import tarjeta_perfil, tarjetas_metricas


def renderizar():
    """Renderizar la página de TikTok."""
    st.title("🎵 TikTok")
    st.markdown("Análisis detallado de perfiles de TikTok.")

    with st.form("form_tiktok"):
        usuario = st.text_input("Nombre de usuario", placeholder="ej: mi_marca")
        limite = st.slider("Videos a analizar", 10, 50, 30)
        analizar = st.form_submit_button("Analizar", type="primary")

    if not analizar or not usuario:
        st.info("Ingresa un nombre de usuario para comenzar el análisis.")
        return

    collector = TikTokCollector()
    calculador = CalculadorMetricas()

    with st.spinner("Obteniendo perfil de TikTok..."):
        perfil = collector.obtener_perfil(usuario)

    if not perfil:
        st.error(f"No se pudo obtener el perfil de @{usuario}")
        return

    tarjeta_perfil(perfil)

    with st.spinner("Obteniendo videos..."):
        publicaciones = collector.obtener_publicaciones(usuario, limite)

    if not publicaciones:
        st.warning("No se encontraron videos.")
        return

    st.success(f"Se analizaron {len(publicaciones)} videos.")

    metricas = calculador.calcular(perfil, publicaciones)

    st.markdown("---")
    st.subheader("Métricas Principales")
    tarjetas_metricas(metricas)

    # Métricas específicas de TikTok
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Rendimiento de Videos")
        # Vistas promedio
        vistas_total = sum(p.vistas for p in publicaciones)
        vistas_prom = vistas_total / len(publicaciones) if publicaciones else 0
        c1, c2 = st.columns(2)
        c1.metric("Vistas Totales", f"{vistas_total:,}")
        c2.metric("Vistas Promedio", f"{vistas_prom:,.0f}")

    with col2:
        st.subheader("Hashtags")
        st.plotly_chart(grafica_hashtags(metricas), use_container_width=True)

    # Top videos
    st.markdown("---")
    st.subheader("Top Videos por Engagement")

    top_pubs = sorted(
        publicaciones,
        key=lambda p: p.engagement_rate(perfil.seguidores),
        reverse=True,
    )[:10]

    for i, pub in enumerate(top_pubs, 1):
        rate = pub.engagement_rate(perfil.seguidores)
        with st.expander(
            f"#{i} - Engagement: {rate:.2f}% | "
            f"❤️ {pub.likes:,} 💬 {pub.comentarios:,} "
            f"👁️ {pub.vistas:,}"
        ):
            st.write(pub.texto[:200] if pub.texto else "Sin descripción")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Likes", f"{pub.likes:,}")
            c2.metric("Comentarios", f"{pub.comentarios:,}")
            c3.metric("Compartidos", f"{pub.compartidos:,}")
            c4.metric("Vistas", f"{pub.vistas:,}")
            if pub.hashtags:
                st.write("Hashtags: " + " ".join(f"#{t}" for t in pub.hashtags))
            if pub.url:
                st.markdown(f"[Ver video]({pub.url})")
