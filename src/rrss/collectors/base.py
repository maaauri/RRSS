"""Clase base abstracta para los collectors de cada plataforma."""

from abc import ABC, abstractmethod
from typing import Optional

from rrss.models.base import Comentario, Perfil, Plataforma, Publicacion


class CollectorBase(ABC):
    """Interfaz base para recolectores de datos de redes sociales.

    Cada plataforma implementa esta interfaz con su propia lógica
    de obtención de datos (API oficial o scraping).
    """

    plataforma: Plataforma

    @abstractmethod
    def obtener_perfil(self, nombre_usuario: str) -> Optional[Perfil]:
        """Obtener información del perfil de un usuario.

        Args:
            nombre_usuario: Nombre de usuario o ID del perfil.

        Returns:
            Perfil con los datos del usuario, o None si no se encontró.
        """
        ...

    @abstractmethod
    def obtener_publicaciones(
        self,
        nombre_usuario: str,
        limite: int = 50,
    ) -> list[Publicacion]:
        """Obtener las publicaciones recientes de un perfil.

        Args:
            nombre_usuario: Nombre de usuario o ID del perfil.
            limite: Número máximo de publicaciones a obtener.

        Returns:
            Lista de publicaciones ordenadas por fecha (más reciente primero).
        """
        ...

    @abstractmethod
    def obtener_comentarios(
        self,
        publicacion_id: str,
        limite: int = 50,
    ) -> list[Comentario]:
        """Obtener comentarios de una publicación.

        Args:
            publicacion_id: ID de la publicación.
            limite: Número máximo de comentarios.

        Returns:
            Lista de comentarios ordenados por relevancia.
        """
        ...

    def recolectar_todo(
        self,
        nombre_usuario: str,
        limite_publicaciones: int = 50,
        limite_comentarios: int = 20,
    ) -> dict:
        """Recolectar todos los datos de un perfil.

        Returns:
            Diccionario con perfil, publicaciones y comentarios.
        """
        perfil = self.obtener_perfil(nombre_usuario)
        if not perfil:
            return {"perfil": None, "publicaciones": [], "comentarios": []}

        publicaciones = self.obtener_publicaciones(nombre_usuario, limite_publicaciones)

        todos_comentarios = []
        for pub in publicaciones[:10]:  # Comentarios solo de las 10 más recientes
            if pub.id:
                comentarios = self.obtener_comentarios(pub.id, limite_comentarios)
                todos_comentarios.extend(comentarios)

        return {
            "perfil": perfil,
            "publicaciones": publicaciones,
            "comentarios": todos_comentarios,
        }
