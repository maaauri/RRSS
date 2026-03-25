# RRSS - Agente de Análisis de Métricas para Redes Sociales

Herramienta de análisis de métricas, rendimiento y contenido para **Instagram**, **Facebook** y **TikTok**. Permite hacer análisis comparativos, proyecciones de crecimiento y obtener insights con inteligencia artificial — similar a herramientas como Metricool o Instrack, pero con control total y personalización.

## Características

- **Análisis de perfiles** en Instagram, Facebook y TikTok
- **Métricas de engagement** (likes, comentarios, compartidos, guardados)
- **Frecuencia de publicación** y mejores horarios para publicar
- **Rendimiento por tipo de contenido** (imágenes, videos, reels, carruseles)
- **Análisis de hashtags** (frecuencia y rendimiento)
- **Comentarios destacados** con análisis de sentimiento
- **Comparación entre perfiles y plataformas** con rankings y radar
- **Proyecciones de crecimiento** basadas en regresión lineal
- **Insights con IA** (OpenAI GPT-4o) — resúmenes ejecutivos, recomendaciones de estrategia
- **Dashboard interactivo** con Streamlit
- **CLI con Rich** para análisis rápidos desde la terminal
- **Exportación a CSV**

## Requisitos Previos

- Python 3.11 o superior
- (Opcional) Token de Meta Graph API para Instagram/Facebook
- (Opcional) Token de TikTok API for Business
- (Opcional) API Key de OpenAI para insights con IA

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/maaauri/RRSS.git
cd RRSS

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -e .

# Instalar dependencias de desarrollo (tests)
pip install -e ".[dev]"
```

## Configuración

Copia el archivo de ejemplo y completa tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

```env
# OpenAI (para insights con IA)
OPENAI_API_KEY=sk-tu-clave-aqui

# Meta Graph API (Instagram y Facebook)
META_ACCESS_TOKEN=tu-token
META_APP_ID=tu-app-id
META_APP_SECRET=tu-app-secret

# TikTok API for Business
TIKTOK_ACCESS_TOKEN=tu-token
TIKTOK_CLIENT_KEY=tu-client-key
TIKTOK_CLIENT_SECRET=tu-client-secret
```

> **Nota:** Sin tokens configurados, el sistema usa automáticamente las librerías de scraping como fallback para perfiles públicos.

## Uso

### CLI (Terminal)

```bash
# Analizar un perfil de Instagram
rrss analizar mi_marca -p instagram

# Analizar y guardar en la base de datos
rrss analizar mi_marca -p instagram --guardar

# Comparar perfiles entre plataformas
rrss comparar marca_a marca_b -p instagram -p tiktok

# Generar proyecciones de crecimiento
rrss proyectar mi_marca -p instagram --dias 30

# Generar reporte completo con exportación CSV
rrss reporte mi_marca -p instagram -p tiktok -o reporte.csv

