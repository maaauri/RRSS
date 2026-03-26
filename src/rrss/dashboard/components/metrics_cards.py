"""Tarjetas de KPIs para el dashboard Streamlit."""

import streamlit as st

from rrss.models.base import MetricasPerfil, Perfil


def tarjeta_perfil(perfil: Perfil):
    """Mostrar tarjeta resumen de un perfil."""
    verificado = " ✓" if perfil.es_verificado else ""
    st.markdown(
        f"### @{perfil.nombre_usuario}{verificado} "
        f"({perfil.plataforma.value.upper()})"
    )
    if perfil.nombre_completo:
        st.caption(perfil.nombre_completo)

    col1, col2, col3 = st.columns(3)
    col1.metric("Seguidores", f"{perfil.seguidores:,}")
    col2.metric("Siguiendo", f"{perfil.siguiendo:,}")
    col3.metric("Publicaciones", f"{perfil.total_publicaciones:,}")

    if perfil.biografia:
        st.caption(perfil.biografia[:150])


def tarjetas_metricas(metricas: MetricasPerfil):
    """Mostrar tarjetas de métricas principales."""
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Engagement Rate",
        f"{metricas.engagement_rate_promedio:.2f}%",
    )
    col2.metric(
        "Likes Promedio",
        f"{metricas.likes_promedio:,.0f}",
    )
    col3.metric(
        "Comentarios Prom.",
        f"{metricas.comentarios_promedio:,.0f}",
    )
    col4.metric(
        "Pubs/Semana",
        f"{metricas.publicaciones_por_semana:.1f}",
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Mejor Día", metricas.mejor_dia or "N/A")
    col6.metric("Mejor Hora", metricas.mejor_hora or "N/A")
    col7.metric("Mejor Tipo", metricas.mejor_tipo_contenido or "N/A")
    col8.metric("Total Pubs Analizadas", str(metricas.total_publicaciones))


def tarjetas_comparacion(
    engagement: dict[str, float],
    seguidores: dict[str, int],
    frecuencia: dict[str, float],
    mejor_engagement: str,
):
    """Mostrar tarjetas de comparación entre perfiles."""
    st.markdown("### Rankings")

    for clave in engagement:
        es_mejor = clave == mejor_engagement
        icono = "🏆 " if es_mejor else ""

        with st.expander(f"{icono}{clave}", expanded=es_mejor):
            c1, c2, c3 = st.columns(3)
            c1.metric("Engagement", f"{engagement.get(clave, 0):.2f}%")
            c2.metric("Seguidores", f"{seguidores.get(clave, 0):,}")
            c3.metric("Pubs/Semana", f"{frecuencia.get(clave, 0):.1f}")
