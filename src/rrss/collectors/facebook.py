"""Collector de datos para Facebook.

Usa Meta Graph API como fuente principal y facebook-scraper como fallback.
"""

import logging
import re
from datetime import datetime
from typing import Optional

import httpx

from rrss.config import META_ACCESS_TOKEN, META_BASE_URL
from rrss.models.base import Comentario, Perfil, Plataforma, Publicacion, TipoContenido
from rrss.collectors.base import CollectorBase

logger = logging.getLogger(__name__)


class FacebookCollector(CollectorBase):
    """Recolector de datos de Facebook (páginas públicas)."""

    plataforma = Plataforma.FACEBOOK

    def __init__(self):
        self._token = META_ACCESS_TOKEN
        self._usar_api = bool(self._token)
        if not self._usar_api:
            logger.info("Sin token de Meta. Usando facebook-scraper como fallback.")

    # --- API Oficial (Meta Graph API) ---

    def _api_get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Hacer una petición GET a la Graph API."""
        params = params or {}
        params["access_token"] = self._token
        try:
            resp = httpx.get(f"{META_BASE_URL}/{endpoint}", params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Error en API de Facebook: {e}")
            return None

    def _obtener_perfil_api(self, page_id: str) -> Optional[Perfil]:
        """Obtener perfil de página usando la Graph API."""
        datos = self._api_get(
            page_id,
            params={
                "fields": "id,name,username,about,fan_count,followers_count,"
                "is_verified,picture{url}"
            },
        )
        if not datos:
            return None

        return Perfil(
            id=datos.get("id"),
            nombre_usuario=datos.get("username", page_id),
            nombre_completo=datos.get("name", ""),
            plataforma=Plataforma.FACEBOOK,
            seguidores=datos.get("followers_count", datos.get("fan_count", 0)),
            biografia=datos.get("about", ""),
            url_avatar=datos.get("picture", {}).get("data", {}).get("url", ""),
            es_verificado=datos.get("is_verified", False),
        )

    def _obtener_publicaciones_api(
        self, page_id: str, limite: int = 50
    ) -> list[Publicacion]:
        """Obtener publicaciones de página usando la Graph API."""
        datos = self._api_get(
            f"{page_id}/posts",
            params={
                "fields": "id,message,created_time,type,permalink_url,"
                "likes.summary(true),comments.summary(true),"
                "shares",
                "limit": limite,
            },
        )
        if not datos or "data" not in datos:
            return []

        publicaciones = []
        for item in datos["data"]:
            tipo_mapa = {
                "photo": TipoContenido.IMAGEN,
                "video": TipoContenido.VIDEO,
                "link": TipoContenido.TEXTO,
                "status": TipoContenido.TEXTO,
            }
            texto = item.get("message", "")
            hashtags = re.findall(r"#(\w+)", texto)

            publicaciones.append(
                Publicacion(
                    id=item.get("id"),
                    perfil_usuario=page_id,
                    plataforma=Plataforma.FACEBOOK,
                    tipo=tipo_mapa.get(item.get("type", ""), TipoContenido.TEXTO),
                    texto=texto,
                    hashtags=hashtags,
                    likes=item.get("likes", {}).get("summary", {}).get("total_count", 0),
                    comentarios=item.get("comments", {})
                    .get("summary", {})
                    .get("total_count", 0),
                    compartidos=item.get("shares", {}).get("count", 0),
                    url=item.get("permalink_url", ""),
                    fecha_publicacion=datetime.fromisoformat(
                        item["created_time"].replace("Z", "+00:00")
                    )
                    if item.get("created_time")
                    else None,
                )
            )
        return publicaciones

    def _obtener_comentarios_api(
        self, publicacion_id: str, limite: int = 50
    ) -> list[Comentario]:
        """Obtener comentarios usando la Graph API."""
        datos = self._api_get(
            f"{publicacion_id}/comments",
            params={
                "fields": "id,message,from,like_count,comment_count,created_time",
                "limit": limite,
                "order": "reverse_chronological",
            },
        )
        if not datos or "data" not in datos:
            return []

        comentarios = []
        for item in datos["data"]:
            comentarios.append(
                Comentario(
                    id=item.get("id"),
                    publicacion_id=publicacion_id,
                    plataforma=Plataforma.FACEBOOK,
                    autor=item.get("from", {}).get("name", ""),
                    texto=item.get("message", ""),
                    likes=item.get("like_count", 0),
                    respuestas=item.get("comment_count", 0),
                    fecha=datetime.fromisoformat(
                        item["created_time"].replace("Z", "+00:00")
                    )
                    if item.get("created_time")
                    else None,
                )
            )
        return comentarios

    # --- Fallback con facebook-scraper ---

    def _obtener_perfil_scraping(self, nombre_usuario: str) -> Optional[Perfil]:
        """Obtener perfil usando facebook-scraper."""
        try:
            from facebook_scraper import get_profile

            datos = get_profile(nombre_usuario)
            if not datos:
                return None

            return Perfil(
                id=str(datos.get("id", "")),
                nombre_usuario=nombre_usuario,
                nombre_completo=datos.get("Name", ""),
                plataforma=Plataforma.FACEBOOK,
                seguidores=datos.get("Followers", 0) or 0,
                siguiendo=datos.get("Following", 0) or 0,
                biografia=datos.get("About", ""),
                url_avatar=datos.get("profile_picture", ""),
            )
        except ImportError:
            logger.error("facebook-scraper no está instalado.")
            return None
        except Exception as e:
            logger.error(f"Error al obtener perfil con facebook-scraper: {e}")
            return None

    def _obtener_publicaciones_scraping(
        self, nombre_usuario: str, limite: int = 50
    ) -> list[Publicacion]:
        """Obtener publicaciones usando facebook-scraper."""
        try:
            from facebook_scraper import get_posts

            publicaciones = []
            for i, post in enumerate(
                get_posts(nombre_usuario, pages=max(1, limite // 10))
            ):
                if i >= limite:
                    break

                texto = post.get("text", "") or ""
                hashtags = re.findall(r"#(\w+)", texto)

                # Determinar tipo
                if post.get("video"):
                    tipo = TipoContenido.VIDEO
                elif post.get("images"):
                    tipo = TipoContenido.IMAGEN
                else:
                    tipo = TipoContenido.TEXTO

                publicaciones.append(
                    Publicacion(
                        id=post.get("post_id"),
                        perfil_usuario=nombre_usuario,
                        plataforma=Plataforma.FACEBOOK,
                        tipo=tipo,
                        texto=texto,
                        hashtags=hashtags,
                        likes=post.get("likes", 0) or 0,
                        comentarios=post.get("comments", 0) or 0,
                        compartidos=post.get("shares", 0) or 0,
                        url=post.get("post_url", ""),
                        fecha_publicacion=post.get("time"),
                    )
                )
            return publicaciones
        except ImportError:
            logger.error("facebook-scraper no está instalado.")
            return []
        except Exception as e:
            logger.error(f"Error al obtener publicaciones con facebook-scraper: {e}")
            return []

    def _obtener_comentarios_scraping(
        self, publicacion_id: str, limite: int = 50
    ) -> list[Comentario]:
        """Obtener comentarios con scraping (limitado)."""
        # facebook-scraper no ofrece extracción directa de comentarios robusta
        logger.warning(
            "La extracción de comentarios con scraping en Facebook es limitada."
        )
        return []

    # --- Interfaz pública ---

    def obtener_perfil(self, nombre_usuario: str) -> Optional[Perfil]:
        if self._usar_api:
            resultado = self._obtener_perfil_api(nombre_usuario)
            if resultado:
                return resultado
            logger.info("API falló, intentando con scraping...")
        return self._obtener_perfil_scraping(nombre_usuario)

    def obtener_publicaciones(
        self, nombre_usuario: str, limite: int = 50
    ) -> list[Publicacion]:
        if self._usar_api:
            resultado = self._obtener_publicaciones_api(nombre_usuario, limite)
            if resultado:
                return resultado
            logger.info("API falló, intentando con scraping...")
        return self._obtener_publicaciones_scraping(nombre_usuario, limite)

    def obtener_comentarios(
        self, publicacion_id: str, limite: int = 50
    ) -> list[Comentario]:
        if self._usar_api:
            resultado = self._obtener_comentarios_api(publicacion_id, limite)
            if resultado:
                return resultado
            logger.info("API falló, intentando con scraping...")
        return self._obtener_comentarios_scraping(publicacion_id, limite)
