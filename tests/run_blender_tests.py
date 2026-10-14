"""python tests/run_blender_tests.py --blender /absolute/path/to/blender"""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--blender',required=True)
a = p.parse_args()
script = Path(__file__).resolve().with_name('blender_integration.py')
with tempfile.TemporaryDirectory(prefix='terrain-toolbox-tests-') as output:
    for phase in ('create','reload'):
        subprocess.run([a.blender,'--background','--factory-startup','--python-exit-code','1',
                        '--python',str(script),'--',phase,output],check=True)
print('PASS: separate-process .blend source + mesh roundtrip and Blender seam checks')
print('UI, undo/redo, remote installation still require the manual checklist.')
