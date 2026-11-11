#!/usr/bin/env bash
# Installs only this application for the current user; no sudo is required.
set -euo pipefail
source_dir="$(dirname "$(readlink -f "$0")")"
exe="$(find "$source_dir" -maxdepth 1 -type f -name 'COLIGEN_USS_UPPER_CAN_v*_Ubuntu_x86_64' -printf '%f\n' | sort -V | tail -n 1)"
test -n "$exe" || { printf 'Executable not found beside installer\n' >&2; exit 1; }
install_dir="$HOME/Applications/$(basename "$source_dir")"
if [ "$source_dir" != "$install_dir" ]; then
    mkdir -p "$install_dir"
    cp -a "$source_dir/." "$install_dir/"
fi
chmod +x "$install_dir/$exe"
desktop_dir="$(xdg-user-dir DESKTOP 2>/dev/null || printf '%s/Desktop' "$HOME")"
mkdir -p "$HOME/.local/share/applications" "$desktop_dir"
desktop="$HOME/.local/share/applications/coligen-uss-upper.desktop"
cat > "$desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=COLIGEN USS UPPER
Comment=Ultrasonic parking visualization
Exec="$install_dir/$exe"
Path=$install_dir
Icon=$install_dir/car.png
Terminal=false
Categories=Development;Engineering;
StartupWMClass=COLIGEN USS UPPER
EOF
chmod +x "$desktop"
cp "$desktop" "$desktop_dir/COLIGEN USS UPPER.desktop"
gio set "$desktop_dir/COLIGEN USS UPPER.desktop" metadata::trusted true 2>/dev/null || true
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
printf 'Installed: %s\nDesktop: %s\n' "$install_dir/$exe" "$desktop_dir/COLIGEN USS UPPER.desktop"
