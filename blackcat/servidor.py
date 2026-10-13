"""Arranque del servidor web de BLACKCAT.

Modos:
  - privado  (defecto): escucha en 127.0.0.1, sin clave. Solo esta maquina.
  - compartido (--share): escucha en la LAN (0.0.0.0) y exige una clave de
    sesion aleatoria para que colegas contribuyan al informe. La clave se
    genera en cada arranque y se guarda en runtime.json (permisos 600).

DEBUG siempre apagado. Sin secretos en el codigo.
"""
from __future__ import annotations

import argparse
import json
import socket
import stat

from . import __version__, config as cfgmod
from .core import seguridad

PUERTO_DEFECTO = 8733


def _ip_lan() -> str:
    """IP local para mostrar la URL en modo compartido (best-effort)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def _guardar_runtime(datos: dict) -> None:
    cfgmod.asegurar_directorios()
    cfgmod.ARCHIVO_RUNTIME.write_text(json.dumps(datos, indent=2), encoding="utf-8")
    try:
        cfgmod.ARCHIVO_RUNTIME.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def ejecutar(host: str | None = None, puerto: int = PUERTO_DEFECTO,
             compartido: bool = False, abrir: bool = False) -> None:
    from .web.app import create_app

    token = seguridad.token_sesion() if compartido else ""
    if host is None:
        host = "0.0.0.0" if compartido else "127.0.0.1"

    app = create_app(compartido=compartido, token=token)

    ip = _ip_lan() if compartido else "127.0.0.1"
    url = f"http://{ip}:{puerto}/"
    _guardar_runtime({
        "pid_url": url, "host": host, "puerto": puerto,
        "compartido": compartido, "token": token, "version": __version__,
    })

    print(f"\n  BLACKCAT v{__version__}  —  les petites cellules grises")
    if compartido:
        print("  Modo: COMPARTIDO (red local)")
        print(f"  URL para colegas : {url}")
        print(f"  Clave de sesion  : {token}")
        print("  (compartí la URL y la clave solo con quien corresponda)")
    else:
        print("  Modo: LOCAL (solo esta maquina)")
        print(f"  URL : {url}")
    print()

    if abrir and not compartido:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass

    # threaded=True para atender a varios contribuyentes en modo compartido.
    app.run(host=host, port=puerto, debug=False, threaded=True, use_reloader=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="blackcat-servidor",
                                 description="Servidor web de BLACKCAT (informes OSINT locales).")
    ap.add_argument("--share", action="store_true", help="exponer en la red local con clave de sesion")
    ap.add_argument("--host", default=None, help="interfaz de escucha (avanzado)")
    ap.add_argument("--port", type=int, default=PUERTO_DEFECTO, help=f"puerto (defecto {PUERTO_DEFECTO})")
    ap.add_argument("--open", action="store_true", help="abrir el navegador al iniciar (solo local)")
    ap.add_argument("--version", action="version", version=f"BLACKCAT {__version__}")
    args = ap.parse_args(argv)
    ejecutar(host=args.host, puerto=args.port, compartido=args.share, abrir=args.open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
