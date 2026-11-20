# -*- mode: python ; coding: utf-8 -*-
"""Build natively on Ubuntu 22.04 x86_64; Windows vendor DLLs are excluded."""

from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files

sys.path.insert(0, str(Path("src").resolve()))
from app_version import EXE_STEM

a = Analysis(
    ["../../src/app.py"],
    pathex=[str(Path("src").resolve())],
    binaries=[],
    datas=collect_data_files("customtkinter") + [
        ("../../assets/car.png", "."),
        ("../../config/ubuntu_config.toml", "linux_defaults"),
        ("../../assets/dbc/M18_Upper_Interface_241113.dbc", "runtime_assets/Database"),
        ("../../assets/dbc/ObstacleTrack_M20251104.dbc", "runtime_assets/Database"),
        ("../../assets/dbc/IPC_matrix_UssDebugDataMCUtoSOC_V1.0_20261019_D4M6.dbc", "runtime_assets/Database"),
    ],
    hiddenimports=[
        "can", "can.io.blf", "cantools", "numpy", "app_version",
        "lauterbach.trace32.rcl",
        "serial", "serial.tools.list_ports", "serial.tools.list_ports_linux",
    ],
    excludes=["can.interfaces.vector"],
    hookspath=[], hooksconfig={}, runtime_hooks=[], noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name=EXE_STEM + "_Ubuntu_x86_64",
    console=False, debug=False, strip=False, upx=False,
)
