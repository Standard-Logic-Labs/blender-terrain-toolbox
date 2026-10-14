# Blender Terrain Toolbox

A small, editable volumetric terrain prototype for **Blender 5.2.2 LTS** (user-supplied target). Version **0.1.0**, milestone 1. Blender is unavailable in the authoring environment: UI, undo/redo, actual `.blend` roundtrip and installation are **not yet verified in Blender**. The executable version is printed at registration and in the panel.

## Install from a remote extension repository

Use this URL in Blender, **not** the Git clone URL:

```text
https://raw.githubusercontent.com/Standard-Logic-Labs/blender-terrain-toolbox/main/extensions/index.json
```

1. Open **Edit > Preferences > Get Extensions**. Allow online access if prompted.
2. Open the **Repositories** menu, use **+ > Add Remote Repository**, and paste the URL above. Give it a recognizable name such as **Standard Logic Labs** if that field is shown.
3. Refresh/synchronize repositories, search **Terrain Toolbox**, and click **Install**. Enable the add-on if required.
4. In the 3D Viewport press **N**, then open the **Terrain** tab.
5. Click **Create Two Preview Tiles**, then **Frame Terrain**.
6. Click **Add Boundary Test Cut**. Both tiles rebuild with one spherical cavity across X = 512 m.

Remote installation and menu labels must be confirmed in your Blender build. The index uses Blender's documented v1 static repository format. Hosting requires no GitHub Pages configuration and no updater code or network permissions inside the extension.

Fallback: download [terrain_authoring-0.1.0.zip](https://raw.githubusercontent.com/Standard-Logic-Labs/blender-terrain-toolbox/main/extensions/terrain_authoring-0.1.0.zip) and use **Get Extensions > Install from Disk**. GitHub's **Download ZIP** is the source checkout, not the installable extension.

## What this milestone implements

- Two tool-owned 512 × 512 m tiles at a default 32 m voxel spacing, in one world-space field.
- Procedural base relief (seed 17) and an ordered sphere subtraction crossing the tile boundary. The cavity includes an undercut, demonstrating a volumetric surface.
- Streaming 8-cell chunks with a one-cell sampling halo, fixed conforming marching tetrahedra, canonical edge interpolation, and shared field-derived normals.
- Persistent versioned JSON source on the Scene; generated meshes are disposable output. Save/open uses Blender's normal `.blend` workflow.
- Explicit undoable creation, operation, regeneration, settings, reset, and display operators. No timers or geometry-changing callbacks.
- A toggleable planar **1 m reference guide**, with wider lines every 5 or 10 m, independent of voxel spacing; a separate mesh wireframe toggle.
- Configurable preview/final spacing and aligned vertical bounds, cost estimate and a build limit.
- Clean module reload script and deterministic test terrain reset.

The guide is at a configurable world-Z datum (default 0.05 m), shown in front of geometry, and hidden from renders. It is **not surface-conforming**. Zoom in to see 1 m intervals; at full-tile scale they are subpixel.

The creation operator sets metric units and unit scale 1; it does not rescale existing objects. Use a fresh scene for the first test. It preserves unrelated objects. Generated object transforms are locked; editing output meshes is temporary and regeneration replaces them.

## Test and development

From a checkout, Python 3.11+ (standard library only):

```sh
python -m unittest discover -s tests -v
python -m compileall -q terrain_authoring tests dev tools
```

Background Blender integration test, Windows PowerShell example (replace the executable path):

```powershell
python tests/run_blender_tests.py --blender 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
```

This launches two isolated factory-startup processes, checks generated Blender meshes and border normals, saves a temporary `.blend`, opens it in the second process, and regenerates it. Failures return a nonzero exit code. It does **not** claim to test UI undo/redo.

See [manual Blender checklist](docs/MANUAL_TESTS.md), [architecture and next milestones](docs/ARCHITECTURE.md), and [test status](docs/TEST_RESULTS.md).

For fast development, disable the remotely installed copy, restart Blender once to remove its imported namespace, then open `dev/reload_addon.py` from this checkout in Blender's Text Editor and press **Alt-P**. Subsequent edits need only **Alt-P**, then **Regenerate from Saved Source**. If a copy is already loaded, the script reloads that copy and prints its exact path. It never silently switches between installed and checkout copies. Do not keep both active. Source and geometry survive unregister/register; save before reload, and reset undo expectations after code reload.

## Publishing updates

1. Modify one module, run the relevant tests and Blender checklist.
2. Increase `version` in `terrain_authoring/blender_manifest.toml`. Do not change the extension `id`.
3. Run `python tools/build_extension.py`. This produces a deterministic ZIP and matching index with SHA-256 and size.
4. Validate with your installed Blender:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --command extension validate extensions/terrain_authoring-0.1.0.zip
```

Use the current version's ZIP filename when publishing an update. Commit the source, generated ZIP, and `extensions/index.json` together. Blender's **Refresh / Check for Updates** then sees the newer version. GitHub Actions runs core/package tests and checks package reproducibility; it does not yet run Blender.

## Deliberate limits

This is a vertical slice, not the complete terrain product. Core source validation allows up to eight connected tiles, but the UI creates/resets only the two-tile test layout. It does not yet provide tile editing, curve operations, stamp assets, brush sculpting, smooth/flatten/blend controls, a general operation editor, adaptive LOD, collision/export, or production-resolution acceleration. Domain outer edges are intentionally open, not capped. See the architecture notes before extending extraction.

License: GPL-3.0-or-later. No third-party runtime dependencies.
