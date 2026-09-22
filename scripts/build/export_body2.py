import numpy as np, sys, time, os
sys.path.insert(0, '/home/claude/tank/build')
from mesher import extract, project
from body import build_parts
import attributes
h = float(sys.argv[1]); outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)
t0 = time.time()
p = build_parts()
v, f, vol, grid = extract(p, h, full=True)
del vol
v, n = project(p, v, f, h=h)
A = attributes.compute(v, p)
np.savez_compressed(os.path.join(outdir, 'body_vn.npz'), v=v.astype(np.float32), n=n.astype(np.float16))
np.savez_compressed(os.path.join(outdir, 'body_attr.npz'), **{k: a.astype(np.float16) for k, a in A.items()})
f = f.astype(np.int32)
half = len(f)//2
np.savez_compressed(os.path.join(outdir, 'body_f0.npz'), f=f[:half])
np.savez_compressed(os.path.join(outdir, 'body_f1.npz'), f=f[half:])
for fn in sorted(os.listdir(outdir)):
    print(fn, round(os.path.getsize(os.path.join(outdir, fn))/1e6, 2), 'MB')
print('verts', v.shape, 'faces', f.shape, 'total %.1fs' % (time.time() - t0))
