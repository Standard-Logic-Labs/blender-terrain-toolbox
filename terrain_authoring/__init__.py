"""Terrain Authoring milestone 1. No third-party runtime dependencies."""

_registered_classes = []


def register():
    import bpy
    from . import operators,ui
    # RNA mesh functions are bound on instances; do not probe bpy.types.Mesh.
    # Normals are checked when an undoable build has an actual staged mesh.
    if _registered_classes:
        return
    registered = []
    try:
        for cls in operators.CLASSES + ui.CLASSES:
            bpy.utils.register_class(cls)
            registered.append(cls)
    except Exception:
        for cls in reversed(registered):
            bpy.utils.unregister_class(cls)
        raise
    _registered_classes.extend(registered)
    print(f'Terrain Authoring 0.1.1 registered in Blender {bpy.app.version_string}')


def unregister():
    import bpy
    for cls in reversed(_registered_classes):
        bpy.utils.unregister_class(cls)
    _registered_classes.clear()
    # Scene JSON and generated meshes deliberately survive disable/reload.
