"""Modelos de datos de BLACKCAT (SQLite via SQLAlchemy).

Entidades:
  - Caso: la investigacion OSINT (con alcance y autorizacion).
  - Hallazgo: cada dato/evidencia recolectada dentro de un caso.
  - Adjunto: archivos (imagenes) asociados a un hallazgo, con su hash.
  - PerfilDestinatario: define COMO se arma el informe para cada publico
    (que secciones, nivel de detalle, que sensibilidad se incluye).
  - RegistroActividad: auditoria liviana (util en modo colaborativo).
"""
from __future__ import annotations

from datetime import datetime, timezone

from .db import db


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


# Valores controlados (whitelists de dominio) -------------------------------
CLASIFICACIONES = ("publico", "interno", "confidencial", "reservado")
ESTADOS_CASO = ("abierto", "en_curso", "cerrado")
CATEGORIAS_HALLAZGO = (
    "persona", "organizacion", "dominio", "infraestructura",
    "red_social", "documento", "ubicacion", "otro",
)
NIVELES_CONFIANZA = ("confirmado", "probable", "sin_verificar")
NIVELES_SENSIBILIDAD = ("normal", "sensible", "interno")

# Orden para comparaciones (mayor = mas restringido)
_ORDEN_CONFIANZA = {"sin_verificar": 0, "probable": 1, "confirmado": 2}
_ORDEN_SENSIBILIDAD = {"normal": 0, "sensible": 1, "interno": 2}


class Caso(db.Model):
    __tablename__ = "casos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), unique=True, nullable=False, index=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, default="")
    objetivo = db.Column(db.Text, default="")            # alcance de la investigacion
    autorizacion = db.Column(db.Text, default="")        # base legal / permiso (etica)
    investigador = db.Column(db.String(120), default="")
    clasificacion = db.Column(db.String(20), default="interno")
    estado = db.Column(db.String(20), default="abierto")
    creado = db.Column(db.DateTime, default=_ahora)
    modificado = db.Column(db.DateTime, default=_ahora, onupdate=_ahora)

    hallazgos = db.relationship(
        "Hallazgo", back_populates="caso",
        cascade="all, delete-orphan", order_by="Hallazgo.numero",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "titulo": self.titulo,
            "descripcion": self.descripcion or "",
            "objetivo": self.objetivo or "",
            "autorizacion": self.autorizacion or "",
            "investigador": self.investigador or "",
            "clasificacion": self.clasificacion,
            "estado": self.estado,
            "creado": self.creado.isoformat() if self.creado else None,
            "modificado": self.modificado.isoformat() if self.modificado else None,
        }


