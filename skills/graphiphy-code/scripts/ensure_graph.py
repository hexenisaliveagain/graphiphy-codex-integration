"""Offline Graphiphy orchestration for source projects or REA artifacts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

def configured_bridge():
    override = os.environ.get('GRAPHIPHY_BRIDGE')
    if override:
        return Path(override).expanduser()
    config = Path(__file__).with_name('engine.json')
    if config.is_file():
        return Path(json.loads(config.read_text('utf-8'))['bridge']).expanduser()
    return Path(__file__).resolve().parents[3] / 'bridge-bin' / 'ReaGraphiphy.dll'


BRIDGE = configured_bridge()
EXTENSIONS = {'.cs', '.java', '.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx', '.ino'}
EXCLUDED = {'.git', '.hg', '.svn', '__pycache__', 'node_modules', '.tox', '.mypy_cache', '.pytest_cache',
            'dist', 'build', 'graphify-out', '.graphify-out', 'venv', '.venv', 'env', '.idea', '.vs',
            '.vscode', 'bin', 'obj', '.pio', 'debug', 'release', '.graphiphy-cache', 'extraction-cache'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(root):
    files = []
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDED and not Path(base, d).is_symlink()
                         and not Path(base, d).is_junction())
        for name in sorted(names):
            path = Path(base, name)
            if path.is_symlink():
                continue
            if path.suffix.lower() in EXTENSIONS or name == '.gitignore':
                files.append({'path': path.relative_to(root).as_posix(), 'sha256': digest(path),
                              'code': path.suffix.lower() in EXTENSIONS})
    return files


def run(args):
    artifact = args.artifact.resolve(strict=True) if args.artifact else None
    project = args.project.resolve(strict=True) if args.project else None
    if project is not None and not project.is_dir():
        raise ValueError('Project must be a directory')
    artifact_hash = digest(artifact) if artifact else None
    namespace = artifact_hash[:16] if artifact_hash else 'project-' + hashlib.sha256(str(project).casefold().encode()).hexdigest()[:16]
    sources = args.source or ([project] if project else [])
    if not sources:
        raise ValueError('--source is required in artifact mode')
    if project and args.output.resolve().is_relative_to(project):
        raise ValueError('Output must be outside the project')
    # Hash adapter and shipped dependencies: changed extractor => fresh graph/cache.
    engine_files = sorted(p for p in args.bridge.parent.rglob('*') if p.is_file()) if args.bridge.exists() else []
    engine = hashlib.sha256(json.dumps([(str(p.relative_to(args.bridge.parent)), digest(p))
                                        for p in engine_files]).encode()).hexdigest()
    results = []
    for source in sources:
        root = source.resolve(strict=True)
        if not root.is_dir():
            raise ValueError(f'Source must be an explicit code directory: {root}')
        if project and not root.is_relative_to(project):
            raise ValueError('Source must be inside the selected project')
        files = inventory(root)
        count = sum(f['code'] for f in files)
        if not count:
            results.append({'status': 'skipped_no_code', 'source_root': str(root)})
            continue
        if not args.bridge.is_file():
            results.append({'status': 'unavailable', 'reason': 'Graphiphy adapter missing', 'source_root': str(root)})
            continue
        identity = {'schema': 2, 'mode': 'artifact' if artifact else 'project',
                    'artifact': str(artifact) if artifact else None, 'artifact_sha256': artifact_hash,
                    'project_root': str(project) if project else None,
                    'source_root': str(root), 'engine_sha256': engine,
                    'helper_sha256': digest(Path(__file__)), 'files': files}
        fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        output = args.output.resolve() / namespace / fingerprint
        if output.is_relative_to(root):
            raise ValueError('Output must be outside source root')
        output.mkdir(parents=True, exist_ok=True)
        manifest_path = output / 'manifest.json'
        products = ['graph.json', 'upstream-graph.json', 'report.md', 'summary.json', 'warnings.json']
        try:
            manifest = json.loads(manifest_path.read_text('utf-8')) if manifest_path.exists() else {}
        except (ValueError, OSError):
            manifest = {}
        valid = (manifest.get('identity') == identity and all((output / p).is_file() and
                 manifest.get('products', {}).get(p) == digest(output / p) for p in products))
        status = 'cached' if valid else 'built'
        if not valid:
            command = ['dotnet', str(args.bridge.resolve()), str(root), str(output)]
            env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1')
            try:
                with (output / 'run.log').open('w', encoding='utf-8') as log:
                    process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                             env=env, timeout=600, check=False)
            except (OSError, subprocess.TimeoutExpired) as error:
                results.append({'status': 'failed', 'reason': str(error), 'output': str(output)})
                continue
            if process.returncode != 0:
                results.append({'status': 'failed', 'returncode': process.returncode, 'output': str(output)})
                continue
            if inventory(root) != files or (artifact and digest(artifact) != artifact_hash):
                results.append({'status': 'failed', 'reason': 'Inputs changed during analysis; retry with stable inputs',
                                'output': str(output)})
                continue
        manifest = {'identity': identity, 'products': {p: digest(output / p) for p in products},
                    'evidence': args.evidence, 'verified_at_unix': time.time(),
                    'limitations': 'Static decompiled/source navigation only; calls unresolved; see graph metadata and warnings.'}
        temporary = output / 'manifest.json.tmp'
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(manifest_path)
        summary = json.loads((output / 'summary.json').read_text('utf-8'))
        results.append({'status': status, 'source_files': count, 'output': str(output), **summary})
    result = {'mode': 'artifact' if artifact else 'project', 'artifact': str(artifact) if artifact else None,
              'artifact_sha256': artifact_hash, 'project_root': str(project) if project else None, 'results': results}
    if any(r['status'] in {'built', 'cached'} for r in results):
        latest = args.output.resolve() / namespace / 'latest.json'
        temporary = latest.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(latest)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--artifact', type=Path)
    mode.add_argument('--project', type=Path)
    parser.add_argument('--source', action='append', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--evidence', action='append', default=[])
    parser.add_argument('--bridge', type=Path, default=BRIDGE)
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if any(r['status'] in {'failed', 'unavailable'} for r in result['results']) else 0
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'failed', 'reason': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
