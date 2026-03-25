"""Página de proyecciones y tendencias."""

import streamlit as st

from rrss.analytics.metrics import CalculadorMetricas
from rrss.analytics.projections import MotorProyecciones
from rrss.collectors.facebook import FacebookCollector
from rrss.collectors.instagram import InstagramCollector
from rrss.collectors.tiktok import TikTokCollector
from rrss.dashboard.components.charts import grafica_proyeccion
from rrss.models.base import Plataforma

COLLECTORS = {
    "Instagram": (Plataforma.INSTAGRAM, InstagramCollector),
    "Facebook": (Plataforma.FACEBOOK, FacebookCollector),
    "TikTok": (Plataforma.TIKTOK, TikTokCollector),
}

TENDENCIA_ICONOS = {
    "crecimiento": "📈",
    "estable": "➡️",
    "decrecimiento": "📉",
}


def renderizar():
    """Renderizar la página de proyecciones."""
    st.title("Proyecciones")
    st.markdown("Proyecciones de crecimiento y tendencias basadas en datos históricos.")

    with st.form("form_proyecciones"):
        col1, col2 = st.columns([3, 1])
        usuario = col1.text_input("Nombre de usuario", placeholder="ej: mi_marca")
        plat_nombre = col2.selectbox("Plataforma", ["Instagram", "Facebook", "TikTok"])
        dias = st.slider("Días a proyectar", 7, 90, 30)
        proyectar = st.form_submit_button("Proyectar", type="primary")

    if not proyectar or not usuario:
        st.info("Ingresa un usuario y selecciona la plataforma para generar proyecciones.")
        return

    plat_enum, collector_clase = COLLECTORS[plat_nombre]
    collector = collector_clase()
    motor = MotorProyecciones()

    with st.spinner(f"Obteniendo datos de @{usuario} en {plat_nombre}..."):
        perfil = collector.obtener_perfil(usuario)
        if not perfil:
            st.error("No se pudo obtener el perfil.")
            return
        publicaciones = collector.obtener_publicaciones(usuario, 50)

    if not publicaciones:
        st.warning("Sin publicaciones para generar proyecciones.")
        return

    st.success(f"Datos obtenidos: {perfil.seguidores:,} seguidores, {len(publicaciones)} publicaciones")

    # --- Proyección de Engagement ---
    st.markdown("---")
    st.subheader("Proyección de Engagement")

    proy_eng = motor.proyectar_engagement(publicaciones, perfil.seguidores, dias)

    icono = TENDENCIA_ICONOS.get(proy_eng.tendencia, "")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Engagement Actual", f"{proy_eng.valor_actual:.2f}%")
    col2.metric("Tendencia", f"{icono} {proy_eng.tendencia.capitalize()}")
    col3.metric("Cambio Semanal", f"{proy_eng.tasa_cambio_semanal:+.2f}%")
    col4.metric("Confianza", f"{proy_eng.confianza:.0%}")

    if proy_eng.valores_proyectados:
        st.plotly_chart(grafica_proyeccion(proy_eng), use_container_width=True)

        valor_final = proy_eng.valores_proyectados[-1]
        cambio = valor_final - proy_eng.valor_actual
        st.info(
            f"En {dias} días, el engagement rate se proyecta en "
            f"**{valor_final:.2f}%** ({cambio:+.2f}% vs actual)"
        )

    # --- Frecuencia Óptima ---
    st.markdown("---")
    st.subheader("Frecuencia Óptima de Publicación")

    freq = motor.analizar_frecuencia_optima(publicaciones, perfil.seguidores)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Frecuencia Actual", f"{freq['frecuencia_actual']} pubs/semana")
        st.metric("Frecuencia Recomendada", freq['frecuencia_recomendada'])

        corr = freq.get('correlacion_frecuencia_engagement', 0)
        if corr > 0.3:
            st.success(
                f"Correlación positiva ({corr:.2f}): Publicar más seguido "
                "mejora el engagement."
            )
        elif corr < -0.3:
            st.warning(
                f"Correlación negativa ({corr:.2f}): Publicar en exceso "
                "podría reducir el engagement."
            )
        else:
            st.info(
                f"Correlación baja ({corr:.2f}): La frecuencia no tiene "
                "un impacto significativo en el engagement."
            )

    with col2:
        mejores_dias = freq.get("mejores_dias", [])
        mejores_horas = freq.get("mejores_horas", [])

        if mejores_dias:
            st.markdown("**Mejores Días para Publicar:**")
            for i, dia in enumerate(mejores_dias, 1):
                st.markdown(f"{i}. {dia}")

        if mejores_horas:
            st.markdown("**Mejores Horas para Publicar:**")
            for i, hora in enumerate(mejores_horas, 1):
                st.markdown(f"{i}. {hora}")

    # --- Insight con IA ---
    st.markdown("---")
    if st.button("Generar Recomendaciones con IA"):
        try:
            from rrss.ai.insights import GeneradorInsights

            calculador = CalculadorMetricas()
            metricas = calculador.calcular(perfil, publicaciones)

            generador = GeneradorInsights()
            with st.spinner("Generando recomendaciones con IA..."):
                recomendaciones = generador.recomendaciones_crecimiento(
                    [metricas], [proy_eng]
                )
            st.markdown("### Recomendaciones de Crecimiento")
            st.markdown(recomendaciones)
        except Exception as e:
            st.error(f"Error al generar recomendaciones: {e}")
