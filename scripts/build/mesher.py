import numpy as np, time
from skimage import measure
from body import build_parts, body_sdf

def eval_grid(parts, h, bounds, detail=True):
    (x0,x1),(y0,y1),(z0,z1) = bounds
    xs = np.arange(x0, x1+1e-9, h, dtype=np.float64)
    ys = np.arange(y0, y1+1e-9, h, dtype=np.float64)
    zs = np.arange(z0, z1+1e-9, h, dtype=np.float64)
    vol = np.empty((len(xs), len(ys), len(zs)), np.float32)
    Y, Z = np.meshgrid(ys, zs, indexing='ij')
    step = max(1, int(2e6 // (len(ys)*len(zs))))
    for i in range(0, len(xs), step):
        xx = xs[i:i+step]
        X = np.broadcast_to(xx[:,None,None], (len(xx),)+Y.shape)
        Yb = np.broadcast_to(Y[None], X.shape); Zb = np.broadcast_to(Z[None], X.shape)
        vol[i:i+step] = body_sdf(X, Yb, Zb, parts, detail).astype(np.float32)
    return xs, ys, zs, vol

def extract(parts, h=0.012, detail=True, full=False):
    bounds = ((-0.64, 4.22), (-0.86 if full else 0.0, 0.86), (0.18, 1.10))
    t = time.time()
    xs, ys, zs, vol = eval_grid(parts, h, bounds, detail)
    t1 = time.time()
    verts, faces, normals, _ = measure.marching_cubes(vol, 0.0, spacing=(h,h,h))
    verts += np.array([xs[0], ys[0], zs[0]])
    print('grid', vol.shape, 'eval %.1fs mc %.1fs' % (t1-t, time.time()-t1), 'verts', len(verts))
    return verts, faces, vol, (xs, ys, zs)

def mesh_normals(v, f):
    a = v[f[:,0]]; b = v[f[:,1]]; c = v[f[:,2]]
    fn = np.cross(b - a, c - a)
    vn = np.zeros_like(v)
    for k in range(3):
        np.add.at(vn, f[:,k], fn)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    return vn

def project(parts, v, f=None, iters=3, detail=True, h=0.012, tips=True):
    e = 1e-4
    v0 = v.copy()
    def grad(x, y, z):
        gx = (body_sdf(x+e, y, z, parts, detail) - body_sdf(x-e, y, z, parts, detail)) / (2*e)
        gy = (body_sdf(x, y+e, z, parts, detail) - body_sdf(x, y-e, z, parts, detail)) / (2*e)
        gz = (body_sdf(x, y, z+e, parts, detail) - body_sdf(x, y, z-e, parts, detail)) / (2*e)
        return gx, gy, gz
    for _ in range(iters):
        x, y, z = v[:,0], v[:,1], v[:,2]
        fv = body_sdf(x, y, z, parts, detail)
        gx, gy, gz = grad(x, y, z)
        g2 = gx*gx + gy*gy + gz*gz
        step = (fv / np.maximum(g2, 0.05))[:,None] * np.stack([gx, gy, gz], 1)
        step = np.nan_to_num(step)
        sl = np.linalg.norm(step, axis=1)
        step[sl > 0.5*h] *= (0.5*h / sl[sl > 0.5*h])[:,None]
        v = v - step
    bad_pos = np.linalg.norm(v - v0, axis=1) > 1.5*h
    v[bad_pos] = v0[bad_pos]
    gx, gy, gz = grad(v[:,0], v[:,1], v[:,2])
    n = np.stack([gx, gy, gz], 1)
    nn = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / (nn + 1e-12)
    if f is not None:
        mn = mesh_normals(v, f)
        dot = (n * mn).sum(1)
        bad = (~np.isfinite(dot)) | (dot < 0.5) | (nn[:,0] < 0.2) | (nn[:,0] > 5)
        n[bad] = mn[bad]
        # outlier suppression: compare with neighbour average
        nb = np.zeros_like(n); cnt = np.zeros(len(n))
        for i, j in ((0,1),(1,2),(2,0),(1,0),(2,1),(0,2)):
            np.add.at(nb, f[:,i], n[f[:,j]]); np.add.at(cnt, f[:,i], 1)
        nb /= np.linalg.norm(nb, axis=1, keepdims=True) + 1e-12
        out = (n * nb).sum(1) < 0.75
        n[out] = nb[out]
        TIPS = [(-0.565, 0.55, 0.45), (-0.565, -0.55, 0.45), (4.18, 0.0, 0.36)]
        TIPS = TIPS if tips else []
        for tx, ty, tz in TIPS:
            near = np.linalg.norm(v - np.array([tx, ty, tz]), axis=1) < 0.06
            n[near] = mn[near]
        print('normals fixed:', bad.sum(), 'outliers:', out.sum(), ' positions kept:', bad_pos.sum())
    return v, n

if __name__ == '__main__':
    import sys
    h = float(sys.argv[1]) if len(sys.argv) > 1 else 0.012
    parts = build_parts()
    v, f, vol, grid = extract(parts, h)
    v, n = project(parts, v, f, h=h)
    np.savez_compressed('/home/claude/tank/build/body_half.npz', v=v.astype(np.float32), f=f.astype(np.int32), n=n.astype(np.float32))
    print('saved', v.shape, f.shape)
