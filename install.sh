#!/usr/bin/env bash
# =====================================================================
#  BLACKCAT - instalador
#  Crea el entorno virtual, instala dependencias, deja el comando
#  'blackcat' disponible en el sistema y el acceso directo en el menu.
#
#  Uso:
#    ./install.sh         (como usuario: instala para el usuario actual)
#    sudo ./install.sh    (como root: instala para todo el sistema)
#  El Suinda @v@  -  les petites cellules grises
# =====================================================================
set -euo pipefail

APP_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$APP_DIR/.venv"

G="\e[38;2;57;255;20m"; D="\e[38;2;31;168;11m"; O="\e[38;2;255;106;0m"; R="\e[0m"
ok(){ printf "  ${G}[ ok ]${R} %b\n" "$1"; }
info(){ printf "  ${D}[ .. ]${R} %b\n" "$1"; }
warn(){ printf "  ${O}[ !! ]${R} %b\n" "$1"; }

printf "\n  ${G}B L A C K C A T${R}  ${O}- instalacion -${R}\n\n"

ES_ROOT=0; [ "$(id -u)" -eq 0 ] && ES_ROOT=1

# --- dependencias de sistema (si falta python venv) ---
if ! python3 -c "import venv" >/dev/null 2>&1; then
  warn "falta python3-venv. Instalalo:  sudo apt-get install -y python3-venv"
fi

# --- entorno virtual ---
info "creando entorno virtual..."
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip >/dev/null 2>&1 || true
info "instalando dependencias (puede tardar)..."
"$VENV/bin/pip" install -q -r "$APP_DIR/requirements.txt"
ok "dependencias instaladas."

chmod +x "$APP_DIR/bin/blackcat"

# --- comando 'blackcat' en el PATH ---
if [ "$ES_ROOT" -eq 1 ]; then
  BIN_DEST="/usr/local/bin/blackcat"
  ICON_DEST="/usr/share/pixmaps/blackcat.png"
  DESK_DEST="/usr/share/applications/blackcat.desktop"
else
  mkdir -p "$HOME/.local/bin" "$HOME/.local/share/icons" "$HOME/.local/share/applications"
  BIN_DEST="$HOME/.local/bin/blackcat"
  ICON_DEST="$HOME/.local/share/icons/blackcat.png"
  DESK_DEST="$HOME/.local/share/applications/blackcat.desktop"
fi

ln -sf "$APP_DIR/bin/blackcat" "$BIN_DEST"
ok "comando disponible: $BIN_DEST"

# --- icono ---
cp -f "$APP_DIR/assets/blackcat-512.png" "$ICON_DEST" 2>/dev/null || true

# --- acceso directo de aplicacion ---
cat > "$DESK_DEST" <<EOF
[Desktop Entry]
Type=Application
Name=BLACKCAT
GenericName=Informes OSINT
Comment=Estacion local de informes OSINT (Hercule)
Exec=$BIN_DEST start
Icon=$ICON_DEST
Terminal=false
Categories=Network;Security;Office;
Keywords=osint;informe;hercule;blackcat;
EOF
ok "acceso directo creado: $DESK_DEST"

if [ "$ES_ROOT" -eq 0 ] && ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
  warn "agrega ~/.local/bin al PATH:  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

printf "\n"
ok "BLACKCAT instalado."
info "arrancalo con:   blackcat start"
info "en red local:    blackcat start --share"
info "detenelo con:    blackcat stop"
printf "  ${D}-- les petites cellules grises${R}\n\n"
