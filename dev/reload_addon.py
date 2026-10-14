"""Open in Blender's Text Editor and Alt-P. Reloads the currently loaded copy.
If no copy is loaded, registers the checkout adjacent to this dev/ directory.
Installed extensions use bl_ext.<repository>.terrain_authoring namespaces.
"""
import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
candidates = [(n,m) for n,m in list(sys.modules.items())
              if n == 'terrain_authoring' or (n.startswith('bl_ext.') and n.endswith('.terrain_authoring'))]
if len(candidates) > 1:
    raise RuntimeError('Multiple Terrain Toolbox copies are loaded. Disable duplicates before reloading.')
if candidates:
    name, addon = candidates[0]
    addon.unregister()
    for module in ('core.state','core.field','core.meshing','normals','bridge','operators','ui'):
        full = f'{name}.{module}'
        if full in sys.modules:
            importlib.reload(sys.modules[full])
    importlib.reload(addon)
else:
    if not (ROOT/'terrain_authoring'/'__init__.py').is_file():
        raise RuntimeError('Open this script from <checkout>/dev/reload_addon.py.')
    sys.path.insert(0,str(ROOT))
    addon = importlib.import_module('terrain_authoring')
addon.register()
print('Terrain development reload complete:',addon.__file__)
print('Saved source and meshes preserved. Regenerate explicitly to apply code changes.')
