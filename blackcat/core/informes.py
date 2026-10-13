"""Motor de informes customizables de BLACKCAT.

A partir de un Caso y un PerfilDestinatario arma un "modelo de informe"
(que secciones y que hallazgos entran, segun el publico) y lo exporta a
Markdown, HTML, PDF o DOCX. Cada formato escapa el contenido del usuario
de forma adecuada; nunca se interpola texto crudo en HTML/PDF.
"""
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

from .. import __version__
from . import seguridad

FIRMA = "El Suinda @v@  ·  BLACKCAT  ·  les petites cellules grises"

_ETIQUETA_CONFIANZA = {
    "confirmado": "CONFIRMADO",
    "probable": "PROBABLE",
    "sin_verificar": "SIN VERIFICAR",
}
_ETIQUETA_CATEGORIA = {
    "persona": "Persona", "organizacion": "Organizacion", "dominio": "Dominio",
    "infraestructura": "Infraestructura", "red_social": "Red social",
    "documento": "Documento", "ubicacion": "Ubicacion", "otro": "Otro",
}


# ---------------------------------------------------------------------------
# Construccion del modelo (aplica el perfil de destinatario)
# ---------------------------------------------------------------------------
def construir_modelo(caso, perfil) -> dict:
    """Devuelve un dict con exactamente lo que el perfil permite mostrar."""
    hallazgos = []
    for h in caso.hallazgos:
        if not (h.cumple_confianza(perfil.confianza_min)
                and h.cumple_sensibilidad(perfil.sensibilidad_max)):
            continue
        item = {
            "numero": h.numero,
            "titulo": h.titulo,
            "categoria": _ETIQUETA_CATEGORIA.get(h.categoria, h.categoria),
            "contenido": h.contenido or "",
            "fecha_dato": h.fecha_dato.strftime("%Y-%m-%d") if h.fecha_dato else "",
            "autor": h.autor or "",
        }
        if perfil.incluir_fuentes:
            item["fuente"] = h.fuente or ""
        if perfil.incluir_url:
            item["url"] = seguridad.url_segura(h.url or "")
        if perfil.incluir_confianza:
            item["confianza"] = _ETIQUETA_CONFIANZA.get(h.confianza, h.confianza)
        if perfil.incluir_hashes:
            item["hash_evidencia"] = h.hash_evidencia or ""
        if perfil.incluir_adjuntos:
            item["adjuntos"] = [
                {"nombre": a.nombre_original, "hash": a.hash_sha256}
                for a in h.adjuntos
            ]
        hallazgos.append(item)

    modelo = {
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "herramienta": f"BLACKCAT v{__version__}",
        "perfil": perfil.nombre,
        "clasificacion": perfil.clasificacion.upper(),
        "encabezado": perfil.encabezado or "Informe OSINT",
        "pie": perfil.pie or "",
        "caso": {
            "codigo": caso.codigo,
            "titulo": caso.titulo,
            "estado": caso.estado,
            "investigador": caso.investigador or "",
            "descripcion": caso.descripcion or "",
            "objetivo": caso.objetivo or "" if perfil.incluir_objetivo else "",
            "autorizacion": caso.autorizacion or "" if perfil.incluir_autorizacion else "",
            "creado": caso.creado.strftime("%Y-%m-%d") if caso.creado else "",
        },
        "opciones": {
            "resumen": perfil.incluir_resumen,
            "objetivo": perfil.incluir_objetivo,
            "autorizacion": perfil.incluir_autorizacion,
            "metadatos": perfil.incluir_metadatos,
            "hashes": perfil.incluir_hashes,
        },
        "total_hallazgos": len(hallazgos),
        "hallazgos": hallazgos,
    }
    return modelo


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def a_markdown(modelo: dict) -> str:
    c = modelo["caso"]
    L = []
    L.append(f"# {modelo['encabezado']}")
    L.append("")
    L.append(f"> **Clasificacion: {modelo['clasificacion']}**  |  Perfil: {modelo['perfil']}")
    L.append("")
    L.append(f"- **Caso:** {c['codigo']} — {c['titulo']}")
    if c["investigador"]:
        L.append(f"- **Investigador:** {c['investigador']}")
    L.append(f"- **Generado:** {modelo['generado']} ({modelo['herramienta']})")
    L.append("")
    if modelo["opciones"]["resumen"] and c["descripcion"]:
        L.append("## Resumen")
        L.append(c["descripcion"])
        L.append("")
    if modelo["opciones"]["objetivo"] and c["objetivo"]:
        L.append("## Objetivo / Alcance")
        L.append(c["objetivo"])
        L.append("")
    if modelo["opciones"]["autorizacion"] and c["autorizacion"]:
        L.append("## Base de autorizacion")
        L.append(c["autorizacion"])
        L.append("")
    L.append(f"## Hallazgos ({modelo['total_hallazgos']})")
    L.append("")
    for h in modelo["hallazgos"]:
        cab = f"### {h['numero']}. {h['titulo']}  [{h['categoria']}]"
        if "confianza" in h:
            cab += f"  ({h['confianza']})"
        L.append(cab)
        if h["contenido"]:
            L.append(h["contenido"])
        if h.get("fuente"):
            L.append(f"- Fuente: {h['fuente']}")
        if h.get("url"):
            L.append(f"- URL: {h['url']}")
        if h.get("fecha_dato"):
            L.append(f"- Fecha del dato: {h['fecha_dato']}")
        if h.get("autor"):
            L.append(f"- Cargado por: {h['autor']}")
        if h.get("hash_evidencia"):
            L.append(f"- SHA-256: `{h['hash_evidencia']}`")
        for a in h.get("adjuntos", []):
            L.append(f"- Adjunto: {a['nombre']}  (SHA-256: {a['hash']})")
        L.append("")
    if modelo["pie"]:
        L.append("---")
        L.append(modelo["pie"])
    L.append("")
    L.append(f"*{FIRMA}*")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# HTML (standalone, tema BLACKCAT) — todo escapado
