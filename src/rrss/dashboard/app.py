"""Aplicación principal del Dashboard Streamlit para RRSS.

Ejecutar con: streamlit run src/rrss/dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="RRSS - Análisis de Redes Sociales",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from rrss.dashboard.pages import (
    comparison,
    facebook,
    instagram,
    overview,
    projections,
    tiktok,
)

# --- Barra lateral ---
st.sidebar.title("📊 RRSS Analytics")
st.sidebar.markdown("Agente de análisis de métricas para redes sociales")

pagina = st.sidebar.radio(
    "Navegación",
    [
        "Vista General",
        "Instagram",
        "Facebook",
        "TikTok",
        "Comparativa",
        "Proyecciones",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Configuración:**\n"
    "Configura tus API keys en el archivo `.env`\n"
    "para acceder a datos de la API oficial."
)

# --- Enrutamiento ---
if pagina == "Vista General":
    overview.renderizar()
elif pagina == "Instagram":
    instagram.renderizar()
elif pagina == "Facebook":
    facebook.renderizar()
elif pagina == "TikTok":
    tiktok.renderizar()
elif pagina == "Comparativa":
    comparison.renderizar()
elif pagina == "Proyecciones":
    projections.renderizar()
