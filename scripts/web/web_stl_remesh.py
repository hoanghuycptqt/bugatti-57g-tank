"""Regular (isotropic) triangulation of the body for the flat-shaded STL viewer, then snapped to the exact surface."""
import numpy as np, sys, time
sys.path.insert(0, '/home/claude/tank/build')
import pymeshlab
from body import build_parts
from mesher import project
t0 = time.time()
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 95000
d = np.load('/home/claude/tank/build/web/body_glb.npz')
v = d['v'].astype(np.float64); f = d['f'].astype(np.int32)
a = np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]], v[f[:,2]]-v[f[:,0]]), axis=1).sum()/2
L = np.sqrt(a/(0.433*TARGET))
print('area %.2f m2 -> edge %.4f m' % (a, L))
ms = pymeshlab.MeshSet()
ms.add_mesh(pymeshlab.Mesh(vertex_matrix=v, face_matrix=f))
ms.meshing_isotropic_explicit_remeshing(iterations=8, targetlen=pymeshlab.PureValue(L), featuredeg=35,
                                        checksurfdist=True, maxsurfdist=pymeshlab.PureValue(0.0015), reprojectflag=True)
m = ms.current_mesh()
vr = m.vertex_matrix().astype(np.float64); fr = m.face_matrix().astype(np.int64)
print('remeshed', len(vr), len(fr), '%.1fs' % (time.time()-t0))
parts = build_parts()
vr, n = project(parts, vr, fr, iters=3, h=0.01)
np.savez_compressed('/home/claude/tank/build/web/body_stl.npz', v=vr.astype(np.float32), f=fr.astype(np.int32))
print('saved %.1fs' % (time.time()-t0))
