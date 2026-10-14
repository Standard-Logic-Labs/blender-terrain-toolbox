"""Regression tests with dynamic-instance doubles; these are not Blender UI tests."""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import terrain_authoring as addon
from terrain_authoring.normals import set_shared_normals

NORMALS = [(0.,0.,1.), (1.,0.,0.), (0.,1.,0.)]


class DynamicMesh:
    def __init__(self, methods):
        self.methods = methods
        self.vertices = [None]*3
        self.loops = [SimpleNamespace(vertex_index=i) for i in (2,0,1,0)]

    def __getattr__(self,name):
        if name in self.methods:
            return self.methods[name]
        raise AttributeError(name)


class NormalCompatibilityTests(unittest.TestCase):
    def test_instance_only_vertex_method(self):
        calls = []
        mesh = DynamicMesh({'normals_split_custom_set_from_vertices': calls.append})
        self.assertFalse(hasattr(type(mesh),'normals_split_custom_set_from_vertices'))
        set_shared_normals(mesh,NORMALS,'test-version')
        self.assertEqual(calls,[NORMALS])

    def test_corner_setter_preserves_vertex_mapping(self):
        calls = []
        mesh = DynamicMesh({'normals_split_custom_set':calls.append})
        set_shared_normals(mesh,NORMALS,'test-version')
        self.assertEqual(calls,[[NORMALS[i] for i in (2,0,1,0)]])

    def test_unsupported_instance_fails_with_version(self):
        with self.assertRaisesRegex(RuntimeError,'Blender test-version'):
            set_shared_normals(DynamicMesh({}),NORMALS,'test-version')

    def test_setter_failure_is_not_silently_ignored(self):
        def reject(normals):
            raise ValueError('Underlying Blender error')
        mesh = DynamicMesh({'normals_split_custom_set_from_vertices': reject})
        with self.assertRaisesRegex(ValueError,'Underlying Blender error'):
            set_shared_normals(mesh,NORMALS,'test-version')

    def test_mismatched_count_does_not_call_setter(self):
        calls = []
        mesh = DynamicMesh({'normals_split_custom_set_from_vertices': calls.append})
        with self.assertRaises(ValueError):
            set_shared_normals(mesh,NORMALS[:2],'test-version')
        self.assertEqual(calls,[])

    def test_registration_does_not_probe_mesh_class(self):
        classes = [type('FakeOperator',(),{}),type('FakePanel',(),{})]
        registered = []
        bpy = SimpleNamespace(types=SimpleNamespace(Mesh=type('Mesh',(),{})),
                              utils=SimpleNamespace(register_class=registered.append,
                                                    unregister_class=registered.remove),
                              app=SimpleNamespace(version_string='test-version'))
        # The original class-level hasattr guard fails against this double.
        with patch.dict(sys.modules,{'bpy':bpy}), \
             patch.object(addon,'operators',SimpleNamespace(CLASSES=(classes[0],)),create=True), \
             patch.object(addon,'ui',SimpleNamespace(CLASSES=(classes[1],)),create=True):
            try:
                addon.register()
                self.assertEqual(registered,classes)
                addon.register()
                self.assertEqual(registered,classes)
            finally:
                addon.unregister()
            self.assertEqual(registered,[])