# Generar insights con IA
rrss insight mi_marca -p instagram -t resumen
rrss insight mi_marca -p instagram -p tiktok -t comparativo
rrss insight mi_marca -p instagram -t crecimiento
rrss insight mi_marca -p instagram -t contenido
rrss insight mi_marca -p instagram -t sentimiento
```

### Dashboard (Streamlit)

```bash
streamlit run src/rrss/dashboard/app.py
```

El dashboard se abre en el navegador con las siguientes secciones:

| Página | Descripción |
|--------|-------------|
| **Vista General** | Análisis rápido de un perfil en múltiples plataformas |
| **Instagram** | Análisis detallado con top posts, hashtags y rendimiento por tipo |
| **Facebook** | Análisis de páginas con reacciones y tendencias |
| **TikTok** | Análisis de videos con vistas, engagement y hashtags |
| **Comparativa** | Comparación multi-perfil con gráficas radar y rankings |
| **Proyecciones** | Tendencias de engagement y frecuencia óptima de publicación |

## Arquitectura

```
src/rrss/
├── models/          # Modelos de datos (Pydantic)
│   ├── base.py      # Perfil, Publicacion, Comentario, MetricasPerfil
│   ├── instagram.py # Modelos específicos de Instagram
│   ├── facebook.py  # Modelos específicos de Facebook
│   └── tiktok.py    # Modelos específicos de TikTok
├── collectors/      # Recolectores de datos (API + scraping)
│   ├── base.py      # Interfaz abstracta CollectorBase
│   ├── instagram.py # Meta Graph API + instaloader
│   ├── facebook.py  # Meta Graph API + facebook-scraper
│   └── tiktok.py    # TikTok API + TikTokApi
├── storage/         # Persistencia
│   └── database.py  # SQLite con historial de métricas
├── analytics/       # Motor de análisis
│   ├── metrics.py   # Cálculo de engagement, frecuencia, hashtags
│   ├── comparator.py # Comparación entre perfiles/plataformas
│   └── projections.py # Regresión lineal y tendencias
├── ai/              # Inteligencia artificial
│   └── insights.py  # OpenAI GPT-4o para resúmenes y recomendaciones
├── cli/             # Interfaz de terminal
│   └── app.py       # Click + Rich
└── dashboard/       # Interfaz web
    ├── app.py       # Streamlit app principal
    ├── pages/       # Páginas del dashboard
    └── components/  # Gráficas (Plotly) y tarjetas de KPIs
```

### Flujo de datos

```
Plataformas (APIs/Scraping)
    ↓
Collectors (normalización)
    ↓
Modelos Pydantic
    ↓
SQLite (persistencia)
    ↓
Analytics Engine (métricas, comparaciones, proyecciones)
    ↓
AI Insights (OpenAI) ← opcional
    ↓
CLI (Rich) / Dashboard (Streamlit)
```

## Métricas Analizadas

### Por Perfil
- **Engagement Rate** — (likes + comentarios + compartidos + guardados) / seguidores × 100
- **Likes, Comentarios, Compartidos Promedio** por publicación
- **Frecuencia de Publicación** — publicaciones por semana
- **Mejor Día y Hora** para publicar (basado en engagement histórico)
- **Rendimiento por Tipo de Contenido** — imagen, video, carrusel, reel
- **Top Publicaciones** por engagement rate
- **Hashtags** — frecuencia de uso y engagement promedio por hashtag

### Comparativo
- Engagement normalizado entre plataformas
- Rankings de seguidores, engagement y frecuencia
- Mejor tipo de contenido global
- Gráfica radar multi-dimensional
- Recomendaciones automáticas

### Proyecciones
- Tendencia de engagement (crecimiento/estable/decrecimiento)
- Tasa de cambio semanal
- Valor proyectado a N días (regresión lineal)
- Coeficiente de confianza (R²)
- Frecuencia óptima de publicación
- Correlación frecuencia-engagement

## Fuentes de Datos

| Plataforma | API Oficial | Fallback (Scraping) |
|------------|-------------|---------------------|
| Instagram | Meta Graph API (requiere cuenta Business/Creator) | instaloader (perfiles públicos) |
| Facebook | Meta Graph API (requiere Page Token) | facebook-scraper (páginas públicas) |
| TikTok | TikTok API for Business (requiere OAuth) | TikTokApi no oficial (perfiles públicos) |

El sistema intenta usar la API oficial primero. Si no hay token configurado o la API falla, usa automáticamente la librería de scraping como fallback.

## Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --tb=short -v
```

## Dependencias Principales

| Paquete | Uso |
|---------|-----|
| `streamlit` | Dashboard web interactivo |
| `plotly` | Gráficas interactivas |
| `rich` + `click` | CLI con colores y tablas |
| `pydantic` | Validación de modelos de datos |
| `pandas` + `numpy` | Análisis numérico y proyecciones |
| `httpx` | Cliente HTTP para APIs oficiales |
| `openai` | Insights con IA (GPT-4o) |
| `instaloader` | Scraping de Instagram |
| `facebook-scraper` | Scraping de Facebook |
| `TikTokApi` | Scraping de TikTok |

## Licencia

MIT
