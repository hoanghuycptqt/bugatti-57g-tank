"""Prepare lighter meshes for web viewing: decimated body with baked paint colours (GLB) and a <10 MB STL."""
import numpy as np, sys, time, os
sys.path.insert(0, '/home/claude/tank/build')
import fast_simplification as fs
from body import build_parts
import attributes
t0 = time.time()
D = '/home/claude/tank/build/body_5mm/'
vn = np.load(D + 'body_vn.npz'); v = vn['v'].astype(np.float64)
f = np.concatenate([np.load(D + 'body_f0.npz')['f'], np.load(D + 'body_f1.npz')['f']]).astype(np.int64)
parts = build_parts()
def srgb2lin(c):
    c = np.asarray(c, float)/255.0
    return np.where(c <= 0.04045, c/12.92, ((c + 0.055)/1.055)**2.4)
LIGHT = srgb2lin((126, 164, 204)); NAVY = srgb2lin((30, 45, 92)); DARK = np.array([0.008, 0.008, 0.009])
def vertex_normals(v, f):
    fn = np.cross(v[f[:,1]] - v[f[:,0]], v[f[:,2]] - v[f[:,0]])
    n = np.zeros_like(v)
    for k in range(3): np.add.at(n, f[:,k], fn)
    return n/(np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
def colours(v, f):
    A = attributes.compute(v, parts)
    t = np.clip(0.5 - A['navy']/0.0024, 0, 1)[:, None]
    col = LIGHT*(1 - t) + NAVY*t
    n = vertex_normals(v, f)
    under = ((n[:,2] < -0.45) & (v[:,2] < 0.30)).astype(float)
    hole = np.clip((0.0022 - A['hole'])/0.0017, 0, 1)
    dark = np.maximum.reduce([hole, A['well'].astype(float), under])[:, None]
    return col*(1 - dark) + DARK*dark
out = {}
for tag, target in (('glb', 420000), ('stl', 112000)):
    red = 1.0 - target/len(f)
    vd, fd = fs.simplify(v.astype(np.float32), f.astype(np.int32), target_reduction=red, agg=6)
    vd = vd.astype(np.float64); fd = fd.astype(np.int64)
    out[tag] = (vd, fd)
    print(tag, 'tris', len(fd), 'verts', len(vd), '%.1fs' % (time.time() - t0))
vg, fg = out['glb']
cg = colours(vg, fg)
np.savez_compressed('/home/claude/tank/build/web/body_glb.npz', v=vg.astype(np.float32), f=fg.astype(np.int32), c=cg.astype(np.float16))
np.savez_compressed('/home/claude/tank/build/web/body_stl.npz', v=out['stl'][0].astype(np.float32), f=out['stl'][1].astype(np.int32))
print('done %.1fs' % (time.time() - t0))
