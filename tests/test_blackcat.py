"""Pruebas de BLACKCAT: seguridad, modelos, motor de informes y rutas web."""
import io
from pathlib import Path

from blackcat import config as cfgmod
from blackcat.core import informes, models, seguridad
from blackcat.core.db import db


# --------------------------------------------------------------------------- #
# Seguridad
# --------------------------------------------------------------------------- #
def test_sha256_texto_estable():
    assert seguridad.sha256_texto("hola") == seguridad.sha256_texto("hola")
    assert len(seguridad.sha256_texto("x")) == 64


def test_url_segura_filtra_esquemas_peligrosos():
    assert seguridad.url_segura("https://ok.com") == "https://ok.com"
    assert seguridad.url_segura("http://ok.com") == "http://ok.com"
    assert seguridad.url_segura("javascript:alert(1)") == ""
    assert seguridad.url_segura("file:///etc/passwd") == ""
    assert seguridad.url_segura("  data:text/html,x ") == ""


def test_validar_opcion_whitelist():
    assert seguridad.validar_opcion("confirmado", models.NIVELES_CONFIANZA, "sin_verificar") == "confirmado"
    assert seguridad.validar_opcion("HACK", models.NIVELES_CONFIANZA, "sin_verificar") == "sin_verificar"


def _png_bytes():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (0, 0, 0)).save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_validar_imagen_acepta_png_y_rechaza_texto():
    assert seguridad.validar_imagen(_png_bytes()) == ("png", "image/png")
    falso = io.BytesIO(b"esto no es una imagen")
    assert seguridad.validar_imagen(falso) is None


def test_nombre_guardado_es_inofensivo():
    n = seguridad.nombre_guardado("png")
    assert n.endswith(".png") and "/" not in n and ".." not in n


# --------------------------------------------------------------------------- #
# Modelos / filtros
# --------------------------------------------------------------------------- #
def test_filtros_confianza_sensibilidad():
    h = models.Hallazgo(numero=1, titulo="x", confianza="probable", sensibilidad="sensible")
    assert h.cumple_confianza("sin_verificar") is True
    assert h.cumple_confianza("confirmado") is False
    assert h.cumple_sensibilidad("interno") is True
    assert h.cumple_sensibilidad("normal") is False


def test_perfiles_base_sembrados(app):
    with app.app_context():
        assert models.PerfilDestinatario.query.count() >= 4
        assert models.PerfilDestinatario.query.filter_by(nombre="Judicial").first()


# --------------------------------------------------------------------------- #
# Motor de informes
# --------------------------------------------------------------------------- #
def _caso_con_hallazgos(app):
    with app.app_context():
        caso = models.Caso(codigo="BC-2026-9001", titulo="Prueba", investigador="Miguel",
                           descripcion="resumen", objetivo="alcance", autorizacion="orden X")
        db.session.add(caso)
        db.session.commit()
        h1 = models.Hallazgo(caso_id=caso.id, numero=1, titulo="Publico confirmado",
                             contenido="dato", confianza="confirmado", sensibilidad="normal")
        h2 = models.Hallazgo(caso_id=caso.id, numero=2, titulo="Interno sin verificar",
                             contenido="secreto", confianza="sin_verificar", sensibilidad="interno")
        db.session.add_all([h1, h2])
        db.session.commit()
        return caso.id


def test_perfil_cliente_filtra_hallazgos(app):
    cid = _caso_con_hallazgos(app)
    with app.app_context():
        caso = models.Caso.query.get(cid)
        cliente = models.PerfilDestinatario.query.filter_by(nombre="Cliente").first()
        tecnico = models.PerfilDestinatario.query.filter_by(nombre="Tecnico / Pericial").first()
        assert informes.construir_modelo(caso, cliente)["total_hallazgos"] == 1
        assert informes.construir_modelo(caso, tecnico)["total_hallazgos"] == 2


def test_exporta_los_cuatro_formatos(app, tmp_path):
    cid = _caso_con_hallazgos(app)
    with app.app_context():
        caso = models.Caso.query.get(cid)
        perfil = models.PerfilDestinatario.query.filter_by(nombre="Tecnico / Pericial").first()
        for fmt in informes.FORMATOS:
            res = informes.exportar(caso, perfil, fmt, tmp_path)
            ruta = Path(res["ruta"])
            assert ruta.is_file() and ruta.stat().st_size > 0
            assert len(res["sha256"]) == 64


