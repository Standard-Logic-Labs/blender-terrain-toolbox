"""Custom-normal adapter: inspect actual mesh instances, not bpy.types.Mesh.

Blender exposes RNA methods dynamically on instances. Class-level hasattr
is not a reliable capability test. Never fall back to independent automatic
tile normals, since that would introduce shading discontinuities.
"""


def set_shared_normals(mesh, normals, blender_version):
    if len(normals) != len(mesh.vertices):
        raise ValueError('Shared normal count must equal the generated vertex count.')
    vertex_setter = getattr(mesh, 'normals_split_custom_set_from_vertices', None)
    if callable(vertex_setter):
        vertex_setter(normals)
        return
    corner_setter = getattr(mesh, 'normals_split_custom_set', None)
    if callable(corner_setter):
        # Preserve the same world-field normal on every corner of each vertex.
        corner_setter([normals[loop.vertex_index] for loop in mesh.loops])
        return
    raise RuntimeError(
        f'Blender {blender_version}: mesh instance exposes neither custom-normal '
        'setter. Terrain generation was cancelled to preserve border shading. '
        'Please send the full traceback and Blender version.'
    )
