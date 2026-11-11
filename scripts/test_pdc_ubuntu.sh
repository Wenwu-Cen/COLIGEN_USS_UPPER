#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
exe="$(find . -maxdepth 1 -type f -name 'COLIGEN_USS_UPPER_CAN_v*_Ubuntu_x86_64' -printf '%f\n' | sort -V | tail -n 1)"
test -n "$exe" || { printf 'Run this script from an extracted Ubuntu release\n' >&2; exit 1; }
exec "./$exe" --pdc-sound-test
