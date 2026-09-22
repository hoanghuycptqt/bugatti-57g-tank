"""Implicit (signed distance-like) modelling kit for the 57G body.
Car frame: x rearward from front axle, y lateral (+ = car's left), z up (ground=0)."""
import numpy as np
from scipy.interpolate import PchipInterpolator, CubicSpline
def P(x, y):
    return CubicSpline(np.asarray(x, float), np.asarray(y, float), bc_type='natural')

def smin(a, b, k):
    """cubic (C2) smooth minimum (union)"""
    if k <= 0: return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h**3 * k / 6.0

def smax(a, b, k):
    return -smin(-a, -b, k)

class Loft:
    """Superellipse-section loft along x.  Params are control-point arrays over xs.
    a, bt, bb are interpolated in squared form so that the ends close with rounded caps."""
    def __init__(self, xs, yc, zc, a, bt, bb, nt, nb, pair=False, n_y=None, a_in=None, nt_in=None):
        xs = np.asarray(xs, float)
        self.x0, self.x1 = xs[0], xs[-1]
        self.pair = pair
        self.fyc = P(xs, yc); self.fzc = P(xs, zc)
        self.fa2 = P(xs, np.asarray(a, float)**2)
        self.fbt2 = P(xs, np.asarray(bt, float)**2)
        self.fbb2 = P(xs, np.asarray(bb, float)**2)
        self.fnt = P(xs, nt); self.fnb = P(xs, nb)
        # optional asymmetric (inboard) half-width / top exponent for paired lofts
        self.fa2_in = P(xs, np.asarray(a_in, float)**2) if a_in is not None else None
        self.fnt_in = P(xs, nt_in) if nt_in is not None else None

    def _rb(self, x, dy, dz, r):
        xc = np.clip(x, self.x0, self.x1)
        a = np.sqrt(np.maximum(self.fa2(xc), 1e-12))
        if self.fa2_in is not None:
            a_in = np.sqrt(np.maximum(self.fa2_in(xc), 1e-12))
            a = np.where(dy >= 0, a, a_in)
        bt = np.sqrt(np.maximum(self.fbt2(xc), 1e-12))
        bb = np.sqrt(np.maximum(self.fbb2(xc), 1e-12))
        up = dz > 0
        b = np.where(up, bt, bb)
        ntop = self.fnt(xc)
        if self.fnt_in is not None:
            ntop = np.where(dy >= 0, ntop, self.fnt_in(xc))
        n = np.where(up, ntop, self.fnb(xc))
        c = np.abs(dy) / r; s = np.abs(dz) / r
        q = (c / a)**n + (s / b)**n
        q = np.maximum(q, 1e-12)
        return q**(-1.0 / n)

    def sdf(self, x, y, z, slope_corr=True):
        yy = np.abs(y) if self.pair else y
        xc = np.clip(x, self.x0, self.x1)
        dy = yy - self.fyc(xc); dz = z - self.fzc(xc)
        r = np.sqrt(dy*dy + dz*dz) + 1e-9
        rb = self._rb(x, dy, dz, r)
        d = r - rb
        if slope_corr:
            h = 0.01
            rp = self._rb(np.minimum(x + h, self.x1), dy, dz, r)
            rm = self._rb(np.maximum(x - h, self.x0), dy, dz, r)
            dx = np.minimum(x + h, self.x1) - np.maximum(x - h, self.x0)
            sl = np.nan_to_num((rp - rm) / np.maximum(dx, 1e-6), nan=0.0, posinf=0.0, neginf=0.0)
            d = d / np.sqrt(1.0 + sl * sl)
        # caps beyond the ends
        before = x < self.x0; after = x > self.x1
        if np.any(before):
            d = np.where(before, np.sqrt((self.x0 - x)**2 + r*r), d)
        if np.any(after):
            d = np.where(after, np.sqrt((x - self.x1)**2 + r*r), d)
        return d

def plane(x, z, p0, n):
    """plane in xz: n=(nx,nz) outward normal (unit), p0=(x0,z0)"""
    return n[0]*(x - p0[0]) + n[1]*(z - p0[1])

def ellcyl_y(x, z, xc, zc, sx, sz):
    """approx distance to an elliptic cylinder along y"""
    u = (x - xc) / sx; v = (z - zc) / sz
    rr = np.sqrt(u*u + v*v) + 1e-9
    # radial approx distance scaled by local radius
    rad = np.sqrt(((x-xc))**2 + ((z-zc))**2) + 1e-9
    return rad * (1.0 - 1.0/rr)

def rbox(p, c, hsize, rad):
    """rounded box sdf; p tuple of arrays, c center, hsize half sizes, rad corner radius"""
    qs = [np.abs(pi - ci) - (hi - rad) for pi, ci, hi in zip(p, c, hsize)]
    outside = np.sqrt(sum(np.maximum(q, 0)**2 for q in qs))
    inside = np.minimum(np.maximum.reduce(qs), 0)
    return outside + inside - rad
