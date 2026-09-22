import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
from geomkit import lathe, new_obj, cylinder, transform_bm, tube_along

def tire_profile(Rt, W=0.155, Rb=0.2413, grooves=True):
    H = Rt - Rb
    hw = W/2
    pts = []
    # inner side (h<0) from bead to tread shoulder
    side = [(Rb, -0.052), (Rb+0.012, -0.062), (Rb+0.035, -0.071), (Rb+0.065, -hw), (Rb+0.095, -hw+0.002),
            (Rt-0.030, -hw+0.010), (Rt-0.014, -hw+0.024), (Rt-0.004, -hw+0.040)]
    pts += side
    # tread with grooves (ribbed racing tread)
    tread_w = hw - 0.040
    if grooves:
        gpos = [-0.030, -0.012, 0.006, 0.024]
        hs = np.linspace(-tread_w, tread_w, 41)
        for h in hs:
            r = Rt - 0.002*(h/tread_w)**2
            for g in gpos:
                if abs(h - g) < 0.0025: r -= 0.004
            pts.append((r, h))
    else:
        pts += [(Rt, -tread_w), (Rt, tread_w)]
    pts += [(r, -h) for (r, h) in reversed(side)]
    return pts

def rim_profile(Rb=0.2413):
    # from inner (h<0) edge to outer flange (h>0); polished alloy rim
    return [(0.226, -0.050), (0.236, -0.056), (0.250, -0.060), (0.258, -0.058), (0.256, -0.050), (Rb+0.002, -0.046),
            (Rb, -0.030), (0.228, -0.022), (0.222, -0.010), (0.222, 0.012), (0.228, 0.022), (Rb, 0.030),
            (Rb+0.002, 0.046), (0.256, 0.050), (0.262, 0.056), (0.262, 0.061), (0.256, 0.065), (0.246, 0.063), (0.236, 0.056), (0.226, 0.050), (0.222, 0.040)]

def build_wheel(name, Rt, side=+1, spare=False):
    """wheel in local frame: axle along local Z, outer face +Z. returns list of objects (parented to an empty)"""
    objs = []
    empty = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(empty)
    # tire
    bm = lathe(tire_profile(Rt), segs=144, axis='Z', mat_idx=0)
    objs.append(new_obj(name+'_Tire', bm, ['M_Rubber'], parent=empty))
    # rim
    bm = lathe(rim_profile(), segs=144, axis='Z', mat_idx=0)
    objs.append(new_obj(name+'_Rim', bm, ['M_AluPolished'], parent=empty))
    # brake drum face with holes (inside, behind spokes)
    prof = [(0.0, -0.030), (0.050, -0.030), (0.060, -0.034), (0.170, -0.034), (0.186, -0.030), (0.200, -0.030), (0.206, -0.040), (0.212, -0.070)]
    bm = lathe(prof, segs=96, axis='Z', mat_idx=0)
    for ring_r, n in ((0.110, 20), (0.150, 28)):
        for k in range(n):
            a = 2*math.pi*(k + 0.5*(ring_r > 0.12))/n
            c = Vector((ring_r*math.cos(a), ring_r*math.sin(a), -0.0335))
            cylinder(bm, c + Vector((0,0,0.0008)), c - Vector((0,0,0.006)), 0.0075, segs=10, mat=1, caps=True)
    # toothed ring (dog teeth) at r~0.19
    for k in range(48):
        a = 2*math.pi*k/48
        c = Vector((0.192*math.cos(a), 0.192*math.sin(a), -0.024))
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-math.sin(a), math.cos(a), 0))
        vs = [c - 0.006*t - 0.004*d, c + 0.006*t - 0.004*d, c + 0.002*t + 0.008*d, c - 0.002*t + 0.008*d]
        v0 = [bm.verts.new(v) for v in vs]; v1 = [bm.verts.new(v + Vector((0,0,-0.012))) for v in vs]
        bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
        for i in range(4):
            bm.faces.new((v0[i], v1[i], v1[(i+1)%4], v0[(i+1)%4]))
    objs.append(new_obj(name+'_Drum', bm, ['M_AluCast', 'M_DarkHole'], parent=empty))
    # hub shell + spokes
    bm = lathe([(0.0, 0.070), (0.028, 0.070), (0.034, 0.064), (0.036, 0.030), (0.052, 0.024), (0.056, 0.010), (0.056, -0.020), (0.050, -0.030), (0.040, -0.034)], segs=48, axis='Z', mat_idx=0)
    objs.append(new_obj(name+'_Hub', bm, ['M_Steel'], parent=empty))
    bm = bmesh.new()
    nsp = 64
    for k in range(nsp):
        a_rim = 2*math.pi*k/nsp
        layer = k % 2
        # hub flange positions
        a_hub = a_rim + (0.18 if layer == 0 else -0.18)
        hz = 0.018 if layer == 0 else -0.026
        rz = -0.006 if layer == 0 else 0.004
        p_hub = Vector((0.050*math.cos(a_hub), 0.050*math.sin(a_hub), hz))
        p_rim = Vector((0.224*math.cos(a_rim), 0.224*math.sin(a_rim), rz))
        cylinder(bm, p_hub, p_rim, 0.0017, segs=6, mat=0, caps=False)
        # nipple at rim
        cylinder(bm, p_rim, p_rim + (p_rim - p_hub).normalized()*(-0.012), 0.0032, segs=6, mat=0, caps=True)
    objs.append(new_obj(name+'_Spokes', bm, ['M_Steel'], parent=empty))
    # knock-off spinner: cap + two ears
    bm = lathe([(0.0, 0.112), (0.020, 0.111), (0.026, 0.106), (0.028, 0.090), (0.034, 0.086), (0.036, 0.074), (0.030, 0.070)], segs=48, axis='Z', mat_idx=0)
    for s in (1, -1):
        # ear: tapered bar
        L0, L1 = 0.030, 0.078
        vs = [Vector((s*L0, -0.012, 0.074)), Vector((s*L1, -0.006, 0.080)), Vector((s*L1, 0.006, 0.080)), Vector((s*L0, 0.012, 0.074))]
        top = [v + Vector((0, 0, 0.016)) for v in vs]
        v0 = [bm.verts.new(v) for v in vs]; v1 = [bm.verts.new(v) for v in top]
        bm.faces.new(list(reversed(v0))); bm.faces.new(v1)
        for i in range(4): bm.faces.new((v0[i], v0[(i+1)%4], v1[(i+1)%4], v1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    objs.append(new_obj(name+'_KnockOff', bm, ['M_SteelDark'], parent=empty))
    return empty, objs

def place_wheel(empty, center_bl, outward_x):
    """center in blender coords; outward_x=+1 means outer face toward +X"""
    R = Matrix.Rotation(math.radians(90*outward_x), 4, 'Y')
    empty.matrix_world = Matrix.Translation(Vector(center_bl)) @ R
