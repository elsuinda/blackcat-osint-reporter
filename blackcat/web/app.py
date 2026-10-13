"""Fabrica de la aplicacion Flask de BLACKCAT.

create_app arma la app endurecida: CSRF, cabeceras de seguridad, base de
datos SQLite y (si corresponde) el control de acceso por token del modo
colaborativo. Valores seguros por defecto: sin DEBUG, sin secretos en el
codigo, cookies HttpOnly/SameSite.
"""
from __future__ import annotations

from pathlib import Path

from flask import (
    Flask, flash, redirect, render_template, request, session, url_for,
)
from flask_wtf.csrf import CSRFError, CSRFProtect

from .. import __version__, config as cfgmod
from ..core import models, seguridad
from ..core.db import db

csrf = CSRFProtect()

_AQUI = Path(__file__).resolve().parent


def create_app(compartido: bool = False, token: str | None = None,
               investigador: str | None = None) -> Flask:
    cfg = cfgmod.cargar_config()
    app = Flask(
        __name__,
        template_folder=str(_AQUI / "templates"),
        static_folder=str(_AQUI / "static"),
    )
    app.config.from_object(cfgmod.ConfigFlask(cfg["secret_key"]))
    app.config["BLACKCAT_COMPARTIDO"] = bool(compartido)
    app.config["BLACKCAT_TOKEN"] = token or ""
    app.config["BLACKCAT_INVESTIGADOR"] = investigador or cfg.get("investigador", "investigador")
    app.config["BLACKCAT_ORG"] = cfg.get("organizacion", "")
    # Cookie segura si se sirve por https (modo compartido con TLS a futuro)
    app.config["SESSION_COOKIE_SECURE"] = False

    db.init_app(app)
    csrf.init_app(app)

    # ---- Cabeceras de seguridad en toda respuesta ----
    @app.after_request
    def _cabeceras(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; "
            "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        return resp

    # ---- Control de acceso (solo modo compartido) ----
    @app.before_request
    def _control_acceso():
        if not app.config["BLACKCAT_COMPARTIDO"]:
            # modo privado: el actor es el investigador local
            session.setdefault("actor", app.config["BLACKCAT_INVESTIGADOR"])
            return None
        ep = request.endpoint or ""
        if ep in ("acceso", "salud", "static"):
            return None
        if not session.get("autorizado"):
            return redirect(url_for("acceso", next=request.path))
        return None

    # ---- Context processor (datos para todas las plantillas) ----
    @app.context_processor
    def _ctx():
        return {
            "BC_VERSION": __version__,
            "BC_COMPARTIDO": app.config["BLACKCAT_COMPARTIDO"],
            "BC_ACTOR": session.get("actor", app.config["BLACKCAT_INVESTIGADOR"]),
            "CLASIFICACIONES": models.CLASIFICACIONES,
        }

    # ---- Manejo de errores ----
    @app.errorhandler(CSRFError)
    def _csrf(e):
        return render_template("error.html", codigo=400,
                               mensaje="Token de seguridad invalido o expirado. Volve a intentar."), 400

    @app.errorhandler(404)
    def _404(e):
        return render_template("error.html", codigo=404,
                               mensaje="No se encontro lo que buscabas."), 404

    @app.errorhandler(413)
    def _413(e):
        return render_template("error.html", codigo=413,
                               mensaje="El archivo supera el limite permitido (10 MB)."), 413

    @app.errorhandler(500)
    def _500(e):
        return render_template("error.html", codigo=500,
                               mensaje="Ocurrio un error interno."), 500

    # ---- Rutas ----
    from .rutas import registrar_rutas
    registrar_rutas(app)

    # ---- Base de datos + perfiles base ----
    with app.app_context():
        db.create_all()
        seguridad.sembrar_perfiles(db)

    return app
