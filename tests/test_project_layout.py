"""The source distribution must build without the author's sibling projects."""
import ast
from pathlib import Path
import subprocess
import sys

from app_version import EXE_STEM
from can_source import DbcDecoder, _find_asset_dir

ROOT = Path(__file__).resolve().parent.parent


def test_models_and_parser_do_not_load_gui_or_hardware_readers():
    script = (
        "import sys; sys.path.insert(0, 'src'); import viewer_models, log_parser; "
        "assert 'tkinter' not in sys.modules; "
        "assert not any(name.endswith('_source') for name in sys.modules)"
    )
    subprocess.run([sys.executable, '-c', script], cwd=ROOT, check=True,
                   capture_output=True, text=True)


def test_dbc_assets_are_available_inside_this_project():
    assert _find_asset_dir('Database').resolve() == ROOT / 'assets' / 'dbc'
    decoder = DbcDecoder()
    assert decoder.accepts(0x640)
    assert (ROOT / 'assets/dbc/M18_Upper_Interface_241113.dbc').is_file()
    assert (ROOT / 'assets/dbc/ObstacleTrack_M20251104.dbc').is_file()


def test_specs_use_the_single_entry_and_local_assets():
    for name in ['viewer.spec', 'viewer_linux.spec']:
        source = (ROOT / name).read_text(encoding='utf-8-sig')
        tree = ast.parse(source)
        analyses = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == 'Analysis']
        assert len(analyses) == 1
        assert ast.literal_eval(analyses[0].args[0]) == ['src/app.py']
        for keyword in analyses[0].keywords:
            if keyword.arg == 'datas':
                paths = keyword.value.right.elts
                for entry in paths:
                    path = ast.literal_eval(entry.elts[0])
                    assert (ROOT / path).exists(), path
                    assert not path.startswith('../')
    assert EXE_STEM.startswith('COLIGEN_USS_UPPER_v')
