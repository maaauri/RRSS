"""Interfaz de línea de comandos para RRSS.

Usa Click para los comandos y Rich para la visualización en terminal.
"""

import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from rrss.analytics.comparator import Comparador
from rrss.analytics.metrics import CalculadorMetricas
from rrss.analytics.projections import MotorProyecciones
from rrss.collectors.facebook import FacebookCollector
from rrss.collectors.instagram import InstagramCollector
from rrss.collectors.tiktok import TikTokCollector
from rrss.models.base import Plataforma
from rrss.storage.database import BaseDatos

consola = Console()

COLORES_PLATAFORMA = {
    "instagram": "magenta",
    "facebook": "blue",
    "tiktok": "cyan",
}

COLLECTORS = {
    Plataforma.INSTAGRAM: InstagramCollector,
    Plataforma.FACEBOOK: FacebookCollector,
    Plataforma.TIKTOK: TikTokCollector,
}


def _obtener_collector(plataforma: Plataforma):
    """Obtener el collector para una plataforma."""
    clase = COLLECTORS.get(plataforma)
    if not clase:
        raise click.ClickException(f"Plataforma no soportada: {plataforma.value}")
    return clase()


def _mostrar_perfil(perfil, plataforma_color: str):
    """Mostrar datos de un perfil en la consola."""
    tabla = Table(
        title=f"Perfil: @{perfil.nombre_usuario}",
        border_style=plataforma_color,
        show_header=False,
    )
    tabla.add_column("Campo", style="bold")
    tabla.add_column("Valor")

    tabla.add_row("Plataforma", perfil.plataforma.value.upper())
    tabla.add_row("Nombre", perfil.nombre_completo)
    tabla.add_row("Seguidores", f"{perfil.seguidores:,}")
    tabla.add_row("Siguiendo", f"{perfil.siguiendo:,}")
    tabla.add_row("Publicaciones", f"{perfil.total_publicaciones:,}")
    tabla.add_row("Verificado", "✓" if perfil.es_verificado else "✗")
    if perfil.biografia:
        tabla.add_row("Biografía", perfil.biografia[:100])

    consola.print(tabla)


def _mostrar_metricas(metricas):
    """Mostrar métricas calculadas en la consola."""
    color = COLORES_PLATAFORMA.get(metricas.plataforma.value, "white")

    tabla = Table(
        title=f"Métricas: @{metricas.nombre_usuario} ({metricas.plataforma.value})",
        border_style=color,
    )
    tabla.add_column("Métrica", style="bold")
    tabla.add_column("Valor", justify="right")

    tabla.add_row("Engagement Rate Promedio", f"{metricas.engagement_rate_promedio:.2f}%")
    tabla.add_row("Likes Promedio", f"{metricas.likes_promedio:,.0f}")
    tabla.add_row("Comentarios Promedio", f"{metricas.comentarios_promedio:,.0f}")
    tabla.add_row("Compartidos Promedio", f"{metricas.compartidos_promedio:,.0f}")
    tabla.add_row("", "")
    tabla.add_row("Publicaciones Analizadas", str(metricas.total_publicaciones))
    tabla.add_row("Publicaciones/Semana", f"{metricas.publicaciones_por_semana:.1f}")
    tabla.add_row("Mejor Día", metricas.mejor_dia or "N/A")
    tabla.add_row("Mejor Hora", metricas.mejor_hora or "N/A")
    tabla.add_row("", "")
    tabla.add_row("Mejor Tipo de Contenido", metricas.mejor_tipo_contenido or "N/A")

    if metricas.rendimiento_por_tipo:
        tabla.add_row("", "")
        for tipo, rate in metricas.rendimiento_por_tipo.items():
            tabla.add_row(f"  └ {tipo}", f"{rate:.2f}%")

    consola.print(tabla)

    # Hashtags
    if metricas.hashtags_frecuentes:
        tabla_hash = Table(title="Top Hashtags", border_style=color)
        tabla_hash.add_column("Hashtag", style="bold")
        tabla_hash.add_column("Frecuencia", justify="right")
        tabla_hash.add_column("Eng. Promedio", justify="right")

        for tag, freq in list(metricas.hashtags_frecuentes.items())[:10]:
            eng = metricas.hashtags_mejor_rendimiento.get(tag, 0)
            tabla_hash.add_row(f"#{tag}", str(freq), f"{eng:,.0f}" if eng else "-")

        consola.print(tabla_hash)


