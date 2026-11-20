#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
python3 -m venv build/ubuntu-venv
python=build/ubuntu-venv/bin/python
"$python" -m pip install tomli==2.2.1
"$python" - <<'PY'
import subprocess, sys, tomli
with open("pyproject.toml", "rb") as stream:
    project = tomli.load(stream)
subprocess.check_call([sys.executable, "-m", "pip", "install",
    *project["project"]["dependencies"], *project["dependency-groups"]["dev"]])
PY
"$python" -m PyInstaller --clean --noconfirm \
    --workpath build/ubuntu/work --distpath build/ubuntu/dist scripts/pyinstaller/ubuntu.spec
version=$("$python" -c 'import sys; sys.path.insert(0,"src"); from app_version import APP_VERSION; print(APP_VERSION)')
release="COLIGEN_USS_UPPER_v${version}_Ubuntu_x86_64"
package="dist/ubuntu/COLIGEN_USS_UPPER"
mkdir -p "$package"
# The stable package folder must contain only the current version's program.
for previous in "$package"/COLIGEN_USS_UPPER_v*_Ubuntu_x86_64; do
    if [ -f "$previous" ] && [ "$(basename "$previous")" != "$release" ]; then
        rm -- "$previous"
    fi
done
# Replace the executable atomically even if an earlier build is running.
install -m 755 "build/ubuntu/dist/COLIGEN_USS_UPPER_v${version}_Ubuntu_x86_64" "$package/.application.new"
mv -f "$package/.application.new" "$package/COLIGEN_USS_UPPER_v${version}_Ubuntu_x86_64"
cp config/ubuntu_config.toml "$package/viewer.toml"
cp docs/UBUNTU_RELEASE.md "$package/README.md"
cp docs/CHANGELOG.md "$package/"
cp docs/VEHICLE_PROFILES.md "$package/"
cp docs/GIT_DECRYPT_DIFF.md "$package/"
cp assets/car.png "$package/"
cp scripts/install_ubuntu.sh "$package/install-desktop.sh"
cp scripts/test_pdc_ubuntu.sh "$package/test-pdc-sound.sh"
chmod +x "$package/"*Ubuntu_x86_64 "$package/"*.sh
tar -C dist/ubuntu -czf "dist/$release.tar.gz" COLIGEN_USS_UPPER
(cd dist && sha256sum "$release.tar.gz") > "dist/$release.tar.gz.sha256"
printf 'Ubuntu release: %s\n' "$package"
