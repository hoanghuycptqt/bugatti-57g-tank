"""Woven (crimped) wire-mesh geometry clipped to a 2D outline."""
import numpy as np, math
from mathutils import Vector
from geomkit import tube_along

def clip_intervals(poly, axis, c):
    """intervals along the other coordinate where the line coord[axis]=c lies inside poly"""
    P = np.asarray(poly, float); Q = np.roll(P, -1, 0)
    o = 1 - axis
    xs = []
    for p, q in zip(P, Q):
        a, b = p[axis], q[axis]
        if (a <= c < b) or (b <= c < a):
            t = (c - a) / (b - a)
            xs.append(p[o] + t*(q[o] - p[o]))
    xs.sort()
    return [(xs[k], xs[k+1]) for k in range(0, len(xs) - 1, 2)]

def build_wires(bm, poly, pitch, radius, map_fn, segs=5, crimp=True, spp=4, inset=0.0, mat=0, rot=0.0):
    """poly: (M,2) outline in param space.  map_fn(U, V) -> (P (N,3) blender coords, N (N,3) offset normal)
    rot: rotate the weave direction (radians) in param space."""
    poly = np.asarray(poly, float)
    c0 = poly.mean(0)
    cr, sr = math.cos(rot), math.sin(rot)
    R = np.array([[cr, -sr], [sr, cr]])
    pl = (poly - c0) @ R            # local (weave-aligned) coords
    umin, vmin = pl.min(0); umax, vmax = pl.max(0)
    A = radius*0.85 if crimp else 0.0
    nu = int((umax - umin)/pitch) + 1; nv = int((vmax - vmin)/pitch) + 1
    uo = umin - 0.5*((nu*pitch) - (umax - umin)); vo = vmin - 0.5*((nv*pitch) - (vmax - vmin))
    def to_param(lu, lv):
        L = np.stack([lu, lv], 1) @ R.T + c0
        return L[:, 0], L[:, 1]
    count = 0
    for fam in (0, 1):
        n_lines = nv if fam == 0 else nu
        for i in range(n_lines + 1):
            c = (vo if fam == 0 else uo) + (i + 0.5)*pitch
            for (a, b) in clip_intervals(pl, 1 if fam == 0 else 0, c):
                a += inset; b -= inset
                if b - a < pitch*0.3: continue
                ts = np.arange(a, b, pitch/spp); ts = np.append(ts, b)
                if fam == 0:
                    lu, lv = ts, np.full_like(ts, c)
                    ph = np.pi*((ts - uo)/pitch - 0.5) + np.pi*i
                    off = A*np.cos(ph)
                else:
                    lu, lv = np.full_like(ts, c), ts
                    ph = np.pi*((ts - vo)/pitch - 0.5) + np.pi*i
                    off = -A*np.cos(ph)
                U, V = to_param(lu, lv)
                P, N = map_fn(U, V)
                ok = np.all(np.isfinite(P), 1)
                P = P + N*off[:, None]
                P = P[ok]
                if len(P) < 2: continue
                tube_along([Vector(p) for p in P], radius, segs=segs, bm=bm, mat=mat)
                count += 1
    return count
