import numpy as np
from sdf import Loft, smin, smax, plane, ellcyl_y, rbox
from details import apply_pockets, SIDE_RECESS

WB = 2.98
PF_SHIFT, PF_NOUT, PF_EXTRA = 0.054, 3.0, 0.009
PR_SHIFT, PR_NOUT, PR_EXTRA, PR_NIN, PR_EXIN = 0.100, 3.8, 0.020, 2.2, 0.06
WHEEL_FC = (0.0, 0.385)
WHEEL_RC = (WB, 0.39)

def L(xs, yc, zc, a, top, bot, nt, nb, pair=False, a_in=None, nt_in=None):
    xs = np.asarray(xs, float); zc = np.broadcast_to(np.asarray(zc, float), xs.shape)
    top = np.asarray(top, float); bot = np.asarray(bot, float)
    yc = np.broadcast_to(np.asarray(yc, float), xs.shape)
    nt = np.broadcast_to(np.asarray(nt, float), xs.shape); nb = np.broadcast_to(np.asarray(nb, float), xs.shape)
    if nt_in is not None: nt_in = np.broadcast_to(np.asarray(nt_in, float), xs.shape)
    return Loft(xs, yc, zc, a, np.maximum(top - zc, 0), np.maximum(zc - bot, 0), nt, nb, pair=pair, a_in=a_in, nt_in=nt_in)

def crown_shift(yc, a, s0, extra_out=0.0, extra_in=0.0):
    """move the crown of a paired fender loft outboard, keeping its outer/inner extents"""
    yc = np.asarray(yc, float); a = np.asarray(a, float)
    w = (a/a.max())**2
    s = s0*w
    return yc + s, a - s + extra_out*w, a + s - extra_in*w

def build_parts():
    p = {}
    # hood dome + nose (centre body, y=0); front face cut by grille plane
    xs  = [-0.62, -0.45, -0.30, -0.15,  0.00,  0.15,  0.30,  0.50,  0.80,  1.10,  1.40,  1.65,  1.90,  2.20,  2.50,  2.80,  3.00,  3.20,  3.45]
    top = [ 0.79,  0.81,  0.838, 0.885, 0.945, 0.975, 1.003, 1.028, 1.045, 1.050, 1.048, 1.038, 1.00,  0.962, 0.938, 0.928, 0.900, 0.82,  0.62]
    a   = [ 0.33,  0.34,  0.345, 0.35,  0.36,  0.38,  0.41,  0.45,  0.50,  0.545, 0.565, 0.57,  0.57,  0.55,  0.50,  0.45,  0.39,  0.28,  0.00]
    bot = [ 0.26,  0.26,  0.26,  0.26,  0.27,  0.30,  0.36,  0.42,  0.45,  0.45,  0.45,  0.45,  0.45,  0.45,  0.45,  0.45,  0.45,  0.46,  0.50]
    zc  = [ 0.55,  0.55,  0.555, 0.56,  0.58,  0.60,  0.62,  0.64,  0.65,  0.65,  0.65,  0.65,  0.65,  0.65,  0.65,  0.65,  0.65,  0.65,  0.65]
    nt  = [ 2.6,   2.6,   2.6,   2.6,   2.7,   2.9,   3.1,   3.25,  3.3,   3.35,  3.35,  3.3,   3.2,   3.0,   2.9,   2.8,   2.7,   2.6,   2.5]
    p['HOOD'] = L(xs, 0, zc, a, top, bot, nt, 4.0)
    # lower body (full width sides + tail)
    xs  = [ 0.15,  0.25,  0.35,  0.42,  0.52,  0.70,  1.00,  1.50,  2.00,  2.50,  2.90,  3.15,  3.35,  3.55,  3.70,  3.82,  3.92,  4.00,  4.06,  4.11,  4.15,  4.18]
    a   = [ 0.00,  0.45,  0.66,  0.74,  0.795, 0.805, 0.805, 0.805, 0.805, 0.80,  0.785, 0.772, 0.765, 0.748, 0.72,  0.685, 0.64,  0.595, 0.545, 0.475, 0.375, 0.00]
    top = [ 0.50,  0.70,  0.83,  0.87,  0.895, 0.905, 0.91,  0.905, 0.885, 0.895, 0.915, 0.90,  0.845, 0.765, 0.675, 0.595, 0.532, 0.492, 0.463, 0.437, 0.41,  0.38]
    bot = [ 0.50,  0.27,  0.26,  0.255, 0.25,  0.25,  0.25,  0.25,  0.25,  0.25,  0.26,  0.262, 0.265, 0.27,  0.272, 0.275, 0.28,  0.284, 0.288, 0.292, 0.30,  0.34]
    zc  = [ 0.50,  0.52,  0.55,  0.55,  0.55,  0.55,  0.55,  0.55,  0.55,  0.55,  0.55,  0.54,  0.51,  0.47,  0.44,  0.415, 0.40,  0.385, 0.375, 0.37,  0.365, 0.36]
    nt  = [ 5.0]*12 + [4.6, 4.0, 3.6, 3.2, 3.0, 2.8, 2.7, 2.6, 2.6, 2.6]
    p['LB'] = L(xs, 0, zc, a, top, bot, nt, 5.0)
    # front pods (fenders)
    xs  = [-0.565, -0.550, -0.525, -0.49,  -0.44,  -0.38,  -0.30, -0.15,  0.00,  0.15,  0.30,  0.45,  0.60,  0.80,  1.00,  1.20,  1.40,  1.60,  1.80]
    yc  = [ 0.55,   0.55,   0.552,  0.554,  0.555,  0.556,  0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556]
    zc  = [ 0.45,   0.45,   0.45,   0.45,   0.452,  0.455,  0.458, 0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.46]
    a   = [ 0.00,   0.105,  0.165,  0.200,  0.217,  0.226,  0.235, 0.245, 0.250, 0.250, 0.249, 0.246, 0.232, 0.195, 0.16,  0.13,  0.10,  0.06,  0.00]
    top = [ 0.45,   0.52,   0.58,   0.638,  0.695,  0.75,   0.80,  0.855, 0.875, 0.878, 0.872, 0.862, 0.848, 0.825, 0.80,  0.775, 0.745, 0.70,  0.46]
    bot = [ 0.45,   0.34,   0.295,  0.272,  0.262,  0.26,   0.26,  0.26,  0.26,  0.26,  0.26,  0.26,  0.26,  0.26,  0.26,  0.26,  0.27,  0.29,  0.46]
    ycs, a_out, a_in = crown_shift(yc, np.array(a)*0.96, PF_SHIFT, PF_EXTRA)
    p['PF'] = L(xs, ycs, zc, a_out, top, bot, PF_NOUT, 3.4, pair=True, a_in=a_in, nt_in=3.3)
    # rear lobes (fenders)
    xs  = [ 1.90,  2.15,  2.40,  2.60,  2.75,  2.90,  3.05,  3.20,  3.40,  3.55,  3.68,  3.78,  3.86]
    yc  = [ 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.556, 0.552, 0.545, 0.535, 0.525]
    zc  = [ 0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.46,  0.455, 0.45,  0.44,  0.43,  0.42,  0.41]
    a   = [ 0.00,  0.10,  0.155, 0.195, 0.228, 0.245, 0.245, 0.243, 0.235, 0.215, 0.18,  0.12,  0.00]
    top = [ 0.46,  0.79,  0.882, 0.925, 0.946, 0.957, 0.958, 0.921, 0.835, 0.75,  0.66,  0.58,  0.43]
    bot = [ 0.46,  0.30,  0.27,  0.26,  0.26,  0.26,  0.26,  0.26,  0.265, 0.265, 0.27,  0.28,  0.41]
    ycs, a_out, a_in = crown_shift(yc, np.array(a)*0.955, PR_SHIFT, PR_EXTRA, PR_EXIN)
    p['PR'] = L(xs, ycs, zc, a_out, top, bot, PR_NOUT, 3.4, pair=True, a_in=a_in, nt_in=PR_NIN)
    return p