# ---------------------------------------------------------------------------
def a_html(modelo: dict) -> str:
    e = html.escape
    c = modelo["caso"]
    out = []
    out.append("<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>")
    out.append(f"<title>{e(modelo['encabezado'])} - {e(c['codigo'])}</title>")
    out.append("<style>"
               "body{background:#0A0E0A;color:#C8D6C8;font-family:'DejaVu Sans Mono',monospace;margin:2.5rem auto;max-width:900px;padding:0 1.2rem;line-height:1.5}"
               "h1{color:#39FF14}h2{color:#39FF14;border-bottom:1px solid #1FA80B;padding-bottom:4px;margin-top:1.8rem}"
               "h3{color:#FF6A00}a{color:#39FF14}code{color:#FF6A00;word-break:break-all}"
               ".clasif{display:inline-block;border:1px solid #FF6A00;color:#FF6A00;padding:2px 10px;border-radius:3px;font-size:.85rem}"
               ".meta{color:#7f9a7f;font-size:.9rem}.h{border-left:2px solid #1FA80B;padding-left:12px;margin:1rem 0}"
               ".pie{color:#7f9a7f;border-top:1px solid #1FA80B;margin-top:2rem;padding-top:8px;font-size:.85rem}"
               "</style></head><body>")
    out.append(f"<h1>{e(modelo['encabezado'])}</h1>")
    out.append(f"<p><span class='clasif'>CLASIFICACION: {e(modelo['clasificacion'])}</span> "
               f"&nbsp; <span class='meta'>Perfil: {e(modelo['perfil'])}</span></p>")
    out.append("<p class='meta'>")
    out.append(f"Caso: <b>{e(c['codigo'])}</b> — {e(c['titulo'])}<br>")
    if c["investigador"]:
        out.append(f"Investigador: {e(c['investigador'])}<br>")
    out.append(f"Generado: {e(modelo['generado'])} ({e(modelo['herramienta'])})</p>")

    if modelo["opciones"]["resumen"] and c["descripcion"]:
        out.append("<h2>Resumen</h2><p>" + e(c["descripcion"]).replace("\n", "<br>") + "</p>")
    if modelo["opciones"]["objetivo"] and c["objetivo"]:
        out.append("<h2>Objetivo / Alcance</h2><p>" + e(c["objetivo"]).replace("\n", "<br>") + "</p>")
    if modelo["opciones"]["autorizacion"] and c["autorizacion"]:
        out.append("<h2>Base de autorizacion</h2><p>" + e(c["autorizacion"]).replace("\n", "<br>") + "</p>")

    out.append(f"<h2>Hallazgos ({modelo['total_hallazgos']})</h2>")
    for h in modelo["hallazgos"]:
        out.append("<div class='h'>")
        titulo = f"{h['numero']}. {e(h['titulo'])} <small>[{e(h['categoria'])}]</small>"
        if "confianza" in h:
            titulo += f" <small>({e(h['confianza'])})</small>"
        out.append(f"<h3>{titulo}</h3>")
        if h["contenido"]:
            out.append("<p>" + e(h["contenido"]).replace("\n", "<br>") + "</p>")
        out.append("<p class='meta'>")
        if h.get("fuente"):
            out.append(f"Fuente: {e(h['fuente'])}<br>")
        if h.get("url"):
            out.append(f"URL: <a href='{e(h['url'])}' rel='noopener noreferrer'>{e(h['url'])}</a><br>")
        if h.get("fecha_dato"):
            out.append(f"Fecha del dato: {e(h['fecha_dato'])}<br>")
        if h.get("autor"):
            out.append(f"Cargado por: {e(h['autor'])}<br>")
        if h.get("hash_evidencia"):
            out.append(f"SHA-256: <code>{e(h['hash_evidencia'])}</code><br>")
        for a in h.get("adjuntos", []):
            out.append(f"Adjunto: {e(a['nombre'] or '')} (SHA-256: {e(a['hash'] or '')})<br>")
        out.append("</p></div>")

    if modelo["pie"]:
        out.append(f"<div class='pie'>{e(modelo['pie'])}</div>")
    out.append(f"<div class='pie'>{e(FIRMA)}</div>")
    out.append("</body></html>")
    return "".join(out)


