"""Segmented pointed-oval vents (front pods and rear lobes)."""
import numpy as np

def seg_oval(center, L, prof, cuts, angle_deg=0.0, inset=0.0, n=40):
    """Polygons (in (a, z) = (|y|, z) plane) of the segments of a pointed oval.
    prof: array (k,2) of (t, halfwidth), t=0 top tip, t=1 bottom tip.
    cuts: list of (t0, t1).  angle>0 leans the top outboard (+a).
    inset: shrink each polygon by this amount (for rounded-corner sdf)."""
    prof = np.asarray(prof, float)
    th = np.radians(angle_deg)
    ax = np.array([np.sin(th), np.cos(th)])      # toward top
    nx = np.array([np.cos(th), -np.sin(th)])     # across
    c = np.asarray(center, float)
    polys = []
    for t0, t1 in cuts:
        dt = inset / L
        ta, tb = t0 + dt, t1 - dt
        ts = np.linspace(ta, tb, n)
        w = np.interp(ts, prof[:, 0], prof[:, 1]) - inset
        w = np.maximum(w, 1e-4)
        s = (0.5 - ts) * L
        right = [c + si*ax + wi*nx for si, wi in zip(s, w)]
        left = [c + si*ax - wi*nx for si, wi in zip(s[::-1], w[::-1])]
        polys.append(np.array(right + left))
    return polys

# front pod vents (per pod, a=|y|), vertical
FV = dict(center=(0.595, 0.540), L=0.304, angle=0.0,
          prof=[(0.0, 0.0), (0.03, 0.011), (0.06, 0.019), (0.10, 0.026), (0.15, 0.031), (0.20, 0.035), (0.25, 0.0385),
                (0.32, 0.041), (0.50, 0.0415), (0.66, 0.041), (0.72, 0.039), (0.80, 0.034), (0.87, 0.026), (0.93, 0.016), (0.97, 0.008), (1.0, 0.0)],
          cuts=[(0.0, 0.196), (0.232, 0.426), (0.466, 0.680), (0.719, 1.0)], r=0.005)
# rear lobe vents: leaning, top outboard
RV = dict(center=(0.582, 0.595), L=0.190, angle=14.0,
          prof=[(0.0, 0.0), (0.04, 0.012), (0.08, 0.020), (0.13, 0.028), (0.20, 0.035), (0.28, 0.040), (0.40, 0.0425),
                (0.55, 0.0425), (0.66, 0.040), (0.76, 0.035), (0.85, 0.027), (0.92, 0.018), (0.97, 0.009), (1.0, 0.0)],
          cuts=[(0.0, 0.245), (0.300, 0.490), (0.545, 0.740), (0.795, 1.0)], r=0.0045)

def front_polys(inset=0.0):
    return seg_oval(FV['center'], FV['L'], FV['prof'], FV['cuts'], FV['angle'], inset)
def rear_polys(inset=0.0):
    return seg_oval(RV['center'], RV['L'], RV['prof'], RV['cuts'], RV['angle'], inset)
