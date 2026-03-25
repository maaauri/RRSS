"""Gestor de base de datos SQLite para almacenar métricas y perfiles."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from rrss.models.base import (
    Comentario,
    MetricasPerfil,
    Perfil,
    Plataforma,
    Publicacion,
    TipoContenido,
)


class BaseDatos:
    """Gestor de la base de datos SQLite."""

    def __init__(self, ruta_db: str | Path = "data/rrss.db"):
        self.ruta_db = Path(ruta_db)
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self._crear_tablas()

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.ruta_db))
        conn.row_factory = sqlite3.Row
        return conn

    def _crear_tablas(self):
        """Crear las tablas si no existen."""
        conn = self._conectar()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS perfiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_usuario TEXT NOT NULL,
                    nombre_completo TEXT DEFAULT '',
                    plataforma TEXT NOT NULL,
                    seguidores INTEGER DEFAULT 0,
                    siguiendo INTEGER DEFAULT 0,
                    total_publicaciones INTEGER DEFAULT 0,
                    biografia TEXT DEFAULT '',
                    url_avatar TEXT DEFAULT '',
                    es_verificado BOOLEAN DEFAULT 0,
                    fecha_recoleccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nombre_usuario, plataforma, fecha_recoleccion)
                );

                CREATE TABLE IF NOT EXISTS publicaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_externo TEXT,
                    perfil_usuario TEXT NOT NULL,
                    plataforma TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    texto TEXT DEFAULT '',
                    hashtags TEXT DEFAULT '[]',
                    likes INTEGER DEFAULT 0,
                    comentarios INTEGER DEFAULT 0,
                    compartidos INTEGER DEFAULT 0,
                    guardados INTEGER DEFAULT 0,
                    vistas INTEGER DEFAULT 0,
                    alcance INTEGER DEFAULT 0,
                    impresiones INTEGER DEFAULT 0,
                    url TEXT DEFAULT '',
                    fecha_publicacion TIMESTAMP,
                    fecha_recoleccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(id_externo, plataforma)
                );

                CREATE TABLE IF NOT EXISTS comentarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_externo TEXT,
                    publicacion_id TEXT NOT NULL,
                    plataforma TEXT NOT NULL,
                    autor TEXT DEFAULT '',
                    texto TEXT DEFAULT '',
                    likes INTEGER DEFAULT 0,
                    respuestas INTEGER DEFAULT 0,
                    fecha TIMESTAMP,
                    sentimiento TEXT
                );

                CREATE TABLE IF NOT EXISTS metricas_perfil (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_usuario TEXT NOT NULL,
                    plataforma TEXT NOT NULL,
                    periodo_inicio TIMESTAMP NOT NULL,
                    periodo_fin TIMESTAMP NOT NULL,
                    datos TEXT NOT NULL,
                    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_perfiles_usuario
                    ON perfiles(nombre_usuario, plataforma);
                CREATE INDEX IF NOT EXISTS idx_publicaciones_usuario
                    ON publicaciones(perfil_usuario, plataforma);
                CREATE INDEX IF NOT EXISTS idx_publicaciones_fecha
                    ON publicaciones(fecha_publicacion);
                CREATE INDEX IF NOT EXISTS idx_comentarios_pub
                    ON comentarios(publicacion_id);
            """)
            conn.commit()
        finally:
            conn.close()

    # --- Perfiles ---

    def guardar_perfil(self, perfil: Perfil):
        """Guardar o actualizar un perfil."""
        conn = self._conectar()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO perfiles
                   (nombre_usuario, nombre_completo, plataforma, seguidores,
                    siguiendo, total_publicaciones, biografia, url_avatar,
                    es_verificado, fecha_recoleccion)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    perfil.nombre_usuario,
                    perfil.nombre_completo,
                    perfil.plataforma.value,
                    perfil.seguidores,
                    perfil.siguiendo,
                    perfil.total_publicaciones,
                    perfil.biografia,
                    perfil.url_avatar,
                    perfil.es_verificado,
                    perfil.fecha_recoleccion.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def obtener_perfiles(
        self,
        nombre_usuario: str,
        plataforma: Optional[Plataforma] = None,
    ) -> list[Perfil]:
        """Obtener historial de perfiles."""
        conn = self._conectar()
        try:
            if plataforma:
                filas = conn.execute(
                    """SELECT * FROM perfiles
                       WHERE nombre_usuario = ? AND plataforma = ?
                       ORDER BY fecha_recoleccion DESC""",
                    (nombre_usuario, plataforma.value),
                ).fetchall()
            else:
                filas = conn.execute(
                    """SELECT * FROM perfiles
                       WHERE nombre_usuario = ?
                       ORDER BY fecha_recoleccion DESC""",
                    (nombre_usuario,),
                ).fetchall()

            return [
                Perfil(
                    id=str(f["id"]),
                    nombre_usuario=f["nombre_usuario"],
                    nombre_completo=f["nombre_completo"],
                    plataforma=Plataforma(f["plataforma"]),
                    seguidores=f["seguidores"],
                    siguiendo=f["siguiendo"],
                    total_publicaciones=f["total_publicaciones"],
                    biografia=f["biografia"],
                    url_avatar=f["url_avatar"],
                    es_verificado=bool(f["es_verificado"]),
                    fecha_recoleccion=datetime.fromisoformat(f["fecha_recoleccion"]),
                )
                for f in filas
            ]
        finally:
            conn.close()

    # --- Publicaciones ---

    def guardar_publicacion(self, pub: Publicacion):
        """Guardar una publicación."""
        conn = self._conectar()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO publicaciones
                   (id_externo, perfil_usuario, plataforma, tipo, texto, hashtags,
                    likes, comentarios, compartidos, guardados, vistas, alcance,
                    impresiones, url, fecha_publicacion, fecha_recoleccion)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pub.id,
                    pub.perfil_usuario,
                    pub.plataforma.value,
                    pub.tipo.value,
                    pub.texto,
                    json.dumps(pub.hashtags),
                    pub.likes,
                    pub.comentarios,
                    pub.compartidos,
                    pub.guardados,
                    pub.vistas,
                    pub.alcance,
                    pub.impresiones,
                    pub.url,
                    pub.fecha_publicacion.isoformat() if pub.fecha_publicacion else None,
                    pub.fecha_recoleccion.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def guardar_publicaciones(self, publicaciones: list[Publicacion]):
        """Guardar múltiples publicaciones."""
        for pub in publicaciones:
            self.guardar_publicacion(pub)

    def obtener_publicaciones(
        self,
        perfil_usuario: str,
        plataforma: Optional[Plataforma] = None,
        limite: int = 100,
    ) -> list[Publicacion]:
        """Obtener publicaciones de un perfil."""
        conn = self._conectar()
        try:
            if plataforma:
                filas = conn.execute(
                    """SELECT * FROM publicaciones
                       WHERE perfil_usuario = ? AND plataforma = ?
                       ORDER BY fecha_publicacion DESC LIMIT ?""",
                    (perfil_usuario, plataforma.value, limite),
                ).fetchall()
            else:
                filas = conn.execute(
                    """SELECT * FROM publicaciones
                       WHERE perfil_usuario = ?
                       ORDER BY fecha_publicacion DESC LIMIT ?""",
                    (perfil_usuario, limite),
                ).fetchall()

            return [
                Publicacion(
                    id=f["id_externo"],
                    perfil_usuario=f["perfil_usuario"],
                    plataforma=Plataforma(f["plataforma"]),
                    tipo=TipoContenido(f["tipo"]),
                    texto=f["texto"],
                    hashtags=json.loads(f["hashtags"]),
                    likes=f["likes"],
                    comentarios=f["comentarios"],
                    compartidos=f["compartidos"],
                    guardados=f["guardados"],
                    vistas=f["vistas"],
                    alcance=f["alcance"],
                    impresiones=f["impresiones"],
                    url=f["url"],
                    fecha_publicacion=(
                        datetime.fromisoformat(f["fecha_publicacion"])
                        if f["fecha_publicacion"]
                        else None
                    ),
                    fecha_recoleccion=datetime.fromisoformat(f["fecha_recoleccion"]),
                )
                for f in filas
            ]
        finally:
            conn.close()

    # --- Comentarios ---

    def guardar_comentario(self, comentario: Comentario):
        """Guardar un comentario."""
        conn = self._conectar()
        try:
            conn.execute(
                """INSERT INTO comentarios
                   (id_externo, publicacion_id, plataforma, autor, texto,
                    likes, respuestas, fecha, sentimiento)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    comentario.id,
                    comentario.publicacion_id,
                    comentario.plataforma.value,
                    comentario.autor,
                    comentario.texto,
                    comentario.likes,
                    comentario.respuestas,
                    comentario.fecha.isoformat() if comentario.fecha else None,
                    comentario.sentimiento,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def guardar_comentarios(self, comentarios: list[Comentario]):
        """Guardar múltiples comentarios."""
        for c in comentarios:
            self.guardar_comentario(c)

    def obtener_comentarios_destacados(
        self,
        publicacion_id: str,
        limite: int = 10,
    ) -> list[Comentario]:
        """Obtener los comentarios más relevantes de una publicación."""
        conn = self._conectar()
        try:
            filas = conn.execute(
                """SELECT * FROM comentarios
                   WHERE publicacion_id = ?
                   ORDER BY (likes + respuestas * 2) DESC
                   LIMIT ?""",
                (publicacion_id, limite),
            ).fetchall()

            return [
                Comentario(
                    id=f["id_externo"],
                    publicacion_id=f["publicacion_id"],
                    plataforma=Plataforma(f["plataforma"]),
                    autor=f["autor"],
                    texto=f["texto"],
                    likes=f["likes"],
                    respuestas=f["respuestas"],
                    fecha=(
                        datetime.fromisoformat(f["fecha"]) if f["fecha"] else None
                    ),
                    sentimiento=f["sentimiento"],
                )
                for f in filas
            ]
        finally:
            conn.close()

    # --- Métricas ---

    def guardar_metricas(self, metricas: MetricasPerfil):
        """Guardar métricas calculadas."""
        conn = self._conectar()
        try:
            conn.execute(
                """INSERT INTO metricas_perfil
                   (nombre_usuario, plataforma, periodo_inicio, periodo_fin,
                    datos, fecha_calculo)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    metricas.nombre_usuario,
                    metricas.plataforma.value,
                    metricas.periodo_inicio.isoformat(),
                    metricas.periodo_fin.isoformat(),
                    metricas.model_dump_json(),
                    metricas.fecha_calculo.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def obtener_metricas(
        self,
        nombre_usuario: str,
        plataforma: Plataforma,
    ) -> list[MetricasPerfil]:
        """Obtener historial de métricas de un perfil."""
        conn = self._conectar()
        try:
            filas = conn.execute(
                """SELECT datos FROM metricas_perfil
                   WHERE nombre_usuario = ? AND plataforma = ?
                   ORDER BY fecha_calculo DESC""",
                (nombre_usuario, plataforma.value),
            ).fetchall()

            return [MetricasPerfil.model_validate_json(f["datos"]) for f in filas]
        finally:
            conn.close()
