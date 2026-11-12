# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import base64
import zlib
import sys
from PyInstaller.utils.hooks import collect_data_files

sys.path.insert(0, str(Path("src").resolve()))
from app_version import EXE_STEM

# Compile the Console source into the frozen app instead of copying an external
# .py file. This preserves the payload on transparent-encryption Windows hosts.
bridge_payload_dir = Path("build/csplus-assets").resolve()
bridge_payload_dir.mkdir(parents=True, exist_ok=True)
bridge_source = Path("scripts/csplus_memory_bridge.py").read_text(encoding="utf-8-sig")
bridge_payload = base64.b85encode(zlib.compress(bridge_source.encode("ascii"))).decode("ascii")
(bridge_payload_dir / "csplus_bridge_payload.py").write_text(
    "BRIDGE_SOURCE_B85 = " + repr(bridge_payload) + "\n", encoding="ascii")


a = Analysis(
    ['src/VehUpperDemo_CAN.py'],
    pathex=['src', str(bridge_payload_dir)],
    binaries=[
        # CanOnlinePort locates the root copy, while zlgcan-driver 0.3.0
        # appends windows/x86_64/zlgcan.dll to the supplied library root.
        ('library/zlgcan.dll', 'can_assets/library'),
        ('library/zlgcan.dll', 'can_assets/library/windows/x86_64'),
        ('library/vxlapi.dll', 'can_assets/library'),
        ('library/vxlapi64.dll', 'can_assets/library'),
    ],
    # Include CTk themes and fonts in the single-file Windows release.
    datas=collect_data_files("customtkinter") + [
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
        'csplus_bridge_payload', 'can', 'can.io.blf', 'can.interfaces.vector',
        'can.interfaces.vector.canlib', 'can.interfaces.vector.xldriver',
        'cantools', 'numpy', 'zlgcan', 'zlgcan_driver', 'app_version',
        'lauterbach.trace32.rcl',
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