class Hallazgo(db.Model):
    __tablename__ = "hallazgos"

    id = db.Column(db.Integer, primary_key=True)
    caso_id = db.Column(db.Integer, db.ForeignKey("casos.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    numero = db.Column(db.Integer, nullable=False)        # secuencial dentro del caso
    titulo = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(30), default="otro")
    fuente = db.Column(db.String(300), default="")
    url = db.Column(db.String(1000), default="")
    contenido = db.Column(db.Text, default="")
    fecha_dato = db.Column(db.DateTime)                   # fecha del dato (no de carga)
    confianza = db.Column(db.String(20), default="sin_verificar")
    sensibilidad = db.Column(db.String(20), default="normal")
    autor = db.Column(db.String(120), default="")         # quien lo cargo
    hash_evidencia = db.Column(db.String(64), default="") # sha256 del contenido
    creado = db.Column(db.DateTime, default=_ahora)

    caso = db.relationship("Caso", back_populates="hallazgos")
    adjuntos = db.relationship(
        "Adjunto", back_populates="hallazgo", cascade="all, delete-orphan",
    )

    def cumple_confianza(self, minimo: str) -> bool:
        return _ORDEN_CONFIANZA.get(self.confianza, 0) >= _ORDEN_CONFIANZA.get(minimo, 0)

    def cumple_sensibilidad(self, maximo: str) -> bool:
        return _ORDEN_SENSIBILIDAD.get(self.sensibilidad, 0) <= _ORDEN_SENSIBILIDAD.get(maximo, 0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "caso_id": self.caso_id,
            "numero": self.numero,
            "titulo": self.titulo,
            "categoria": self.categoria,
            "fuente": self.fuente or "",
            "url": self.url or "",
            "contenido": self.contenido or "",
            "fecha_dato": self.fecha_dato.isoformat() if self.fecha_dato else None,
            "confianza": self.confianza,
            "sensibilidad": self.sensibilidad,
            "autor": self.autor or "",
            "hash_evidencia": self.hash_evidencia or "",
            "creado": self.creado.isoformat() if self.creado else None,
            "adjuntos": [a.to_dict() for a in self.adjuntos],
        }


class Adjunto(db.Model):
    __tablename__ = "adjuntos"

    id = db.Column(db.Integer, primary_key=True)
    hallazgo_id = db.Column(db.Integer, db.ForeignKey("hallazgos.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    nombre_original = db.Column(db.String(300))
    nombre_guardado = db.Column(db.String(300))           # uuid + extension
    mime = db.Column(db.String(100))
    hash_sha256 = db.Column(db.String(64), default="")
    creado = db.Column(db.DateTime, default=_ahora)

    hallazgo = db.relationship("Hallazgo", back_populates="adjuntos")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre_original": self.nombre_original,
            "nombre_guardado": self.nombre_guardado,
            "mime": self.mime,
            "hash_sha256": self.hash_sha256 or "",
        }


class PerfilDestinatario(db.Model):
    __tablename__ = "perfiles_destinatario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    descripcion = db.Column(db.String(300), default="")
    idioma = db.Column(db.String(10), default="es")
    # Secciones que se incluyen en el informe
    incluir_resumen = db.Column(db.Boolean, default=True)
    incluir_objetivo = db.Column(db.Boolean, default=True)
    incluir_hallazgos = db.Column(db.Boolean, default=True)
    incluir_fuentes = db.Column(db.Boolean, default=True)
    incluir_url = db.Column(db.Boolean, default=True)
    incluir_confianza = db.Column(db.Boolean, default=True)
    incluir_metadatos = db.Column(db.Boolean, default=True)
    incluir_hashes = db.Column(db.Boolean, default=False)
    incluir_adjuntos = db.Column(db.Boolean, default=True)
    incluir_autorizacion = db.Column(db.Boolean, default=False)
    # Filtros de contenido
    sensibilidad_max = db.Column(db.String(20), default="interno")   # hasta que nivel entra
    confianza_min = db.Column(db.String(20), default="sin_verificar")  # desde que nivel entra
    # Presentacion
    clasificacion = db.Column(db.String(20), default="interno")
    encabezado = db.Column(db.String(200), default="")
    pie = db.Column(db.String(200), default="")
    es_predefinido = db.Column(db.Boolean, default=False)
    creado = db.Column(db.DateTime, default=_ahora)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion or "",
            "idioma": self.idioma,
            "incluir_resumen": self.incluir_resumen,
            "incluir_objetivo": self.incluir_objetivo,
            "incluir_hallazgos": self.incluir_hallazgos,
            "incluir_fuentes": self.incluir_fuentes,
            "incluir_url": self.incluir_url,
            "incluir_confianza": self.incluir_confianza,
            "incluir_metadatos": self.incluir_metadatos,
            "incluir_hashes": self.incluir_hashes,
            "incluir_adjuntos": self.incluir_adjuntos,
            "incluir_autorizacion": self.incluir_autorizacion,
            "sensibilidad_max": self.sensibilidad_max,
            "confianza_min": self.confianza_min,
            "clasificacion": self.clasificacion,
            "encabezado": self.encabezado or "",
            "pie": self.pie or "",
            "es_predefinido": self.es_predefinido,
        }


class RegistroActividad(db.Model):
    __tablename__ = "registro_actividad"

    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(120), default="")          # quien (modo colaborativo)
    accion = db.Column(db.String(200))
    detalle = db.Column(db.String(500), default="")
    ip = db.Column(db.String(64), default="")
    creado = db.Column(db.DateTime, default=_ahora)
