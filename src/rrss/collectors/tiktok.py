"""Collector de datos para TikTok.

Usa la API oficial de TikTok for Business como fuente principal
y TikTokApi (no oficial) como fallback.
"""

import logging
import re
from datetime import datetime
from typing import Optional

import httpx

from rrss.config import TIKTOK_ACCESS_TOKEN, TIKTOK_BASE_URL
from rrss.models.base import Comentario, Perfil, Plataforma, Publicacion, TipoContenido
from rrss.collectors.base import CollectorBase

logger = logging.getLogger(__name__)


class TikTokCollector(CollectorBase):
    """Recolector de datos de TikTok."""

    plataforma = Plataforma.TIKTOK

    def __init__(self):
        self._token = TIKTOK_ACCESS_TOKEN
        self._usar_api = bool(self._token)
        if not self._usar_api:
            logger.info("Sin token de TikTok. Usando TikTokApi como fallback.")

    # --- API Oficial (TikTok for Business) ---

    def _api_post(self, endpoint: str, datos: Optional[dict] = None) -> Optional[dict]:
        """Hacer una petición POST a la API de TikTok."""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        try:
            resp = httpx.post(
                f"{TIKTOK_BASE_URL}/{endpoint}",
                headers=headers,
                json=datos or {},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Error en API de TikTok: {e}")
            return None

    def _obtener_perfil_api(self, nombre_usuario: str) -> Optional[Perfil]:
        """Obtener perfil usando la API oficial de TikTok."""
        datos = self._api_post(
            "user/info/",
            datos={
                "fields": [
                    "display_name",
                    "follower_count",
                    "following_count",
                    "video_count",
                    "bio_description",
                    "avatar_url",
                    "is_verified",
                    "likes_count",
                ]
            },
        )
        if not datos or "data" not in datos:
            return None

        user = datos["data"].get("user", {})
        return Perfil(
            id=user.get("open_id", ""),
            nombre_usuario=nombre_usuario,
            nombre_completo=user.get("display_name", ""),
            plataforma=Plataforma.TIKTOK,
            seguidores=user.get("follower_count", 0),
            siguiendo=user.get("following_count", 0),
            total_publicaciones=user.get("video_count", 0),
            biografia=user.get("bio_description", ""),
            url_avatar=user.get("avatar_url", ""),
            es_verificado=user.get("is_verified", False),
        )

    def _obtener_publicaciones_api(
        self, nombre_usuario: str, limite: int = 50
    ) -> list[Publicacion]:
        """Obtener videos usando la API oficial."""
        datos = self._api_post(
            "video/list/",
            datos={
                "max_count": min(limite, 20),
                "fields": [
                    "id",
                    "title",
                    "create_time",
                    "like_count",
                    "comment_count",
                    "share_count",
                    "view_count",
                    "video_description",
                    "share_url",
                ],
            },
        )
        if not datos or "data" not in datos:
            return []

        publicaciones = []
        for video in datos["data"].get("videos", []):
            texto = video.get("video_description", "") or video.get("title", "")
            hashtags = re.findall(r"#(\w+)", texto)

            publicaciones.append(
                Publicacion(
                    id=video.get("id"),
                    perfil_usuario=nombre_usuario,
                    plataforma=Plataforma.TIKTOK,
                    tipo=TipoContenido.VIDEO,
                    texto=texto,
                    hashtags=hashtags,
                    likes=video.get("like_count", 0),
                    comentarios=video.get("comment_count", 0),
                    compartidos=video.get("share_count", 0),
                    vistas=video.get("view_count", 0),
                    url=video.get("share_url", ""),
                    fecha_publicacion=datetime.fromtimestamp(video["create_time"])
                    if video.get("create_time")
                    else None,
                )
            )
        return publicaciones

    def _obtener_comentarios_api(
        self, publicacion_id: str, limite: int = 50
    ) -> list[Comentario]:
        """Obtener comentarios de un video usando la API oficial."""
        datos = self._api_post(
            "video/comment/list/",
            datos={
                "video_id": publicacion_id,
                "max_count": min(limite, 50),
                "fields": [
                    "id",
                    "text",
                    "like_count",
                    "reply_count",
                    "create_time",
                    "user",
                ],
            },
        )
        if not datos or "data" not in datos:
            return []

        comentarios = []
        for item in datos["data"].get("comments", []):
            comentarios.append(
                Comentario(
                    id=item.get("id"),
                    publicacion_id=publicacion_id,
                    plataforma=Plataforma.TIKTOK,
                    autor=item.get("user", {}).get("display_name", ""),
                    texto=item.get("text", ""),
                    likes=item.get("like_count", 0),
                    respuestas=item.get("reply_count", 0),
                    fecha=datetime.fromtimestamp(item["create_time"])
                    if item.get("create_time")
                    else None,
                )
            )
        return comentarios

    # --- Fallback con TikTokApi (no oficial) ---

    def _obtener_perfil_scraping(self, nombre_usuario: str) -> Optional[Perfil]:
        """Obtener perfil usando TikTokApi (no oficial)."""
        try:
            from TikTokApi import TikTokApi

            with TikTokApi() as api:
                user = api.user(username=nombre_usuario)
                info = user.info()
                stats = info.get("stats", {})
                user_data = info.get("user", {})

                return Perfil(
                    id=user_data.get("id", ""),
                    nombre_usuario=nombre_usuario,
                    nombre_completo=user_data.get("nickname", ""),
                    plataforma=Plataforma.TIKTOK,
                    seguidores=stats.get("followerCount", 0),
                    siguiendo=stats.get("followingCount", 0),
                    total_publicaciones=stats.get("videoCount", 0),
                    biografia=user_data.get("signature", ""),
                    url_avatar=user_data.get("avatarLarger", ""),
                    es_verificado=user_data.get("verified", False),
                )
        except ImportError:
            logger.error("TikTokApi no está instalado.")
            return None
        except Exception as e:
            logger.error(f"Error al obtener perfil de TikTok con scraping: {e}")
            return None

    def _obtener_publicaciones_scraping(
        self, nombre_usuario: str, limite: int = 50
    ) -> list[Publicacion]:
        """Obtener videos usando TikTokApi (no oficial)."""
        try:
            from TikTokApi import TikTokApi

            with TikTokApi() as api:
                user = api.user(username=nombre_usuario)
                publicaciones = []

                for i, video in enumerate(user.videos(count=limite)):
                    if i >= limite:
                        break

                    info = video.info() if hasattr(video, "info") else video.as_dict
                    texto = info.get("desc", "")
                    hashtags = re.findall(r"#(\w+)", texto)
                    stats = info.get("stats", {})

                    publicaciones.append(
                        Publicacion(
                            id=info.get("id"),
                            perfil_usuario=nombre_usuario,
                            plataforma=Plataforma.TIKTOK,
                            tipo=TipoContenido.VIDEO,
                            texto=texto,
                            hashtags=hashtags,
                            likes=stats.get("diggCount", 0),
                            comentarios=stats.get("commentCount", 0),
                            compartidos=stats.get("shareCount", 0),
                            vistas=stats.get("playCount", 0),
                            url=f"https://www.tiktok.com/@{nombre_usuario}/video/{info.get('id', '')}",
                            fecha_publicacion=datetime.fromtimestamp(info["createTime"])
                            if info.get("createTime")
                            else None,
                        )
                    )
                return publicaciones
        except ImportError:
            logger.error("TikTokApi no está instalado.")
            return []
        except Exception as e:
            logger.error(f"Error al obtener videos de TikTok con scraping: {e}")
            return []

    def _obtener_comentarios_scraping(
        self, publicacion_id: str, limite: int = 50
    ) -> list[Comentario]:
        """Obtener comentarios con TikTokApi (limitado)."""
        try:
            from TikTokApi import TikTokApi

            with TikTokApi() as api:
                video = api.video(id=publicacion_id)
                comentarios = []

                for i, comment in enumerate(video.comments(count=limite)):
                    if i >= limite:
                        break
                    info = comment.as_dict if hasattr(comment, "as_dict") else {}
                    comentarios.append(
                        Comentario(
                            id=info.get("cid", ""),
                            publicacion_id=publicacion_id,
                            plataforma=Plataforma.TIKTOK,
                            autor=info.get("user", {}).get("nickname", ""),
                            texto=info.get("text", ""),
                            likes=info.get("digg_count", 0),
                            respuestas=info.get("reply_comment_total", 0),
                            fecha=datetime.fromtimestamp(info["create_time"])
                            if info.get("create_time")
                            else None,
                        )
                    )
                return comentarios
        except ImportError:
            logger.error("TikTokApi no está instalado.")
            return []
        except Exception as e:
            logger.error(f"Error al obtener comentarios de TikTok con scraping: {e}")
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
