"""Explicit installation of the two skills; never overwrites existing skills."""
import argparse
import json
import os
from pathlib import Path
import shutil

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME', Path.home()/'.codex')))
    args = parser.parse_args()
    bridge = args.bridge.expanduser().resolve(strict=True)
    if not bridge.is_file():
        parser.error('--bridge must be a built adapter DLL')
    source = Path(__file__).resolve().parents[1]/'skills'
    targets = [(source/name, args.codex_home.expanduser()/'skills'/name) for name in ('graphiphy-code','rea-graphiphy')]
    if any(dst.exists() for _, dst in targets):
        parser.error('An installed skill already exists; back it up and review before replacing manually.')
    for src, dst in targets:
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__','engine.json'))
    config = targets[0][1]/'scripts'/'engine.json'
    config.write_text(json.dumps({'bridge':str(bridge)},indent=2)+'\n',encoding='utf-8')
    print('Installed graphiphy-code and rea-graphiphy; existing configuration was not modified.')

if __name__ == '__main__':
    main()
