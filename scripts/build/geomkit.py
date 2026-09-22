"""bpy/bmesh geometry helpers (run inside Blender python)"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix

def get_mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    return m

def new_obj(name, bm, mats=(), parent=None, smooth=True, coll=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for mt in mats:
        me.materials.append(get_mat(mt))
    if smooth:
        me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    if parent: ob.parent = parent
    return ob

def lathe(profile, segs=96, axis='Z', mat_idx=None, bm=None, cap=False):
    """profile: list of (r, h) points; revolve around axis. returns bmesh"""
    bm = bm or bmesh.new()
    rings = []
    for i in range(segs):
        a = 2*math.pi*i/segs
        ca, sa = math.cos(a), math.sin(a)
        ring = []
        for (r, h) in profile:
            if axis == 'Z': co = (r*ca, r*sa, h)
            elif axis == 'Y': co = (r*ca, h, r*sa)
            else: co = (h, r*ca, r*sa)
            ring.append(bm.verts.new(co))
        rings.append(ring)
    n = len(profile)
    faces = []
    for i in range(segs):
        r0, r1 = rings[i], rings[(i+1) % segs]
        for j in range(n-1):
            f = bm.faces.new((r0[j], r1[j], r1[j+1], r0[j+1]))
            if mat_idx is not None: f.material_index = mat_idx if not callable(mat_idx) else mat_idx(j)
            faces.append(f)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def tube_along(points, radius, segs=12, bm=None, closed=False, mat=0):
    """sweep circle along polyline points (list of Vector)"""
    bm = bm or bmesh.new()
    pts = [Vector(p) for p in points]
    n = len(pts)
    rings = []
    prev_nrm = None
    for i in range(n):
        if closed:
            t = (pts[(i+1) % n] - pts[i-1]).normalized()
        else:
            t = (pts[min(i+1, n-1)] - pts[max(i-1, 0)]).normalized()
        if prev_nrm is None:
            up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            nrm = t.cross(up).normalized()
        else:
            nrm = (prev_nrm - t*prev_nrm.dot(t)).normalized()
        prev_nrm = nrm
        b = t.cross(nrm).normalized()
        ring = [bm.verts.new(pts[i] + radius*(math.cos(2*math.pi*k/segs)*nrm + math.sin(2*math.pi*k/segs)*b)) for k in range(segs)]
        rings.append(ring)
    rng = range(n) if closed else range(n-1)
    for i in rng:
        r0, r1 = rings[i], rings[(i+1) % n]
        for k in range(segs):
            f = bm.faces.new((r0[k], r0[(k+1) % segs], r1[(k+1) % segs], r1[k]))
            f.material_index = mat
    if not closed:
        for ring in (rings[0], rings[-1]):
            f = bm.faces.new(ring); f.material_index = mat
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def cylinder(bm, p0, p1, r, segs=16, mat=0, caps=True):
    p0, p1 = Vector(p0), Vector(p1)
    t = (p1 - p0); L = t.length; t.normalize()
    up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    u = t.cross(up).normalized(); w = t.cross(u).normalized()
    r0 = [bm.verts.new(p0 + r*(math.cos(2*math.pi*k/segs)*u + math.sin(2*math.pi*k/segs)*w)) for k in range(segs)]
    r1 = [bm.verts.new(p1 + r*(math.cos(2*math.pi*k/segs)*u + math.sin(2*math.pi*k/segs)*w)) for k in range(segs)]
    for k in range(segs):
        f = bm.faces.new((r0[k], r0[(k+1) % segs], r1[(k+1) % segs], r1[k])); f.material_index = mat
    if caps:
        f = bm.faces.new(list(reversed(r0))); f.material_index = mat
        f = bm.faces.new(r1); f.material_index = mat
    return bm

def transform_bm(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm

def look_matrix(origin, zdir, xhint=(1,0,0)):
    """matrix mapping local frame (x,y,z) to world with local z along zdir"""
    z = Vector(zdir).normalized()
    xh = Vector(xhint)
    if abs(xh.dot(z)) > 0.95: xh = Vector((0,1,0)) if abs(z.y) < 0.95 else Vector((1,0,0))
    x = (xh - z*xh.dot(z)).normalized()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(origin)
    return M
