<div align="center">

# 🐈‍⬛ BLACKCAT

**Estación local de informes OSINT — customizables por destinatario.**

Parte del ecosistema **Hercule** · *les petites cellules grises*

</div>

---

BLACKCAT es una herramienta de **uso local** para quien hace trabajo OSINT. No
recolecta por su cuenta: te da una estación ordenada para **registrar casos y
hallazgos** y, sobre todo, para **generar informes a medida de cada destinatario**
(técnico, gerencial, judicial, cliente…) a partir de los mismos datos.

Corre en tu máquina (`127.0.0.1`). Si lo necesitás, puede además levantar un
**servidor web en la red local** para que colegas contribuyan al informe, protegido
con una clave de sesión.

## Qué resuelve

- **Un caso, muchos informes.** El mismo material se entrega distinto según a quién
  va dirigido. Elegís un **perfil de destinatario** al exportar y BLACKCAT filtra
  secciones, nivel de detalle y sensibilidad automáticamente.
- **Trazabilidad.** Cada hallazgo y cada informe llevan su **hash SHA-256**.
- **Colaboración opcional en LAN.** Varios investigadores sobre un mismo caso, con
  registro de quién cargó qué — sin exponer nada a internet.

## Características

- Casos con código correlativo (`BC-AÑO-N`), alcance y **base de autorización**.
- Hallazgos con categoría, fuente, URL, **nivel de confianza** y **sensibilidad**.
- Adjuntos de imagen validados por contenido (no solo por extensión), con su hash.
- **4 perfiles de destinatario** listos + los que quieras crear.
- Exportación a **PDF, Word (DOCX), HTML y Markdown**.
- Tema oscuro con la estética Hercule (negro / verde fluor / naranja).

## Instalación

Requisitos: Python 3.11+ y `python3-venv`.

```bash
git clone https://github.com/elsuinda/blackcat-osint-reporter
cd blackcat-osint-reporter
./install.sh            # o: sudo ./install.sh  (instalación a nivel sistema)
```

El instalador crea el entorno virtual, deja el comando `blackcat` disponible y
agrega el acceso directo **BLACKCAT** al menú de aplicaciones.

> En Hercule (Debian 13 personalizado) esto lo hace el propio instalador de apps:
> BLACKCAT queda clonado e instalado, y su ficha de uso aparece en
> `Documents/Hercule/informes/apps/`.

## Uso

```bash
blackcat start            # servidor local + abre el navegador (http://127.0.0.1:8733)
blackcat start --share    # además lo publica en la red local (con clave de sesión)
blackcat status           # estado
blackcat stop             # detener
```

1. Creá un **caso** y cargá su objetivo y autorización.
2. Agregá **hallazgos** a medida que investigás (marcá su confianza y sensibilidad).
3. En el caso, elegí un **perfil de destinatario** y el **formato**, y generá el informe.

## Seguridad

BLACKCAT se construyó con desarrollo seguro de base: ver [SECURITY.md](SECURITY.md)
y la auditoría en [AUDITORIA.md](AUDITORIA.md). En resumen: sin secretos en el código
(la `SECRET_KEY` se autogenera con permisos `600`), protección CSRF, cabeceras de
seguridad (CSP, X-Frame-Options, nosniff), validación de entrada con whitelist,
escape en todos los formatos de salida, subidas validadas por contenido y `DEBUG`
siempre apagado. El modo compartido exige una clave de sesión aleatoria.

## Licencia

GPL-3.0. Ver [LICENSE](LICENSE).

---

<div align="center">

*Desarrollado por Miguel — El Suinda @v@*
*les petites cellules grises*

</div>
