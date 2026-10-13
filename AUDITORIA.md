# Auditoría y reconstrucción — BLACKCAT

**Proyecto:** blackcat-osint-reporter
**Responsable:** Miguel — El Suinda
**Fecha:** 2026-10-12

Este documento registra la auditoría de la versión original del repositorio y la
reconstrucción completa de la herramienta con desarrollo seguro.

## 1. Resumen

La versión original era un esqueleto de aplicación Flask (generador de informes OSINT
con autenticación LDAP/local) incompleto y no funcional, con varias fallas de
seguridad graves — entre ellas la exposición de una clave privada. Se decidió
**reconstruir la herramienta desde cero** manteniendo el concepto (BLACKCAT: informes
OSINT), reorientándola a una **estación de uso local para el investigador**, con
informes customizables por destinatario y un modo colaborativo opcional en red local.

## 2. Hallazgos de la versión original

| # | Severidad | Hallazgo | Estado |
|---|-----------|----------|--------|
| 1 | **Crítica** | Clave SSH privada (`githubkey`) versionada en el repo público. El `.gitignore` no la cubría (sin extensión). | Eliminada del árbol y del historial; `.gitignore` reforzado. Requiere **revocación de la clave** en GitHub. |
| 2 | **Crítica** | Usuario `admin` con contraseña fija `SecretPassword` creado automáticamente e impreso por consola. | Eliminado. BLACKCAT no crea usuarios por defecto. |
| 3 | **Alta** | Inyección HTML/SSRF en la generación de PDF (texto del informe interpolado sin escape; `pdfkit`/wkhtmltopdf). | Eliminada. PDF con ReportLab (sin binario externo) y escape de todo el contenido. |
| 4 | **Alta** | Inyección LDAP en el armado del DN y los filtros de autenticación. | Eliminada. Se quitó LDAP; el acceso local no requiere login y el modo compartido usa token. |
| 5 | **Alta** | Escucha en `0.0.0.0` por defecto y configuración `default` con `DEBUG=True`. | Corregido. `127.0.0.1` por defecto y `DEBUG` siempre apagado. |
| 6 | **Media** | Sin protección CSRF pese a tener Flask-WTF disponible. | Corregido. CSRF en todos los formularios. |
| 7 | **Media** | Exportación de informes sin control de pertenencia (IDOR). | Resuelto por diseño: estación local de un investigador / colaboración autenticada por token. |
| 8 | **Media** | `playsound` ejecutándose en el servidor; dependencias problemáticas. | Eliminadas. |
| 9 | **Baja** | Imports rotos, modelos vacíos: la aplicación no arrancaba. | Resuelto: base de código nueva, probada y funcional. |

## 3. Reconstrucción — medidas aplicadas

- Sin secretos en el código; `SECRET_KEY` autogenerada con permisos `600`.
- Validación de entrada con whitelist; URLs restringidas a `http`/`https`.
- Escape de salida en HTML, PDF, DOCX y Markdown.
- Subidas validadas por contenido (magic bytes), nombre aleatorio y límite de tamaño.
- Cabeceras de seguridad (CSP sin scripts inline, X-Frame-Options, nosniff, Referrer-Policy).
- Descargas protegidas contra *path traversal*.
- Modo compartido opt-in con clave de sesión aleatoria y comparación de tiempo constante.
- Batería de pruebas automatizadas (`pytest`) cubriendo seguridad, filtros de informe,
  exportación en los 4 formatos, escape de contenido malicioso y rutas web.

## 4. Acción pendiente a cargo del titular

La clave SSH expuesta estuvo publicada; además de eliminarla del repositorio, **debe
revocarse en GitHub y rotarse** (generar un par nuevo). Quitarla del historial no
basta: mientras la clave siga siendo válida, el riesgo persiste.

---

*Miguel — El Suinda · les petites cellules grises*
