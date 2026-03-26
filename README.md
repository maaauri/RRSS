# RRSS - Agente de Analisis de Metricas para Redes Sociales

Herramienta de analisis de metricas, rendimiento y contenido para **Instagram**, **Facebook** y **TikTok**. Permite hacer analisis comparativos, proyecciones de crecimiento y obtener insights con inteligencia artificial — similar a herramientas como Metricool o Instrack, pero con control total y personalizacion.

## Caracteristicas

- **Analisis de perfiles** en Instagram, Facebook y TikTok
- **Metricas de engagement** (likes, comentarios, compartidos, guardados)
- **Frecuencia de publicacion** y mejores horarios para publicar
- **Rendimiento por tipo de contenido** (imagenes, videos, reels, carruseles)
- **Analisis de hashtags** (frecuencia y rendimiento)
- **Comentarios destacados** con analisis de sentimiento
- **Comparacion entre perfiles y plataformas** con rankings y radar
- **Proyecciones de crecimiento** basadas en regresion lineal
- **Insights con IA** (OpenAI GPT-4o) — resumenes ejecutivos, recomendaciones de estrategia
- **Dashboard interactivo** con Streamlit
- **CLI con Rich** para analisis rapidos desde la terminal
- **Exportacion a CSV**

## Requisitos Previos

- Python 3.11 o superior
- (Opcional) Token de Meta Graph API para Instagram/Facebook
- (Opcional) Token de TikTok API for Business
- (Opcional) API Key de OpenAI para insights con IA

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/maaauri/RRSS.git
cd RRSS

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias core
pip install -e .

# Instalar scraping de Instagram (recomendado)
pip install -e ".[instagram]"

# Instalar todas las librerias de scraping
pip install -e ".[scraping]"

# Instalar dependencias de desarrollo (tests)
pip install -e ".[dev]"
```

## Configuracion

### 1. Variables de entorno

Copia el archivo de ejemplo y completa tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

```env
# OpenAI (para insights con IA)
OPENAI_API_KEY=sk-tu-clave-aqui

# Meta Graph API (Instagram y Facebook)
META_ACCESS_TOKEN=EAAxxxxxxxxx...
META_APP_ID=123456789
META_APP_SECRET=abc123def456

# TikTok API for Business
TIKTOK_ACCESS_TOKEN=tu-token
TIKTOK_CLIENT_KEY=tu-client-key
TIKTOK_CLIENT_SECRET=tu-client-secret

# Instaloader (para scraping con sesion autenticada)
INSTAGRAM_USERNAME=tu_usuario
```

### 2. Autenticacion en Instagram (scraping con instaloader)

Instagram bloquea peticiones anonimas (error 403). Para que el scraping funcione necesitas autenticarte:

```bash
# Paso 1: Crear sesion interactiva (una sola vez)
rrss login tu_usuario_instagram

# Paso 2: Configurar en .env
INSTAGRAM_USERNAME=tu_usuario_instagram
```

El comando `rrss login` pide la contrasena de forma segura y soporta 2FA. La sesion se guarda localmente y se reutiliza en todos los analisis.

> **Importante:** Usa una cuenta secundaria para el scraping, no tu cuenta principal. Si recibes error "Please wait a few minutes", espera 5-10 minutos (rate limiting temporal de Instagram).

### 3. Meta Graph API (opcional, para datos oficiales)

Para usar la API oficial de Instagram/Facebook en vez de scraping:

1. Ve a **developers.facebook.com** e inicia sesion
2. Click en **"Mis Apps"** → **"Crear App"** → tipo **"Empresa"**
3. Agrega el producto **"Instagram Graph API"**
4. **App ID y App Secret**: Configuracion → Basica
5. **Access Token**: Ve a **developers.facebook.com/tools/explorer/**
   - Selecciona tu app
   - Genera token con permisos: `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`
6. **Token de larga duracion (~60 dias)**: Visita en tu navegador:
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=TU_APP_ID&client_secret=TU_APP_SECRET&fb_exchange_token=TU_TOKEN_TEMPORAL
   ```
7. **Obtener tu Instagram Business Account ID**:
   - En el Graph API Explorer: `GET /me/accounts` → copia el `id` de tu pagina
   - Luego: `GET /{page_id}?fields=instagram_business_account` → ese `id` es el que usas

> **Requisito:** Tu cuenta de Instagram debe ser Business o Creator y estar conectada a una pagina de Facebook.

### Prioridad de autenticacion

El sistema usa las fuentes de datos en este orden:

| Prioridad | Metodo | Requisito |
|-----------|--------|-----------|
| 1 | Meta Graph API / TikTok API | Token valido en `.env` |
| 2 | Scraping autenticado | Sesion de instaloader (`rrss login`) |
| 3 | Scraping anonimo | Nada (puede dar error 403) |

## Uso

### CLI (Terminal)

