"""Collector de datos para Instagram.

Usa Meta Graph API como fuente principal y instaloader como fallback
para perfiles públicos.
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


class InstagramCollector(CollectorBase):
    """Recolector de datos de Instagram."""

    plataforma = Plataforma.INSTAGRAM

    def __init__(self):
        self._token = META_ACCESS_TOKEN
        self._usar_api = bool(self._token)
        if not self._usar_api:
            logger.info("Sin token de Meta. Usando instaloader como fallback.")

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
            logger.error(f"Error en API de Instagram: {e}")
            return None

    def _obtener_perfil_api(self, nombre_usuario: str) -> Optional[Perfil]:
        """Obtener perfil usando la Graph API (requiere ID de cuenta Business)."""
        # La Graph API necesita el ID de la cuenta de Instagram Business
        # Se asume que nombre_usuario es el ID numérico cuando se usa la API
        datos = self._api_get(
            nombre_usuario,
            params={
                "fields": "id,username,name,biography,followers_count,"
                "follows_count,media_count,profile_picture_url,is_verified"
            },
        )
        if not datos:
            return None

        return Perfil(
            id=datos.get("id"),
            nombre_usuario=datos.get("username", nombre_usuario),
            nombre_completo=datos.get("name", ""),
            plataforma=Plataforma.INSTAGRAM,
            seguidores=datos.get("followers_count", 0),
            siguiendo=datos.get("follows_count", 0),
            total_publicaciones=datos.get("media_count", 0),
            biografia=datos.get("biography", ""),
            url_avatar=datos.get("profile_picture_url", ""),
            es_verificado=datos.get("is_verified", False),
        )

    def _obtener_publicaciones_api(
        self, nombre_usuario: str, limite: int = 50
    ) -> list[Publicacion]:
        """Obtener publicaciones usando la Graph API."""
        datos = self._api_get(
            f"{nombre_usuario}/media",
            params={
                "fields": "id,caption,media_type,like_count,comments_count,"
                "timestamp,permalink,media_url",
                "limit": limite,
            },
        )
        if not datos or "data" not in datos:
            return []

        publicaciones = []
        for item in datos["data"]:
            tipo_mapa = {
                "IMAGE": TipoContenido.IMAGEN,
                "VIDEO": TipoContenido.VIDEO,
                "CAROUSEL_ALBUM": TipoContenido.CARRUSEL,
            }
            texto = item.get("caption", "")
            hashtags = re.findall(r"#(\w+)", texto)

            publicaciones.append(
                Publicacion(
                    id=item.get("id"),
                    perfil_usuario=nombre_usuario,
                    plataforma=Plataforma.INSTAGRAM,
                    tipo=tipo_mapa.get(item.get("media_type", ""), TipoContenido.IMAGEN),
                    texto=texto,
                    hashtags=hashtags,
                    likes=item.get("like_count", 0),
                    comentarios=item.get("comments_count", 0),
                    url=item.get("permalink", ""),
                    fecha_publicacion=datetime.fromisoformat(
                        item["timestamp"].replace("Z", "+00:00")
                    )
                    if item.get("timestamp")
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
                "fields": "id,text,username,like_count,replies{id,text,username,like_count,timestamp},timestamp",
                "limit": limite,
            },
        )
        if not datos or "data" not in datos:
            return []

        comentarios = []
        for item in datos["data"]:
            respuestas = item.get("replies", {}).get("data", [])
            comentarios.append(
                Comentario(
                    id=item.get("id"),
                    publicacion_id=publicacion_id,
                    plataforma=Plataforma.INSTAGRAM,
                    autor=item.get("username", ""),
                    texto=item.get("text", ""),
                    likes=item.get("like_count", 0),
                    respuestas=len(respuestas),
                    fecha=datetime.fromisoformat(
                        item["timestamp"].replace("Z", "+00:00")
                    )
                    if item.get("timestamp")
                    else None,
                )
            )
        return comentarios

    # --- Fallback con instaloader ---

    def _obtener_perfil_scraping(self, nombre_usuario: str) -> Optional[Perfil]:
        """Obtener perfil usando instaloader (perfiles públicos)."""
        try:
            import instaloader

            loader = instaloader.Instaloader()
            profile = instaloader.Profile.from_username(loader.context, nombre_usuario)

            return Perfil(
                id=str(profile.userid),
                nombre_usuario=profile.username,
                nombre_completo=profile.full_name,
                plataforma=Plataforma.INSTAGRAM,
                seguidores=profile.followers,
                siguiendo=profile.followees,
                total_publicaciones=profile.mediacount,
                biografia=profile.biography,
                url_avatar=profile.profile_pic_url,
                es_verificado=profile.is_verified,
            )
        except ImportError:
            logger.error("instaloader no está instalado.")
            return None
        except Exception as e:
            logger.error(f"Error al obtener perfil con instaloader: {e}")
            return None

    def _obtener_publicaciones_scraping(
        self, nombre_usuario: str, limite: int = 50
    ) -> list[Publicacion]:
        """Obtener publicaciones usando instaloader."""
        try:
            import instaloader

            loader = instaloader.Instaloader()
            profile = instaloader.Profile.from_username(loader.context, nombre_usuario)

            publicaciones = []
            for i, post in enumerate(profile.get_posts()):
                if i >= limite:
                    break

                if post.is_video:
                    tipo = TipoContenido.VIDEO
                elif post.typename == "GraphSidecar":
                    tipo = TipoContenido.CARRUSEL
                else:
                    tipo = TipoContenido.IMAGEN

                texto = post.caption or ""
                hashtags = re.findall(r"#(\w+)", texto)

                publicaciones.append(
                    Publicacion(
                        id=post.shortcode,
                        perfil_usuario=nombre_usuario,
                        plataforma=Plataforma.INSTAGRAM,
                        tipo=tipo,
                        texto=texto,
                        hashtags=hashtags,
                        likes=post.likes,
                        comentarios=post.comments,
                        vistas=post.video_view_count if post.is_video else 0,
                        url=f"https://www.instagram.com/p/{post.shortcode}/",
                        fecha_publicacion=post.date_utc,
                    )
                )
            return publicaciones
        except ImportError:
            logger.error("instaloader no está instalado.")
            return []
        except Exception as e:
            logger.error(f"Error al obtener publicaciones con instaloader: {e}")
            return []

    def _obtener_comentarios_scraping(
        self, publicacion_id: str, limite: int = 50
    ) -> list[Comentario]:
        """Obtener comentarios usando instaloader."""
        try:
            import instaloader

            loader = instaloader.Instaloader()
            post = instaloader.Post.from_shortcode(loader.context, publicacion_id)

            comentarios = []
            for i, comment in enumerate(post.get_comments()):
                if i >= limite:
                    break
                comentarios.append(
                    Comentario(
                        id=str(comment.id),
                        publicacion_id=publicacion_id,
                        plataforma=Plataforma.INSTAGRAM,
                        autor=comment.owner.username if comment.owner else "",
                        texto=comment.text,
                        likes=comment.likes_count,
                        respuestas=comment.answers.count if hasattr(comment, "answers") else 0,
                        fecha=comment.created_at_utc,
                    )
                )
            return comentarios
        except ImportError:
            logger.error("instaloader no está instalado.")
            return []
        except Exception as e:
            logger.error(f"Error al obtener comentarios con instaloader: {e}")
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
