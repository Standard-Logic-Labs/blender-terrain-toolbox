# Terrain Toolbox development rules

Read README.md, docs/ARCHITECTURE.md, docs/TEST_RESULTS.md and the affected module before editing. Work in small runnable milestones; preserve source schema and deterministic world-space sampling. Never replace volumetric terrain with a heightfield-only representation.

- Blender user target: 5.2.2 LTS. Detect actual executable version; do not claim Blender tests unless run.
- No third-party runtime dependencies without user agreement.
- Scene source JSON is authoritative. Generated meshes are disposable.
- Geometry mutations belong to explicit undoable operators, never background callbacks.
- Preserve 512 m tile dimensions, globally aligned spacing, shared operation order, conforming border triangulation and matching field normals.
- Keep core Python independent of bpy and relative imports compatible with bl_ext namespaces.
- Run relevant unittest tests; use tests/run_blender_tests.py when Blender is available. Manual UI checks remain separate.
- Rebuild the extension package with tools/build_extension.py after source changes. Bump manifest version for published updates. Commit ZIP and index with source; test_package checks exact correspondence.
- Do not silently claim eight-tile UI, sculpting, spline tools, or production sparse meshing is complete.