```bash
# Iniciar sesion en Instagram (una sola vez)
rrss login mi_usuario

# Analizar un perfil de Instagram
rrss analizar mi_marca -p instagram

# Analizar con logs detallados
rrss -v analizar mi_marca -p instagram

# Analizar y guardar en la base de datos
rrss analizar mi_marca -p instagram --guardar

# Comparar perfiles entre plataformas
rrss comparar marca_a marca_b -p instagram -p tiktok

# Generar proyecciones de crecimiento
rrss proyectar mi_marca -p instagram --dias 30

# Generar reporte completo con exportacion CSV
rrss reporte mi_marca -p instagram -p tiktok -o reporte.csv

# Generar insights con IA (requiere OPENAI_API_KEY)
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

| Pagina | Descripcion |
|--------|-------------|
| **Vista General** | Analisis rapido de un perfil en multiples plataformas |
| **Instagram** | Analisis detallado con top posts, hashtags y rendimiento por tipo |
| **Facebook** | Analisis de paginas con reacciones y tendencias |
| **TikTok** | Analisis de videos con vistas, engagement y hashtags |
| **Comparativa** | Comparacion multi-perfil con graficas radar y rankings |
| **Proyecciones** | Tendencias de engagement y frecuencia optima de publicacion |

## Arquitectura

```
src/rrss/
├── models/          # Modelos de datos (Pydantic)
│   ├── base.py      # Perfil, Publicacion, Comentario, MetricasPerfil
│   ├── instagram.py # Modelos especificos de Instagram
│   ├── facebook.py  # Modelos especificos de Facebook
│   └── tiktok.py    # Modelos especificos de TikTok
├── collectors/      # Recolectores de datos (API + scraping)
│   ├── base.py      # Interfaz abstracta CollectorBase
│   ├── instagram.py # Meta Graph API + instaloader (con reintentos)
│   ├── facebook.py  # Meta Graph API + facebook-scraper
│   └── tiktok.py    # TikTok API + TikTokApi
├── storage/         # Persistencia
│   └── database.py  # SQLite con historial de metricas
├── analytics/       # Motor de analisis
│   ├── metrics.py   # Calculo de engagement, frecuencia, hashtags
│   ├── comparator.py # Comparacion entre perfiles/plataformas
│   └── projections.py # Regresion lineal y tendencias
├── ai/              # Inteligencia artificial
│   └── insights.py  # OpenAI GPT-4o para resumenes y recomendaciones
├── cli/             # Interfaz de terminal
│   └── app.py       # Click + Rich (incluye comando login)
└── dashboard/       # Interfaz web
    ├── app.py       # Streamlit app principal
    ├── pages/       # Paginas del dashboard
    └── components/  # Graficas (Plotly) y tarjetas de KPIs
```

### Flujo de datos

```
Plataformas (APIs/Scraping)
    ↓
Collectors (normalizacion + reintentos + rate limiting)
    ↓
Modelos Pydantic
    ↓
SQLite (persistencia)
    ↓
Analytics Engine (metricas, comparaciones, proyecciones)
    ↓
AI Insights (OpenAI) ← opcional
    ↓
CLI (Rich) / Dashboard (Streamlit)
```

## Metricas Analizadas

### Por Perfil
- **Engagement Rate** — (likes + comentarios + compartidos + guardados) / seguidores x 100
- **Likes, Comentarios, Compartidos Promedio** por publicacion
- **Frecuencia de Publicacion** — publicaciones por semana
- **Mejor Dia y Hora** para publicar (basado en engagement historico)
- **Rendimiento por Tipo de Contenido** — imagen, video, carrusel, reel
- **Top Publicaciones** por engagement rate
- **Hashtags** — frecuencia de uso y engagement promedio por hashtag

### Comparativo
- Engagement normalizado entre plataformas
- Rankings de seguidores, engagement y frecuencia
- Mejor tipo de contenido global
- Grafica radar multi-dimensional
- Recomendaciones automaticas

### Proyecciones
- Tendencia de engagement (crecimiento/estable/decrecimiento)
- Tasa de cambio semanal
- Valor proyectado a N dias (regresion lineal)
- Coeficiente de confianza (R2)
- Frecuencia optima de publicacion
- Correlacion frecuencia-engagement

## Fuentes de Datos

| Plataforma | API Oficial | Fallback (Scraping) |
|------------|-------------|---------------------|
| Instagram | Meta Graph API (cuenta Business/Creator) | instaloader (requiere sesion) |
| Facebook | Meta Graph API (Page Token) | facebook-scraper (paginas publicas) |
| TikTok | TikTok API for Business (OAuth) | TikTokApi no oficial (perfiles publicos) |

El sistema intenta usar la API oficial primero. Si no hay token configurado o la API falla, usa automaticamente la libreria de scraping como fallback.

## Solucion de Problemas

| Error | Causa | Solucion |
|-------|-------|----------|
| `403 Forbidden` | Instagram bloquea peticiones anonimas | Ejecuta `rrss login tu_usuario` |
| `Profile X does not exist` | Usuario incorrecto o sesion expirada | Verifica el @ exacto en instagram.com; renueva sesion con `rrss login` |
| `Please wait a few minutes` | Rate limiting temporal | Espera 5-10 minutos e intenta de nuevo |
| `Login error: "fail"` | Instagram bloqueo login automatico | Usa `rrss login` (interactivo) en vez de credenciales en `.env` |
| `No module named 'rrss'` | Paquete no instalado | Ejecuta `pip install -e .` |
| `instaloader no esta instalado` | Dependencia opcional faltante | Ejecuta `pip install -e ".[instagram]"` |

## Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/

# Con detalle
python -m pytest tests/ -v --tb=short
```

## Dependencias

### Core (se instalan con `pip install -e .`)

| Paquete | Uso |
|---------|-----|
| `streamlit` | Dashboard web interactivo |
| `plotly` | Graficas interactivas |
| `rich` + `click` | CLI con colores y tablas |
| `pydantic` | Validacion de modelos de datos |
| `pandas` + `numpy` | Analisis numerico y proyecciones |
| `httpx` | Cliente HTTP para APIs oficiales |
| `openai` | Insights con IA (GPT-4o) |

### Opcionales (scraping)

| Paquete | Instalacion | Uso |
|---------|-------------|-----|
| `instaloader` | `pip install -e ".[instagram]"` | Scraping de Instagram |
| `facebook-scraper` | `pip install -e ".[facebook]"` | Scraping de Facebook |
| `TikTokApi` | `pip install -e ".[tiktok]"` | Scraping de TikTok |

## Licencia

MIT
