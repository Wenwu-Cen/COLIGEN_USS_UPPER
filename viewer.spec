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
    ['src/app.py'],
    pathex=['src', str(bridge_payload_dir)],
    binaries=[
        ('library/windows/x86_64/zlgcan.dll', 'runtime_assets/library/windows/x86_64'),
        ('library/vxlapi64.dll', 'runtime_assets/library'),
        ('library/windows/x86_64/tosun/libTSCAN.dll', 'runtime_assets/library/windows/x86_64/tosun'),
        ('library/windows/x86_64/tosun/libTSH.dll', 'runtime_assets/library/windows/x86_64/tosun'),
    ],
    # Include CTk themes and fonts in the single-file Windows release.
    datas=collect_data_files("customtkinter") + [
        ('assets/car.ico', '.'),
        ('assets/car.png', '.'),
        ('config/viewer.toml', '.'),
        (
            'library/windows/x86_64/kerneldlls',
            'runtime_assets/library/windows/x86_64/kerneldlls',
        ),
        ('assets/dbc/M18_Upper_Interface_241113.dbc', 'runtime_assets/Database'),
        ('assets/dbc/ObstacleTrack_M20251104.dbc', 'runtime_assets/Database'),
        ('assets/dbc/IPC_matrix_UssDebugDataMCUtoSOC_V1.0_20261019_D4M6.dbc', 'runtime_assets/Database'),
    ],
    hiddenimports=[
        'csplus_bridge_payload', 'can', 'can.io.blf', 'can.interfaces.vector',
        'can.interfaces.vector.canlib', 'can.interfaces.vector.xldriver',
        'cantools', 'numpy', 'app_version',
        'serial', 'serial.tools.list_ports', 'serial.tools.list_ports_windows',
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
