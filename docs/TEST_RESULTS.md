# Milestone 1 verification status

## Executed in the authoring environment

- Inspected the repository at initial commit `dc71ed65c6b3f35cc260abbe3b3163b34b375107`; only README existed. No existing terrain implementation or AGENTS instructions were present.
- Blender executable: not installed. `bpy`: not installed. User reports Blender **5.2.2 LTS**.
- `python -m unittest discover -s tests -v`: **17 passed**. Includes exact X-border edges/normals, Y-border and negative tile coordinates, changed chunk size, no internal unmatched or nonmanifold edges in the test output, undercut and outward winding, JSON regeneration, seed/enabled behavior, ordered booleans, validation, 16 m final seam, archive/index/source consistency, and six regression tests for dynamic-instance normal setters, fallback mapping, error handling and registration without mesh-class probing.
- `python -m compileall -q terrain_authoring tests dev tools`: **passed**.
- Official standalone extension CLI retrieved from the Blender `v5.2.2` source tag: ZIP `validate` passed. Static index fields matched official `server-generate` output (using an absolute archive URL). This runs packaging code only, not Blender.
- Tests use the Python standard library. No third-party runtime dependency is required.

## Provided but not yet executed in Blender

- `python tests/run_blender_tests.py --blender <path>`: two separate Blender processes; creates/regenerates meshes, checks Blender-space borders/custom normals, unregister/register, saves/reopens a .blend and compares source and geometry hashes.
- Full executable invocation of `blender --command extension validate` is still optional to repeat locally; the corresponding standalone official packaging validator passed here.
- Manual remote installation, viewport guide/shading, UI interaction, undo/redo and reload checklist.

Source-level correctness tests do not establish Blender UI compatibility. The user-supplied 5.2.2 target has not been executed here. The current documented mesh custom-normal API was checked; exact 5.2 API page retrieval was unavailable. Version 0.1.1 removes the invalid registration-time class-level capability check. Normal assignment now resolves methods on the actual staged mesh instance and reports the actual Blender version if neither documented setter exists.

## 0.1.1 correction

User reported the exact 0.1.0 registration error: "This Blender build lacks the required custom vertex-normal API". The guard used `hasattr(bpy.types.Mesh, ...)`, which is not a reliable test of instance RNA functions. Removed that guard. Added the instance-based adapter and preserved the same shared normal values for both vertex and corner APIs. A registration regression with an intentionally method-less class and dynamic-instance adapter tests passes. These doubles do not substitute for running Blender. The official binary download endpoint returned HTTP 403; native Blender tests remain pending. The 0.1.1 ZIP passed the official standalone 5.2.2 extension validator.
