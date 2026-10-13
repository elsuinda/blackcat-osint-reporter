"""Utilidades de seguridad: hashes, tokens, validacion y subidas seguras.

Centraliza las defensas para que las rutas y servicios no reinventen
validacion. Todo lo que entra por formulario pasa por aca.
"""
from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import datetime
from pathlib import Path

from werkzeug.utils import secure_filename

from .. import config
from . import models


# ---------------------------------------------------------------------------
# Hashes de integridad
# ---------------------------------------------------------------------------
def sha256_texto(texto: str) -> str:
    return hashlib.sha256((texto or "").encode("utf-8")).hexdigest()


def sha256_archivo(ruta: Path, bloque: int = 65536) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Tokens / codigos
# ---------------------------------------------------------------------------
def token_sesion() -> str:
    """Token de acceso para el modo colaborativo (compartido por LAN)."""
    return secrets.token_urlsafe(24)


def codigo_caso(anio: int | None = None, correlativo: int = 1) -> str:
    anio = anio or datetime.now().year
    return f"BC-{anio}-{correlativo:04d}"


# ---------------------------------------------------------------------------
# Validacion de dominio (whitelists)
# ---------------------------------------------------------------------------
def validar_opcion(valor: str, permitidos: tuple, por_defecto: str) -> str:
    """Devuelve el valor si esta en la whitelist; si no, el por_defecto."""
    return valor if valor in permitidos else por_defecto


_URL_OK = re.compile(r"^https?://", re.IGNORECASE)


def url_segura(url: str) -> str:
    """Solo acepta http/https. Evita javascript:, file:, data:, etc."""
    url = (url or "").strip()
    if not url:
        return ""
    return url if _URL_OK.match(url) else ""


def texto_limpio(valor: str | None, maximo: int = 100_000) -> str:
    """Normaliza un texto libre: recorta y limita longitud. El escape para
    salida (HTML/PDF/DOCX) se hace en la capa de presentacion."""
    if valor is None:
        return ""
    valor = valor.replace("\x00", "").strip()
    return valor[:maximo]


# ---------------------------------------------------------------------------
# Subidas de archivos
# ---------------------------------------------------------------------------
# Firmas (magic bytes) de los tipos de imagen permitidos
_FIRMAS = {
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"GIF87a": ("gif", "image/gif"),
    b"GIF89a": ("gif", "image/gif"),
    b"BM": ("bmp", "image/bmp"),
    b"RIFF": ("webp", "image/webp"),  # se refina abajo
}


def _tipo_por_contenido(cabecera: bytes) -> tuple[str, str] | None:
    for firma, info in _FIRMAS.items():
        if cabecera.startswith(firma):
            if firma == b"RIFF" and cabecera[8:12] != b"WEBP":
                continue
            return info
    return None


def validar_imagen(stream) -> tuple[str, str] | None:
    """Valida por CONTENIDO (no solo por extension). Devuelve (ext, mime)
    si es una imagen permitida, o None. Deja el stream al inicio."""
    pos = stream.tell()
    cabecera = stream.read(16)
    stream.seek(pos)
    tipo = _tipo_por_contenido(cabecera)
    if not tipo:
        return None
    ext, mime = tipo
    if ext not in config.EXTENSIONES_IMAGEN:
        return None
    return ext, mime


def nombre_guardado(extension: str) -> str:
    """Nombre unico e inofensivo para guardar en disco."""
    ext = secure_filename(extension).lower().lstrip(".") or "bin"
    return f"{uuid.uuid4().hex}.{ext}"


def nombre_original_seguro(nombre: str) -> str:
    base = secure_filename(nombre or "")
    return base[:200] or "archivo"


# ---------------------------------------------------------------------------
# Siembra de perfiles de destinatario predefinidos
# ---------------------------------------------------------------------------
PERFILES_BASE = [
    {
        "nombre": "Tecnico / Pericial",
        "descripcion": "Informe completo con fuentes, hashes y metadatos. Para analistas y uso pericial.",
        "incluir_hashes": True, "incluir_autorizacion": True,
        "sensibilidad_max": "interno", "confianza_min": "sin_verificar",
        "clasificacion": "reservado", "es_predefinido": True,
        "encabezado": "Informe tecnico OSINT",
    },
    {
        "nombre": "Ejecutivo / Gerencial",
        "descripcion": "Resumen y hallazgos clave, sin tecnicismos ni datos internos. Para direccion.",
        "incluir_fuentes": False, "incluir_url": False, "incluir_hashes": False,
        "incluir_metadatos": False, "incluir_adjuntos": False,
        "sensibilidad_max": "normal", "confianza_min": "probable",
        "clasificacion": "confidencial", "es_predefinido": True,
        "encabezado": "Resumen ejecutivo",
    },
    {
        "nombre": "Judicial",
        "descripcion": "Con base de autorizacion, fuentes y hashes de integridad. Formato para presentacion.",
        "incluir_hashes": True, "incluir_autorizacion": True, "incluir_metadatos": True,
        "sensibilidad_max": "interno", "confianza_min": "sin_verificar",
        "clasificacion": "reservado", "es_predefinido": True,
        "encabezado": "Informe para autoridad competente",
    },
    {
        "nombre": "Cliente",
        "descripcion": "Presentable, solo hallazgos confirmados/probables. Sin datos internos ni sensibles.",
        "incluir_fuentes": True, "incluir_url": True, "incluir_hashes": False,
        "incluir_metadatos": False, "incluir_autorizacion": False, "incluir_adjuntos": True,
        "sensibilidad_max": "normal", "confianza_min": "probable",
        "clasificacion": "confidencial", "es_predefinido": True,
        "encabezado": "Informe de investigacion",
    },
]


def sembrar_perfiles(db) -> None:
    """Crea los perfiles predefinidos si aun no existen."""
    for datos in PERFILES_BASE:
        existe = models.PerfilDestinatario.query.filter_by(nombre=datos["nombre"]).first()
        if existe:
            continue
        db.session.add(models.PerfilDestinatario(**datos))
    db.session.commit()
