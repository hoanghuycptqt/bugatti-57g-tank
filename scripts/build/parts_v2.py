"""Second-generation detail parts (overrides of build_parts functions)."""
import bpy, bmesh, math, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, '/home/claude/tank/build')
import build_parts as BP
import surf, details, vents
from wiremesh import build_wires
from geomkit import lathe, cylinder, transform_bm, tube_along, look_matrix
from build_parts import obj, V, BL, BLV, nose_pt, NN, NT, NU, plate_from_outline, rivet

def merge_into(dst, src_bm):
    me = bpy.data.meshes.new('tmp'); src_bm.to_mesh(me); src_bm.free(); dst.from_mesh(me); bpy.data.meshes.remove(me)

def add_uv_planar(ob, axis_u, axis_v, origin, scale):
    """planar UV from object-space coordinates (world == object here)"""
    me = ob.data
    uv = me.uv_layers.new(name='UVMap')
    co = np.empty(len(me.vertices)*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    li = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', li)
    p = co[li] - np.asarray(origin, np.float32)
    u = p @ np.asarray(axis_u, np.float32) / scale + 0.5
    v = p @ np.asarray(axis_v, np.float32) / scale + 0.5
    uv.data.foreach_set('uv', np.stack([u, v], 1).astype(np.float32).ravel())

# ------------------------------------------------------------------ nose: grille & intake with woven mesh
def nose_map(w):
    def f(U, V):
        P = np.stack([nose_pt(u, v, w) for u, v in zip(U, V)])
        Pb = surf.to_bl(P)
        Nb = np.tile(surf.dir_to_bl(NN), (len(U), 1))
        return Pb, Nb
    return f

def build_grille():
    uv = details.grille_outline_uv()
    bm = bmesh.new()
    n = build_wires(bm, uv, pitch=0.0097, radius=0.00075, map_fn=nose_map(-0.010), segs=5)
    obj('Grille_Mesh', bm, ['M_WireMesh'])
    bm = bmesh.new()
    pts = [BL(nose_pt(u*0.995, v, -0.0285)) for u, v in uv]
    plate_from_outline(bm, pts, surf.dir_to_bl(NN), 0.0, 0)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    obj('Grille_Core', bm, ['M_Radiator'], smooth=False)
    # radiator core honeycomb hint: horizontal fins behind the mesh
    bm = bmesh.new()
    vmin, vmax = uv[:, 1].min(), uv[:, 1].max()
    for v in np.arange(vmin + 0.004, vmax, 0.0045):
        from wiremesh import clip_intervals
        for a, b in clip_intervals(uv, 1, v):
            p0 = nose_pt(a + 0.002, v, -0.0275); p1 = nose_pt(b - 0.002, v, -0.0275)
            q0 = nose_pt(a + 0.002, v, -0.0205); q1 = nose_pt(b - 0.002, v, -0.0205)
            vs = [bm.verts.new(V(BL(p))) for p in (p0, p1, q1, q0)]
            bm.faces.new(vs)
    obj('Radiator_Fins', bm, ['M_Radiator'], smooth=False)
    return n

def build_intake():
    uv = details.intake_outline_uv()
    bm = bmesh.new()
    build_wires(bm, uv, pitch=0.0100, radius=0.00075, map_fn=nose_map(-0.012), segs=5)
    obj('Intake_Mesh', bm, ['M_WireMesh'])
    bm = bmesh.new()
    pts = [BL(nose_pt(u, v, -0.054)) for u, v in uv]
    plate_from_outline(bm, pts, surf.dir_to_bl(NN), 0.0, 0)
    obj('Intake_Back', bm, ['M_Radiator'], smooth=False)
    for s in (1, -1):
        tag = 'L' if s > 0 else 'R'
        cen = nose_pt(s*0.14, details.z_to_v(0.345), -0.036)
        M = look_matrix(BL(cen), surf.dir_to_bl(NN))
        bm = lathe([(0.0, -0.030), (0.030, -0.026), (0.046, -0.012), (0.052, -0.004), (0.054, 0.002), (0.052, 0.006), (0.047, 0.007)], segs=48, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('DrivingLamp_Body_' + tag, bm, ['M_Chrome'])
        bm = lathe([(0.0, 0.010), (0.022, 0.009), (0.040, 0.005), (0.047, 0.001)], segs=48, axis='Z', mat_idx=0)
        transform_bm(bm, M); o = obj('DrivingLamp_Lens_' + tag, bm, ['M_LampGlassFluted'])
        add_uv_planar(o, surf.dir_to_bl(NU), surf.dir_to_bl(NT), BL(cen), 0.1)
        bm = lathe([(0.0, -0.026), (0.02, -0.022), (0.035, -0.012), (0.045, 0.0)], segs=48, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('DrivingLamp_Refl_' + tag, bm, ['M_Chrome'])
        bm = lathe([(0.0, -0.006), (0.006, -0.005), (0.007, 0.004), (0.004, 0.008), (0.0, 0.009)], segs=16, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('DrivingLamp_Bulb_' + tag, bm, ['M_Bulb'])

# ------------------------------------------------------------------ front pod vents (woven mesh + rivets)
def vent_map_front(s):
    def f(A_, Z_):
        P0 = np.stack([np.full_like(A_, -1.0), s*A_, Z_], 1)
        H = surf.raycast_many(P0, [1, 0, 0])
        H = H + np.array([0.007, 0, 0])
        return surf.to_bl(H), np.tile(surf.dir_to_bl([-1, 0, 0]), (len(A_), 1))
    return f

def vent_map_rear(s):
    def f(A_, Z_):
        P0 = np.stack([np.full_like(A_, 4.6), s*A_, Z_], 1)
        H = surf.raycast_many(P0, [-1, 0, 0])
        H = H + np.array([-0.007, 0, 0])
        return surf.to_bl(H), np.tile(surf.dir_to_bl([1, 0, 0]), (len(A_), 1))
    return f

def mirror_poly(poly, s):
    return poly if s > 0 else poly

def build_vents():
    bm_mesh = bmesh.new(); bm_riv = bmesh.new(); bm_back = bmesh.new()
    for s in (1, -1):
        mp = vent_map_front(s)
        for poly in details.FV_POLYS:
            build_wires(bm_mesh, poly, pitch=0.0068, radius=0.00062, map_fn=mp, segs=5)
        # rivets on an offset of the whole outline
        whole = vents.seg_oval(vents.FV['center'], vents.FV['L'], vents.FV['prof'], [(0.0, 1.0)], 0.0, inset=-0.014, n=120)[0]
        per = np.vstack([whole, whole[:1]])
        seg = np.linalg.norm(np.diff(per, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
        L = cum[-1]; nr = int(L / 0.031)
        ts = np.arange(nr) * L / nr
        pts = np.stack([np.interp(ts, cum, per[:, 0]), np.interp(ts, cum, per[:, 1])], 1)
        # skip rivets hidden by the headlamp guard (lower outboard region)
        P0 = np.stack([np.full(len(pts), -1.0), s*pts[:, 0], pts[:, 1]], 1)
        H = surf.raycast_many(P0, [1, 0, 0])
        for h in H:
            if not np.all(np.isfinite(h)): continue
            rivet(bm_riv, h, surf.normal_nd(h)[0], r=0.0036)
    obj('PodVents_Mesh', bm_mesh, ['M_WireMesh'])
    obj('PodVents_Rivets', bm_riv, ['M_Paint'])
    # rear lobe vents: coarse bright wire mesh
    bm_mesh = bmesh.new()
    for s in (1, -1):
        mp = vent_map_rear(s)
        for poly in details.RV_POLYS:
            build_wires(bm_mesh, poly, pitch=0.0135, radius=0.0009, map_fn=mp, segs=5, rot=math.radians(vents.RV['angle']*s*0 + 0))
    obj('RearVents_Mesh', bm_mesh, ['M_WireBright'])

# ------------------------------------------------------------------ headlamps with woven guard dome
def build_headlamps():
    for s in (1, -1):
        tag = 'L' if s > 0 else 'R'
        yc = s*details.HEAD['y']; zc = details.HEAD['z']
        M = look_matrix(BL([-0.505, yc, zc]), surf.dir_to_bl([-1, 0, 0]))
        bm = lathe([(0.0, 0.0), (0.03, 0.002), (0.06, 0.010), (0.080, 0.022), (0.090, 0.030)], segs=64, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Headlamp_Refl_'+tag, bm, ['M_Chrome'])
        bm = lathe([(0.0, 0.035), (0.008, 0.033), (0.012, 0.024), (0.009, 0.012), (0.004, 0.006)], segs=24, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Headlamp_Bulb_'+tag, bm, ['M_Bulb'])
        M2 = look_matrix(BL([-0.535, yc, zc]), surf.dir_to_bl([-1, 0, 0]))
        bm = lathe([(0.078, -0.012), (0.082, 0.000), (0.088, 0.006), (0.094, 0.004), (0.098, -0.004), (0.099, -0.014), (0.096, -0.020)], segs=72, axis='Z', mat_idx=0)
        transform_bm(bm, M2); obj('Headlamp_Bezel_'+tag, bm, ['M_Chrome'])
        bm = lathe([(0.0, 0.012), (0.03, 0.010), (0.06, 0.006), (0.080, 0.000)], segs=72, axis='Z', mat_idx=0)
        transform_bm(bm, M2); o = obj('Headlamp_Lens_'+tag, bm, ['M_LampGlassFluted'])
        add_uv_planar(o, (1, 0, 0), (0, 0, 1), BL([-0.535, yc, zc]), 0.16)
        # woven guard dome (spherical cap R_base=0.118, h=0.06) in front of the lamp
        Rb, hd = 0.118, 0.060
        rs = (Rb*Rb + hd*hd)/(2*hd)
        M3 = look_matrix(BL([-0.548, yc, zc]), surf.dir_to_bl([-1, 0, 0]))
        M3n = M3.to_3x3()
        def dome_map(U, Vv):
            r2 = U*U + Vv*Vv
            zz = np.sqrt(np.maximum(rs*rs - r2, 0.0)) - (rs - hd)
            P = np.stack([U, Vv, zz], 1)
            Nl = np.stack([U, Vv, zz + (rs - hd)], 1); Nl /= np.linalg.norm(Nl, axis=1, keepdims=True)
            Pw = np.array([tuple(M3 @ Vector(p)) for p in P]); Nw = np.array([tuple(M3n @ Vector(n)) for n in Nl])
            return Pw, Nw
        circ = np.array([(Rb*math.cos(a), Rb*math.sin(a)) for a in np.linspace(0, 2*math.pi, 97)[:-1]])
        bm = bmesh.new()
        build_wires(bm, circ, pitch=0.0092, radius=0.0007, map_fn=dome_map, segs=5, spp=4)
        obj('Headlamp_Guard_'+tag, bm, ['M_WireMeshGuard'])
        ring = [BL([-0.548, yc + Rb*math.cos(2*math.pi*k/64), zc + Rb*math.sin(2*math.pi*k/64)]) for k in range(64)]
        bm = tube_along([V(p) for p in ring], 0.0026, segs=8, closed=True)
        obj('Headlamp_GuardRim_'+tag, bm, ['M_WireMeshGuard'])
        # painted mounting bracket (triangular plate) from the pod face to the guard top + bolt below
        top_pt = np.array([-0.556, yc, zc + Rb - 0.004])
        hit = surf.raycast([top_pt[0] - 0.3, yc, zc + 0.150], [1, 0, 0])
        p1 = hit if hit is not None else top_pt + np.array([0.05, 0, 0.03])
        w = 0.024
        bm = bmesh.new()
        pts = [top_pt + [0, -w, 0], top_pt + [0, w, 0], p1 + [0.004, w*0.8, 0.0], p1 + [0.004, -w*0.8, 0.0]]
        plate_from_outline(bm, [BL(p) for p in pts], surf.dir_to_bl([0, 0, 1]), 0.003, 0)
        obj('Headlamp_Bracket_'+tag, bm, ['M_Paint'], smooth=False)
        for dy in (-0.012, 0.012):
            b = lathe([(0.0, 0.004), (0.004, 0.0035), (0.0045, 0.0)], segs=12, axis='Z', mat_idx=0)
            transform_bm(b, look_matrix(BL(top_pt + [0.012, dy, 0.003]), surf.dir_to_bl([0, 0, 1])))
            obj('Headlamp_BracketBolt_%s_%d' % (tag, dy > 0), b, ['M_Steel'])
        ring_bot = np.array([-0.548, yc, zc - Rb])
        hb = surf.raycast([-0.8, yc, zc - Rb + 0.008], [1, 0, 0])
        b = bmesh.new()
        if hb is not None:
            cylinder(b, BLV(ring_bot + [0, 0, 0.004]), BLV(hb + [0.004, 0, 0.0]), 0.0035, segs=10)
        b2 = lathe([(0.0, 0.006), (0.0055, 0.0055), (0.006, 0.0)], segs=12, axis='Z', mat_idx=0)
        transform_bm(b2, look_matrix(BL(ring_bot + [-0.002, 0, 0.004]), surf.dir_to_bl([-1, 0, 0])))
        merge_into(b, b2)
        obj('Headlamp_GuardBolt_'+tag, b, ['M_Steel'])

# ------------------------------------------------------------------ side lamp (right side, in its body recess)
def build_side_lamp():
    zc = 0.763; x_front = 1.461; x_rear = 1.700
    ys = surf.raycast_many(np.array([[1.53, -1.4, zc]]), [0, 1, 0])[0][1]     # smooth-surface y (~ -0.792)
    assert np.isfinite(ys), 'side lamp surface not found'
    ya = ys - 0.032
    prof = []
    Lp = x_rear - x_front
    for k in range(33):
        t = k/32
        r = 0.077*(1 - t**2.4)**0.62 if t < 1 else 0.0
        prof.append((max(r, 0.0004), x_front + 0.006 + t*(Lp - 0.006)))
    bm = lathe(prof, segs=48, axis='Z', mat_idx=0)
    # lathe axis Z -> car +x ; place axis at (ya, zc)
    Mx = Matrix(((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 1)))
    for v in bm.verts:
        lx, ly, lz = v.co            # lz = car x ; (lx, ly) radial
        car = np.array([lz, ya + lx, zc + ly])
        v.co = V(BL(car))
    obj('SideLamp_Pod', bm, ['M_Paint'])
    M = look_matrix(BL([x_front, ya, zc]), surf.dir_to_bl([-1, 0, 0]))
    bm = lathe([(0.070, -0.010), (0.071, 0.002), (0.076, 0.009), (0.081, 0.010), (0.0835, 0.005), (0.083, -0.006), (0.079, -0.012)], segs=64, axis='Z', mat_idx=0)
    transform_bm(bm, M); obj('SideLamp_Bezel', bm, ['M_Nickel'])
    bm = lathe([(0.0, 0.006), (0.030, 0.0055), (0.055, 0.003), (0.071, -0.001)], segs=64, axis='Z', mat_idx=0)
    transform_bm(bm, M); o = obj('SideLamp_Lens', bm, ['M_LampGlassFluted'])
    add_uv_planar(o, (1, 0, 0), (0, 0, 1), BL([x_front, ya, zc]), 0.15)
    bm = lathe([(0.0, -0.045), (0.03, -0.040), (0.055, -0.025), (0.070, -0.008)], segs=48, axis='Z', mat_idx=0)
    transform_bm(bm, M); obj('SideLamp_Refl', bm, ['M_Chrome'])
    for a in (math.radians(60), math.radians(240)):          # bezel screws
        p = np.array([x_front - 0.009, ya + 0.0795*math.cos(a), zc + 0.0795*math.sin(a)])
        b = lathe([(0.0, 0.003), (0.0035, 0.0025), (0.004, 0.0)], segs=12, axis='Z', mat_idx=0)
        transform_bm(b, look_matrix(BL(p), surf.dir_to_bl([-1, 0, 0])))
        obj('SideLamp_Screw_%d' % int(math.degrees(a)), b, ['M_Nickel'])

# ------------------------------------------------------------------ fuel filler (stadium frame, boot, two flip caps)
def stadium(cx, cy, hl, hw, n=24):
    pts = []
    for a in np.linspace(-math.pi/2, math.pi/2, n):
        pts.append((cx + hl - hw + hw*math.cos(a), cy + hw*math.sin(a)))
    for a in np.linspace(math.pi/2, 3*math.pi/2, n):
        pts.append((cx - hl + hw + hw*math.cos(a), cy + hw*math.sin(a)))
    return np.array(pts)

def build_fuel_filler():
    hit = surf.raycast([2.57, 0.0, 2.0], [0, 0, -1]); n = surf.normal(hit)[0]
    M = look_matrix(BL(hit + 0.0008*n), tuple(surf.dir_to_bl(n)), xhint=tuple(surf.dir_to_bl([0, 1, 0])))
    outer = stadium(0, 0, 0.167, 0.085, 28); inner = stadium(0, 0, 0.150, 0.068, 28)
    bm = bmesh.new()
    to = [bm.verts.new((u, v, 0.005)) for u, v in outer]; ti = [bm.verts.new((u, v, 0.006)) for u, v in inner]
    bo = [bm.verts.new((u, v, -0.001)) for u, v in outer]; bi = [bm.verts.new((u, v, -0.001)) for u, v in inner]
    N = len(outer)
    for i in range(N):
        j = (i+1) % N
        bm.faces.new((to[i], to[j], ti[j], ti[i]))
        bm.faces.new((bo[j], to[j], to[i], bo[i]))
        bm.faces.new((ti[i], ti[j], bi[j], bi[i]))
    transform_bm(bm, M); obj('FuelFiller_Frame', bm, ['M_Nickel'])
    # boot (black leather) dished below
    bm = bmesh.new()
    rings = []
    for k, (sc, dz) in enumerate([(1.0, 0.0), (0.93, -0.012), (0.80, -0.022), (0.6, -0.028)]):
        rings.append([bm.verts.new((u*sc, v*sc, dz)) for u, v in inner])
    for k in range(3):
        for i in range(N):
            j = (i+1) % N
            bm.faces.new((rings[k][i], rings[k][j], rings[k+1][j], rings[k+1][i]))
    bm.faces.new(rings[-1][::-1])
    transform_bm(bm, M); obj('FuelFiller_Boot', bm, ['M_SeatLeather'])
    # screws around frame
    bm = bmesh.new()
    mid = stadium(0, 0, 0.1585, 0.0765, 60)
    per = np.vstack([mid, mid[:1]]); seg = np.linalg.norm(np.diff(per, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    for t in np.arange(10) * cum[-1] / 10 + 0.02:
        u = np.interp(t, cum, per[:, 0]); v = np.interp(t, cum, per[:, 1])
        b = lathe([(0.0, 0.0085), (0.0035, 0.008), (0.0045, 0.0055)], segs=12, axis='Z', mat_idx=0)
        bmesh.ops.translate(b, vec=Vector((u, v, 0.0)), verts=b.verts)
        merge_into(bm, b)
    transform_bm(bm, M); obj('FuelFiller_Screws', bm, ['M_Nickel'])
    # two flip caps: neck + lid + hinge + knurled tab
    for s in (1, -1):
        tag = 'L' if s > 0 else 'R'
        bm = lathe([(0.036, -0.03), (0.037, 0.004), (0.041, 0.006), (0.041, 0.012)], segs=40, axis='Z', mat_idx=0)
        bmesh.ops.translate(bm, vec=Vector((s*0.075, 0.0, 0.0)), verts=bm.verts)
        transform_bm(bm, M); obj('FuelFiller_Neck_'+tag, bm, ['M_Nickel'])
        bm = lathe([(0.0, 0.026), (0.030, 0.0255), (0.040, 0.023), (0.043, 0.019), (0.043, 0.012), (0.041, 0.011)], segs=48, axis='Z', mat_idx=0)
        bmesh.ops.translate(bm, vec=Vector((s*0.075, 0.0, 0.0)), verts=bm.verts)
        transform_bm(bm, M); obj('FuelFiller_Lid_'+tag, bm, ['M_Nickel'])
        bm = lathe([(0.0, 0.031), (0.006, 0.030), (0.0075, 0.026)], segs=24, axis='Z', mat_idx=0)   # centre screw
        bmesh.ops.translate(bm, vec=Vector((s*0.075, 0.0, 0.0)), verts=bm.verts)
        transform_bm(bm, M); obj('FuelFiller_LidScrew_'+tag, bm, ['M_Nickel'])
        bm = bmesh.new()                                   # hinge knuckle (toward the car centre)
        cylinder(bm, Vector((s*0.075 - s*0.046, -0.014, 0.018)), Vector((s*0.075 - s*0.046, 0.014, 0.018)), 0.006, segs=16)
        transform_bm(bm, M); obj('FuelFiller_Hinge_'+tag, bm, ['M_Nickel'])
        bm = bmesh.new()                                   # knurled latch tab (outboard)
        bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.012, 0.022, 0.020), verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector((s*0.075 + s*0.048, 0.0, 0.017)), verts=bm.verts)
        transform_bm(bm, M); o = obj('FuelFiller_Tab_'+tag, bm, ['M_Nickel'], smooth=False)
        bv = o.modifiers.new('bev', 'BEVEL'); bv.width = 0.002; bv.segments = 2

# ------------------------------------------------------------------ tail: lamps, holes, tube, exhaust, tow stubs
def build_tail():
    bmb = bmesh.new(); bml = bmesh.new(); bma = bmesh.new(); bmh = bmesh.new()
    for yy, amber in ((0.535, False), (0.316, True), (-0.316, True), (-0.535, False)):
        hit = surf.raycast([4.8, yy, 0.320], [-1, 0, 0]); n = surf.normal(hit)[0]
        n2 = n + np.array([0.6, 0, 0]); n2 /= np.linalg.norm(n2)          # lamps point mostly rearward
        M = look_matrix(BL(hit - 0.004*n2), tuple(surf.dir_to_bl(n2)))
        b = lathe([(0.021, 0.0), (0.0235, 0.004), (0.0245, 0.020), (0.0265, 0.024), (0.0290, 0.027), (0.0290, 0.029), (0.0265, 0.031), (0.022, 0.030)], segs=40, axis='Z', mat_idx=0)
        transform_bm(b, M); merge_into(bmb, b)
        b = lathe([(0.0, 0.031), (0.012, 0.0305), (0.0225, 0.0290)], segs=40, axis='Z', mat_idx=0)
        transform_bm(b, M); merge_into(bma if amber else bml, b)
    for yy in (0.462, 0.388, 0.237, 0.158, 0.079, 0.0, -0.079, -0.158, -0.237, -0.388, -0.462):
        hit = surf.raycast([4.8, yy, 0.322], [-1, 0, 0]); n = surf.normal(hit)[0]
        M = look_matrix(BL(hit + 0.0004*n), tuple(surf.dir_to_bl(n)))
        b = lathe([(0.0, -0.001), (0.0088, -0.001)], segs=18, axis='Z', mat_idx=0); transform_bm(b, M)
        merge_into(bmh, b)
    obj('TailLamp_Bodies', bmb, ['M_Chrome']); obj('TailLamp_Lenses', bml, ['M_RedLens']); obj('TailLamp_LensesAmber', bma, ['M_AmberLens'])
    obj('Tail_Holes', bmh, ['M_DarkHole'], smooth=False)
    # upper small lamps (chrome domes on black bases)
    for s in (1, -1):
        tag = 'L' if s > 0 else 'R'
        hit = surf.raycast([4.8, s*0.293, 0.446], [-1, 0, 0]); n = surf.normal(hit)[0]
        M = look_matrix(BL(hit), tuple(surf.dir_to_bl(n)))
        b = lathe([(0.0, 0.004), (0.017, 0.004), (0.018, 0.0), (0.012, -0.002)], segs=24, axis='Z', mat_idx=0); transform_bm(b, M)
        obj('TailLamp_Small_Base_'+tag, b, ['M_BlackGloss'])
        # lamp body projects downward-rear
        n3 = n + np.array([0, 0, -0.9]); n3 /= np.linalg.norm(n3)
        M3 = look_matrix(BL(hit + 0.004*n), tuple(surf.dir_to_bl(n3)))
        b = lathe([(0.0, 0.034), (0.008, 0.033), (0.012, 0.028), (0.0125, 0.012), (0.009, 0.004), (0.006, 0.0)], segs=24, axis='Z', mat_idx=0); transform_bm(b, M3)
        obj('TailLamp_Small_'+tag, b, ['M_Chrome'])
        b = lathe([(0.0, 0.0345), (0.008, 0.034)], segs=24, axis='Z', mat_idx=0); transform_bm(b, M3)
        obj('TailLamp_SmallLens_'+tag, b, ['M_AmberLens'])
    # light-blue breather tube below the spare (car right, y=-0.20)
    hit = surf.raycast([4.8, -0.20, 0.47], [-1, 0, 0]); n = surf.normal(hit)[0]
    dtube = 0.75*n + np.array([0.0, 0.0, -0.66]); dtube = dtube/np.linalg.norm(dtube)
    M = look_matrix(BL(hit - 0.006*n), tuple(surf.dir_to_bl(dtube)))
    b = lathe([(0.0, 0.0), (0.017, 0.0), (0.018, 0.012), (0.021, 0.014), (0.021, 0.020), (0.018, 0.022), (0.018, 0.072), (0.013, 0.074), (0.0125, 0.06)], segs=32, axis='Z', mat_idx=0)
    transform_bm(b, M); obj('Tail_BreatherTube', b, ['M_Paint'])
    # tow stubs (side bumperettes)
    for s in (1, -1):
        hit = surf.raycast([3.83, s*1.2, 0.405], [0, -s, 0]); n = surf.normal(hit)[0]
        M = look_matrix(BL(hit), tuple(surf.dir_to_bl(n)))
        b = lathe([(0.0, 0.074), (0.013, 0.074), (0.021, 0.070), (0.024, 0.062), (0.022, 0.055), (0.016, 0.051), (0.0145, 0.036), (0.022, 0.034), (0.022, 0.0), (0.028, -0.004)], segs=32, axis='Z', mat_idx=0)
        transform_bm(b, M); obj('TowStub_%d' % (s > 0), b, ['M_Steel'])
    # exhaust: downpipe from engine bay, silencer section, straight pipe under the left sill, open end at x=3.97
    yl = 0.37
    pts = [[0.70, 0.30, 0.43], [0.80, 0.33, 0.35], [0.90, yl, 0.262], [0.98, yl, 0.212], [1.06, yl, 0.198], [1.30, yl, 0.196]]
    bm = tube_along([BLV(p) for p in pts], 0.024, segs=18)
    obj('Exhaust_Downpipe', bm, ['M_ExhaustSteel'])
    bm = lathe([(0.024, 0.0), (0.034, 0.03), (0.036, 0.08), (0.036, 0.40), (0.034, 0.45), (0.024, 0.48)], segs=24, axis='Z', mat_idx=0)
    transform_bm(bm, look_matrix(BLV([1.02, yl, 0.197]), tuple(surf.dir_to_bl([1, 0, 0]))))
    obj('Exhaust_Silencer', bm, ['M_ExhaustSteel'])
    pts = [[1.48, yl, 0.196], [2.2, yl, 0.197], [3.0, yl, 0.199], [3.55, yl, 0.200], [3.70, yl - 0.012, 0.200], [3.80, yl - 0.055, 0.201], [3.875, 0.235, 0.201], [3.925, 0.185, 0.202], [3.955, 0.160, 0.202]]
    bm = tube_along([BLV(p) for p in pts], 0.020, segs=16)
    # open end: add an inner sleeve so the pipe reads as hollow
    b = lathe([(0.020, 0.0), (0.0165, 0.0), (0.0165, -0.05)], segs=16, axis='Z', mat_idx=0)
    dd = np.array([3.955, 0.160, 0.202]) - np.array([3.925, 0.185, 0.202])
    transform_bm(b, look_matrix(BLV([3.955, 0.160, 0.202]), tuple(surf.dir_to_bl(dd/np.linalg.norm(dd)))))
    merge_into(bm, b)
    obj('Exhaust_Pipe', bm, ['M_ExhaustSteel'])
    # hangers
    bm = bmesh.new()
    for xh in (2.25, 3.62):
        top = surf.raycast([xh, yl, 0.0], [0, 0, 1])
        ztop = top[2] + 0.01 if top is not None else 0.26
        cylinder(bm, BLV([xh, yl, 0.21]), BLV([xh, yl, ztop]), 0.005, segs=8)
    obj('Exhaust_Hangers', bm, ['M_Underbody'])
    # chassis (hidden mostly): axles, differential, frame rails
    bm = bmesh.new()
    cylinder(bm, BLV([0.0, -0.62, 0.385]), BLV([0.0, 0.62, 0.385]), 0.030, segs=16)
    cylinder(bm, BLV([2.98, -0.62, 0.39]), BLV([2.98, 0.62, 0.39]), 0.040, segs=16)
    for s in (1, -1):
        cylinder(bm, BLV([-0.35, s*0.40, 0.33]), BLV([4.0, s*0.40, 0.33]), 0.035, segs=12)
    b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=24, v_segments=12, radius=0.12); bmesh.ops.translate(b, vec=BLV([2.98, 0.0, 0.39]), verts=b.verts)
    merge_into(bm, b)
    obj('Chassis_Axles', bm, ['M_Underbody'])
