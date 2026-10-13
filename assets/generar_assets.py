#!/usr/bin/env python3
"""Genera el logo y los iconos de BLACKCAT (gato negro, paleta Hercule).

Silueta de gato negro sentado, ojos verde fluor (#39FF14), nariz naranja
(#FF6A00), glow CRT, sobre tile oscuro. Produce:
  - web/static/img/logo.svg        (logo con tile, para la UI)
  - web/static/img/favicon.png     (64 px)
  - assets/blackcat-512.png        (icono app grande)
  - assets/blackcat-256.png
  - assets/blackcat.ico            (multi-size para Windows/.desktop)
Reproducible: correr  python assets/generar_assets.py
"""
from pathlib import Path

import cairosvg
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
IMG = RAIZ / "blackcat" / "web" / "static" / "img"
ASSETS = RAIZ / "assets"

NEGRO = "#0A0E0A"
NEGRO2 = "#05070a"
VERDE = "#39FF14"
VERDE2 = "#1FA80B"
NARANJA = "#FF6A00"

# Silueta de gato negro sentado, de frente (viewBox 512x512).
# Todas las piezas comparten el mismo negro => se leen como una sola silueta.
_SILUETA = f"""
  <g fill="{NEGRO2}">
    <!-- cuerpo (campana) -->
    <path d="M256 248 C182 248 150 326 150 404 C150 436 170 452 202 454
             L310 454 C342 452 362 436 362 404 C362 326 330 248 256 248 Z"/>
    <!-- patas delanteras -->
    <ellipse cx="216" cy="452" rx="26" ry="18"/>
    <ellipse cx="296" cy="452" rx="26" ry="18"/>
    <!-- cola curva a la derecha -->
    <path d="M352 446 C424 452 448 380 424 326 C412 300 384 304 388 338
             C393 376 372 408 338 416 Z"/>
    <!-- cabeza -->
    <ellipse cx="256" cy="196" rx="94" ry="84"/>
    <!-- orejas -->
    <polygon points="184,132 166,48 242,116"/>
    <polygon points="328,132 346,48 270,116"/>
  </g>
  <!-- ojos verde fluor -->
  <g>
    <ellipse cx="224" cy="198" rx="17" ry="26" fill="{VERDE}"/>
    <ellipse cx="288" cy="198" rx="17" ry="26" fill="{VERDE}"/>
    <!-- pupilas (rendija) -->
    <ellipse cx="224" cy="198" rx="5" ry="20" fill="{NEGRO2}"/>
    <ellipse cx="288" cy="198" rx="5" ry="20" fill="{NEGRO2}"/>
  </g>
  <!-- nariz naranja -->
  <polygon points="256,228 246,220 266,220" fill="{NARANJA}"/>
  <!-- bigotes -->
  <g stroke="{VERDE2}" stroke-width="3" stroke-linecap="round" opacity="0.8">
    <path d="M252 232 C210 230 186 224 160 232" fill="none"/>
    <path d="M252 238 C212 240 190 244 166 252" fill="none"/>
    <path d="M260 232 C302 230 326 224 352 232" fill="none"/>
    <path d="M260 238 C300 240 322 244 346 252" fill="none"/>
  </g>
"""


def _svg(con_tile: bool) -> str:
    defs = f"""
    <defs>
      <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="5" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>"""
    fondo = ""
    if con_tile:
        fondo = (f'<rect x="20" y="20" width="472" height="472" rx="104" '
                 f'fill="{NEGRO}" stroke="{VERDE2}" stroke-width="6"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            f'{defs}{fondo}<g filter="url(#glow)">{_SILUETA}</g></svg>')


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    svg_tile = _svg(con_tile=True)
    (IMG / "logo.svg").write_text(svg_tile, encoding="utf-8")
    (ASSETS / "blackcat.svg").write_text(svg_tile, encoding="utf-8")

    def rasterizar(svg: str, destino: Path, px: int) -> None:
        cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                         write_to=str(destino), output_width=px, output_height=px)

    rasterizar(svg_tile, IMG / "favicon.png", 64)
    rasterizar(svg_tile, ASSETS / "blackcat-512.png", 512)
    rasterizar(svg_tile, ASSETS / "blackcat-256.png", 256)

    # .ico multi-size desde el PNG 512
    base = Image.open(ASSETS / "blackcat-512.png").convert("RGBA")
    base.save(ASSETS / "blackcat.ico",
              sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    print("Assets generados:")
    for p in (IMG / "logo.svg", IMG / "favicon.png",
              ASSETS / "blackcat-512.png", ASSETS / "blackcat-256.png", ASSETS / "blackcat.ico"):
        print("  -", p.relative_to(RAIZ))


if __name__ == "__main__":
    main()
