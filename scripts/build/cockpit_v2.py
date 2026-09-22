"""cockpit v2"""
import bpy, bmesh, math, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, '/home/claude/tank/build')
import surf
from geomkit import lathe, cylinder, transform_bm, tube_along, look_matrix
from build_parts import obj, V, BL, BLV
from parts_v2 import merge_into

def build_cockpit():
    from shapes2d import rounded_rect
    # windscreen (driver side, y<0): curved screen leaning back ~40 deg, dark steel posts, central mirror
    y0, y1 = -0.363, -0.108
    lean = math.radians(40.0); Hs = 0.205
    cols = 20; rows = 8
    bm = bmesh.new(); grid = []
    base = []
    for i in range(cols+1):
        s = i/cols
        y = y0 + (y1 - y0)*s
        h = surf.raycast([1.672, y, 2.0], [0, 0, -1])
        base.append(h)
    for j in range(rows+1):
        t = j/rows
        row = []
        for i in range(cols+1):
            s = i/cols
            y = y0 + (y1 - y0)*s
            bulge = 0.022*(1 - (2*s - 1)**2)                    # forward bow of the screen
            top_arc = 0.018*(1 - (2*s - 1)**2)                  # arched top edge
            hh = (Hs + top_arc)*t
            b = base[i]
            x = b[0] + 0.004 + hh*math.sin(lean) - bulge*math.sin(math.pi*min(1.0, 0.15 + t))
            z = b[2] + 0.010 + hh*math.cos(lean)
            row.append(bm.verts.new(BLV([x, y, z])))
        grid.append(row)
    for j in range(rows):
        for i in range(cols):
            bm.faces.new((grid[j][i], grid[j][i+1], grid[j+1][i+1], grid[j+1][i]))
    top = [grid[rows][i].co.copy() for i in range(cols+1)]
    left = [grid[j][0].co.copy() for j in range(rows+1)]
    right = [grid[j][cols].co.copy() for j in range(rows+1)]
    obj('Windscreen_Glass', bm, ['M_Screen'])
    bm = tube_along(top, 0.0022, segs=8)
    obj('Windscreen_TopEdge', bm, ['M_SteelDark'])
    bm = bmesh.new()
    for side in (left, right):
        p_low = side[0] - Vector((0, 0, 0.03))
        pts = [p_low] + side + [side[-1] + (side[-1] - side[-2]).normalized()*0.012]
        b = tube_along(pts, 0.0055, segs=10); merge_into(bm, b)
        # clamp block at the base
        c = side[0]
        b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0); bmesh.ops.scale(b, vec=(0.022, 0.03, 0.02), verts=b.verts)
        bmesh.ops.translate(b, vec=c + Vector((0, 0.0, -0.004)), verts=b.verts); merge_into(bm, b)
    obj('Windscreen_Posts', bm, ['M_SteelDark'])
    # streamlined navy fairing under the screen base
    bm = bmesh.new()
    prof_x = np.linspace(1.590, 1.690, 10)
    ysec = np.linspace(-0.372, -0.098, 14)
    rows_v = []
    for xx in prof_x:
        tt = (xx - prof_x[0])/(prof_x[-1] - prof_x[0])
        hmax = 0.034*math.sin(0.5*math.pi*tt)**0.8
        row = []
        for yy in ysec:
            ss = (yy - ysec[0])/(ysec[-1] - ysec[0])
            prof = (1 - (2*ss - 1)**4)**0.5
            base_h = surf.raycast([xx, yy, 2.0], [0, 0, -1])
            row.append(bm.verts.new(BLV([xx, yy, base_h[2] - 0.004 + hmax*prof])))
        rows_v.append(row)
    for i in range(len(prof_x)-1):
        for j in range(len(ysec)-1):
            bm.faces.new((rows_v[i][j], rows_v[i+1][j], rows_v[i+1][j+1], rows_v[i][j+1]))
    back = rows_v[-1]
    bots = [bm.verts.new(v.co - Vector((0, 0, 0.0))) for v in back]
    for j in range(len(ysec)-1):
        pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj('Windscreen_Fairing', bm, ['M_PaintNavy'])
    sd = o.modifiers.new('solid', 'SOLIDIFY'); sd.thickness = 0.003
    # central rectangular rear-view mirror on a stalk (slightly to the passenger side)
    mb = surf.raycast([1.60, 0.062, 2.0], [0, 0, -1]); mn = surf.normal(mb)[0]
    head = mb + np.array([0.0, 0.0, 0.085])
    bm = bmesh.new()
    cylinder(bm, BLV(mb - 0.004*mn), BLV(head), 0.004, segs=10)
    b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0); bmesh.ops.scale(b, vec=(0.018, 0.030, 0.004), verts=b.verts)
    bmesh.ops.translate(b, vec=BLV(mb + 0.002*mn), verts=b.verts); merge_into(bm, b)
    obj('Mirror_Centre_Stalk', bm, ['M_Chrome'])
    Mm = look_matrix(BLV(head + [0.006, 0, 0.012]), tuple(surf.dir_to_bl([0.97, 0.0, 0.24])), xhint=tuple(surf.dir_to_bl([0, 1, 0])))
    rr = rounded_rect(0.0, 0.0, 0.062, 0.026, 0.008, n=6)
    bm = bmesh.new()
    fr_o = [bm.verts.new((u*1.0, v*1.0, 0.004)) for u, v in rr]; fr_i = [bm.verts.new((u*0.93, v*0.86, 0.006)) for u, v in rr]
    bk = [bm.verts.new((u*1.0, v*1.0, -0.008)) for u, v in rr]
    Nr = len(rr)
    for i in range(Nr):
        j = (i+1) % Nr
        bm.faces.new((fr_o[i], fr_o[j], fr_i[j], fr_i[i])); bm.faces.new((bk[i], bk[j], fr_o[j], fr_o[i]))
    bm.faces.new(bk[::-1])
    transform_bm(bm, Mm); obj('Mirror_Centre_Frame', bm, ['M_BlackGloss'])
    bm = bmesh.new(); gl = [bm.verts.new((u*0.93, v*0.86, 0.0045)) for u, v in rr]; bm.faces.new(gl)
    transform_bm(bm, Mm); obj('Mirror_Centre_Glass', bm, ['M_Mirror'], smooth=False)
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
        transform_bm(bm, M); obj('Mirror_Back_'+tag, bm, ['M_PaintNavy'])
        bm = lathe([(0.034, 0.002), (0.039, 0.004), (0.041, 0.008), (0.040, 0.011), (0.036, 0.010)], segs=40, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Mirror_Rim_'+tag, bm, ['M_Chrome'])
        bm = lathe([(0.0, 0.0085), (0.035, 0.0085)], segs=40, axis='Z', mat_idx=0)
        transform_bm(bm, M); obj('Mirror_Glass_'+tag, bm, ['M_Mirror'])
    # dashboard panel (black crackle) = the cockpit front wall, following the scuttle's inner contour
    ys = np.linspace(-0.445, 0.445, 41)
    def wall_x(yv, zv):
        h = surf.raycast([2.05, yv, zv], [-1, 0, 0], tmax=0.6)
        return None if (h is None or h[0] < 1.60) else h[0]
    ztop = []
    for yv in ys:
        zt = 0.70
        for zv in np.arange(0.70, 1.12, 0.005):
            if wall_x(yv, zv) is None: break
            zt = zv
        ztop.append(zt - 0.012)
    DASH = dict(ys=ys, ztop=np.array(ztop))
    bm = bmesh.new(); grid = []
    nz = 14
    for j in range(nz + 1):
        row = []
        for yv, zt in zip(ys, ztop):
            zv = 0.66 + (zt - 0.66)*j/nz
            wx = wall_x(yv, zv)
            wx = (wx if wx is not None else 1.705) + 0.004
            row.append(bm.verts.new(BLV([wx, yv, zv])))
        grid.append(row)
    for j in range(nz):
        for i in range(len(ys) - 1):
            bm.faces.new((grid[j][i], grid[j][i+1], grid[j+1][i+1], grid[j+1][i]))
    o = obj('Dashboard', bm, ['M_Crackle'])
    sd = o.modifiers.new('solid', 'SOLIDIFY'); sd.thickness = 0.004; sd.offset = 1.0
    def dash_x(yv, zv):
        wx = wall_x(yv, zv)
        return (wx if wx is not None else 1.705) + 0.004
    # gauges: (y, z, radius, atlas tile)  -- tile 0 tach, 1 water, 2 oil, 3 amps, 4 fuel, 5 clock, 6 switch panel
    gauges = [(-0.215, 0.865, 0.064, 0), (-0.075, 0.905, 0.026, 1), (-0.075, 0.845, 0.026, 2), (-0.020, 0.915, 0.024, 3),
              (-0.020, 0.860, 0.024, 4), (-0.022, 0.805, 0.024, 5), (0.095, 0.860, 0.040, 6)]
    bmr = bmesh.new(); bmg = bmesh.new()
    face_objs = []
    for gi, (yy, zz, r, tile) in enumerate(gauges):
        xx = dash_x(yy, zz) + 0.0012
        M = look_matrix(BLV([xx, yy, zz]), tuple(surf.dir_to_bl([1, 0.0, 0.0])), xhint=tuple(surf.dir_to_bl([0, -1, 0])))
        b = lathe([(r*0.86, 0.004), (r, 0.006), (r*1.08, 0.004), (r*1.1, 0.0)], segs=48, axis='Z', mat_idx=0); transform_bm(b, M)
        merge_into(bmr, b)
        b = lathe([(0.0, 0.0072), (r*0.86, 0.0072)], segs=48, axis='Z', mat_idx=0); transform_bm(b, M)
        merge_into(bmg, b)
        # face disc with UVs into the atlas (4x2 tiles)
        fb = bmesh.new(); uvl = fb.loops.layers.uv.new('UVMap')
        n = 48; cen = fb.verts.new((0, 0, 0.002)); ring = [fb.verts.new((r*0.86*math.cos(2*math.pi*k/n), r*0.86*math.sin(2*math.pi*k/n), 0.002)) for k in range(n)]
        tu, tv = tile % 4, tile // 4
        for k in range(n):
            f = fb.faces.new((cen, ring[k], ring[(k+1) % n]))
            for loop in f.loops:
                lx, ly = loop.vert.co.x/(r*0.86), loop.vert.co.y/(r*0.86)
                loop[uvl].uv = ((tu + 0.5 + 0.48*lx)/4.0, (tv + 0.5 + 0.48*ly)/2.0)
        transform_bm(fb, M)
        face_objs.append(obj('Gauge_Face_%d' % gi, fb, ['M_GaugeFace'], smooth=False))
    obj('Gauge_Bezels', bmr, ['M_Chrome']); obj('Gauge_Glass', bmg, ['M_Glass'], smooth=False)
    # a few toggle switches / knobs on the dash
    bmk = bmesh.new()
    for (yy, zz) in [(-0.33, 0.80), (-0.33, 0.93), (0.02, 0.96), (0.19, 0.93), (0.26, 0.80), (0.30, 0.90), (-0.12, 0.78), (0.14, 0.78)]:
        xx = dash_x(yy, zz) + 0.001
        M = look_matrix(BLV([xx, yy, zz]), tuple(surf.dir_to_bl([1, 0, 0])))
        b = lathe([(0.0, 0.022), (0.0045, 0.021), (0.005, 0.012), (0.009, 0.010), (0.010, 0.0)], segs=16, axis='Z', mat_idx=0); transform_bm(b, M)
        merge_into(bmk, b)
    obj('Dash_Knobs', bmk, ['M_Nickel'])
    # steering wheel (driver side y<0): wood rim with finger grips, 4 flat polished spokes ('+'), riveted boss
    c = np.array([1.936, -0.245, 0.911]); tilt = math.radians(18.0)
    nd = np.array([math.cos(tilt), 0.0, math.sin(tilt)])            # wheel axis toward the driver
    M = look_matrix(BLV(c), tuple(surf.dir_to_bl(nd)), xhint=tuple(surf.dir_to_bl([0, 1, 0])))
    Rw = 0.212; nring = 192
    ring = []
    for k in range(nring):
        a = 2*math.pi*k/nring
        grip = 0.0022*max(0.0, math.cos(a*36))**6                   # finger grips on the inner side
        r = Rw - grip
        ring.append(Vector((r*math.cos(a), r*math.sin(a), 0.0)))
    bm = tube_along(ring, 0.0135, segs=14, closed=True); transform_bm(bm, M); obj('SteeringWheel_Rim', bm, ['M_Wood'])
    bm = bmesh.new()
    for k in range(4):
        a = math.radians(90*k + 90)
        d = Vector((math.cos(a), math.sin(a), 0.0)); t = Vector((-math.sin(a), math.cos(a), 0.0))
        r0, r1, w0, w1 = 0.040, 0.206, 0.0095, 0.0060
        vs = [d*r0 - t*w0, d*r1 - t*w1, d*r1 + t*w1, d*r0 + t*w0]
        dish = lambda L: -0.032*(1 - min(1.0, max(0.0, (L - r0)/(r1 - r0))))      # spokes dished toward the boss
        v0 = [bm.verts.new(v + Vector((0, 0, dish(v.length) - 0.0035))) for v in vs]
        v1 = [bm.verts.new(v + Vector((0, 0, dish(v.length)))) for v in vs]
        bm.faces.new(v0[::-1]); bm.faces.new(v1)
        for i in range(4): bm.faces.new((v0[i], v0[(i+1)%4], v1[(i+1)%4], v1[i]))
    obj_sp = None
    b2 = lathe([(0.0, -0.030), (0.036, -0.030), (0.046, -0.034), (0.048, -0.040), (0.040, -0.046), (0.022, -0.050), (0.020, -0.075)], segs=40, axis='Z', mat_idx=0)
    merge_into(bm, b2)
    for k in range(8):                                               # boss rivets
        a = 2*math.pi*(k + 0.5)/8
        b3 = lathe([(0.0, -0.0275), (0.0022, -0.028), (0.0028, -0.0302)], segs=10, axis='Z', mat_idx=0)
        bmesh.ops.translate(b3, vec=Vector((0.030*math.cos(a), 0.030*math.sin(a), 0.0)), verts=b3.verts)
        merge_into(bm, b3)
    transform_bm(bm, M); o = obj('SteeringWheel_Spokes', bm, ['M_AluPolished'])
    bv = o.modifiers.new('bev', 'BEVEL'); bv.width = 0.0012; bv.segments = 2; bv.limit_method = 'ANGLE'
    # column (black) from the boss into the dashboard
    p_top = c - 0.075*nd; p_bot = c - 0.32*nd
    bm = bmesh.new(); cylinder(bm, BLV(p_top), BLV(p_bot), 0.019, segs=20)
    obj('SteeringColumn', bm, ['M_BlackGloss'])
    # bucket seats: curved padded shell backs + rounded cushions (black leather)
    for s, tag in ((-1, 'Driver'), (1, 'Passenger')):
        yc = s*0.235
        bm = bmesh.new()
        Rb, Hb, th = 0.235, 0.40, 0.065
        ang = np.radians(np.linspace(-80, 80, 17)); hs = np.linspace(0.0, 1.0, 9)
        axis_x = 2.13                                            # vertical axis in front of the backrest
        recline = math.radians(14)
        def pt(a, h, rr):
            lx = rr*math.cos(a); ly = rr*math.sin(a)
            zz = 0.40 + h*Hb*(1.0 - 0.10*(abs(a)/1.4)**2)
            xx = axis_x + lx + (zz - 0.40)*math.tan(recline)
            return BLV([xx, yc + ly*(1.0 + 0.10*h), zz])
        inner = [[bm.verts.new(pt(a, h, Rb)) for a in ang] for h in hs]
        outer = [[bm.verts.new(pt(a, h, Rb + th)) for a in ang] for h in hs]
        nA, nH = len(ang), len(hs)
        for j in range(nH-1):
            for i in range(nA-1):
                bm.faces.new((inner[j][i], inner[j+1][i], inner[j+1][i+1], inner[j][i+1]))
                bm.faces.new((outer[j][i], outer[j][i+1], outer[j+1][i+1], outer[j+1][i]))
        for i in range(nA-1):
            bm.faces.new((inner[-1][i], outer[-1][i], outer[-1][i+1], inner[-1][i+1]))
            bm.faces.new((inner[0][i], inner[0][i+1], outer[0][i+1], outer[0][i]))
        for j in range(nH-1):
            bm.faces.new((inner[j][0], outer[j][0], outer[j+1][0], inner[j+1][0]))
            bm.faces.new((inner[j][-1], inner[j+1][-1], outer[j+1][-1], outer[j][-1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        back = obj('Seat_Back_'+tag, bm, ['M_SeatLeather'])
        sub = back.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 3
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.40, 0.40, 0.085), verts=bm.verts)
        bmesh.ops.translate(bm, vec=BLV([2.15, yc, 0.40]), verts=bm.verts)
        cush = obj('Seat_Cushion_'+tag, bm, ['M_SeatLeather'])
        sub = cush.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 3
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

