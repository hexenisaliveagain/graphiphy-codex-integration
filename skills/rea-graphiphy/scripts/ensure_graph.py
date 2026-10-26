"""REA compatibility entrypoint, sharing the installed project/artifact helper."""
from pathlib import Path
import runpy

helper = Path(__file__).resolve().parents[2] / 'graphiphy-code' / 'scripts' / 'ensure_graph.py'
if not helper.is_file():
    raise SystemExit('Install both companion skills; shared Graphiphy helper is missing.')
runpy.run_path(str(helper), run_name='__main__')