def body_sdf(x, y, z, p, detail=True):
    hood = p['HOOD'].sdf(x, y, z)
    lb = p['LB'].sdf(x, y, z)
    F = smin(hood, lb, 0.07)
    d_pl = plane(x, z, (-0.43, 0.30), (-0.950, 0.311))
    F = smax(F, d_pl, 0.05)
    F = smin(F, p['PF'].sdf(x, y, z), 0.06)
    F = smin(F, p['PR'].sdf(x, y, z), 0.07)
    if detail:
        ay = np.abs(y)
        wf = smax(ellcyl_y(x, z, WHEEL_FC[0], WHEEL_FC[1], 0.445, 0.452), 0.47 - ay, 0.02)
        wr = smax(ellcyl_y(x, z, WHEEL_RC[0], WHEEL_RC[1], 0.48, 0.445), 0.47 - ay, 0.02)
        F = smax(F, -wf, 0.018)
        F = smax(F, -wr, 0.018)
        ck = rbox((x, y, z), (2.06, 0.0, 1.0), (0.36, 0.47, 0.66), 0.10)
        F = smax(F, -ck, 0.02)
        F = apply_pockets(F, x, y, z)
        F = side_recess(F, x, y, z)
        F = slot_recess(F, x, y, z)
    return F

def _smoothstep(e0, e1, t):
    u = np.clip((t - e0)/(e1 - e0), 0.0, 1.0)
    return u*u*(3 - 2*u)

def side_recess(F, x, y, z):
    """shallow oval dish around the right-side driving lamp (y<0 only): smooth displacement of the field"""
    R = SIDE_RECESS
    m = (y < -0.5) & (np.abs(x - R['xc']) < R['A'] + 0.03) & (np.abs(z - R['zc']) < R['B'] + 0.03)
    if not np.any(m):
        return F
    F = np.array(F, dtype=float, copy=True)
    u = (x[m] - R['xc'])/R['A']; v = (z[m] - R['zc'])/R['B']
    rr = np.sqrt(u*u + v*v)
    w = 1.0 - _smoothstep(0.80, 1.0, rr)
    F[m] = F[m] + R['depth']*w
    return F

def slot_recess(F, x, y, z):
    """recessed slanted panel on both flanks (smooth-edged)"""
    from details import SLOT
    ay = np.abs(y)
    m = (ay > 0.70) & (x > 1.15) & (x < 1.38) & (z > 0.44) & (z < 0.78)
    if not np.any(m):
        return F
    F = np.array(F, dtype=float, copy=True)
    xx, zz = x[m], z[m]
    (x0, z0), (x1, z1) = SLOT['p0'], SLOT['p1']
    L = np.hypot(x1-x0, z1-z0); tx, tz = (x1-x0)/L, (z1-z0)/L
    s = (xx - x0)*tx + (zz - z0)*tz
    n_ = -(xx - x0)*tz + (zz - z0)*tx
    hw = 0.5*SLOT['w']*abs(tz)
    q1 = np.maximum(np.maximum(-s, s - L), np.abs(n_) - hw)
    w = 1.0 - _smoothstep(-0.006, 0.002, q1)
    F[m] = F[m] + SLOT['depth']*w
    return F
