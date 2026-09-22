import numpy as np
from body import build_parts, body_sdf
_P = build_parts()
OFF = 1.49
def sdf(p):
    p = np.atleast_2d(np.asarray(p, float))
    return body_sdf(p[:,0], p[:,1], p[:,2], _P)
def normal(p, e=1e-4):
    p = np.atleast_2d(np.asarray(p, float))
    g = []
    for k in range(3):
        d = np.zeros(3); d[k] = e
        g.append((sdf(p + d) - sdf(p - d)) / (2*e))
    g = np.stack(g, 1)
    return g / (np.linalg.norm(g, axis=1, keepdims=True) + 1e-12)
def raycast(p0, d, tmax=2.0, n=4000):
    """first surface hit along ray from p0 (outside) direction d"""
    p0 = np.asarray(p0, float); d = np.asarray(d, float); d = d/np.linalg.norm(d)
    ts = np.linspace(0, tmax, n)
    pts = p0[None] + ts[:,None]*d[None]
    f = sdf(pts)
    idx = np.where((f[:-1] > 0) & (f[1:] <= 0))[0]
    if len(idx) == 0: return None
    i = idx[0]; a, b = ts[i], ts[i+1]
    for _ in range(40):
        m = 0.5*(a+b)
        if sdf(p0 + m*d)[0] > 0: a = m
        else: b = m
    return p0 + 0.5*(a+b)*d
def project(p):
    p = np.asarray(p, float)
    for _ in range(6):
        f = sdf(p)[0]; n = normal(p)[0]
        p = p - f*n
    return p
def to_bl(p):
    p = np.asarray(p, float)
    if p.ndim == 1: return np.array([p[1], p[0]-OFF, p[2]])
    return np.stack([p[:,1], p[:,0]-OFF, p[:,2]], 1)
def dir_to_bl(d):
    d = np.asarray(d, float)
    if d.ndim == 1: return np.array([d[1], d[0], d[2]])
    return np.stack([d[:,1], d[:,0], d[:,2]], 1)

def sdf_nd(p):
    """smooth body without pockets / cut-outs details"""
    p = np.atleast_2d(np.asarray(p, float))
    return body_sdf(p[:,0], p[:,1], p[:,2], _P, False)

def raycast_many(P0, d, tmax=1.2, step=0.004, detail=False):
    """vectorised first-hit along common direction d for many origins; returns (N,3) (nan if miss)"""
    P0 = np.atleast_2d(np.asarray(P0, float)); d = np.asarray(d, float); d = d/np.linalg.norm(d)
    f = sdf if detail else sdf_nd
    ts = np.arange(0.0, tmax + step, step)
    N = len(P0)
    vals = np.empty((N, len(ts)))
    for j, t in enumerate(ts):
        vals[:, j] = f(P0 + t*d)
    hit = (vals[:, :-1] > 0) & (vals[:, 1:] <= 0)
    has = hit.any(1)
    j0 = np.argmax(hit, 1)
    a = ts[j0].copy(); b = ts[np.minimum(j0 + 1, len(ts)-1)].copy()
    for _ in range(30):
        m = 0.5*(a + b)
        fm = f(P0 + m[:, None]*d)
        a = np.where(fm > 0, m, a); b = np.where(fm > 0, b, m)
    out = P0 + (0.5*(a + b))[:, None]*d
    out[~has] = np.nan
    return out

def normal_nd(p, e=1e-4):
    p = np.atleast_2d(np.asarray(p, float))
    g = []
    for k in range(3):
        dd = np.zeros(3); dd[k] = e
        g.append((sdf_nd(p + dd) - sdf_nd(p - dd)) / (2*e))
    g = np.stack(g, 1)
    return g / (np.linalg.norm(g, axis=1, keepdims=True) + 1e-12)
