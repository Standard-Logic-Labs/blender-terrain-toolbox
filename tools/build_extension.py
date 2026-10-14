"""Deterministic stdlib packaging and Blender v1 static repository index.
Run from anywhere: python tools/build_extension.py
Does not substitute for Blender's extension validate command.
"""
import hashlib
import json
from pathlib import Path
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'terrain_authoring'
OUTPUT = ROOT / 'extensions'
BASE_URL = 'https://raw.githubusercontent.com/Standard-Logic-Labs/blender-terrain-toolbox/main/extensions/'


def build():
    manifest = tomllib.loads((SOURCE / 'blender_manifest.toml').read_text())
    OUTPUT.mkdir(exist_ok=True)
    archive = OUTPUT / f"{manifest['id']}-{manifest['version']}.zip"
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(SOURCE.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                info = zipfile.ZipInfo(path.relative_to(SOURCE).as_posix(),date_time=(2026,1,1,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info,path.read_bytes())
    data = {k:v for k,v in manifest.items() if k != 'build'}
    data.update(archive_url=BASE_URL+archive.name,archive_size=archive.stat().st_size,
                archive_hash='sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest())
    index = dict(version='v1',blocklist=[],data=[data])
    (OUTPUT/'index.json').write_text(json.dumps(index,indent=2)+'\n')
    print(f'{archive.name}: {archive.stat().st_size:,} bytes')
    print(data['archive_hash'])
    return archive


if __name__ == '__main__':
    build()
