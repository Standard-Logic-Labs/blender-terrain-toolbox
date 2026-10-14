# Architecture decisions — milestone 1

## Source and evaluation

`core/state.py` is the versioned source schema and validator. One Scene currently holds one terrain group. Tile dimensions are fixed at 512 m; integer XY tile coordinates are edge-connected, unique, and limited to eight. Preview and final voxel spacing divide 512 exactly. Both vertical bounds must align with both spacings. No per-tile settings or independent operation copies exist.

`core/field.py` evaluates the same negative-inside field anywhere in global meters. The procedural height base is an implicit signed field, not an exact Euclidean SDF. Sphere primitives are exact SDFs; ordered max/min boolean operations permit multi-valued vertical surfaces, caves and undercuts. No algorithm assumes the base field is a conservative distance bound. The persisted seed drives a deterministic trigonometric base; richer noise is deferred. The base and operations are the source of truth, not sampled voxel files.

`core/meshing.py` samples a streaming chunk grid on demand. Each chunk stores its dense samples plus one-cell halo temporarily, then discards them. This avoids allocating the entire terrain volume, but **still visits every cell**; it is not yet a sparse acceleration structure or editable persistent voxel cache. Output and edge caches accumulate per tile. Fine production terrain needs sparse active-chunk bounds, operation influence indexing, dirty chunk caching, and meshing performance work.

## Meshing and seams

A globally consistent six-tetrahedra subdivision around cube corner 0 to 6 makes all adjacent cube-face diagonals agree. Each tetrahedron has a fixed one- or two-triangle case; no fan triangulation or border stitching is used. This trades higher triangle count and directional bias for a small unambiguous extractor. It stays behind a replaceable interface; a future Marching Cubes implementation must preserve global cell ownership and handle ambiguous face cases consistently.

Only a chunk's owned half-open cells emit triangles. The positive border samples and one-cell outside halo are evaluated even at tile boundaries. Duplicate halo samples are recomputed by the exact same world-coordinate function; they are mathematically shared samples, not separately authored border data. Field gradients sample either side of a boundary directly. Normals are therefore independent of the subset of triangles belonging to a tile.

Interpolation sorts global edge endpoints before floating-point evaluation. Exact-zero endpoints use a shared point key; degenerates are rejected. One per-tile edge map welds chunk boundaries. Tile meshes retain duplicate coincident boundary vertices, with identical positions and source normals; they are not one welded object. Outward winding uses the field gradient. Smooth custom normals are supplied to Blender. Hard boolean creases are currently smoothed; preserving sharp features is a later task.

The outer domain boundary is not artificially closed, including Z bounds. Bounds that cut through a cavity can expose clipped surfaces. Defaults enclose the test cavity vertically. Near-zero ties, small features, and topology vary with sampling resolution. Features smaller than a few voxels may be missed; no claim of arbitrary fine-detail recovery is made.

## Blender state and mutation

`bridge.py` converts source to Blender meshes. Versioned JSON is stored under `Scene["terrain_authoring_source_v1"]`, including tile layout, fixed dimensions, both resolutions, bounds, seed, ordered operations, visibility state and group UUID. JSON survives disabling/reloading the extension. Unknown schemas fail rather than silently overwrite.

All output is tagged by owner UUID and role. Numeric extraction and new datablocks are staged before old generated objects are replaced. Unrelated objects are retained. Linked or cross-scene shared terrain objects are rejected. This milestone supports local standalone groups, not library-linked assets or duplicated-scene group editing.

`operators.py` owns scene mutations and uses `REGISTER, UNDO`; settings are staged in an operator dialog and applied only on confirmation. There are no geometry update callbacks, timers, modal background workers or file-load mutators. Save and reopen use normal Blender commands. `ui.py` reads source state only. Blender's global undo must be enabled for UI undo tests.

## Cost controls

Defaults: two tiles, 32 m preview spacing, -192 to +128 m vertical bounds, 5,120 cells total. Final defaults to 16 m, 40,960 cells. The conservative triangle ceiling is 12 triangles per cell. The UI estimate budgets 320 bytes per potential triangle plus 16 MiB for staging/Blender/one undo copy; actual allocations depend on topology and Blender. It is a planning estimate, not a measured limit. Builds over a 512 MiB estimate require acknowledgment in settings. Builds above 400,000 cells are refused. Multiple undo states can consume additional memory. All builds are synchronous in M1.

## Milestones after validation

1. **Current gate:** verify installation, UI, save/reopen, undo/redo, and normals on the user's Blender 5.2.2 LTS. Fix precise tracebacks before adding scope.
2. Tile layout authoring up to eight tiles; typed operation records, reorder/remove/edit controls; active-chunk caching and cancellation strategy compatible with undo.
3. Parametric add/subtract stamps, influence bounds, smooth boolean blends, and a defined asset packing/referencing contract.
4. Curve sampling in world coordinates for roads/rivers/ridges/tunnels; per-operation profiles, width, depth, strength and falloff.
5. Surface editing operations, production sparse evaluation, higher-resolution export and more extensive seam/feature regression scenes.

A heightfield-only rewrite would violate the product requirements. Preserve the volumetric interface even when a new operation initially targets surface relief.
