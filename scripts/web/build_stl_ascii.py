"""Compact ASCII STL (~2.5 MB) for GitHub's in-repo 3D preview. GitHub shows text STL files reliably even on
slow links, because the file content comes with the page; binary files are fetched separately and can time out.
Units: millimetres (integers), Z up."""
import bpy, sys, numpy as np, os
sys.path.insert(0, '/home/claude/tank/build')
import preview as PV
import fast_simplification as fs
OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '/home/claude/tank/build/web/57G_Tank_preview.stl'
bpy.ops.wm.open_mainfile(filepath='/home/claude/tank/build/web/glb_scene.blend')
SKIP_KEYS = ('Grille_Mesh', 'PodVents_Mesh', 'Intake_Mesh', 'Headlamp_Guard_', 'RearVents_Mesh', 'Body', 'Lettering',
             'Rivets', 'Spokes', 'Screw', 'Bolt', 'Gauge_', 'Dash_Knobs', 'Hinge', 'Buckle', 'Latch', 'Bulb', 'Refl',
             'Chassis_Axles', 'Exhaust_Hangers', 'Exhaust_Downpipe', 'Cockpit_Floor', 'FuelFiller_Tab', 'FuelFiller_Neck', 'Mirror_Glass',
             'Mirror_Centre_Glass', 'TailLamp_SmallLens', 'Intake_Back', 'Radiator_Fins', 'Grille_Core', 'GearLever', 'SteeringColumn')
TARGET = {'_Drum': 70, '_Hub': 40, '_KnockOff': 40, 'Seat_Back': 90, 'SteeringWheel_Rim': 140,
          'SideLamp_Pod': 120, 'Gauge_Bezels': 40, 'TailLamp_Bodies': 100, 'Dashboard': 80}
GENERIC = 0.12
dg = bpy.context.evaluated_depsgraph_get()
COUNT = []
V, F, off = [], [], 0
def add(co, tri):
    global off
    V.append(co.astype(np.float64)); F.append(tri.astype(np.int64) + off); off += len(co)
BODY_T = int(os.environ.get('BODY_T', '7600'))
b = np.load('/home/claude/tank/build/web/body_stl_ascii.npz')
bv, bf = b['v'].astype(np.float32), b['f'].astype(np.int32)
if len(bf) > BODY_T:
    bv, bf = fs.simplify(bv, bf, target_reduction=1 - BODY_T/len(bf), agg=2)
add(PV.to_bl(np.asarray(bv, np.float64)), np.asarray(bf)[:, ::-1].astype(np.int64))
nb = len(bf)
def lathe(co, nseg, nbins, ring=False):
    c = co.mean(0); X = co - c
    w, U = np.linalg.eigh(X.T @ X); ax = U[:, 0]                  # smallest spread = wheel axis
    a = X @ ax; R = np.linalg.norm(X - np.outer(a, ax), axis=1)
    e1 = np.cross(ax, [0, 0, 1.0]); e1 = e1/np.linalg.norm(e1) if np.linalg.norm(e1) > 1e-6 else np.cross(ax, [1.0, 0, 0]); e2 = np.cross(ax, e1)
    rin = R.min()
    if ring:
        prof = [(a.min(), rin), (a.min(), R.max()), (a.max(), R.max()), (a.max(), rin)]
    else:
        edges = np.linspace(a.min(), a.max(), nbins + 1)
        outer = []
        for i in range(nbins):
            m = (a >= edges[i]) & (a <= edges[i+1])
            outer.append((0.5*(edges[i] + edges[i+1]), R[m].max() if m.any() else R.max()))
        prof = [(a.min(), rin), (a.min(), 0.5*(rin + outer[0][1]))] + outer + [(a.max(), 0.5*(rin + outer[-1][1])), (a.max(), rin)]
    P = len(prof); th = np.linspace(0, 2*np.pi, nseg, endpoint=False)
    verts = np.array([c + pa*ax + pr*(np.cos(t)*e1 + np.sin(t)*e2) for t in th for (pa, pr) in prof])
    tris = []
    for i in range(nseg):
        for j in range(P):
            v00 = i*P + j; v01 = i*P + (j+1) % P; v10 = ((i+1) % nseg)*P + j; v11 = ((i+1) % nseg)*P + (j+1) % P
            tris += [(v00, v10, v11), (v00, v11, v01)]
    return verts, np.array(tris)
for o in bpy.data.objects:
    if o.type != 'MESH' or any(k in o.name for k in SKIP_KEYS): continue
    oe = o.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles()
    co = np.empty(len(me.vertices)*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    tri = np.empty(len(me.loop_triangles)*3, np.int32); me.loop_triangles.foreach_get('vertices', tri); tri = tri.reshape(-1, 3)
    M = np.array(o.matrix_world, dtype=np.float64); co = co @ M[:3, :3].T + M[:3, 3]
    oe.to_mesh_clear()
    if o.name.endswith('_Tire'):
        lv, lt = lathe(co, 26, 5); add(lv, lt); COUNT.append((len(lt), o.name)); continue
    if o.name.endswith('_Rim'):
        lv, lt = lathe(co, 26, 0, ring=True); add(lv, lt); COUNT.append((len(lt), o.name)); continue
    tgt = next((t for k, t in TARGET.items() if k in o.name), None)
    if tgt is None and len(tri) > 120: tgt = max(40, int(GENERIC*len(tri)))
    if tgt and len(tri) > tgt:
        co, tri = fs.simplify(co.astype(np.float32), tri.astype(np.int32), target_reduction=1 - tgt/len(tri), agg=4)
    add(np.asarray(co, np.float64), np.asarray(tri)); COUNT.append((len(tri), o.name))
Vt = np.concatenate(V)*1000.0; Ft = np.concatenate(F)
Vq = np.round(Vt).astype(np.int64)                       # 1 mm grid
a, bq, c = Vq[Ft[:, 0]], Vq[Ft[:, 1]], Vq[Ft[:, 2]]
n = np.cross((bq - a).astype(float), (c - a).astype(float)); nl = np.linalg.norm(n, axis=1)
ok = nl > 1e-9
a, bq, c, n = a[ok], bq[ok], c[ok], n[ok]/nl[ok, None]
def fmt_n(x):
    s = '%.2f' % x
    s = s.rstrip('0').rstrip('.') if '.' in s else s
    return '0' if s in ('-0', '') else s
lines = ['solid bugatti_57g_tank']
for i in range(len(a)):
    lines.append('facet normal %s %s %s\nouter loop\nvertex %d %d %d\nvertex %d %d %d\nvertex %d %d %d\nendloop\nendfacet' % (
        fmt_n(n[i, 0]), fmt_n(n[i, 1]), fmt_n(n[i, 2]), *a[i], *bq[i], *c[i]))
lines.append('endsolid bugatti_57g_tank\n')
open(OUT, 'w').write('\n'.join(lines))
COUNT.sort(reverse=True); print('top parts', COUNT[:14], 'parts total', sum(c for c, _ in COUNT))
print('ASCII STL facets', len(a), '(body %d)' % nb, 'size %.2f MB' % (os.path.getsize(OUT)/1e6))
