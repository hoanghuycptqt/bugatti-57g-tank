import bpy, sys, math, json, time, numpy as np
sys.path.insert(0, '/home/claude/tank/build')
import preview as PV
t0 = time.time()
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
body_npz = args[0] if args else '/home/claude/tank/build/body_6mm_full.npz'
out_parts = args[1] if len(args) > 1 else '/home/claude/tank/build/parts_v2.blend'
sc = PV.setup_scene()
import build_parts as BP
BP.COLL = None
import parts_v2 as P2, cockpit_v2 as CK, wheel
# parts
BP.build_straps(); BP.build_hood_top()
P2.build_grille(); P2.build_intake(); P2.build_vents(); P2.build_headlamps()
P2.build_side_lamp(); P2.build_fuel_filler(); P2.build_tail()
CK.build_cockpit()
BP.build_spare()
for nm, x, R, s in [('W_FL', 0.0, 0.395, 1), ('W_FR', 0.0, 0.395, -1), ('W_RL', 2.98, 0.40, 1), ('W_RR', 2.98, 0.40, -1)]:
    e, objs = wheel.build_wheel(nm, R, s)
    wheel.place_wheel(e, (s*0.675, x - 1.49, R - 0.008), s)
print('parts built in %.1fs' % (time.time() - t0), len(bpy.data.objects), 'objects')
# save parts-only file (compressed) for transfer
bpy.ops.wm.save_as_mainfile(filepath=out_parts, compress=True)
print('saved parts', out_parts)
