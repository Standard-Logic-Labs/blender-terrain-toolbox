"""Streaming chunked marching tetrahedra on a globally conforming grid.

Each cube uses the same 0->6 body diagonal (Freudenthal subdivision).
Shared face diagonals match in X/Y/Z. Each tetra emits 0, 1 or 2 triangles
using fixed cases, never a polygon fan. Edge interpolation orders GLOBAL
endpoints first, giving identical floating-point results across chunks/tiles.
One-cell halos are evaluated per chunk; only owned cells emit triangles.
"""
from dataclasses import dataclass, field as dc_field
from .field import Field
from .state import TILE_SIZE, spacing, validate, estimate, MAX_CELLS

CORNERS = ((0,0,0),(1,0,0),(1,1,0),(0,1,0),
           (0,0,1),(1,0,1),(1,1,1),(0,1,1))
TETS = ((0,1,2,6),(0,2,3,6),(0,3,7,6),
        (0,7,4,6),(0,4,5,6),(0,5,1,6))


@dataclass
class MeshData:
    vertices: list = dc_field(default_factory=list)
    faces: list = dc_field(default_factory=list)
    normals: list = dc_field(default_factory=list)


def sub(a,b):
    return tuple(x-y for x,y in zip(a,b))


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def extract_tile(state, tile, chunk_size=8):
    validate(state)
    if estimate(state)['cells'] > MAX_CELLS:
        raise ValueError('Build exceeds milestone cell budget; increase spacing or reduce vertical span.')
    if chunk_size < 1:
        raise ValueError('Chunk size must be positive.')
    h = spacing(state)
    n = TILE_SIZE // h
    x0, y0 = tile[0]*n, tile[1]*n
    z0, z1 = int(state['z_min']/h), int(state['z_max']/h)
    sdf, out, edge_ids = Field(state), MeshData(), {}

    def point(a,b,samples):
        a,b = sorted((a,b))
        va,vb = samples[a],samples[b]
        # Exact zeros use a grid-point key, merging all incident edge endpoints.
        key = ('p',a) if va == 0 else ('p',b) if vb == 0 else ('e',a,b)
        if key in edge_ids:
            return edge_ids[key]
        t = va/(va-vb)
        p = tuple((a[k]+t*(b[k]-a[k]))*h for k in range(3))
        idx = len(out.vertices)
        edge_ids[key] = idx
        out.vertices.append(p)
        out.normals.append(sdf.normal(p, h*0.01))
        return idx

    def emit(ids):
        if len(set(ids)) != 3:
            return
        a,b,c = (out.vertices[i] for i in ids)
        fn = cross(sub(b,a),sub(c,a))
        if sum(v*v for v in fn) < 1e-20:
            return
        centroid = tuple((a[k]+b[k]+c[k])/3 for k in range(3))
        normal = sdf.normal(centroid,h*0.01)
        if sum(fn[k]*normal[k] for k in range(3)) < 0:
            ids = (ids[0],ids[2],ids[1])
        out.faces.append(tuple(ids))

    for cx in range(x0,x0+n,chunk_size):
        for cy in range(y0,y0+n,chunk_size):
            for cz in range(z0,z1,chunk_size):
                ex,ey,ez = min(cx+chunk_size,x0+n),min(cy+chunk_size,y0+n),min(cz+chunk_size,z1)
                samples = {(x,y,z): sdf(x*h,y*h,z*h)
                           for x in range(cx-1,ex+2) for y in range(cy-1,ey+2)
                           for z in range(cz-1,ez+2)}
                for x in range(cx,ex):
                    for y in range(cy,ey):
                        for z in range(cz,ez):
                            pts = [(x+dx,y+dy,z+dz) for dx,dy,dz in CORNERS]
                            vs = [samples[p] for p in pts]
                            if min(vs) >= 0 or max(vs) < 0:
                                continue
                            for tet in TETS:
                                inside = [i for i in tet if vs[i] < 0]
                                outside = [i for i in tet if vs[i] >= 0]
                                count = len(inside)
                                if count in (0,4):
                                    continue
                                def edge(i,j):
                                    return point(pts[i],pts[j],samples)
                                if count == 1:
                                    emit(tuple(edge(inside[0],j) for j in outside))
                                elif count == 3:
                                    emit(tuple(edge(outside[0],j) for j in inside))
                                else:
                                    a,b = inside
                                    c,d = outside
                                    ac,ad,bc,bd = edge(a,c),edge(a,d),edge(b,c),edge(b,d)
                                    emit((ac,ad,bd))
                                    emit((ac,bd,bc))
    # Remove any unused vertices created by exact-zero degenerate cases.
    used = sorted({i for face in out.faces for i in face})
    remap = {old:new for new,old in enumerate(used)}
    return MeshData([out.vertices[i] for i in used],
                    [tuple(remap[i] for i in f) for f in out.faces],
                    [out.normals[i] for i in used])
