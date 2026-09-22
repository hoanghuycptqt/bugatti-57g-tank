import numpy as np
def sd_polygon(px, py, poly):
    """signed distance from points (px,py) arrays to closed polygon poly (N,2); negative inside"""
    poly = np.asarray(poly, float)
    vx, vy = poly[:,0], poly[:,1]
    d = np.full(px.shape, np.inf)
    s = np.ones(px.shape)
    n = len(poly)
    for i in range(n):
        j = (i - 1) % n
        ex, ey = vx[j]-vx[i], vy[j]-vy[i]
        wx, wy = px - vx[i], py - vy[i]
        t = np.clip((wx*ex + wy*ey) / (ex*ex + ey*ey), 0, 1)
        bx, by = wx - ex*t, wy - ey*t
        d = np.minimum(d, bx*bx + by*by)
        c1 = py >= vy[i]; c2 = py < vy[j]; c3 = ex*wy > ey*wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)

def catmull(points, n=24, closed=True):
    P = np.asarray(points, float)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    out = []
    for i in range(1, len(P)-2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t*t, t*t*t
            out.append(0.5*((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*t2 + (-p0+3*p1-3*p2+p3)*t3))
    return np.array(out)

def rounded_rect(cx, cy, hw, hh, r, n=12):
    pts = []
    for (sx, sy, a0) in ((1,1,0),( -1,1,90),(-1,-1,180),(1,-1,270)):
        ccx, ccy = cx + sx*(hw - r), cy + sy*(hh - r)
        for a in np.linspace(np.radians(a0), np.radians(a0+90), n):
            pts.append((ccx + r*np.cos(a), ccy + r*np.sin(a)))
    return np.array(pts)
