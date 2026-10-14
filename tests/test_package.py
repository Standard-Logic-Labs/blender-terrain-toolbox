import hashlib
import json
from pathlib import Path
import tomllib
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class ExtensionPackageTests(unittest.TestCase):
    def test_index_matches_archive_and_source(self):
        index = json.loads((ROOT/'extensions/index.json').read_text())
        self.assertEqual(index['version'],'v1')
        entry = index['data'][0]
        archive = ROOT/'extensions'/entry['archive_url'].rsplit('/',1)[1]
        self.assertEqual(entry['archive_size'],archive.stat().st_size)
        self.assertEqual(entry['archive_hash'],'sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive) as z:
            self.assertIsNone(z.testzip())
            self.assertIn('__init__.py',z.namelist())
            manifest = tomllib.loads(z.read('blender_manifest.toml').decode())
            for k,v in manifest.items():
                if k != 'build':
                    self.assertEqual(v,entry[k])
            for name in z.namelist():
                self.assertNotIn('__pycache__',name)
                self.assertEqual(z.read(name),(ROOT/'terrain_authoring'/name).read_bytes())


if __name__ == '__main__':
    unittest.main()
