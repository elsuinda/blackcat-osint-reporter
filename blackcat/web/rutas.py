"""Rutas de BLACKCAT. Toda entrada se valida; toda salida se escapa en la
plantilla (Jinja2 autoescape) o en el motor de informes."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import (
    abort, current_app, flash, redirect, render_template, request,
    send_file, session, url_for,
)
from sqlalchemy import func

from .. import config as cfgmod
from ..core import informes, models, seguridad
from ..core.db import db
from . import forms


def _actor() -> str:
    return session.get("actor") or current_app.config.get("BLACKCAT_INVESTIGADOR", "investigador")


def _registrar(accion: str, detalle: str = "") -> None:
    reg = models.RegistroActividad(
        actor=_actor(), accion=accion[:200], detalle=detalle[:500],
        ip=(request.remote_addr or "")[:64],
    )
    db.session.add(reg)
    db.session.commit()


def _siguiente_codigo() -> str:
    anio = datetime.now().year
    prefijo = f"BC-{anio}-"
    n = (db.session.query(func.count(models.Caso.id))
         .filter(models.Caso.codigo.like(prefijo + "%")).scalar() or 0)
    return seguridad.codigo_caso(anio, n + 1)


def _siguiente_numero_hallazgo(caso_id: int) -> int:
    maximo = (db.session.query(func.max(models.Hallazgo.numero))
              .filter_by(caso_id=caso_id).scalar() or 0)
    return maximo + 1


def _aplicar_caso(caso, form) -> None:
    caso.titulo = seguridad.texto_limpio(form.titulo.data, 200)
    caso.investigador = seguridad.texto_limpio(form.investigador.data, 120)
    caso.clasificacion = seguridad.validar_opcion(form.clasificacion.data, models.CLASIFICACIONES, "interno")
    caso.estado = seguridad.validar_opcion(form.estado.data, models.ESTADOS_CASO, "abierto")
    caso.descripcion = seguridad.texto_limpio(form.descripcion.data)
    caso.objetivo = seguridad.texto_limpio(form.objetivo.data)
    caso.autorizacion = seguridad.texto_limpio(form.autorizacion.data)


def _guardar_adjunto(hallazgo, archivo) -> None:
    if not archivo or not archivo.filename:
        return
    tipo = seguridad.validar_imagen(archivo.stream)
    if not tipo:
        flash("El adjunto no es una imagen valida; se omitio.", "warn")
        return
    ext, mime = tipo
    guardado = seguridad.nombre_guardado(ext)
    destino = cfgmod.DIR_SUBIDAS / guardado
    cfgmod.asegurar_directorios()
    archivo.save(str(destino))
    adj = models.Adjunto(
        hallazgo_id=hallazgo.id,
        nombre_original=seguridad.nombre_original_seguro(archivo.filename),
        nombre_guardado=guardado, mime=mime,
        hash_sha256=seguridad.sha256_archivo(destino),
    )
    db.session.add(adj)
    db.session.commit()


def registrar_rutas(app):  # noqa: C901 (rutas lineales, claridad > fragmentar)

    # ----------------------------- salud / acceso -----------------------------
    @app.route("/salud")
    def salud():
        return {"app": "blackcat", "estado": "ok"}

    @app.route("/acceso", methods=["GET", "POST"])
    def acceso():
        if not app.config["BLACKCAT_COMPARTIDO"]:
            return redirect(url_for("index"))
        form = forms.AccesoForm()
        if form.validate_on_submit():
            import hmac
            esperado = app.config["BLACKCAT_TOKEN"]
            if hmac.compare_digest(form.token.data.strip(), esperado):
                session["autorizado"] = True
                session["actor"] = seguridad.texto_limpio(form.nombre.data, 120)
                _registrar("acceso", "ingreso al espacio compartido")
                destino = request.args.get("next", "")
                if not destino.startswith("/"):
                    destino = url_for("index")
                return redirect(destino)
            flash("Clave incorrecta.", "error")
        return render_template("acceso.html", form=form)

    @app.route("/salir")
    def salir():
        session.clear()
        return redirect(url_for("acceso") if app.config["BLACKCAT_COMPARTIDO"] else url_for("index"))

    # ----------------------------- index -----------------------------
    @app.route("/")
    def index():
        casos = models.Caso.query.order_by(models.Caso.creado.desc()).all()
        total_hallazgos = db.session.query(func.count(models.Hallazgo.id)).scalar() or 0
        return render_template("index.html", casos=casos, total_hallazgos=total_hallazgos)

    # ----------------------------- casos -----------------------------
    @app.route("/casos/nuevo", methods=["GET", "POST"])
    def caso_nuevo():
        form = forms.CasoForm()
        if not form.investigador.data:
            form.investigador.data = _actor()
        if form.validate_on_submit():
            caso = models.Caso(codigo=_siguiente_codigo())
            _aplicar_caso(caso, form)
            db.session.add(caso)
            db.session.commit()
            _registrar("caso_nuevo", caso.codigo)
            flash(f"Caso {caso.codigo} creado.", "ok")
            return redirect(url_for("caso_detalle", caso_id=caso.id))
        return render_template("caso_form.html", form=form, nuevo=True)

    @app.route("/caso/<int:caso_id>")
    def caso_detalle(caso_id):
        caso = models.Caso.query.get_or_404(caso_id)
        perfiles = models.PerfilDestinatario.query.order_by(models.PerfilDestinatario.nombre).all()
        exp = forms.ExportForm()
        exp.perfil_id.choices = [(p.id, p.nombre) for p in perfiles]
        return render_template("caso_detalle.html", caso=caso, export_form=exp)

    @app.route("/caso/<int:caso_id>/editar", methods=["GET", "POST"])
    def caso_editar(caso_id):
        caso = models.Caso.query.get_or_404(caso_id)
        form = forms.CasoForm(obj=caso)
        if form.validate_on_submit():
            _aplicar_caso(caso, form)
            db.session.commit()
            _registrar("caso_editar", caso.codigo)
            flash("Caso actualizado.", "ok")
            return redirect(url_for("caso_detalle", caso_id=caso.id))
        return render_template("caso_form.html", form=form, nuevo=False, caso=caso)

    @app.route("/caso/<int:caso_id>/eliminar", methods=["POST"])
    def caso_eliminar(caso_id):
        caso = models.Caso.query.get_or_404(caso_id)
        codigo = caso.codigo
        db.session.delete(caso)
        db.session.commit()
        _registrar("caso_eliminar", codigo)
        flash(f"Caso {codigo} eliminado.", "ok")
        return redirect(url_for("index"))

    # ----------------------------- hallazgos -----------------------------
    @app.route("/caso/<int:caso_id>/hallazgo/nuevo", methods=["GET", "POST"])
    def hallazgo_nuevo(caso_id):
        caso = models.Caso.query.get_or_404(caso_id)
        form = forms.HallazgoForm()
        if form.validate_on_submit():
            h = models.Hallazgo(
                caso_id=caso.id, numero=_siguiente_numero_hallazgo(caso.id),
                titulo=seguridad.texto_limpio(form.titulo.data, 200),
                categoria=seguridad.validar_opcion(form.categoria.data, models.CATEGORIAS_HALLAZGO, "otro"),
                fuente=seguridad.texto_limpio(form.fuente.data, 300),
                url=seguridad.url_segura(form.url.data),
                contenido=seguridad.texto_limpio(form.contenido.data),
                fecha_dato=form.fecha_dato.data and datetime.combine(form.fecha_dato.data, datetime.min.time()),
                confianza=seguridad.validar_opcion(form.confianza.data, models.NIVELES_CONFIANZA, "sin_verificar"),
                sensibilidad=seguridad.validar_opcion(form.sensibilidad.data, models.NIVELES_SENSIBILIDAD, "normal"),
                autor=_actor(),
            )
            h.hash_evidencia = seguridad.sha256_texto(h.contenido)
            db.session.add(h)
            db.session.commit()
            _guardar_adjunto(h, form.imagen.data)
            _registrar("hallazgo_nuevo", f"{caso.codigo} #{h.numero}")
            flash(f"Hallazgo #{h.numero} agregado.", "ok")
            return redirect(url_for("caso_detalle", caso_id=caso.id))
        return render_template("hallazgo_form.html", form=form, caso=caso, nuevo=True)

    @app.route("/hallazgo/<int:hallazgo_id>/editar", methods=["GET", "POST"])
    def hallazgo_editar(hallazgo_id):
        h = models.Hallazgo.query.get_or_404(hallazgo_id)
        form = forms.HallazgoForm(obj=h)
        if form.validate_on_submit():
            h.titulo = seguridad.texto_limpio(form.titulo.data, 200)
            h.categoria = seguridad.validar_opcion(form.categoria.data, models.CATEGORIAS_HALLAZGO, "otro")
            h.fuente = seguridad.texto_limpio(form.fuente.data, 300)
            h.url = seguridad.url_segura(form.url.data)
            h.contenido = seguridad.texto_limpio(form.contenido.data)
            h.fecha_dato = form.fecha_dato.data and datetime.combine(form.fecha_dato.data, datetime.min.time())
            h.confianza = seguridad.validar_opcion(form.confianza.data, models.NIVELES_CONFIANZA, "sin_verificar")
            h.sensibilidad = seguridad.validar_opcion(form.sensibilidad.data, models.NIVELES_SENSIBILIDAD, "normal")
            h.hash_evidencia = seguridad.sha256_texto(h.contenido)
            db.session.commit()
            _guardar_adjunto(h, form.imagen.data)
            _registrar("hallazgo_editar", f"{h.caso.codigo} #{h.numero}")
            flash("Hallazgo actualizado.", "ok")
            return redirect(url_for("caso_detalle", caso_id=h.caso_id))
        return render_template("hallazgo_form.html", form=form, caso=h.caso, nuevo=False, hallazgo=h)

    @app.route("/hallazgo/<int:hallazgo_id>/eliminar", methods=["POST"])
    def hallazgo_eliminar(hallazgo_id):
        h = models.Hallazgo.query.get_or_404(hallazgo_id)
        caso_id = h.caso_id
        num = h.numero
        db.session.delete(h)
        db.session.commit()
        _registrar("hallazgo_eliminar", f"#{num}")
        flash(f"Hallazgo #{num} eliminado.", "ok")
        return redirect(url_for("caso_detalle", caso_id=caso_id))

    # ----------------------------- exportar / descargar -----------------------------
    @app.route("/caso/<int:caso_id>/exportar", methods=["POST"])
    def caso_exportar(caso_id):
        caso = models.Caso.query.get_or_404(caso_id)
        perfiles = models.PerfilDestinatario.query.all()
        form = forms.ExportForm()
        form.perfil_id.choices = [(p.id, p.nombre) for p in perfiles]
        if not form.validate_on_submit():
            flash("No se pudo generar el informe (datos invalidos).", "error")
            return redirect(url_for("caso_detalle", caso_id=caso.id))
        perfil = models.PerfilDestinatario.query.get_or_404(form.perfil_id.data)
        formato = form.formato.data if form.formato.data in informes.FORMATOS else "pdf"
        try:
            res = informes.exportar(caso, perfil, formato, cfgmod.DIR_INFORMES)
        except Exception as exc:  # noqa: BLE001
            current_app.logger.error("export fallo: %s", exc)
            flash("Error al generar el informe.", "error")
            return redirect(url_for("caso_detalle", caso_id=caso.id))
        _registrar("informe", f"{caso.codigo} / {perfil.nombre} / {formato} / sha256:{res['sha256'][:16]}")
        flash(f"Informe generado para '{perfil.nombre}' ({res['total_hallazgos']} hallazgos). "
              f"SHA-256: {res['sha256']}", "ok")
        session["ultimo_informe"] = res["nombre"]
        return redirect(url_for("descargar", nombre=res["nombre"]))

    @app.route("/descargar/<path:nombre>")
    def descargar(nombre):
        base = cfgmod.DIR_INFORMES.resolve()
        objetivo = (base / nombre).resolve()
        if base != objetivo.parent or not objetivo.is_file():
            abort(404)
        return send_file(str(objetivo), as_attachment=True, download_name=objetivo.name)

    # ----------------------------- perfiles -----------------------------
    @app.route("/perfiles")
    def perfiles():
        lista = models.PerfilDestinatario.query.order_by(models.PerfilDestinatario.nombre).all()
        return render_template("perfiles.html", perfiles=lista)

    def _aplicar_perfil(p, form):
        p.nombre = seguridad.texto_limpio(form.nombre.data, 80)
        p.descripcion = seguridad.texto_limpio(form.descripcion.data, 300)
        p.encabezado = seguridad.texto_limpio(form.encabezado.data, 200)
        p.pie = seguridad.texto_limpio(form.pie.data, 200)
        p.clasificacion = seguridad.validar_opcion(form.clasificacion.data, models.CLASIFICACIONES, "interno")
        p.sensibilidad_max = seguridad.validar_opcion(form.sensibilidad_max.data, models.NIVELES_SENSIBILIDAD, "interno")
        p.confianza_min = seguridad.validar_opcion(form.confianza_min.data, models.NIVELES_CONFIANZA, "sin_verificar")
        for campo in ("incluir_resumen", "incluir_objetivo", "incluir_autorizacion",
                      "incluir_hallazgos", "incluir_fuentes", "incluir_url",
                      "incluir_confianza", "incluir_metadatos", "incluir_hashes",
                      "incluir_adjuntos"):
            setattr(p, campo, bool(getattr(form, campo).data))

    @app.route("/perfiles/nuevo", methods=["GET", "POST"])
    def perfil_nuevo():
        form = forms.PerfilForm()
        if form.validate_on_submit():
            if models.PerfilDestinatario.query.filter_by(nombre=form.nombre.data.strip()).first():
                flash("Ya existe un perfil con ese nombre.", "error")
            else:
                p = models.PerfilDestinatario()
                _aplicar_perfil(p, form)
                db.session.add(p)
                db.session.commit()
                _registrar("perfil_nuevo", p.nombre)
                flash("Perfil creado.", "ok")
                return redirect(url_for("perfiles"))
        return render_template("perfil_form.html", form=form, nuevo=True)

    @app.route("/perfil/<int:perfil_id>/editar", methods=["GET", "POST"])
    def perfil_editar(perfil_id):
        p = models.PerfilDestinatario.query.get_or_404(perfil_id)
        form = forms.PerfilForm(obj=p)
        if form.validate_on_submit():
            _aplicar_perfil(p, form)
            db.session.commit()
            _registrar("perfil_editar", p.nombre)
            flash("Perfil actualizado.", "ok")
            return redirect(url_for("perfiles"))
        return render_template("perfil_form.html", form=form, nuevo=False, perfil=p)

    @app.route("/perfil/<int:perfil_id>/eliminar", methods=["POST"])
    def perfil_eliminar(perfil_id):
        p = models.PerfilDestinatario.query.get_or_404(perfil_id)
        if p.es_predefinido:
            flash("No se pueden eliminar los perfiles predefinidos.", "error")
            return redirect(url_for("perfiles"))
        nombre = p.nombre
        db.session.delete(p)
        db.session.commit()
        _registrar("perfil_eliminar", nombre)
        flash("Perfil eliminado.", "ok")
        return redirect(url_for("perfiles"))

    # ----------------------------- actividad -----------------------------
    @app.route("/actividad")
    def actividad():
        regs = (models.RegistroActividad.query
                .order_by(models.RegistroActividad.creado.desc()).limit(200).all())
        return render_template("actividad.html", registros=regs)
