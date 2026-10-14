import copy
import math
import unittest
from collections import Counter
from terrain_authoring.core import state
from terrain_authoring.core.field import Field
from terrain_authoring.core.meshing import extract_tile, cross, sub


def surface(mesh):
    return {tuple(sorted(mesh.vertices[i] for i in f)) for f in mesh.faces}


def boundary(mesh,axis,coordinate):
    edges = Counter()
    for f in mesh.faces:
        for a,b in zip(f,(f[1],f[2],f[0])):
            p,q = mesh.vertices[a],mesh.vertices[b]
            if p[axis] == coordinate and q[axis] == coordinate:
                edges[tuple(sorted((p,q)))] += 1
    return {e for e,count in edges.items() if count == 1}


def border_normals(mesh,axis,coordinate):
    return {p:n for p,n in zip(mesh.vertices,mesh.normals) if p[axis] == coordinate}


class TerrainCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = state.with_test_cut(state.default_state())
        cls.left = extract_tile(cls.s,(0,0))
        cls.right = extract_tile(cls.s,(1,0))

    def test_x_seam_edges_and_normals_exact(self):
        a,b = boundary(self.left,0,512),boundary(self.right,0,512)
        self.assertGreater(len(a),20)
        self.assertEqual(a,b)
        self.assertEqual(border_normals(self.left,0,512),border_normals(self.right,0,512))

    def test_y_seam_and_negative_tile_coordinates(self):
        s = copy.deepcopy(self.s)
        s['tiles'] = [[-1,-1],[-1,0]]
        s['operations'][0]['center'] = [-256,0,-32]
        a,b = (extract_tile(s,t) for t in s['tiles'])
        self.assertTrue(boundary(a,1,0))
        self.assertEqual(boundary(a,1,0),boundary(b,1,0))
        self.assertEqual(border_normals(a,1,0),border_normals(b,1,0))

    def test_chunk_size_does_not_change_surface(self):
        other = extract_tile(self.s,(0,0),chunk_size=5)
        self.assertEqual(surface(self.left),surface(other))
        self.assertEqual(dict(zip(self.left.vertices,self.left.normals)),dict(zip(other.vertices,other.normals)))

    def test_no_internal_holes_or_nonmanifold_edges(self):
        counts = Counter()
        for mesh in (self.left,self.right):
            for f in mesh.faces:
                for a,b in zip(f,(f[1],f[2],f[0])):
                    counts[tuple(sorted((mesh.vertices[a],mesh.vertices[b])))] += 1
        for edge,count in counts.items():
            self.assertIn(count,(1,2))
            if count == 1:
                self.assertTrue(any(all(p[axis] == value for p in edge)
                                    for axis,value in ((0,0),(0,1024),(1,0),(1,512))))

    def test_mesh_has_undercut_and_valid_triangles(self):
        self.assertTrue(any(n[2] < -0.1 for n in self.left.normals))
        sdf = Field(self.s)
        for f in self.left.faces:
            a,b,c = (self.left.vertices[i] for i in f)
            n = cross(sub(b,a),sub(c,a))
            self.assertGreater(sum(v*v for v in n),1e-20)
            center = tuple((a[k]+b[k]+c[k])/3 for k in range(3))
            self.assertGreaterEqual(sum(x*y for x,y in zip(n,sdf.normal(center,0.32))),0)
        self.assertTrue(all(math.isfinite(v) for p in self.left.vertices for v in p))

    def test_json_roundtrip_reproduces_mesh(self):
        restored = state.loads(state.dumps(self.s))
        self.assertEqual(self.s,restored)
        self.assertEqual(self.left,extract_tile(restored,(0,0)))

    def test_seed_and_disabled_operation(self):
        base = state.default_state()
        off = copy.deepcopy(self.s)
        off['operations'][0]['enabled'] = False
        p = (512,256,-32)
        self.assertGreater(Field(self.s)(*p),0)
        self.assertLess(Field(base)(*p),0)
        self.assertEqual(Field(base)(*p),Field(off)(*p))
        base['seed'] += 1
        self.assertNotEqual(Field(base)(*p),Field(off)(*p))

    def test_operation_order_is_meaningful(self):
        s = copy.deepcopy(self.s)
        add = dict(kind='SPHERE_ADD',center=[512,256,-32],radius=32,enabled=True)
        s['operations'].append(add)
        self.assertLess(Field(s)(512,256,-32),0)
        s['operations'].reverse()
        self.assertGreater(Field(s)(512,256,-32),0)

    def test_resolution_and_eight_tile_validation(self):
        s = state.default_state()
        s['tiles'] = [[i,0] for i in range(8)]
        state.validate(s)
        s['tiles'].append([8,0])
        with self.assertRaises(ValueError):
            state.validate(s)
        s = state.default_state()
        s['tiles'] = [[0,0],[2,0]]
        with self.assertRaises(ValueError):
            state.validate(s)
        s = state.default_state()
        s['z_min'] = -191
        with self.assertRaises(ValueError):
            state.validate(s)
        self.assertEqual(state.estimate(state.default_state())['cells'],5120)

    def test_final_resolution_seam(self):
        s = copy.deepcopy(self.s)
        s['mode'] = 'FINAL'
        a,b = (extract_tile(s,t) for t in s['tiles'])
        self.assertTrue(boundary(a,0,512))
        self.assertEqual(boundary(a,0,512),boundary(b,0,512))
        self.assertEqual(border_normals(a,0,512),border_normals(b,0,512))


if __name__ == '__main__':
    unittest.main()
