import numpy as np
from sdf import smin, smax
from shapes2d import sd_polygon, catmull, rounded_rect

# nose plane: through (-0.43, 0.30) normal n=(-0.950, 0.311) (outward), up t=(0.311, 0.950)
NP0 = np.array([-0.43, 0.30]); NN = np.array([-0.950, 0.311]); NT = np.array([0.311, 0.950])
def nose_uvw(x, y, z):
    dx, dz = x - NP0[0], z - NP0[1]
    w = NN[0]*dx + NN[1]*dz
    v = NT[0]*dx + NT[1]*dz
    return y, v, w
def z_to_v(z):  # on the plane, v for given z
    return (z - NP0[1]) / NT[1]

GRILLE_UZ = [(0.0, 0.846), (0.075, 0.840), (0.122, 0.821), (0.148, 0.785), (0.157, 0.715), (0.156, 0.62),
             (0.149, 0.535), (0.133, 0.483), (0.095, 0.462), (0.0, 0.457)]
def grille_outline_uv(n=10):
    half = GRILLE_UZ
    pts = [(u, z) for u, z in half] + [(-u, z) for u, z in reversed(half[1:-1])]
    c = catmull(pts, n=n, closed=True)
    return np.stack([c[:,0], z_to_v(c[:,1])], 1)

INTAKE = dict(u=0.255, z0=0.292, z1=0.398, r=0.045)
def intake_outline_uv():
    zc = 0.5*(INTAKE['z0'] + INTAKE['z1']); hh = 0.5*(INTAKE['z1'] - INTAKE['z0'])
    rr = rounded_rect(0.0, zc, INTAKE['u'], hh, INTAKE['r'], n=10)
    return np.stack([rr[:,0], z_to_v(rr[:,1])], 1)

import vents as _V
HEAD = dict(y=0.462, z=0.372, r=0.097, x_front=-0.62, x_back=-0.505)
# per-segment surface x (min,max) sampled from the smooth body (no pockets)
FV_SURF = [(-0.4918, -0.4429), (-0.5317, -0.5005), (-0.5601, -0.5357), (-0.5647, -0.5543)]
RV_SURF = [(3.6483, 3.7145), (3.7204, 3.7704), (3.7827, 3.8282), (3.8409, 3.8994)]
FV_POLYS = _V.front_polys(); FV_IN = _V.front_polys(inset=_V.FV['r'])
RV_POLYS = _V.rear_polys(); RV_IN = _V.rear_polys(inset=_V.RV['r'])
SIDE_RECESS = dict(xc=1.529, zc=0.763, A=0.197, B=0.103, depth=0.018)
SPARE = dict(c=np.array([3.50, 0.0, 0.655]), tilt=np.radians(24.0), R=0.418, h=0.13, ext=0.055)
SLOT = dict(p0=(1.223, 0.480), p1=(1.312, 0.743), w=0.052, depth=0.012)

def _box(x, y, z, lo, hi):
    ay = np.abs(y)
    return (x >= lo[0]) & (x <= hi[0]) & (ay >= lo[1]) & (ay <= hi[1]) & (z >= lo[2]) & (z <= hi[2])

