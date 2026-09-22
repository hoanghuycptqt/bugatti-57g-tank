"""Per-vertex scalar fields for the paint shader (all signed: negative = inside region)."""
import numpy as np
from shapes2d import sd_polygon, rounded_rect
from sdf import ellcyl_y, rbox
import body, details

SWOOSH_XZ = [(1.82, 0.915), (1.93, 0.86), (2.03, 0.79), (2.12, 0.71), (2.21, 0.625), (2.30, 0.54),
             (2.39, 0.46), (2.46, 0.39), (2.525, 0.315),   # front/lower edge down to tip
             (2.47, 0.40), (2.40, 0.50), (2.34, 0.60), (2.295, 0.70), (2.265, 0.80), (2.25, 0.90), (2.25, 0.96), (1.80, 0.96)]
DOOR = dict(x0=1.84, x1=2.39, z0=0.58, z1=0.93, r=0.065)
SEAM_X = 1.135
NOSE_SEAM_Z = 0.412
# navy apron wrapping the lower inner corners of the front pods (front view), in (|y|, z)
APRON = [(0.0, -0.1), (0.0, 0.345), (0.335, 0.345), (0.35, 0.32), (0.37, 0.295), (0.40, 0.275), (0.44, 0.26), (0.48, 0.245), (0.53, 0.22), (0.53, -0.1)]
# navy V below the spare-wheel recess, in (y, z) seen from behind
VNOTCH = [(-0.207, 0.56), (0.207, 0.56), (0.0, 0.397)]

def _keep_sign(g, mask, big=1.0):
    return np.where(mask, g, np.where(g >= 0, big, -big))

def compute(v, parts):
    x, y, z = v[:,0].astype(float), v[:,1].astype(float), v[:,2].astype(float)
    ay = np.abs(y)
    def hood_dom_f(x, y, z):
        hood = parts['HOOD'].sdf(x, y, z)
        others = np.minimum(np.minimum(parts['LB'].sdf(x, y, z), parts['PF'].sdf(x, y, z)), parts['PR'].sdf(x, y, z))
        return hood - others
    hd = hood_dom_f(x, y, z)
    e = 5e-4
    gx = (hood_dom_f(x+e, y, z) - hood_dom_f(x-e, y, z))/(2*e)
    gy = (hood_dom_f(x, y+e, z) - hood_dom_f(x, y-e, z))/(2*e)
    gz = (hood_dom_f(x, y, z+e) - hood_dom_f(x, y, z-e))/(2*e)
    gn = np.sqrt(gx*gx + gy*gy + gz*gz)
    hdn = hd / np.clip(gn, 0.3, 3.0)                 # ~ signed distance to hood/fender seam
    # --- navy regions (min of signed fields)
    rim = np.maximum.reduce([0.875 - z, np.abs(x - 2.07) - 0.55, ay - 0.74])
    sw = sd_polygon(x, z, np.array(SWOOSH_XZ)); sw = np.where(ay > 0.35, sw, 1.0)
    apron = sd_polygon(ay, z, np.array(APRON)); apron = np.where(x < -0.30, apron, 1.0)
    P, C = details.pockets_sdf(x, y, z, comps=True)
    spare = C.get('spare', np.full_like(x, 10.0)) - 0.004
    vn = sd_polygon(y, z, np.array(VNOTCH)); vn = np.where(x > 3.85, vn, 1.0)
    ck = rbox((x, y, z), (2.06, 0.0, 1.0), (0.36, 0.47, 0.66), 0.10) - 0.003
    navy = np.minimum.reduce([hdn, rim, sw, apron, spare, vn, ck])
    # --- panel gaps (signed, sign preserved outside their masks)
    g_seam = _keep_sign(x - SEAM_X, (ay > 0.45) & (z > 0.24) & (z < 0.975))
    door_poly = rounded_rect(0.5*(DOOR['x0']+DOOR['x1']), 0.5*(DOOR['z0']+DOOR['z1']), 0.5*(DOOR['x1']-DOOR['x0']), 0.5*(DOOR['z1']-DOOR['z0']), DOOR['r'], n=16)
    g_door = _keep_sign(sd_polygon(x, z, door_poly), (ay > 0.55) & (z < 0.895))
    g_hood = _keep_sign(hdn, (x < SEAM_X) & (x > -0.62) & (z > NOSE_SEAM_Z - 0.004))
    g_nose = _keep_sign(z - NOSE_SEAM_Z, (x < -0.33) & (ay < 0.345) & (z > 0.37) & (z < 0.46))
    # --- dark masks
    wf = ellcyl_y(x, z, body.WHEEL_FC[0], body.WHEEL_FC[1], 0.445, 0.452)
    wr = ellcyl_y(x, z, body.WHEEL_RC[0], body.WHEEL_RC[1], 0.48, 0.445)
    well = np.where((np.minimum(wf, wr) < 0.004) & (ay > 0.46) & (ay < 0.79) & (z < 0.86), 1.0, 0.0)
    hole = np.minimum.reduce([C.get(k, np.full_like(x, 10.0)) for k in ('grille', 'intake', 'fvent', 'rvent')])
    out = dict(navy=navy, g_seam=g_seam, g_door=g_door, g_hood=g_hood, g_nose=g_nose, well=well, hole=hole)
    return {k: np.clip(a, -8.0, 8.0).astype(np.float32) for k, a in out.items()}
