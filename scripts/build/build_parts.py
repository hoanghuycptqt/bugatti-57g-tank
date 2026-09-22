"""Build all detail parts for the 57G Tank (runs in bpy)."""
import bpy, bmesh, math, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, '/home/claude/tank/build')
import surf, details, wheel
from geomkit import lathe, new_obj, cylinder, transform_bm, tube_along, look_matrix, get_mat
from shapes2d import rounded_rect

BL = surf.to_bl
def V(p): return Vector(tuple(float(c) for c in p))
def BLV(p): return V(BL(np.asarray(p, float)))
def BLD(d): return V(surf.dir_to_bl(np.asarray(d, float)))

COLL = None
def obj(name, bm, mats, smooth=True):
    return new_obj(name, bm, mats, coll=COLL, smooth=smooth)

def poly_face(bm, pts, mat=0):
    vs = [bm.verts.new(V(p)) for p in pts]
    f = bm.faces.new(vs); f.material_index = mat
    return f

def plate_from_outline(bm, pts3d, normal, thick=0.0, mat=0):
    """filled polygon (n-gon, triangulated) + optional thickness along -normal"""
    top = [bm.verts.new(V(p)) for p in pts3d]
    f = bm.faces.new(top); f.material_index = mat
    if thick > 0:
        nb = V(normal) * thick
        bot = [bm.verts.new(v.co - nb) for v in top]
        f2 = bm.faces.new(list(reversed(bot))); f2.material_index = mat
        n = len(top)
        for i in range(n):
            ff = bm.faces.new((top[i], bot[i], bot[(i+1) % n], top[(i+1) % n])); ff.material_index = mat
    return bm

# ---------------------------------------------------------------- nose plane frame (car coords)
NP0 = np.array([-0.43, 0.0, 0.30]); NU = np.array([0, 1.0, 0]); NT = np.array([0.311, 0, 0.950]); NN = np.array([-0.950, 0, 0.311])
def nose_pt(u, v, w):
    return NP0 + u*NU + v*NT + w*NN

def build_grille():
    uv = details.grille_outline_uv()
    # mesh insert
    bm = bmesh.new()
    pts = [BL(nose_pt(u, v, -0.022)) for u, v in uv]
    plate_from_outline(bm, pts, surf.dir_to_bl(NN), 0.0, 0)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    ob = obj('Grille_Mesh', bm, ['M_WireMesh'], smooth=False)
    # radiator core plate
    bm = bmesh.new()
    pts = [BL(nose_pt(u*0.99, v, -0.0285)) for u, v in uv]
    plate_from_outline(bm, pts, surf.dir_to_bl(NN), 0.0, 0)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    obj('Grille_Core', bm, ['M_Radiator'], smooth=False)
    # rim tube (nickel) around the outline, slightly outside
    c = uv.mean(0)
    ring = []
    for u, v in uv:
        d = np.array([u, v]) - c; d = d/np.linalg.norm(d)
        uu, vv = np.array([u, v]) + 0.004*d
        ring.append(BL(nose_pt(uu, vv, 0.0015)))
    bm = tube_along([V(p) for p in ring], 0.0065, segs=10, closed=True)
    obj('Grille_Rim', bm, ['M_Nickel'])