_GRILLE_UV = None
_INTAKE_UV = None
def pockets_sdf(x, y, z, comps=False):
    global _GRILLE_UV, _INTAKE_UV
    if _GRILLE_UV is None:
        _GRILLE_UV = grille_outline_uv(); _INTAKE_UV = intake_outline_uv()
    x = np.asarray(x, float); y = np.asarray(y, float); z = np.asarray(z, float)
    shp = np.broadcast(x, y, z).shape
    x = np.broadcast_to(x, shp); y = np.broadcast_to(y, shp); z = np.broadcast_to(z, shp)
    ay = np.abs(y)
    P = np.full(shp, 10.0)
    C = {}
    def put(mask, fn, tag=None):
        if np.any(mask):
            idx = np.nonzero(mask)
            val = fn(x[idx], y[idx], ay[idx], z[idx])
            P[idx] = np.minimum(P[idx], val)
            if comps and tag is not None:
                if tag not in C: C[tag] = np.full(shp, 10.0)
                C[tag][idx] = np.minimum(C[tag][idx], val)
    # grille
    def f_grille(x, y, ay, z):
        u, v, w = nose_uvw(x, y, z)
        return np.maximum(sd_polygon(u, v, _GRILLE_UV), -w - 0.030)
    put(_box(x, y, z, (-0.62, 0.0, 0.40), (-0.05, 0.20, 0.90)), f_grille, 'grille')
    def f_intake(x, y, ay, z):
        u, v, w = nose_uvw(x, y, z)
        return np.maximum(sd_polygon(u, v, _INTAKE_UV), -w - 0.055)
    put(_box(x, y, z, (-0.62, 0.0, 0.20), (-0.25, 0.30, 0.45)), f_intake, 'intake')
    def f_head(x, y, ay, z):
        rad = np.sqrt((ay - HEAD['y'])**2 + (z - HEAD['z'])**2) - HEAD['r']
        return np.maximum(rad, np.maximum(HEAD['x_front'] - x, x - HEAD['x_back']))
    put(_box(x, y, z, (-0.66, 0.33, 0.24), (-0.45, 0.59, 0.50)), f_head, 'head')
    for poly, pin, (xs0, xs1) in zip(FV_POLYS, FV_IN, FV_SURF):
        xf = xs1 + 0.015
        lo = (-0.70, poly[:,0].min()-0.02, poly[:,1].min()-0.02); hi = (xf + 0.03, poly[:,0].max()+0.02, poly[:,1].max()+0.02)
        def f_vent(x, y, ay, z, pin=pin, xf=xf):
            return np.maximum(sd_polygon(ay, z, pin) - _V.FV['r'], np.maximum(-0.70 - x, x - xf))
        put(_box(x, y, z, lo, hi), f_vent, 'fvent')
    for poly, pin, (xs0, xs1) in zip(RV_POLYS, RV_IN, RV_SURF):
        xf = xs0 - 0.015
        lo = (xf - 0.03, poly[:,0].min()-0.02, poly[:,1].min()-0.02); hi = (4.10, poly[:,0].max()+0.02, poly[:,1].max()+0.02)
        def f_rvent(x, y, ay, z, pin=pin, xf=xf):
            return np.maximum(sd_polygon(ay, z, pin) - _V.RV['r'], np.maximum(xf - x, x - 4.10))
        put(_box(x, y, z, lo, hi), f_rvent, 'rvent')
    def f_spare(x, y, ay, z):
        # recess around the tilted spare wheel: elliptic in the wheel plane, extended rearward (e)
        t = SPARE['tilt']; axx, axz = np.sin(t), np.cos(t)
        e = SPARE['ext']
        cx = SPARE['c'][0] + e*np.cos(t); cz = SPARE['c'][2] - e*np.sin(t)
        dx, dy, dz = x - cx, y - SPARE['c'][1], z - cz
        al = dx*axx + dz*axz
        pu = dx*np.cos(t) - dz*np.sin(t)
        a_u, a_v = SPARE['R'] + e, SPARE['R']
        u = pu/a_u; v = dy/a_v
        rr = np.sqrt(u*u + v*v) + 1e-9
        rad = np.sqrt(pu*pu + dy*dy) + 1e-9
        d_ell = rad*(1.0 - 1.0/rr)
        return np.maximum(d_ell, np.maximum(-al - SPARE['h']*0.5, al - 0.40))
    put(_box(x, y, z, (3.0, 0.0, 0.38), (4.1, 0.50, 1.0)), f_spare, 'spare')
    def f_slot(x, y, ay, z):
        (x0, z0), (x1, z1) = SLOT['p0'], SLOT['p1']
        L = np.hypot(x1-x0, z1-z0); tx, tz = (x1-x0)/L, (z1-z0)/L
        s = (x - x0)*tx + (z - z0)*tz
        n_ = -(x - x0)*tz + (z - z0)*tx
        hw = 0.5*SLOT['w']*abs(tz)
        d2 = np.maximum(np.maximum(-s, s - L), np.abs(n_) - hw)
        return np.maximum(d2 - 0.004, 0.805 - SLOT['depth'] - ay)
    if comps: return P, C
    return P

POCKET_K = {'grille': 0.006, 'intake': 0.006, 'head': 0.006, 'fvent': 0.0055, 'rvent': 0.0055, 'spare': 0.014, 'slot': 0.010}
def apply_pockets(F, x, y, z):
    P, C = pockets_sdf(x, y, z, comps=True)
    for tag, Pk in C.items():
        F = smax(F, -Pk, POCKET_K.get(tag, 0.006))
    return F
