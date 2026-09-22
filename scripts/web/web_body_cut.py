"""Web body: decimated mesh cut exactly along the paint boundaries, so the two-tone split,
panel gaps and dark recesses are real geometry edges with three plain materials (no textures)."""
import numpy as np, sys, time
sys.path.insert(0, '/home/claude/tank/build')
from body import build_parts, WHEEL_FC, WHEEL_RC
from mesher import project, mesh_normals
from sdf import ellcyl_y
import attributes
t0 = time.time()
parts = build_parts()
d = np.load('/home/claude/tank/build/web/body_glb.npz')
v = d['v'].astype(np.float64); f = d['f'].astype(np.int64)
v, n = project(parts, v, f, iters=3, h=0.008)
A = attributes.compute(v, parts)
x, y, z = v[:, 0], v[:, 1], v[:, 2]; ay = np.abs(y)
wf = ellcyl_y(x, z, WHEEL_FC[0], WHEEL_FC[1], 0.445, 0.452)
wr = ellcyl_y(x, z, WHEEL_RC[0], WHEEL_RC[1], 0.48, 0.445)
F = {k: A[k].astype(np.float64) for k in ('navy', 'g_seam', 'g_door', 'g_hood', 'g_nose', 'hole')}
F['well'] = np.maximum.reduce([np.minimum(wf, wr) - 0.004, 0.46 - ay, ay - 0.79, z - 0.86])
F['under'] = np.maximum(n[:, 2] + 0.55, z - 0.275)
F['nx'], F['ny'], F['nz'] = n[:, 0].copy(), n[:, 1].copy(), n[:, 2].copy()
print('fields ready %.1fs' % (time.time() - t0), len(v), len(f))

def cut(v, f, F, key, c):
    phi = F[key] - c
    s = phi > 0
    sf = s[f]; cnt = sf.sum(1)
    mixed = (cnt == 1) | (cnt == 2)
    if not mixed.any():
        return v, f, F, 0
    fm = f[mixed]; sm = sf[mixed]; cm = cnt[mixed]
    odd = np.where(cm[:, None] == 1, sm, ~sm)          # the vertex alone on its side
    k = np.argmax(odd, 1)
    idx = (np.arange(3)[None, :] + k[:, None]) % 3       # cyclic rotation keeps winding
    r = np.take_along_axis(fm, idx, 1)
    a, b, cc = r[:, 0], r[:, 1], r[:, 2]
    E = np.concatenate([np.stack([a, b], 1), np.stack([a, cc], 1)])
    E.sort(1)
    ue, inv = np.unique(E, axis=0, return_inverse=True)
    inv = inv.ravel()
    i, j = ue[:, 0], ue[:, 1]
    t = phi[i]/(phi[i] - phi[j]); t = np.clip(t, 0.004, 0.996)
    nv = v[i] + t[:, None]*(v[j] - v[i])
    base = len(v)
    v = np.concatenate([v, nv])
    for kk in F:
        F[kk] = np.concatenate([F[kk], F[kk][i] + t*(F[kk][j] - F[kk][i])])
    m = len(fm)
    pab = base + inv[:m]; pac = base + inv[m:]
    newf = np.concatenate([np.stack([a, pab, pac], 1), np.stack([pab, b, cc], 1), np.stack([pab, cc, pac], 1)])
    f = np.concatenate([f[~mixed], newf])
    return v, f, F, m

GW = 0.0013      # half width of a panel gap line
cuts = [('navy', 0.0), ('hole', 0.00135), ('well', 0.0), ('under', 0.0)]
for g in ('g_seam', 'g_door', 'g_hood', 'g_nose'):
    cuts += [(g, GW), (g, -GW)]
for key, c in cuts:
    v, f, F, m = cut(v, f, F, key, c)
    print('cut %-7s %+.4f  split %6d  -> tris %d' % (key, c, m, len(f)))
# classify by centroid
C = {k: F[k][f].mean(1) for k in F}
gap = np.zeros(len(f), bool)
for g in ('g_seam', 'g_door', 'g_hood', 'g_nose'):
    gap |= np.abs(C[g]) < GW
dark = gap | (C['hole'] < 0.00135) | (C['well'] < 0) | (C['under'] < 0)
mat = np.where(dark, 2, np.where(C['navy'] < 0, 1, 0)).astype(np.uint8)
# normals: analytic for the new vertices, interpolated fallback
nI = np.stack([F['nx'], F['ny'], F['nz']], 1); nI /= np.linalg.norm(nI, axis=1, keepdims=True) + 1e-12
n0 = len(d['v'])
if len(v) > n0:
    _, nA = project(parts, v[n0:].copy(), None, iters=0, h=0.008)
    ok = (nA*nI[n0:]).sum(1) > 0.8
    nI[n0:][ok] = nA[ok]
    nn = nI[n0:]; nn[ok] = nA[ok]; nI[n0:] = nn
# drop degenerate triangles
ar = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
keep = ar > 1e-12
f, mat = f[keep], mat[keep]
print('materials light/navy/dark:', np.bincount(mat, minlength=3), 'verts', len(v), 'tris', len(f))
np.savez_compressed('/home/claude/tank/build/web/body_cut.npz', v=v.astype(np.float32), f=f.astype(np.int32),
                    m=mat, n=nI.astype(np.float32))
print('saved %.1fs' % (time.time() - t0))
