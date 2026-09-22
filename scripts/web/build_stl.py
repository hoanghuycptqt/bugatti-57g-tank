"""Binary STL (< 10 MB) for GitHub's built-in 3D viewer: decimated body + decimated main parts."""
import bpy, sys, numpy as np, os
sys.path.insert(0, '/home/claude/tank/build')
import preview as PV
import fast_simplification as fs
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT = args[0] if args else '/home/claude/tank/build/web/57G_Tank.stl'
BODY_NPZ = args[1] if len(args) > 1 else '/home/claude/tank/build/web/body_stl.npz'
MODE = args[2] if len(args) > 2 else 'hd'
LITE = MODE in ('lite', 'tiny')                  # lighter versions for GitHub's viewer
BUDGET = 185000
bpy.ops.wm.open_mainfile(filepath='/home/claude/tank/build/web/glb_scene.blend')
SKIP = ('Grille_Mesh', 'PodVents_Mesh', 'Intake_Mesh', 'Headlamp_Guard_R', 'Headlamp_Guard_L', 'RearVents_Mesh',
        'Body', 'Lettering_Drivers', 'Hood_Rivets_Louvers', 'PodVents_Rivets')
TARGET = {'_Tire': 2500, 'Seat_Back': 2200, '_Rim': 1800, 'SteeringWheel_Rim': 2200, '_Drum': 1200, 'SideLamp_Pod': 2000, 'SteeringWheel_Spokes': 1800}
BODY_T = 90000
GENERIC = 0.5
if LITE:
    TARGET = {'_Tire': 900, 'Seat_Back': 800, '_Rim': 700, 'SteeringWheel_Rim': 800, '_Drum': 500, 'SideLamp_Pod': 800, 'SteeringWheel_Spokes': 700}
    BODY_T = 45000
if MODE == 'tiny':
    TARGET = {'_Tire': 500, 'Seat_Back': 400, '_Rim': 400, 'SteeringWheel_Rim': 400, '_Drum': 250, 'SideLamp_Pod': 400, 'SteeringWheel_Spokes': 300, '_Spokes': 1100}
    GENERIC = 0.3
    BODY_T = 26000
dg = bpy.context.evaluated_depsgraph_get()
parts = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name in SKIP: continue
    oe = o.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles()
    co = np.empty(len(me.vertices)*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    tri = np.empty(len(me.loop_triangles)*3, np.int32); me.loop_triangles.foreach_get('vertices', tri); tri = tri.reshape(-1, 3)
    M = np.array(o.matrix_world, dtype=np.float64)
    co = (co @ M[:3, :3].T + M[:3, 3]).astype(np.float32)
    parts.append((o.name, co, tri)); oe.to_mesh_clear()
b = np.load(BODY_NPZ)
bv = PV.to_bl(b['v'].astype(np.float64)).astype(np.float32); bf = b['f'][:, ::-1].astype(np.int32)
if len(bf) > 1.1*BODY_T: bv, bf = fs.simplify(bv, bf, target_reduction=1 - BODY_T/len(bf), agg=6)
small = sum(len(t) for _, _, t in parts if len(t) <= 2500)
big = sum(len(t) for _, _, t in parts if len(t) > 2500)
keep_ratio = min(1.0, (BUDGET - len(bf) - small) / max(big, 1))
print('parts', len(parts), 'small tris', small, 'big tris', big, 'keep ratio %.3f' % keep_ratio)
V, F, off = [bv], [bf], len(bv)
for name, co, tri in parts:
    tgt = next((t for k, t in TARGET.items() if k in name), None)
    if tgt is None and LITE and len(tri) > 400:
        tgt = max(150, int(GENERIC*len(tri)))
    if tgt and len(tri) > tgt:
        co, tri = fs.simplify(co, tri, target_reduction=1 - tgt/len(tri), agg=5)
    V.append(co.astype(np.float32)); F.append(tri.astype(np.int64) + off); off += len(co)
V = np.concatenate(V); F = np.concatenate(F)
V = V - np.array([0, 0, 0], np.float32)
a, bb, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
n = np.cross(bb - a, c - a); nl = np.linalg.norm(n, axis=1, keepdims=True); ok = nl[:, 0] > 1e-14
n = n / np.maximum(nl, 1e-20)
a, bb, c, n = a[ok], bb[ok], c[ok], n[ok]
rec = np.zeros(len(a), dtype=np.dtype([('n', '<f4', 3), ('a', '<f4', 3), ('b', '<f4', 3), ('c', '<f4', 3), ('attr', '<u2')]))
rec['n'], rec['a'], rec['b'], rec['c'] = n, a, bb, c
with open(OUT, 'wb') as fh:
    hdr = b'Bugatti Type 57G Tank (1937) - procedural model, units: metres, Z up'
    fh.write(hdr.ljust(80, b' ')); fh.write(np.uint32(len(rec)).tobytes()); fh.write(rec.tobytes())
print('STL tris', len(rec), 'size %.2f MB' % (os.path.getsize(OUT)/1e6))
print('bbox', V.min(0), V.max(0))