@click.group()
@click.option("--db", default="data/rrss.db", help="Ruta a la base de datos SQLite.")
@click.option("--verbose", "-v", is_flag=True, help="Mostrar logs detallados.")
@click.pass_context
def cli(ctx, db: str, verbose: bool):
    """RRSS - Agente de Análisis de Métricas para Redes Sociales."""
    ctx.ensure_object(dict)
    ctx.obj["db"] = BaseDatos(db)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)


@cli.command()
@click.argument("usuario")
@click.option(
    "--plataforma",
    "-p",
    type=click.Choice(["instagram", "facebook", "tiktok"]),
    required=True,
    help="Plataforma a analizar.",
)
@click.option("--limite", "-l", default=50, help="Número máximo de publicaciones.")
@click.option("--guardar", "-g", is_flag=True, help="Guardar datos en la base de datos.")
@click.pass_context
def analizar(ctx, usuario: str, plataforma: str, limite: int, guardar: bool):
    """Analizar un perfil de red social."""
    plat = Plataforma(plataforma)
    color = COLORES_PLATAFORMA.get(plataforma, "white")
    db: BaseDatos = ctx.obj["db"]

    consola.print(
        Panel(
            f"Analizando @{usuario} en {plataforma.upper()}...",
            border_style=color,
        )
    )

    # Recolectar datos
    collector = _obtener_collector(plat)

    with consola.status("Obteniendo perfil..."):
        perfil = collector.obtener_perfil(usuario)

    if not perfil:
        consola.print(f"[red]No se pudo obtener el perfil de @{usuario}[/red]")
        return

    _mostrar_perfil(perfil, color)

    with consola.status("Obteniendo publicaciones..."):
        publicaciones = collector.obtener_publicaciones(usuario, limite)

    consola.print(f"\n[{color}]Se obtuvieron {len(publicaciones)} publicaciones.[/{color}]")

    if not publicaciones:
        consola.print("[yellow]Sin publicaciones para analizar.[/yellow]")
        return

    # Calcular métricas
    calculador = CalculadorMetricas()
    metricas = calculador.calcular(perfil, publicaciones)
    _mostrar_metricas(metricas)

    # Guardar en DB
    if guardar:
        with consola.status("Guardando en base de datos..."):
            db.guardar_perfil(perfil)
            db.guardar_publicaciones(publicaciones)
            db.guardar_metricas(metricas)
        consola.print("[green]✓ Datos guardados en la base de datos.[/green]")


@cli.command()
@click.argument("usuarios", nargs=-1, required=True)
@click.option(
    "--plataformas",
    "-p",
    multiple=True,
    type=click.Choice(["instagram", "facebook", "tiktok"]),
    help="Plataformas a comparar. Si no se especifica, se comparan todas.",
)
@click.pass_context
def comparar(ctx, usuarios: tuple, plataformas: tuple):
    """Comparar perfiles entre plataformas.

    Ejemplo: rrss comparar usuario1 usuario2 -p instagram -p tiktok
    """
    if not plataformas:
        plataformas = ("instagram", "facebook", "tiktok")

    consola.print(
        Panel(
            f"Comparando {len(usuarios)} perfil(es) en {len(plataformas)} plataforma(s)...",
            border_style="green",
        )
    )

    todas_metricas = []
    calculador = CalculadorMetricas()

    for usuario in usuarios:
        for plat_str in plataformas:
            plat = Plataforma(plat_str)
            color = COLORES_PLATAFORMA.get(plat_str, "white")

            consola.print(f"  [{color}]→ @{usuario} en {plat_str}...[/{color}]")

            collector = _obtener_collector(plat)
            perfil = collector.obtener_perfil(usuario)

            if not perfil:
                consola.print(f"    [yellow]⚠ No se pudo obtener el perfil[/yellow]")
                continue

            publicaciones = collector.obtener_publicaciones(usuario, 50)
            if publicaciones:
                metricas = calculador.calcular(perfil, publicaciones)
                todas_metricas.append(metricas)
            else:
                consola.print(f"    [yellow]⚠ Sin publicaciones[/yellow]")

    if len(todas_metricas) < 2:
        consola.print("[red]Se necesitan al menos 2 perfiles para comparar.[/red]")
        return

    # Comparar
    comparador = Comparador()
    resultado = comparador.comparar(todas_metricas)

    # Mostrar tabla comparativa
    tabla = Table(title="Comparación de Perfiles", border_style="green")
    tabla.add_column("Perfil", style="bold")
    tabla.add_column("Seguidores", justify="right")
    tabla.add_column("Engagement", justify="right")
    tabla.add_column("Pubs/Semana", justify="right")
    tabla.add_column("Mejor Tipo", justify="center")

    for clave, eng in resultado.engagement_por_perfil.items():
        segs = resultado.seguidores_por_perfil.get(clave, 0)
        freq = resultado.frecuencia_por_perfil.get(clave, 0)
        # Buscar mejor tipo en las métricas
        mejor_tipo = ""
        for m in todas_metricas:
            if f"{m.nombre_usuario}@{m.plataforma.value}" == clave:
                mejor_tipo = m.mejor_tipo_contenido
                break

        es_mejor = clave == resultado.mejor_engagement
        estilo = "bold green" if es_mejor else ""

        tabla.add_row(
            clave,
            f"{segs:,}",
            f"{eng:.2f}%",
            f"{freq:.1f}",
            mejor_tipo or "N/A",
            style=estilo,
        )

    consola.print(tabla)

    # Resumen
    consola.print(
        Panel(resultado.resumen, title="Resumen", border_style="green")
    )

    # Recomendaciones
    if resultado.recomendaciones:
        consola.print("\n[bold]Recomendaciones:[/bold]")
        for i, rec in enumerate(resultado.recomendaciones, 1):
            consola.print(f"  {i}. {rec}")