# ---------------------------------------------------------------------------
# PDF (reportlab, sin binarios externos) — escapado con xml escape
# ---------------------------------------------------------------------------
def a_pdf(modelo: dict, ruta: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    )

    verde = colors.HexColor("#1FA80B")
    naranja = colors.HexColor("#C25000")
    negro = colors.HexColor("#0A0E0A")

    ss = getSampleStyleSheet()
    est_titulo = ParagraphStyle("t", parent=ss["Title"], textColor=verde, fontSize=20)
    est_h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=verde)
    est_h3 = ParagraphStyle("h3", parent=ss["Heading3"], textColor=naranja)
    est_n = ParagraphStyle("n", parent=ss["BodyText"], textColor=negro, fontSize=10, leading=14)
    est_meta = ParagraphStyle("m", parent=ss["BodyText"], textColor=colors.HexColor("#555"), fontSize=8)
    est_clasif = ParagraphStyle("c", parent=ss["BodyText"], textColor=naranja, fontSize=10)

    def P(txt, estilo):
        return Paragraph(_xml_escape(txt or "").replace("\n", "<br/>"), estilo)

    c = modelo["caso"]
    flow = []
    flow.append(P(modelo["encabezado"], est_titulo))
    flow.append(P(f"CLASIFICACION: {modelo['clasificacion']}  |  Perfil: {modelo['perfil']}", est_clasif))
    flow.append(Spacer(1, 4 * mm))
    meta = f"Caso: {c['codigo']} — {c['titulo']}"
    if c["investigador"]:
        meta += f"\nInvestigador: {c['investigador']}"
    meta += f"\nGenerado: {modelo['generado']} ({modelo['herramienta']})"
    flow.append(P(meta, est_meta))
    flow.append(Spacer(1, 3 * mm))
    flow.append(HRFlowable(width="100%", color=verde))

    if modelo["opciones"]["resumen"] and c["descripcion"]:
        flow.append(P("Resumen", est_h2)); flow.append(P(c["descripcion"], est_n))
    if modelo["opciones"]["objetivo"] and c["objetivo"]:
        flow.append(P("Objetivo / Alcance", est_h2)); flow.append(P(c["objetivo"], est_n))
    if modelo["opciones"]["autorizacion"] and c["autorizacion"]:
        flow.append(P("Base de autorizacion", est_h2)); flow.append(P(c["autorizacion"], est_n))

    flow.append(P(f"Hallazgos ({modelo['total_hallazgos']})", est_h2))
    for h in modelo["hallazgos"]:
        cab = f"{h['numero']}. {h['titulo']} [{h['categoria']}]"
        if "confianza" in h:
            cab += f" ({h['confianza']})"
        flow.append(P(cab, est_h3))
        if h["contenido"]:
            flow.append(P(h["contenido"], est_n))
        lineas = []
        if h.get("fuente"):
            lineas.append(f"Fuente: {h['fuente']}")
        if h.get("url"):
            lineas.append(f"URL: {h['url']}")
        if h.get("fecha_dato"):
            lineas.append(f"Fecha del dato: {h['fecha_dato']}")
        if h.get("autor"):
            lineas.append(f"Cargado por: {h['autor']}")
        if h.get("hash_evidencia"):
            lineas.append(f"SHA-256: {h['hash_evidencia']}")
        for a in h.get("adjuntos", []):
            lineas.append(f"Adjunto: {a['nombre']} (SHA-256: {a['hash']})")
        if lineas:
            flow.append(P("\n".join(lineas), est_meta))
        flow.append(Spacer(1, 2 * mm))

    flow.append(Spacer(1, 4 * mm))
    flow.append(HRFlowable(width="100%", color=verde))
    if modelo["pie"]:
        flow.append(P(modelo["pie"], est_meta))
    flow.append(P(FIRMA, est_meta))

    doc = SimpleDocTemplate(str(ruta), pagesize=A4,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            title=modelo["encabezado"], author=c["investigador"] or "BLACKCAT")
    doc.build(flow)


