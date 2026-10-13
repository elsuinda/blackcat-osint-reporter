"""Formularios WTForms. Dan CSRF automatico y validacion de entrada."""
from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField, DateField, SelectField, StringField, SubmitField, TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from ..core import models

_URL_MSG = "Solo se admiten direcciones http:// o https://"


def _url_opcional(form, field):
    v = (field.data or "").strip()
    if v and not (v.startswith("http://") or v.startswith("https://")):
        raise ValidationError(_URL_MSG)


_op_clasif = [(x, x.capitalize()) for x in models.CLASIFICACIONES]
_op_estado = [(x, x.replace("_", " ").capitalize()) for x in models.ESTADOS_CASO]
_op_categoria = [(x, x.replace("_", " ").capitalize()) for x in models.CATEGORIAS_HALLAZGO]
_op_confianza = [(x, x.replace("_", " ").capitalize()) for x in models.NIVELES_CONFIANZA]
_op_sensibilidad = [(x, x.capitalize()) for x in models.NIVELES_SENSIBILIDAD]


class CasoForm(FlaskForm):
    titulo = StringField("Titulo", validators=[DataRequired(), Length(max=200)])
    investigador = StringField("Investigador", validators=[Optional(), Length(max=120)])
    clasificacion = SelectField("Clasificacion", choices=_op_clasif, default="interno")
    estado = SelectField("Estado", choices=_op_estado, default="abierto")
    descripcion = TextAreaField("Resumen / descripcion", validators=[Optional(), Length(max=20000)])
    objetivo = TextAreaField("Objetivo / alcance", validators=[Optional(), Length(max=20000)])
    autorizacion = TextAreaField("Base de autorizacion (etica/legal)",
                                 validators=[Optional(), Length(max=20000)])
    submit = SubmitField("Guardar caso")


class HallazgoForm(FlaskForm):
    titulo = StringField("Titulo", validators=[DataRequired(), Length(max=200)])
    categoria = SelectField("Categoria", choices=_op_categoria, default="otro")
    confianza = SelectField("Confianza", choices=_op_confianza, default="sin_verificar")
    sensibilidad = SelectField("Sensibilidad", choices=_op_sensibilidad, default="normal")
    fuente = StringField("Fuente", validators=[Optional(), Length(max=300)])
    url = StringField("URL", validators=[Optional(), Length(max=1000), _url_opcional])
    fecha_dato = DateField("Fecha del dato", validators=[Optional()])
    contenido = TextAreaField("Contenido / detalle", validators=[Optional(), Length(max=100000)])
    imagen = FileField("Adjuntar imagen",
                       validators=[Optional(),
                                   FileAllowed(["png", "jpg", "jpeg", "gif", "bmp", "webp"],
                                               "Solo imagenes")])
    submit = SubmitField("Guardar hallazgo")


class PerfilForm(FlaskForm):
    nombre = StringField("Nombre del perfil", validators=[DataRequired(), Length(max=80)])
    descripcion = StringField("Descripcion", validators=[Optional(), Length(max=300)])
    encabezado = StringField("Encabezado del informe", validators=[Optional(), Length(max=200)])
    pie = StringField("Pie de pagina", validators=[Optional(), Length(max=200)])
    clasificacion = SelectField("Clasificacion", choices=_op_clasif, default="interno")
    sensibilidad_max = SelectField("Incluir sensibilidad hasta", choices=_op_sensibilidad,
                                    default="interno")
    confianza_min = SelectField("Incluir confianza desde", choices=_op_confianza,
                                default="sin_verificar")
    incluir_resumen = BooleanField("Resumen", default=True)
    incluir_objetivo = BooleanField("Objetivo/alcance", default=True)
    incluir_autorizacion = BooleanField("Base de autorizacion", default=False)
    incluir_hallazgos = BooleanField("Hallazgos", default=True)
    incluir_fuentes = BooleanField("Fuentes", default=True)
    incluir_url = BooleanField("URLs", default=True)
    incluir_confianza = BooleanField("Nivel de confianza", default=True)
    incluir_metadatos = BooleanField("Metadatos", default=True)
    incluir_hashes = BooleanField("Hashes de integridad", default=False)
    incluir_adjuntos = BooleanField("Adjuntos", default=True)
    submit = SubmitField("Guardar perfil")


class ExportForm(FlaskForm):
    perfil_id = SelectField("Perfil de destinatario", coerce=int, validators=[DataRequired()])
    formato = SelectField("Formato", choices=[
        ("pdf", "PDF"), ("docx", "Word (DOCX)"),
        ("html", "HTML"), ("md", "Markdown"),
    ], default="pdf")
    submit = SubmitField("Generar informe")


class AccesoForm(FlaskForm):
    nombre = StringField("Tu nombre / alias", validators=[DataRequired(), Length(max=120)])
    token = StringField("Clave de la sesion", validators=[DataRequired(), Length(max=200)])
    submit = SubmitField("Entrar")
