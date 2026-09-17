# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))
from app_version import EXE_STEM


a = Analysis(
    ['src/VehUpperDemo_CAN.py'],
    pathex=['src'],
    binaries=[
        # CanOnlinePort locates the root copy, while zlgcan-driver 0.3.0
        # appends windows/x86_64/zlgcan.dll to the supplied library root.
        ('library/zlgcan.dll', 'can_assets/library'),
        ('library/zlgcan.dll', 'can_assets/library/windows/x86_64'),
        ('library/vxlapi.dll', 'can_assets/library'),
    ],
    datas=[
        ('assets/car.ico', '.'),
        ('config/can_upper_config.toml', '.'),
        ('library/bitrate.cfg.yaml', 'can_assets/library'),
        (
            'library/windows/x86_64/kerneldlls',
            'can_assets/library/windows/x86_64/kerneldlls',
        ),
        ('../CAN_S20/Database/M18_Upper_Interface_241113.dbc', 'can_assets/Database'),
        ('../CAN_S20/Database/ObstacleTrack_M20251104.dbc', 'can_assets/Database'),
    ],
    hiddenimports=[
        'can', 'can.io.blf', 'can.interfaces.vector',
        'can.interfaces.vector.canlib', 'can.interfaces.vector.xldriver',
        'cantools', 'numpy', 'zlgcan', 'zlgcan_driver', 'app_version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=EXE_STEM,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/car.ico'],
)