def test_informe_escapa_contenido_malicioso(app):
    with app.app_context():
        caso = models.Caso(codigo="BC-2026-9002", titulo="XSS")
        db.session.add(caso)
        db.session.commit()
        h = models.Hallazgo(caso_id=caso.id, numero=1,
                            titulo="<script>alert(1)</script>", contenido="<b>x</b>")
        db.session.add(h)
        db.session.commit()
        perfil = models.PerfilDestinatario.query.filter_by(nombre="Tecnico / Pericial").first()
        html = informes.a_html(informes.construir_modelo(caso, perfil))
        assert "<script>alert(1)" not in html
        assert "&lt;script&gt;" in html


# --------------------------------------------------------------------------- #
# Rutas web
# --------------------------------------------------------------------------- #
def test_salud(cliente):
    r = cliente.get("/salud")
    assert r.status_code == 200 and r.json["estado"] == "ok"


def test_flujo_caso_hallazgo_y_export(app, cliente):
    # crear caso
    r = cliente.post("/casos/nuevo", data={
        "titulo": "Caso web", "investigador": "Miguel",
        "clasificacion": "interno", "estado": "abierto",
        "descripcion": "d", "objetivo": "o", "autorizacion": "a",
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        caso = models.Caso.query.filter_by(titulo="Caso web").first()
        assert caso is not None
        cid = caso.id
    # agregar hallazgo
    r = cliente.post(f"/caso/{cid}/hallazgo/nuevo", data={
        "titulo": "H1", "categoria": "persona", "confianza": "confirmado",
        "sensibilidad": "normal", "fuente": "fuente", "url": "https://x.com",
        "contenido": "contenido",
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        h = models.Hallazgo.query.filter_by(caso_id=cid).first()
        assert h and h.numero == 1 and len(h.hash_evidencia) == 64
        pid = models.PerfilDestinatario.query.filter_by(nombre="Cliente").first().id
    # exportar -> redirige a descarga
    r = cliente.post(f"/caso/{cid}/exportar",
                     data={"perfil_id": pid, "formato": "pdf"}, follow_redirects=False)
    assert r.status_code == 302 and "/descargar/" in r.headers["Location"]


def test_url_peligrosa_se_descarta_en_hallazgo(app, cliente):
    cliente.post("/casos/nuevo", data={
        "titulo": "C", "clasificacion": "interno", "estado": "abierto",
    }, follow_redirects=True)
    with app.app_context():
        cid = models.Caso.query.filter_by(titulo="C").first().id
    # 1a capa: el formulario rechaza el esquema peligroso (no se crea el hallazgo)
    cliente.post(f"/caso/{cid}/hallazgo/nuevo", data={
        "titulo": "H", "categoria": "otro", "confianza": "sin_verificar",
        "sensibilidad": "normal", "url": "javascript:alert(1)", "contenido": "x",
    }, follow_redirects=True)
    with app.app_context():
        assert models.Hallazgo.query.filter_by(caso_id=cid).count() == 0
    # con URL valida si se crea y se guarda
    cliente.post(f"/caso/{cid}/hallazgo/nuevo", data={
        "titulo": "H", "categoria": "otro", "confianza": "sin_verificar",
        "sensibilidad": "normal", "url": "https://ok.com", "contenido": "x",
    }, follow_redirects=True)
    with app.app_context():
        h = models.Hallazgo.query.filter_by(caso_id=cid).first()
        assert h is not None and h.url == "https://ok.com"


def test_descarga_bloquea_path_traversal(cliente):
    r = cliente.get("/descargar/..%2f..%2fetc%2fpasswd")
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Modo compartido
# --------------------------------------------------------------------------- #
def test_compartido_exige_clave(app_compartido):
    c = app_compartido.test_client()
    r = c.get("/", follow_redirects=False)
    assert r.status_code == 302 and "/acceso" in r.headers["Location"]
    assert c.get("/salud").status_code == 200  # salud siempre accesible


def test_compartido_login_token(app_compartido):
    c = app_compartido.test_client()
    # token incorrecto
    r = c.post("/acceso", data={"nombre": "Ana", "token": "mala"}, follow_redirects=False)
    assert r.status_code == 200  # se queda en el form
    # token correcto
    r = c.post("/acceso", data={"nombre": "Ana", "token": "CLAVE-TEST-123"}, follow_redirects=False)
    assert r.status_code == 302
    assert c.get("/", follow_redirects=False).status_code == 200