# ---------------------------------------------------------------------------
# DOCX (python-docx) — texto plano, la libreria escapa sola
# ---------------------------------------------------------------------------
def a_docx(modelo: dict, ruta: Path) -> None:
    from docx import Document
    from docx.shared import Pt, RGBColor

    verde = RGBColor(0x1F, 0xA8, 0x0B)
    naranja = RGBColor(0xC2, 0x50, 0x00)
    c = modelo["caso"]
    doc = Document()

    t = doc.add_heading(modelo["encabezado"], level=0)
    for run in t.runs:
        run.font.color.rgb = verde
    p = doc.add_paragraph()
    r = p.add_run(f"CLASIFICACION: {modelo['clasificacion']}  |  Perfil: {modelo['perfil']}")
    r.font.color.rgb = naranja
    r.font.size = Pt(10)

    meta = doc.add_paragraph()
    meta.add_run(f"Caso: {c['codigo']} — {c['titulo']}\n").bold = True
    if c["investigador"]:
        meta.add_run(f"Investigador: {c['investigador']}\n")
    meta.add_run(f"Generado: {modelo['generado']} ({modelo['herramienta']})")

    if modelo["opciones"]["resumen"] and c["descripcion"]:
        doc.add_heading("Resumen", level=1); doc.add_paragraph(c["descripcion"])
    if modelo["opciones"]["objetivo"] and c["objetivo"]:
        doc.add_heading("Objetivo / Alcance", level=1); doc.add_paragraph(c["objetivo"])
    if modelo["opciones"]["autorizacion"] and c["autorizacion"]:
        doc.add_heading("Base de autorizacion", level=1); doc.add_paragraph(c["autorizacion"])

    doc.add_heading(f"Hallazgos ({modelo['total_hallazgos']})", level=1)
    for h in modelo["hallazgos"]:
        cab = f"{h['numero']}. {h['titulo']} [{h['categoria']}]"
        if "confianza" in h:
            cab += f" ({h['confianza']})"
        hd = doc.add_heading(cab, level=2)
        for run in hd.runs:
            run.font.color.rgb = naranja
        if h["contenido"]:
            doc.add_paragraph(h["contenido"])
        detalle = []
        if h.get("fuente"):
            detalle.append(f"Fuente: {h['fuente']}")
        if h.get("url"):
            detalle.append(f"URL: {h['url']}")
        if h.get("fecha_dato"):
            detalle.append(f"Fecha del dato: {h['fecha_dato']}")
        if h.get("autor"):
            detalle.append(f"Cargado por: {h['autor']}")
        if h.get("hash_evidencia"):
            detalle.append(f"SHA-256: {h['hash_evidencia']}")
        for a in h.get("adjuntos", []):
            detalle.append(f"Adjunto: {a['nombre']} (SHA-256: {a['hash']})")
        if detalle:
            pd = doc.add_paragraph("\n".join(detalle))
            for run in pd.runs:
                run.font.size = Pt(8)

    if modelo["pie"]:
        doc.add_paragraph(modelo["pie"])
    doc.add_paragraph(FIRMA)
    doc.save(str(ruta))


# ---------------------------------------------------------------------------
# Punto de entrada: exportar a un formato y devolver ruta + hash
# ---------------------------------------------------------------------------
FORMATOS = ("md", "html", "pdf", "docx")


def exportar(caso, perfil, formato: str, dir_salida: Path) -> dict:
    formato = formato if formato in FORMATOS else "pdf"
    modelo = construir_modelo(caso, perfil)
    dir_salida.mkdir(parents=True, exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug_perfil = "".join(ch for ch in perfil.nombre.lower().replace(" ", "-") if ch.isalnum() or ch == "-")
    nombre = f"{caso.codigo}_{slug_perfil}_{sello}.{formato}"
    ruta = dir_salida / nombre

    if formato == "md":
        ruta.write_text(a_markdown(modelo), encoding="utf-8")
    elif formato == "html":
        ruta.write_text(a_html(modelo), encoding="utf-8")
    elif formato == "pdf":
        a_pdf(modelo, ruta)
    elif formato == "docx":
        a_docx(modelo, ruta)

    return {
        "ruta": str(ruta),
        "nombre": nombre,
        "formato": formato,
        "sha256": seguridad.sha256_archivo(ruta),
        "total_hallazgos": modelo["total_hallazgos"],
    }
