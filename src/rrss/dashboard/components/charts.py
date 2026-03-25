"""Componentes de gráficas reutilizables con Plotly."""

import plotly.express as px
import plotly.graph_objects as go

from rrss.analytics.comparator import ResultadoComparacion
from rrss.analytics.projections import Proyeccion
from rrss.models.base import MetricasPerfil

COLORES = {
    "instagram": "#E1306C",
    "facebook": "#1877F2",
    "tiktok": "#00F2EA",
}


def grafica_engagement_comparativo(metricas: list[MetricasPerfil]) -> go.Figure:
    """Gráfica de barras comparando engagement entre perfiles/plataformas."""
    etiquetas = [f"@{m.nombre_usuario}\n({m.plataforma.value})" for m in metricas]
    valores = [m.engagement_rate_promedio for m in metricas]
    colores = [COLORES.get(m.plataforma.value, "#888") for m in metricas]

    fig = go.Figure(
        data=[
            go.Bar(
                x=etiquetas,
                y=valores,
                marker_color=colores,
                text=[f"{v:.2f}%" for v in valores],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="Engagement Rate por Perfil",
        yaxis_title="Engagement Rate (%)",
        template="plotly_dark",
        height=400,
    )
    return fig


def grafica_seguidores_comparativo(metricas: list[MetricasPerfil]) -> go.Figure:
    """Gráfica de barras de seguidores."""
    etiquetas = [f"@{m.nombre_usuario}\n({m.plataforma.value})" for m in metricas]
    valores = [m.seguidores_fin for m in metricas]
    colores = [COLORES.get(m.plataforma.value, "#888") for m in metricas]

    fig = go.Figure(
        data=[
            go.Bar(
                x=etiquetas,
                y=valores,
                marker_color=colores,
                text=[f"{v:,}" for v in valores],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="Seguidores por Perfil",
        yaxis_title="Seguidores",
        template="plotly_dark",
        height=400,
    )
    return fig


def grafica_rendimiento_por_tipo(metricas: MetricasPerfil) -> go.Figure:
    """Gráfica de rendimiento por tipo de contenido."""
    if not metricas.rendimiento_por_tipo:
        fig = go.Figure()
        fig.update_layout(
            title="Sin datos de rendimiento por tipo",
            template="plotly_dark",
        )
        return fig

    tipos = list(metricas.rendimiento_por_tipo.keys())
    valores = list(metricas.rendimiento_por_tipo.values())
    color = COLORES.get(metricas.plataforma.value, "#888")

    fig = go.Figure(
        data=[
            go.Bar(
                x=tipos,
                y=valores,
                marker_color=color,
                text=[f"{v:.2f}%" for v in valores],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title=f"Engagement por Tipo de Contenido (@{metricas.nombre_usuario})",
        yaxis_title="Engagement Rate (%)",
        template="plotly_dark",
        height=400,
    )
    return fig


def grafica_hashtags(metricas: MetricasPerfil) -> go.Figure:
    """Gráfica de hashtags más frecuentes."""
    if not metricas.hashtags_frecuentes:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de hashtags", template="plotly_dark")
        return fig

    tags = list(metricas.hashtags_frecuentes.keys())[:10]
    frecuencias = [metricas.hashtags_frecuentes[t] for t in tags]
    color = COLORES.get(metricas.plataforma.value, "#888")

    fig = go.Figure(
        data=[
            go.Bar(
                x=frecuencias,
                y=[f"#{t}" for t in tags],
                orientation="h",
                marker_color=color,
                text=frecuencias,
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="Hashtags Más Frecuentes",
        xaxis_title="Frecuencia",
        template="plotly_dark",
        height=400,
        yaxis=dict(autorange="reversed"),
    )
    return fig


def grafica_proyeccion(proyeccion: Proyeccion) -> go.Figure:
    """Gráfica de línea con proyección temporal."""
    if not proyeccion.valores_proyectados:
        fig = go.Figure()
        fig.update_layout(
            title="Sin datos para proyección", template="plotly_dark"
        )
        return fig

    fig = go.Figure()

    # Punto actual
    fig.add_trace(
        go.Scatter(
            x=["Actual"],
            y=[proyeccion.valor_actual],
            mode="markers",
            name="Actual",
            marker=dict(size=12, color="#FFD700"),
        )
    )

    # Línea de proyección
    fig.add_trace(
        go.Scatter(
            x=proyeccion.fechas_proyectadas,
            y=proyeccion.valores_proyectados,
            mode="lines+markers",
            name="Proyección",
            line=dict(dash="dash", color="#00F2EA"),
            marker=dict(size=4),
        )
    )

    fig.update_layout(
        title=f"Proyección: {proyeccion.metrica} ({proyeccion.tendencia})",
        yaxis_title=proyeccion.metrica,
        xaxis_title="Fecha",
        template="plotly_dark",
        height=400,
    )
    return fig


def grafica_radar_comparativo(comparacion: ResultadoComparacion) -> go.Figure:
    """Gráfica de radar comparando métricas normalizadas."""
    categorias = ["Engagement", "Seguidores", "Frecuencia"]

    fig = go.Figure()

    # Normalizar valores (0-100)
    max_eng = max(comparacion.engagement_por_perfil.values() or [1])
    max_seg = max(comparacion.seguidores_por_perfil.values() or [1])
    max_freq = max(comparacion.frecuencia_por_perfil.values() or [1])

    for clave in comparacion.engagement_por_perfil:
        eng_norm = (comparacion.engagement_por_perfil.get(clave, 0) / max_eng) * 100
        seg_norm = (comparacion.seguidores_por_perfil.get(clave, 0) / max_seg) * 100
        freq_norm = (comparacion.frecuencia_por_perfil.get(clave, 0) / max_freq) * 100

        plataforma = clave.split("@")[-1] if "@" in clave else ""
        color = COLORES.get(plataforma, "#888")

        fig.add_trace(
            go.Scatterpolar(
                r=[eng_norm, seg_norm, freq_norm, eng_norm],
                theta=categorias + [categorias[0]],
                fill="toself",
                name=clave,
                line=dict(color=color),
                opacity=0.6,
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Comparación Radar",
        template="plotly_dark",
        height=450,
    )
    return fig