def build_intake():
    uv = details.intake_outline_uv()
    bm = bmesh.new()
    pts = [BL(nose_pt(u, v, -0.030)) for u, v in uv]
    plate_from_outline(bm, pts, surf.dir_to_bl(NN), 0.0, 0)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    obj('Intake_Mesh', bm, ['M_WireMesh'], smooth=False)
    bm = bmesh.new()
    pts = [BL(nose_pt(u, v, -0.054)) for u, v in uv]
    plate_from_outline(bm, pts, surf.dir_to_bl(NN), 0.0, 0)
    obj('Intake_Back', bm, ['M_Radiator'], smooth=False)
    # two driving lamps behind the mesh
    for s in (1, -1):
        cen = nose_pt(s*0.14, details.z_to_v(0.345), -0.036)
        M = look_matrix(BL(cen), surf.dir_to_bl(NN))
        bm = lathe([(0.0, 0.004), (0.035, 0.002), (0.046, -0.004), (0.050, -0.010), (0.052, -0.004), (0.050, 0.004), (0.044, 0.006)], segs=48, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('DrivingLamp_Bezel_%s' % ('L' if s > 0 else 'R'), bm, ['M_Chrome'])
        bm = lathe([(0.0, 0.010), (0.022, 0.008), (0.040, 0.003), (0.045, 0.0)], segs=48, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('DrivingLamp_Lens_%s' % ('L' if s > 0 else 'R'), bm, ['M_LampGlass'])
        bm = lathe([(0.0, -0.040), (0.02, -0.036), (0.035, -0.022), (0.044, -0.004)], segs=48, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('DrivingLamp_Refl_%s' % ('L' if s > 0 else 'R'), bm, ['M_Chrome'])

def mesh_dome(bm, R, h, segs=48, rings=10, mat=0):
    """spherical cap facing +Z, base radius R, height h (open base)"""
    rs = (R*R + h*h) / (2*h)
    zc = h - rs
    verts = []
    top = bm.verts.new((0, 0, h))
    prev = None
    ang0 = math.asin(R/rs)
    ringsv = []
    for i in range(1, rings+1):
        a = ang0*i/rings
        r = rs*math.sin(a); z = zc + rs*math.cos(a)
        ringsv.append([bm.verts.new((r*math.cos(2*math.pi*k/segs), r*math.sin(2*math.pi*k/segs), z)) for k in range(segs)])
    for k in range(segs):
        f = bm.faces.new((top, ringsv[0][k], ringsv[0][(k+1) % segs])); f.material_index = mat
    for i in range(rings-1):
        for k in range(segs):
            f = bm.faces.new((ringsv[i][k], ringsv[i+1][k], ringsv[i+1][(k+1) % segs], ringsv[i][(k+1) % segs])); f.material_index = mat
    return bm, ringsv[-1]

def build_headlamps():
    for s in (1, -1):
        tag = 'L' if s > 0 else 'R'
        yc = s*details.HEAD['y']; zc = details.HEAD['z']
        # reflector bowl inside pocket
        M = look_matrix(BL([-0.505, yc, zc]), surf.dir_to_bl([-1, 0, 0]))
        bm = lathe([(0.0, 0.0), (0.03, 0.002), (0.06, 0.010), (0.080, 0.022), (0.090, 0.030)], segs=64, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Headlamp_Refl_'+tag, bm, ['M_Chrome'])
        # bulb
        bm = lathe([(0.0, 0.035), (0.008, 0.033), (0.012, 0.024), (0.009, 0.012), (0.004, 0.006)], segs=24, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Headlamp_Bulb_'+tag, bm, ['M_Bulb'])
        # bezel ring (chrome) at pocket mouth
        M2 = look_matrix(BL([-0.535, yc, zc]), surf.dir_to_bl([-1, 0, 0]))
        bm = lathe([(0.078, -0.012), (0.082, 0.000), (0.088, 0.006), (0.094, 0.004), (0.098, -0.004), (0.099, -0.014), (0.096, -0.020)], segs=72, axis='Z', mat_idx=0)
        transform_bm(bm, M2); obj('Headlamp_Bezel_'+tag, bm, ['M_Chrome'])
        # lens (slightly domed)
        bm = lathe([(0.0, 0.012), (0.03, 0.010), (0.06, 0.006), (0.080, 0.000)], segs=72, axis='Z', mat_idx=0)
        transform_bm(bm, M2); obj('Headlamp_Lens_'+tag, bm, ['M_LampGlassFluted'])
        # wire mesh guard dome in front
        M3 = look_matrix(BL([-0.548, yc, zc]), surf.dir_to_bl([-1, 0, 0]))
        bm = bmesh.new()
        bm, rim = mesh_dome(bm, 0.118, 0.060, segs=64, rings=12)
        transform_bm(bm, M3); obj('Headlamp_Guard_'+tag, bm, ['M_WireMeshGuard'])
        # guard rim wire + bracket
        ring = [BL([-0.548, yc + 0.118*math.cos(2*math.pi*k/64)*1.0, zc + 0.118*math.sin(2*math.pi*k/64)]) for k in range(64)]
        bm = tube_along([V(p) for p in ring], 0.0028, segs=8, closed=True)
        obj('Headlamp_GuardRim_'+tag, bm, ['M_SteelDark'])
        # bracket on top of guard: small plate to pod surface
        top_pt = np.array([-0.555, yc, zc + 0.118])
        hit = surf.raycast([top_pt[0] - 0.3, yc, zc + 0.135], [1, 0, 0])
        bm = bmesh.new()
        p0 = top_pt; p1 = hit if hit is not None else top_pt + np.array([0.05, 0, 0.02])
        w = 0.022
        pts = [p0 + [0, -w, 0], p0 + [0, w, 0], p1 + [0.01, w, 0.005], p1 + [0.01, -w, 0.005]]
        plate_from_outline(bm, [BL(p) for p in pts], surf.dir_to_bl([0, 0, 1]), 0.004, 0)
        obj('Headlamp_Bracket_'+tag, bm, ['M_Paint'], smooth=False)

def rivet(bm, p, n, r=0.0042, mat=0):
    M = look_matrix(BL(p), surf.dir_to_bl(n))
    b2 = lathe([(0.0, 0.0028), (r*0.6, 0.0022), (r, 0.0004), (r*1.02, -0.001)], segs=10, axis='Z', mat_idx=mat)
    transform_bm(b2, M)
    b2.verts.ensure_lookup_table()
    me = bpy.data.meshes.new('tmp'); b2.to_mesh(me); b2.free()
    bm.from_mesh(me); bpy.data.meshes.remove(me)

def build_vents():
    bm_mesh = bmesh.new(); bm_riv = bmesh.new()
    for s in (1, -1):
        for poly, xs in zip(details.vent_polys(), details.VENT_SURF_X):
            pts = [BL([xs + 0.024, s*y, z]) for y, z in poly]
            if s < 0: pts = list(reversed(pts))
            plate_from_outline(bm_mesh, pts, surf.dir_to_bl([-1, 0, 0]), 0.0, 0)
            # rivets around (offset outline)
            c = poly.mean(0)
            per = np.vstack([poly, poly[:1]])
            seglen = np.linalg.norm(np.diff(per, axis=0), axis=1); L = seglen.sum()
            nr = max(4, int(L / 0.028))
            for k in range(nr):
                t = k * L / nr
                i = np.searchsorted(np.cumsum(seglen), t)
                i = min(i, len(seglen)-1)
                t0 = t - (np.cumsum(seglen)[i] - seglen[i])
                pp = per[i] + (per[i+1] - per[i]) * (t0 / max(seglen[i], 1e-9))
                d = pp - c; d = d / (np.linalg.norm(d) + 1e-9)
                py, pz = pp + 0.013*d
                hit = surf.raycast([-0.8, s*py, pz], [1, 0, 0])
                if hit is not None:
                    rivet(bm_riv, hit, surf.normal(hit)[0])
    bmesh.ops.triangulate(bm_mesh, faces=bm_mesh.faces)
    obj('PodVents_Mesh', bm_mesh, ['M_WireMesh'], smooth=False)
    obj('PodVents_Rivets', bm_riv, ['M_Paint'])

def build_straps():
    for s in (1, -1):
        tag = 'L' if s > 0 else 'R'
        u = s*0.255
        v0, v1 = details.z_to_v(0.395), details.z_to_v(0.60)
        vs = np.linspace(v0, v1, 12)
        w = 0.016
        bm = bmesh.new()
        top = []; bot = []
        for v in vs:
            p = nose_pt(u, v, 0.0)
            hit = surf.project(p + 0.02*NN)
            nrm = surf.normal(hit)[0]
            top.append((BL(hit + 0.004*nrm + [0, -w, 0]), BL(hit + 0.004*nrm + [0, w, 0])))
            bot.append((BL(hit + 0.0005*nrm + [0, -w, 0]), BL(hit + 0.0005*nrm + [0, w, 0])))
        tv = [(bm.verts.new(V(a)), bm.verts.new(V(b))) for a, b in top]
        bv = [(bm.verts.new(V(a)), bm.verts.new(V(b))) for a, b in bot]
        for i in range(len(tv)-1):
            bm.faces.new((tv[i][0], tv[i][1], tv[i+1][1], tv[i+1][0]))
            bm.faces.new((bv[i][0], bv[i+1][0], bv[i+1][1], bv[i][1]))
            bm.faces.new((tv[i][0], tv[i+1][0], bv[i+1][0], bv[i][0]))
            bm.faces.new((tv[i][1], bv[i][1], bv[i+1][1], tv[i+1][1]))
        obj('HoodStrap_'+tag, bm, ['M_Leather'], smooth=False)
        # buckle frame
        pb = surf.project(nose_pt(u, details.z_to_v(0.50), 0.02))
        nrm = surf.normal(pb)[0]
        M = look_matrix(BL(pb + 0.006*nrm), surf.dir_to_bl(nrm), xhint=(0, 0, 1))
        bm = bmesh.new()
        for (a, b, c_, d) in [((-0.024, -0.022), (0.024, -0.022), (0.024, -0.017), (-0.024, -0.017)), ((-0.024, 0.017), (0.024, 0.017), (0.024, 0.022), (-0.024, 0.022)),
                              ((-0.024, -0.022), (-0.019, -0.022), (-0.019, 0.022), (-0.024, 0.022)), ((0.019, -0.022), (0.024, -0.022), (0.024, 0.022), (0.019, 0.022))]:
            vv = [bm.verts.new((q[0], q[1], 0.0)) for q in (a, b, c_, d)]
            vt = [bm.verts.new((q[0], q[1], 0.004)) for q in (a, b, c_, d)]
            bm.faces.new(vt); bm.faces.new(list(reversed(vv)))
            for i in range(4): bm.faces.new((vv[i], vv[(i+1) % 4], vt[(i+1) % 4], vt[i]))
        transform_bm(bm, M); obj('HoodStrap_Buckle_'+tag, bm, ['M_Steel'], smooth=False)
        # latch rod (chrome) outboard of strap
        pa = surf.project(nose_pt(s*0.305, details.z_to_v(0.43), 0.02))
        pb2 = surf.project(nose_pt(s*0.31, details.z_to_v(0.60), 0.02))
        na = surf.normal(pa)[0]; nb = surf.normal(pb2)[0]
        pts = [pa + 0.012*na, pa + 0.018*na, pb2 + 0.018*nb, pb2 + 0.010*nb + 0.02*NT]
        bm = tube_along([BLV(p) for p in pts], 0.0045, segs=10)
        obj('HoodLatch_'+tag, bm, ['M_Chrome'])

def build_hood_top():
    # centre hinge strip with rivets
    bm = bmesh.new(); bmr = bmesh.new()
    xs = np.linspace(-0.20, 1.12, 90)
    left = []; right = []
    for x in xs:
        hit = surf.raycast([x, 0.0, 2.0], [0, 0, -1])
        n = surf.normal(hit)[0]
        side = np.cross(n, [1, 0, 0]); side = side / np.linalg.norm(side)
        left.append(hit + 0.0035*n + 0.007*side); right.append(hit + 0.0035*n - 0.007*side)
    lv = [bm.verts.new(BLV(p)) for p in left]; rv = [bm.verts.new(BLV(p)) for p in right]
    for i in range(len(xs)-1):
        bm.faces.new((lv[i], rv[i], rv[i+1], lv[i+1]))
    obj('Hood_Hinge', bm, ['M_Paint'], smooth=True)
    for x in np.arange(-0.18, 1.11, 0.032):
        hit = surf.raycast([x, 0.0, 2.0], [0, 0, -1]); n = surf.normal(hit)[0]
        rivet(bmr, hit + 0.003*n, n, r=0.0032)
    # hood louvers: 4 columns
    for yc in (-0.215, -0.12, 0.12, 0.215):
        for x in np.arange(0.06, 0.88, 0.034):
            hit = surf.raycast([x, yc, 2.0], [0, 0, -1])
            if hit is None: continue
            n = surf.normal(hit)[0]
            # louver: small raised shell open toward rear (+x)
            M = look_matrix(BL(hit), surf.dir_to_bl(n), xhint=tuple(surf.dir_to_bl([1, 0, 0])))
            lb = bmesh.new()
            L, W, H = 0.013, 0.030, 0.0042
            prof = []
            ring = []
            nseg = 8
            for k in range(nseg+1):
                a = math.pi*k/nseg
                ring.append((-L*0.5 + L*0.5*(1-math.cos(a))*0.9, W*math.cos(a), H*math.sin(a)))
            # sweep: front closed, open at rear (x=+L/2)
            vs0 = [lb.verts.new((-L*0.5, W*math.cos(math.pi*k/nseg), 0.0)) for k in range(nseg+1)]
            vs1 = [lb.verts.new((L*0.5, W*math.cos(math.pi*k/nseg)*0.98, H*math.sin(math.pi*k/nseg))) for k in range(nseg+1)]
            for k in range(nseg):
                lb.faces.new((vs0[k], vs0[k+1], vs1[k+1], vs1[k]))
            transform_bm(lb, M)
            me = bpy.data.meshes.new('tmp'); lb.to_mesh(me); lb.free(); bmr.from_mesh(me); bpy.data.meshes.remove(me)
    obj('Hood_Rivets_Louvers', bmr, ['M_Paint'], smooth=True)
    # small chrome cap on left cowl shoulder
    hit = surf.raycast([1.494, 0.42, 2.0], [0, 0, -1]); n = surf.normal(hit)[0]
    M = look_matrix(BL(hit), surf.dir_to_bl(n))
    bm = lathe([(0.0, 0.0135), (0.010, 0.0132), (0.016, 0.0118), (0.030, 0.0105), (0.0355, 0.0085), (0.0365, 0.004), (0.036, 0.0), (0.034, -0.004)], segs=48, axis='Z', mat_idx=0)
    transform_bm(bm, M); obj('Cowl_Cap', bm, ['M_Nickel'])

def build_all():
    build_grille(); build_intake(); build_headlamps(); build_vents(); build_straps(); build_hood_top()

if __name__ == '__main__':
    COLL = bpy.context.scene.collection
    build_all()

# ======================================================================= cockpit
def build_cockpit():
    # windscreen (driver side, y<0): curved glass + frame
    y0, y1 = -0.37, -0.12
    base_x = 1.635
    hit0 = surf.raycast([base_x, -0.245, 2.0], [0, 0, -1])
    zb = hit0[2] + 0.012
    H = 0.145; tilt = math.radians(28)
    cols = 16; rows = 6
    bm = bmesh.new(); grid = []
    for j in range(rows+1):
        t = j/rows
        row = []
        for i in range(cols+1):
            s = i/cols
            y = y0 + (y1 - y0)*s
            bulge = 0.018*(1 - (2*s - 1)**2)
            x = base_x + t*H*math.sin(tilt) - bulge
            z = zb + t*H*math.cos(tilt) + 0.012*math.sin(math.pi*s)*t
            row.append(bm.verts.new(BLV([x, y, z])))
        grid.append(row)
    for j in range(rows):
        for i in range(cols):
            bm.faces.new((grid[j][i], grid[j][i+1], grid[j+1][i+1], grid[j+1][i]))
    # frame: top edge + sides (capture coords before bm is freed)
    top = [grid[rows][i].co.copy() for i in range(cols+1)]
    left = [grid[j][0].co.copy() for j in range(rows+1)]
    right = [grid[j][cols].co.copy() for j in range(rows+1)]
    obj('Windscreen_Glass', bm, ['M_Glass'])
    bm = tube_along(top, 0.0045, segs=8)
    bm2 = tube_along(left, 0.0055, segs=8); me = bpy.data.meshes.new('t'); bm2.to_mesh(me); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bm2 = tube_along(right, 0.0055, segs=8); me = bpy.data.meshes.new('t'); bm2.to_mesh(me); bm.from_mesh(me); bpy.data.meshes.remove(me)
    obj('Windscreen_Frame', bm, ['M_SteelDark'])
    # rear-view mirrors on shoulders
    for s in (1, -1):
        tag = 'L' if s > 0 else 'R'
        base = surf.raycast([1.60, s*0.55, 2.0], [0, 0, -1])
        head = base + np.array([0.0, 0.0, 0.085])
        bm = bmesh.new()
        cylinder(bm, BLV(base - [0, 0, 0.01]), BLV(head), 0.006, segs=10)
        cylinder(bm, BLV(base), BLV(base + [0, 0, 0.004]), 0.018, segs=16)
        obj('Mirror_Stalk_'+tag, bm, ['M_Chrome'])
        M = look_matrix(BLV(head + [0.004, 0, 0.0]), tuple(surf.dir_to_bl([1, 0, 0])))
        bm = lathe([(0.0, -0.022), (0.02, -0.021), (0.033, -0.014), (0.039, -0.004), (0.040, 0.004), (0.038, 0.006)], segs=40, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Mirror_Back_'+tag, bm, ['M_BlackGloss'])
        bm = lathe([(0.034, 0.002), (0.039, 0.004), (0.041, 0.008), (0.040, 0.011), (0.036, 0.010)], segs=40, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Mirror_Rim_'+tag, bm, ['M_Chrome'])
        bm = lathe([(0.0, 0.0085), (0.035, 0.0085)], segs=40, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Mirror_Glass_'+tag, bm, ['M_Mirror'])
    # dashboard panel (black crackle) across cockpit front
    bm = bmesh.new()
    xs_d = 1.748
    ys = np.linspace(-0.44, 0.44, 23); zs = np.linspace(0.70, 0.985, 8)
    g = [[bm.verts.new(BLV([xs_d + 0.03*(zz - 0.70) + 0.025*(yy/0.44)**2, yy, zz])) for yy in ys] for zz in zs]
    for j in range(len(zs)-1):
        for i in range(len(ys)-1):
            bm.faces.new((g[j][i], g[j][i+1], g[j+1][i+1], g[j+1][i]))
    obj('Dashboard', bm, ['M_Crackle'])
    # gauges: (y, z, radius)
    gauges = [(-0.215, 0.865, 0.064), (-0.075, 0.905, 0.026), (-0.075, 0.845, 0.026), (-0.020, 0.915, 0.024), (-0.020, 0.860, 0.024), (-0.022, 0.805, 0.024), (0.095, 0.860, 0.040)]
    bmr = bmesh.new(); bmf = bmesh.new(); bmg = bmesh.new()
    for (yy, zz, r) in gauges:
        xx = xs_d + 0.03*(zz - 0.70) + 0.025*(yy/0.44)**2 - 0.002
        M = look_matrix(BLV([xx, yy, zz]), tuple(surf.dir_to_bl([1, -0.0, 0.25])))
        b = lathe([(r*0.86, 0.004), (r, 0.006), (r*1.08, 0.004), (r*1.1, 0.0)], segs=40, axis='Z', mat_idx=0); transform_bm(b, M)
        me = bpy.data.meshes.new('t'); b.to_mesh(me); bmr.from_mesh(me); bpy.data.meshes.remove(me)
        b = lathe([(0.0, 0.002), (r*0.86, 0.002)], segs=40, axis='Z', mat_idx=0); transform_bm(b, M)
        me = bpy.data.meshes.new('t'); b.to_mesh(me); bmf.from_mesh(me); bpy.data.meshes.remove(me)
        b = lathe([(0.0, 0.0065), (r*0.86, 0.0065)], segs=40, axis='Z', mat_idx=0); transform_bm(b, M)
        me = bpy.data.meshes.new('t'); b.to_mesh(me); bmg.from_mesh(me); bpy.data.meshes.remove(me)
    obj('Gauge_Bezels', bmr, ['M_Chrome']); obj('Gauge_Faces', bmf, ['M_GaugeFace'], smooth=False); obj('Gauge_Glass', bmg, ['M_Glass'], smooth=False)
    # steering wheel (driver side y<0)
    c = np.array([1.93, -0.245, 0.905]); nrm = np.array([-0.62, 0.0, 0.78]); nrm /= np.linalg.norm(nrm)
    M = look_matrix(BLV(c), tuple(surf.dir_to_bl(-nrm)), xhint=tuple(surf.dir_to_bl([0, 1, 0])))
    ring = [Vector((0.212*math.cos(2*math.pi*k/96), 0.212*math.sin(2*math.pi*k/96), 0.0)) for k in range(96)]
    bm = tube_along(ring, 0.0135, segs=12, closed=True); transform_bm(bm, M); obj('SteeringWheel_Rim', bm, ['M_Wood'])
    bm = bmesh.new()
    for k in range(4):
        a = math.radians(45 + 90*k)
        d = Vector((math.cos(a), math.sin(a), 0.0)); t = Vector((-math.sin(a), math.cos(a), 0.0))
        for (r0, r1, w0, w1) in [(0.03, 0.205, 0.011, 0.006)]:
            vs = [d*r0 - t*w0, d*r1 - t*w1, d*r1 + t*w1, d*r0 + t*w0]
            v0 = [bm.verts.new(v + Vector((0, 0, -0.004 - 0.02*(1 - (v.length/0.205))))) for v in vs]
            v1 = [bm.verts.new(v + Vector((0, 0, 0.0 - 0.02*(1 - (v.length/0.205))))) for v in vs]
            bm.faces.new(v0[::-1]); bm.faces.new(v1)
            for i in range(4): bm.faces.new((v0[i], v0[(i+1)%4], v1[(i+1)%4], v1[i]))
    b2 = lathe([(0.0, -0.012), (0.034, -0.014), (0.038, -0.024), (0.03, -0.034), (0.02, -0.06)], segs=32, axis='Z', mat_idx=0)
    me = bpy.data.meshes.new('t'); b2.to_mesh(me); bm.from_mesh(me); bpy.data.meshes.remove(me)
    transform_bm(bm, M); obj('SteeringWheel_Spokes', bm, ['M_AluBrushed'], smooth=False)
    # column
    bm = bmesh.new(); cylinder(bm, BLV(c + 0.06*(-nrm)*-1 + np.array([0, 0, 0])), BLV(np.array([1.755, -0.245, 0.77])), 0.018, segs=16)
    obj('SteeringColumn', bm, ['M_BlackGloss'])
    # seats
    for s, tag in ((-1, 'Driver'), (1, 'Passenger')):
        yc = s*0.235
        bm = bmesh.new()
        # cushion: rounded box via lathe-free approach -> simple subdivided box
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.36, 0.40, 0.09), verts=bm.verts)
        bmesh.ops.translate(bm, vec=BLV([2.17, yc, 0.405]), verts=bm.verts)
        cush = obj('Seat_Cushion_'+tag, bm, ['M_SeatLeather'])
        sub = cush.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.38, 0.07, 0.40), verts=bm.verts)
        R = Matrix.Rotation(math.radians(-14), 4, 'X')
        bmesh.ops.transform(bm, matrix=R, verts=bm.verts)
        bmesh.ops.translate(bm, vec=BLV([2.36, yc, 0.64]), verts=bm.verts)
        back = obj('Seat_Back_'+tag, bm, ['M_SeatLeather'])
        sub = back.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
    # gear lever with ivory knob
    bm = bmesh.new(); cylinder(bm, BLV([1.99, -0.03, 0.36]), BLV([1.95, -0.03, 0.74]), 0.008, segs=12)
    obj('GearLever', bm, ['M_Chrome'])
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.024)
    bmesh.ops.translate(bm, vec=BLV([1.95, -0.03, 0.755]), verts=bm.verts)
    obj('GearKnob', bm, ['M_Ivory'])
    # cockpit floor mat
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.70, 0.92, 0.01), verts=bm.verts)
    bmesh.ops.translate(bm, vec=BLV([2.06, 0.0, 0.345]), verts=bm.verts)
    obj('Cockpit_Floor', bm, ['M_Interior'], smooth=False)

# ======================================================================= side & rear
def build_side_rear():
    # side lamp pod (right side, y<0) : teardrop + chrome-bezel lamp facing forward
    zc = 0.762; yc = -0.842
    prof = []
    for k in range(25):
        t = k/24
        x = 1.452 + t*0.30
        r = 0.058*(1 - t**2.2)**0.75
        prof.append((max(r, 0.0005), x))
    bm = lathe(prof, segs=40, axis='Z', mat_idx=0)
    M = Matrix.Translation(BLV([0, yc, zc]) - Vector((0, 0, 0))) @ Matrix.Rotation(math.radians(-90), 4, 'X')
    # lathe along Z -> map Z to car +x (blender +Y)
    bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(-90), 4, 'X'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((yc, -OFF_Y_BL, zc)), verts=bm.verts)
    obj('SideLamp_Pod', bm, ['M_Paint'])
    M = look_matrix(BLV([1.452, yc, zc]), tuple(surf.dir_to_bl([-1, 0, 0])))
    bm = lathe([(0.044, -0.004), (0.050, 0.004), (0.056, 0.006), (0.060, 0.0), (0.060, -0.012)], segs=48, axis='Z', mat_idx=0)
    transform_bm(bm, M); obj('SideLamp_Bezel', bm, ['M_Chrome'])
    bm = lathe([(0.0, 0.008), (0.03, 0.006), (0.046, 0.001)], segs=48, axis='Z', mat_idx=0)
    transform_bm(bm, M); obj('SideLamp_Lens', bm, ['M_LampGlassFluted'])
    # fuel filler plate + caps on deck
    hit = surf.raycast([2.57, 0.0, 2.0], [0, 0, -1]); n = surf.normal(hit)[0]
    M = look_matrix(BLV(hit + 0.001*n), tuple(surf.dir_to_bl(n)), xhint=tuple(surf.dir_to_bl([0, 1, 0])))
    ring_out = [(0.150*math.cos(a), 0.082*math.sin(a)) for a in np.linspace(0, 2*math.pi, 64, endpoint=False)]
    bm = bmesh.new()
    top = [bm.verts.new((u, v, 0.004)) for u, v in ring_out]; bot = [bm.verts.new((u, v, -0.002)) for u, v in ring_out]
    bm.faces.new(top); bm.faces.new(bot[::-1])
    for i in range(64): bm.faces.new((top[i], bot[i], bot[(i+1)%64], top[(i+1)%64]))
    transform_bm(bm, M); obj('FuelFiller_Plate', bm, ['M_Nickel'])
    for s in (1, -1):
        b = lathe([(0.0, 0.040), (0.035, 0.039), (0.044, 0.034), (0.046, 0.020), (0.044, 0.004)], segs=40, axis='Z', mat_idx=0)
        bmesh.ops.translate(b, vec=Vector((s*0.068, 0.0, 0.0)), verts=b.verts)
        transform_bm(b, M); obj('FuelFiller_Cap_%d' % (s > 0), b, ['M_Nickel'])
    # rear vents mesh inserts
    for s in (1, -1):
        rv = details.REARVENT
        pts = []
        for a in np.linspace(0, 2*math.pi, 48, endpoint=False):
            yy = s*(rv['y'] + rv['a']*math.cos(a)); zz = rv['z'] + rv['b']*math.sin(a)
            hit = surf.raycast([4.6, yy*0.999, zz], [-1, 0, 0])
            pts.append(hit)
        pts = np.array([p for p in pts if p is not None])
        cen = pts.mean(0); nn = surf.normal(surf.raycast([4.6, s*rv['y'], rv['z'] + 0.3], [-1, 0, 0]))[0]
        bm = bmesh.new()
        ins = [BL(p - 0.02*np.array([1, 0, 0])) for p in pts]
        if s < 0: ins = ins[::-1]
        plate_from_outline(bm, ins, (0, 0, 1), 0.0, 0); bmesh.ops.triangulate(bm, faces=bm.faces)
        obj('RearVent_Mesh_%d' % (s > 0), bm, ['M_WireMesh'], smooth=False)
    # tail lamps and holes along lower tail
    bml = bmesh.new(); bmb = bmesh.new(); bmh = bmesh.new()
    for yy in (0.53, 0.30, -0.30, -0.53):
        hit = surf.raycast([4.8, yy, 0.322], [-1, 0, 0]); n = surf.normal(hit)[0]
        M = look_matrix(BLV(hit), tuple(surf.dir_to_bl(n)))
        b = lathe([(0.021, 0.002), (0.026, 0.010), (0.030, 0.012), (0.032, 0.006), (0.032, -0.004)], segs=32, axis='Z', mat_idx=0); transform_bm(b, M)
        me = bpy.data.meshes.new('t'); b.to_mesh(me); bmb.from_mesh(me); bpy.data.meshes.remove(me)
        b = lathe([(0.0, 0.020), (0.012, 0.018), (0.022, 0.010)], segs=32, axis='Z', mat_idx=0); transform_bm(b, M)
        me = bpy.data.meshes.new('t'); b.to_mesh(me); bml.from_mesh(me); bpy.data.meshes.remove(me)
    for yy in (0.47, 0.41, 0.24, 0.17, 0.10, 0.035, -0.035, -0.10, -0.17, -0.24, -0.41, -0.47):
        hit = surf.raycast([4.8, yy, 0.322], [-1, 0, 0]); n = surf.normal(hit)[0]
        M = look_matrix(BLV(hit + 0.0005*n), tuple(surf.dir_to_bl(n)))
        b = lathe([(0.0, 0.0), (0.0085, 0.0)], segs=16, axis='Z', mat_idx=0); transform_bm(b, M)
        me = bpy.data.meshes.new('t'); b.to_mesh(me); bmh.from_mesh(me); bpy.data.meshes.remove(me)
    obj('TailLamp_Bezels', bmb, ['M_Chrome']); obj('TailLamp_Lenses', bml, ['M_RedLens']); obj('Tail_Holes', bmh, ['M_DarkHole'], smooth=False)
    # small upper tail lamps
    for s in (1, -1):
        hit = surf.raycast([4.8, s*0.29, 0.447], [-1, 0, 0]); n = surf.normal(hit)[0]
        M = look_matrix(BLV(hit), tuple(surf.dir_to_bl(n)))
        b = lathe([(0.0, 0.045), (0.012, 0.044), (0.015, 0.036), (0.014, 0.010), (0.010, 0.0)], segs=24, axis='Z', mat_idx=0); transform_bm(b, M)
        obj('TailLamp_Small_%d' % (s > 0), b, ['M_Chrome'])
        b = lathe([(0.0, 0.0462), (0.011, 0.0455)], segs=24, axis='Z', mat_idx=0); transform_bm(b, M)
        obj('TailLamp_SmallLens_%d' % (s > 0), b, ['M_RedLens'])
    # tow stubs
    for s in (1, -1):
        hit = surf.raycast([3.83, s*1.2, 0.41], [0, -s, 0]); n = surf.normal(hit)[0]
        M = look_matrix(BLV(hit), tuple(surf.dir_to_bl(n)))
        b = lathe([(0.0, 0.070), (0.012, 0.070), (0.022, 0.066), (0.026, 0.056), (0.024, 0.048), (0.016, 0.044), (0.016, 0.0), (0.024, -0.004)], segs=32, axis='Z', mat_idx=0); transform_bm(b, M)
        obj('TowStub_%d' % (s > 0), b, ['M_Chrome'])
    # exhaust pipe (left side, under body) with chrome tip at rear
    pts = [[0.55, 0.42, 0.205], [1.5, 0.42, 0.205], [2.5, 0.42, 0.205], [3.55, 0.40, 0.215], [3.95, 0.33, 0.24], [4.12, 0.30, 0.285], [4.19, 0.30, 0.298]]
    bm = tube_along([BLV(p) for p in pts[:-1]], 0.026, segs=16); obj('Exhaust_Pipe', bm, ['M_ExhaustSteel'])
    b = lathe([(0.024, -0.09), (0.030, -0.088), (0.031, 0.0), (0.028, 0.004), (0.024, 0.0)], segs=32, axis='Z', mat_idx=0)
    M = look_matrix(BLV(pts[-1]), tuple(surf.dir_to_bl(np.array(pts[-1]) - np.array(pts[-2]))))
    transform_bm(b, M); obj('Exhaust_Tip', b, ['M_Chrome'])
    # underbody: pan, axles, differential
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(4.30, 1.30, 0.012), verts=bm.verts)
    bmesh.ops.translate(bm, vec=BLV([1.85, 0.0, 0.262]), verts=bm.verts); obj('Underbody_Pan', bm, ['M_Underbody'], smooth=False)
    bm = bmesh.new()
    cylinder(bm, BLV([0.0, -0.62, 0.385]), BLV([0.0, 0.62, 0.385]), 0.030, segs=16)
    cylinder(bm, BLV([2.98, -0.62, 0.39]), BLV([2.98, 0.62, 0.39]), 0.040, segs=16)
    for s in (1, -1):
        cylinder(bm, BLV([-0.35, s*0.40, 0.33]), BLV([4.0, s*0.40, 0.33]), 0.035, segs=12)   # frame rails (round approx)
    b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=24, v_segments=12, radius=0.12); bmesh.ops.translate(b, vec=BLV([2.98, 0.0, 0.39]), verts=b.verts)
    me = bpy.data.meshes.new('t'); b.to_mesh(me); bm.from_mesh(me); bpy.data.meshes.remove(me)
    obj('Chassis_Axles', bm, ['M_Underbody'])

OFF_Y_BL = surf.OFF

def build_spare():
    import wheel as W
    e, objs = W.build_wheel('W_Spare', 0.395, 1)
    t = details.SPARE['tilt']; c = details.SPARE['c']
    axis = np.array([math.sin(t), 0.0, math.cos(t)])
    cen = c + axis*(0.02)
    M = look_matrix(BLV(cen), tuple(surf.dir_to_bl(axis)), xhint=tuple(surf.dir_to_bl([0, 1, 0])))
    e.matrix_world = M
    return e

def build_rest():
    build_cockpit(); build_side_rear(); build_spare()