@cli.command()
@click.argument("usuario")
@click.option(
    "--plataforma",
    "-p",
    type=click.Choice(["instagram", "facebook", "tiktok"]),
    required=True,
)
@click.option("--dias", "-d", default=30, help="Días a proyectar (default: 30).")
@click.pass_context
def proyectar(ctx, usuario: str, plataforma: str, dias: int):
    """Generar proyecciones de crecimiento para un perfil."""
    plat = Plataforma(plataforma)
    color = COLORES_PLATAFORMA.get(plataforma, "white")

    consola.print(
        Panel(
            f"Generando proyecciones para @{usuario} ({plataforma})...",
            border_style=color,
        )
    )

    collector = _obtener_collector(plat)
    motor = MotorProyecciones()

    with consola.status("Obteniendo datos..."):
        perfil = collector.obtener_perfil(usuario)
        if not perfil:
            consola.print(f"[red]No se pudo obtener el perfil.[/red]")
            return
        publicaciones = collector.obtener_publicaciones(usuario, 50)

    # Proyección de engagement
    proy_eng = motor.proyectar_engagement(publicaciones, perfil.seguidores, dias)

    tabla = Table(title="Proyecciones", border_style=color)
    tabla.add_column("Métrica", style="bold")
    tabla.add_column("Valor Actual", justify="right")
    tabla.add_column("Tendencia", justify="center")
    tabla.add_column(f"Proyección {dias}d", justify="right")
    tabla.add_column("Confianza", justify="right")

    # Engagement
    valor_proy_eng = proy_eng.valores_proyectados[-1] if proy_eng.valores_proyectados else "N/A"
    tendencia_emoji = {
        "crecimiento": "[green]↑[/green]",
        "estable": "[yellow]→[/yellow]",
        "decrecimiento": "[red]↓[/red]",
    }
    tabla.add_row(
        "Engagement Rate",
        f"{proy_eng.valor_actual:.2f}%",
        tendencia_emoji.get(proy_eng.tendencia, proy_eng.tendencia),
        f"{valor_proy_eng:.2f}%" if isinstance(valor_proy_eng, float) else str(valor_proy_eng),
        f"{proy_eng.confianza:.0%}",
    )

    consola.print(tabla)

    # Frecuencia óptima
    freq = motor.analizar_frecuencia_optima(publicaciones, perfil.seguidores)
    consola.print(
        Panel(
            f"Frecuencia actual: {freq['frecuencia_actual']} pubs/semana\n"
            f"Recomendada: {freq['frecuencia_recomendada']}\n"
            f"Mejores días: {', '.join(freq.get('mejores_dias', []))}\n"
            f"Mejores horas: {', '.join(freq.get('mejores_horas', []))}",
            title="Frecuencia Óptima",
            border_style=color,
        )
    )


