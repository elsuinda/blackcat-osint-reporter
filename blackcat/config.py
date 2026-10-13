"""Configuracion y rutas de BLACKCAT.

Todo el estado del usuario (base de datos, config, subidas, PID del
servidor) vive bajo ~/.blackcat con permisos restrictivos. La SECRET_KEY
se genera una sola vez de forma aleatoria y se guarda con permisos 600:
nunca hay secretos escritos en el codigo.
"""
from __future__ import annotations

import json
import os
import secrets
import stat
from pathlib import Path


# ---------------------------------------------------------------------------
# Rutas base (se pueden sobreescribir con variables de entorno para pruebas)
# ---------------------------------------------------------------------------
def _dir_base() -> Path:
    env = os.environ.get("BLACKCAT_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".blackcat"


DIR_BASE = _dir_base()
DIR_SUBIDAS = DIR_BASE / "subidas"
DIR_INFORMES = DIR_BASE / "informes"
ARCHIVO_CONFIG = DIR_BASE / "config.json"
ARCHIVO_DB = DIR_BASE / "blackcat.db"
ARCHIVO_PID = DIR_BASE / "blackcat.pid"
ARCHIVO_LOG = DIR_BASE / "blackcat.log"
ARCHIVO_RUNTIME = DIR_BASE / "runtime.json"  # datos de la sesion activa (modo, token)

# Limites de subida
MAX_SUBIDA_BYTES = 10 * 1024 * 1024  # 10 MB por archivo
EXTENSIONES_IMAGEN = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}


def asegurar_directorios() -> None:
    """Crea el arbol ~/.blackcat con permisos de solo-usuario (700)."""
    for d in (DIR_BASE, DIR_SUBIDAS, DIR_INFORMES):
        d.mkdir(parents=True, exist_ok=True)
        try:
            d.chmod(0o700)
        except OSError:
            pass


def _escribir_json_seguro(ruta: Path, datos: dict) -> None:
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        ruta.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600
    except OSError:
        pass


def cargar_config() -> dict:
    """Carga (o crea) la config del usuario. Genera SECRET_KEY la 1a vez."""
    asegurar_directorios()
    cfg: dict = {}
    if ARCHIVO_CONFIG.exists():
        try:
            cfg = json.loads(ARCHIVO_CONFIG.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            cfg = {}
    cambiado = False
    if not cfg.get("secret_key"):
        cfg["secret_key"] = secrets.token_urlsafe(48)
        cambiado = True
    cfg.setdefault("investigador", os.environ.get("USER") or os.environ.get("USERNAME") or "investigador")
    cfg.setdefault("organizacion", "")
    if cambiado:
        _escribir_json_seguro(ARCHIVO_CONFIG, cfg)
    return cfg


def guardar_config(cfg: dict) -> None:
    asegurar_directorios()
    _escribir_json_seguro(ARCHIVO_CONFIG, cfg)


class ConfigFlask:
    """Config base para la app Flask. Valores seguros por defecto."""

    def __init__(self, secret_key: str):
        self.SECRET_KEY = secret_key
        self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{ARCHIVO_DB}"
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.MAX_CONTENT_LENGTH = MAX_SUBIDA_BYTES
        self.UPLOAD_FOLDER = str(DIR_SUBIDAS)
        # Cookies endurecidas
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"
        self.WTF_CSRF_TIME_LIMIT = None
        self.JSON_AS_ASCII = False
        self.TEMPLATES_AUTO_RELOAD = False
