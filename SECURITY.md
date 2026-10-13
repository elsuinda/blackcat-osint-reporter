# Seguridad de BLACKCAT

BLACKCAT maneja información sensible de investigaciones. Estas son las medidas de
seguridad implementadas y las recomendaciones de uso.

## Diseño seguro

- **Sin secretos en el código.** La `SECRET_KEY` se genera de forma aleatoria la
  primera vez y se guarda en `~/.blackcat/config.json` con permisos `600`. No hay
  contraseñas, claves ni tokens embebidos en el repositorio.
- **Sin usuarios por defecto.** No se crea ningún administrador con credenciales
  conocidas.
- **Protección CSRF** en todos los formularios (Flask-WTF).
- **Cabeceras de seguridad** en toda respuesta: `Content-Security-Policy`
  (sin scripts inline), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: no-referrer`.
- **Validación de entrada con whitelist.** Las opciones (categorías, confianza,
  clasificación, etc.) se validan contra listas cerradas. Las URLs solo admiten
  `http`/`https` (se descartan `javascript:`, `file:`, `data:`…).
- **Escape de salida en todos los formatos.** HTML y PDF escapan el contenido del
  usuario; nunca se interpola texto crudo. No se usan motores que ejecuten HTML
  arbitrario (el PDF se genera con ReportLab, sin binarios externos).
- **Subidas validadas por contenido** (magic bytes), no solo por extensión; nombre
  de guardado aleatorio (UUID); límite de 10 MB por archivo.
- **Descargas protegidas** contra *path traversal* (se verifica que el archivo esté
  dentro del directorio de informes).
- **`DEBUG` siempre apagado** y escucha en `127.0.0.1` por defecto.
- **Cookies** `HttpOnly` y `SameSite=Lax`.

## Modo compartido (red local)

- Se activa explícitamente con `blackcat start --share`.
- Exige una **clave de sesión aleatoria** generada en cada arranque; la comparación
  es de tiempo constante (`hmac.compare_digest`).
- Registra la actividad de cada contribuyente (quién, qué, cuándo, IP).
- **No debe exponerse a internet.** Está pensado para una LAN de confianza. Para
  acceso remoto, usá una VPN; no abras el puerto en el router.

## Datos

- Todo el estado vive bajo `~/.blackcat/` (base SQLite, config, subidas, informes),
  con permisos restrictivos. Nada se versiona ni se envía a terceros.

## Reporte de vulnerabilidades

Si encontrás un problema de seguridad, reportalo de forma privada al responsable del
proyecto antes de divulgarlo.