@cli.command()
@click.argument("usuario")
@click.option(
    "--plataformas",
    "-p",
    multiple=True,
    type=click.Choice(["instagram", "facebook", "tiktok"]),
)
@click.option("--archivo", "-o", default=None, help="Ruta para exportar CSV.")
@click.pass_context
def reporte(ctx, usuario: str, plataformas: tuple, archivo: Optional[str]):
    """Generar un reporte completo de un perfil.

    Ejemplo: rrss reporte mi_marca -p instagram -p tiktok -o reporte.csv
    """
    if not plataformas:
        plataformas = ("instagram", "facebook", "tiktok")

    consola.print(
        Panel(
            f"Generando reporte completo para @{usuario}...",
            border_style="green",
        )
    )

    calculador = CalculadorMetricas()
    filas_csv = []

    for plat_str in plataformas:
        plat = Plataforma(plat_str)
        color = COLORES_PLATAFORMA.get(plat_str, "white")

        collector = _obtener_collector(plat)

        with consola.status(f"Analizando {plat_str}..."):
            perfil = collector.obtener_perfil(usuario)
            if not perfil:
                consola.print(f"  [{color}]⚠ No disponible en {plat_str}[/{color}]")
                continue

            publicaciones = collector.obtener_publicaciones(usuario, 50)

        _mostrar_perfil(perfil, color)

        if publicaciones:
            metricas = calculador.calcular(perfil, publicaciones)
            _mostrar_metricas(metricas)

            filas_csv.append({
                "plataforma": plat_str,
                "usuario": usuario,
                "seguidores": perfil.seguidores,
                "siguiendo": perfil.siguiendo,
                "publicaciones": perfil.total_publicaciones,
                "engagement_rate": f"{metricas.engagement_rate_promedio:.2f}",
                "likes_promedio": f"{metricas.likes_promedio:.0f}",
                "comentarios_promedio": f"{metricas.comentarios_promedio:.0f}",
                "pubs_por_semana": f"{metricas.publicaciones_por_semana:.1f}",
                "mejor_dia": metricas.mejor_dia,
                "mejor_hora": metricas.mejor_hora,
                "mejor_tipo_contenido": metricas.mejor_tipo_contenido,
            })

        consola.print()

    # Exportar CSV
    if archivo and filas_csv:
        ruta = Path(archivo)
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=filas_csv[0].keys())
            writer.writeheader()
            writer.writerows(filas_csv)
        consola.print(f"[green]✓ Reporte exportado a: {ruta.absolute()}[/green]")


@cli.command()
@click.argument("usuario")
@click.option(
    "--plataformas",
    "-p",
    multiple=True,
    type=click.Choice(["instagram", "facebook", "tiktok"]),
)
@click.option("--tipo", "-t", type=click.Choice([
    "resumen", "comparativo", "crecimiento", "contenido", "sentimiento"
]), default="resumen", help="Tipo de análisis con IA.")
@click.pass_context
def insight(ctx, usuario: str, plataformas: tuple, tipo: str):
    """Generar insights con IA (requiere OPENAI_API_KEY).

    Ejemplo: rrss insight mi_marca -p instagram -t resumen
    """
    from rrss.ai.insights import GeneradorInsights

    if not plataformas:
        plataformas = ("instagram", "facebook", "tiktok")

    consola.print(
        Panel(
            f"Generando insight '{tipo}' para @{usuario}...",
            border_style="yellow",
        )
    )

    calculador = CalculadorMetricas()
    generador = GeneradorInsights()
    todas_metricas = []
    todos_comentarios = []

    for plat_str in plataformas:
        plat = Plataforma(plat_str)
        collector = _obtener_collector(plat)

        with consola.status(f"Recolectando datos de {plat_str}..."):
            datos = collector.recolectar_todo(usuario)

        if datos["perfil"] and datos["publicaciones"]:
            metricas = calculador.calcular(datos["perfil"], datos["publicaciones"])
            todas_metricas.append(metricas)
            todos_comentarios.extend(datos["comentarios"])

    if not todas_metricas:
        consola.print("[red]No se obtuvieron datos para generar insights.[/red]")
        return

    with consola.status("Generando insight con IA..."):
        if tipo == "resumen":
            resultado = generador.resumen_ejecutivo(todas_metricas)
        elif tipo == "comparativo":
            comparador = Comparador()
            comp = comparador.comparar(todas_metricas)
            resultado = generador.analisis_comparativo(comp)
        elif tipo == "crecimiento":
            motor = MotorProyecciones()
            proyecciones = []
            for m in todas_metricas:
                # Usar publicaciones para proyectar engagement
                resultado_temp = motor.proyectar_engagement([], 0)
                proyecciones.append(resultado_temp)
            resultado = generador.recomendaciones_crecimiento(
                todas_metricas, proyecciones
            )
        elif tipo == "contenido":
            resultado = generador.analisis_contenido(todas_metricas)
        elif tipo == "sentimiento":
            resultado = generador.analisis_sentimiento_comentarios(todos_comentarios)
        else:
            resultado = generador.resumen_ejecutivo(todas_metricas)

    consola.print(
        Panel(
            resultado,
            title=f"Insight: {tipo.upper()}",
            border_style="yellow",
            padding=(1, 2),
        )
    )
