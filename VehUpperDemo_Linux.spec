# -*- mode: python ; coding: utf-8 -*-
"""Build natively on Ubuntu 22.04 x86_64; Windows vendor DLLs are excluded."""

from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files

sys.path.insert(0, str(Path("src").resolve()))
from app_version import EXE_STEM

a = Analysis(
    ["src/VehUpperDemo_CAN.py"],
    pathex=["src"],
    binaries=[],
    datas=collect_data_files("customtkinter") + [
        ("assets/car.png", "."),
        ("config/ubuntu_config.toml", "linux_defaults"),
        ("../CAN_S20/Database/M18_Upper_Interface_241113.dbc", "can_assets/Database"),
        ("../CAN_S20/Database/ObstacleTrack_M20251104.dbc", "can_assets/Database"),
    ],
    hiddenimports=[
        "can", "can.io.blf", "cantools", "numpy", "app_version",
        "lauterbach.trace32.rcl",
    ],
    excludes=["zlgcan", "zlgcan_driver", "can.interfaces.vector"],
    hookspath=[], hooksconfig={}, runtime_hooks=[], noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name=EXE_STEM + "_Ubuntu_x86_64",
    console=False, debug=False, strip=False, upx=False,
)
