"""Synthetic helpers/installation tests and an optional real-engine smoke test."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'skills/graphiphy-code/scripts/ensure_graph.py'
REA=ROOT/'skills/rea-graphiphy/scripts/ensure_graph.py'
ENGINE=os.environ.get('GRAPHIPHY_TEST_BRIDGE')

def invoke(helper, *args):
    return subprocess.run([sys.executable,'-B',str(helper),*map(str,args)],capture_output=True,text=True,encoding='utf-8')

class HelperTests(unittest.TestCase):
    def test_no_code_and_missing_engine_in_both_entrypoints(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir()
            missing=root/'missing.dll';artifact=root/'artifact.bin';artifact.write_bytes(b'synthetic')
            p=invoke(HELPER,'--project',source,'--output',root/'out','--bridge',missing)
            self.assertEqual(json.loads(p.stdout)['results'][0]['status'],'skipped_no_code')
            (source/'sample.ino').write_text('void setup() {}\nvoid loop() {}\n')
            p=invoke(REA,'--artifact',artifact,'--source',source,'--output',root/'out','--bridge',missing)
            self.assertEqual(p.returncode,1,p.stderr)
            self.assertEqual(json.loads(p.stdout)['results'][0]['status'],'unavailable')

    def test_project_rejects_external_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);project=root/'project';project.mkdir();other=root/'other';other.mkdir()
            p=invoke(HELPER,'--project',project,'--source',other,'--output',root/'out','--bridge',root/'missing.dll')
            self.assertEqual(p.returncode,1)
            self.assertIn('inside the selected project',json.loads(p.stdout)['reason'])

    def test_installation_is_portable_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);bridge=root/'adapter.dll';bridge.write_bytes(b'fixture, never executed')
            home=root/'codex';installer=ROOT/'scripts/install_skills.py'
            p=invoke(installer,'--bridge',bridge,'--codex-home',home)
            self.assertEqual(p.returncode,0,p.stderr)
            config=home/'skills/graphiphy-code/scripts/engine.json'
            self.assertEqual(Path(json.loads(config.read_text())['bridge']),bridge.resolve())
            p=invoke(installer,'--bridge',bridge,'--codex-home',home)
            self.assertNotEqual(p.returncode,0)
            artifact=root/'fixture.bin';artifact.write_bytes(b'fixture')
            source=root/'empty';source.mkdir()
            p=invoke(home/'skills/rea-graphiphy/scripts/ensure_graph.py','--artifact',artifact,'--source',source,'--output',root/'out')
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout)['results'][0]['status'],'skipped_no_code')

    @unittest.skipUnless(ENGINE,'Set GRAPHIPHY_TEST_BRIDGE for real extraction')
    def test_real_engine_cache_corruption_arduino_and_file_qualification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir()
            (source/'A.java').write_text('class A { void ping() {} }')
            (source/'B.java').write_text('class B { void ping() {} }')
            (source/'sample.ino').write_text('void setup() {}\nvoid loop() {}\n')
            def run():
                p=invoke(HELPER,'--project',source,'--output',root/'out','--bridge',ENGINE)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
                return json.loads(p.stdout)['results'][0]
            first=run();self.assertEqual(first['status'],'built')
            graph_path=Path(first['output'])/'graph.json'
            graph=json.loads(graph_path.read_text())
            pings=[n for n in graph['nodes'] if n['label']=='ping']
            self.assertEqual(len({n['id'] for n in pings}),2)
            self.assertTrue(any(n['source_file'].endswith('sample.ino') for n in graph['nodes']))
            self.assertEqual(run()['status'],'cached')
            graph_path.write_text('{}');self.assertEqual(run()['status'],'built')
            (source/'B.java').write_text('class B { void changed() {} }')
            changed=run();self.assertEqual(changed['status'],'built')
            self.assertNotEqual(changed['output'],first['output'])

if __name__=='__main__':unittest.main()
