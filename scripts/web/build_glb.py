"""Assemble the web GLB: parts from parts_v2.blend + cut body + lettering, with plain PBR materials."""
import bpy, sys, math, numpy as np
sys.path.insert(0, '/home/claude/tank/build')
import preview as PV
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT = args[0] if args else '/home/claude/tank/build/web/57G_Tank_raw.glb'
bpy.ops.wm.open_mainfile(filepath='/home/claude/tank/build/parts_v2.blend')
for o in list(bpy.data.objects):
    if o.type not in ('MESH', 'EMPTY'):
        bpy.data.objects.remove(o, do_unlink=True)

# ---------- plain PBR materials (values taken from the render scene) ----------
M = {  # name: (base linear rgb, metallic, roughness, coat, transmission, ior)
    'M_Paint':          ((0.185, 0.305, 0.490), 0.0, 0.20, 1.0, 0, 1.5),   # web-calibrated to match the renders
    'M_PaintNavy':      ((0.020, 0.031, 0.098), 0.0, 0.20, 1.0, 0, 1.5),
    'M_BodyDark':       ((0.008, 0.008, 0.009), 0.0, 0.75, 0.0, 0, 1.5),
    'M_AluCast':        ((0.36, 0.36, 0.355), 1.0, 0.55, 0, 0, 1.5),
    'M_AluPolished':    ((0.91, 0.92, 0.93), 1.0, 0.12, 0, 0, 1.5),
    'M_AmberLens':      ((0.60, 0.26, 0.05), 0.0, 0.08, 0, 0.85, 1.5),
    'M_BlackGloss':     ((0.012, 0.012, 0.014), 0.0, 0.12, 1.0, 0, 1.5),
    'M_Bulb':           ((0.95, 0.95, 0.92), 0.0, 0.35, 0, 0.6, 1.5),
    'M_Chrome':         ((0.93, 0.93, 0.95), 1.0, 0.06, 0, 0, 1.5),
    'M_Crackle':        ((0.012, 0.012, 0.013), 0.0, 0.55, 0, 0, 1.5),
    'M_DarkHole':       ((0.004, 0.004, 0.004), 0.0, 0.90, 0, 0, 1.5),
    'M_ExhaustSteel':   ((0.035, 0.031, 0.028), 0.35, 0.62, 0, 0, 1.5),
    'M_GaugeFace':      ((1.0, 1.0, 1.0), 0.0, 0.45, 0, 0, 1.5),
    'M_Glass':          ((1.0, 1.0, 1.0), 0.0, 0.0, 0, 1.0, 1.5),
    'M_Interior':       ((0.02, 0.02, 0.022), 0.0, 0.80, 0, 0, 1.5),
    'M_Ivory':          ((0.82, 0.76, 0.60), 0.0, 0.22, 0.6, 0, 1.5),
    'M_LampGlassFluted':((1.0, 1.0, 1.0), 0.0, 0.03, 0, 1.0, 1.5),
    'M_Leather':        ((0.107, 0.045, 0.019), 0.0, 0.55, 0, 0, 1.5),
    'M_Lettering':      ((0.761, 0.761, 0.672), 0.0, 0.30, 0.8, 0, 1.5),
    'M_Mirror':         ((0.96, 0.96, 0.97), 1.0, 0.0, 0, 0, 1.5),
    'M_Nickel':         ((0.82, 0.78, 0.68), 1.0, 0.14, 0, 0, 1.5),
    'M_Radiator':       ((0.012, 0.012, 0.012), 0.2, 0.65, 0, 0, 1.5),
    'M_RedLens':        ((0.55, 0.015, 0.01), 0.0, 0.05, 0, 0.9, 1.5),
    'M_Rubber':         ((0.016, 0.016, 0.017), 0.0, 0.72, 0, 0, 1.5),
    'M_Screen':         ((0.93, 0.95, 0.94), 0.0, 0.12, 0, 1.0, 1.49),
    'M_SeatLeather':    ((0.007, 0.007, 0.007), 0.0, 0.42, 0, 0, 1.5),
    'M_Steel':          ((0.42, 0.42, 0.43), 1.0, 0.38, 0, 0, 1.5),
    'M_SteelDark':      ((0.035, 0.035, 0.038), 0.6, 0.38, 0, 0, 1.5),
    'M_Underbody':      ((0.018, 0.018, 0.02), 0.0, 0.70, 0, 0, 1.5),
    'M_WireBright':     ((0.78, 0.78, 0.80), 1.0, 0.25, 0, 0, 1.5),
    'M_WireMesh':       ((0.13, 0.13, 0.14), 0.85, 0.45, 0, 0, 1.5),
    'M_WireMeshGuard':  ((0.42, 0.42, 0.44), 0.9, 0.36, 0, 0, 1.5),
    'M_Wood':           ((0.098, 0.027, 0.008), 0.0, 0.30, 0.9, 0, 1.5),
}
def plain(name, spec):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    img = None
    for n in nt.nodes:
        if n.type == 'TEX_IMAGE' and n.image is not None:
            img = n.image
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (300, 0)
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(p.outputs['BSDF'], out.inputs['Surface'])
    col, met, rou, coat, tr, ior = spec
    p.inputs['Base Color'].default_value = (*col, 1.0)
    p.inputs['Metallic'].default_value = met
    p.inputs['Roughness'].default_value = rou
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Coat Roughness'].default_value = 0.035 if coat > 0 else 0.03
    p.inputs['Transmission Weight'].default_value = tr
    p.inputs['IOR'].default_value = ior
    if name == 'M_GaugeFace':
        img = bpy.data.images.load('/home/claude/tank/build/web/tex/gauges_atlas.png', check_existing=True)
    if img is not None:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.location = (-400, 0)
        nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
        print('texture kept on', name, img.name, img.filepath)
    return m
for name, spec in M.items():
    plain(name, spec)
unknown = [m.name for m in bpy.data.materials if m.name not in M and m.users]
print('materials without spec:', unknown)

# ---------- material assignment as in the final render scene on the Mac ----------
import json
MAC = json.load(open('/home/claude/tank/build/web/mac_objects.json'))
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name not in MAC or o.name in ('Body', 'Lettering_Drivers'): continue
    want = MAC[o.name]['m']
    for i, nm in enumerate(want):
        if i < len(o.material_slots) and nm and (o.material_slots[i].material is None or o.material_slots[i].material.name != nm):
            print('remap', o.name, i, o.material_slots[i].material.name if o.material_slots[i].material else None, '->', nm)
            o.material_slots[i].material = bpy.data.materials[nm]
# ---------- body (cut along paint boundaries) ----------
d = np.load('/home/claude/tank/build/web/body_cut.npz')
v, f, mi, n = d['v'], d['f'], d['m'], d['n']
def make_mesh_mat(name, v, f, n, mi):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v)); me.vertices.foreach_set('co', v.astype(np.float32).ravel())
    nl = len(f)*3
    me.loops.add(nl); me.loops.foreach_set('vertex_index', f.astype(np.int32).ravel())
    me.polygons.add(len(f))
    me.polygons.foreach_set('loop_start', np.arange(0, nl, 3, dtype=np.int32))
    me.polygons.foreach_set('material_index', mi.astype(np.int32))   # set before validate so removals stay aligned
    me.polygons.foreach_set('use_smooth', np.ones(len(f), bool))
    me.update(); bad = me.validate()
    print('body faces in/out', len(f), len(me.polygons), 'validate changed', bad)
    me.normals_split_custom_set_from_vertices([tuple(x) for x in n])
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob
nb = np.stack([n[:, 1], n[:, 0], n[:, 2]], 1)   # directions: swap axes, no offset
ob = make_mesh_mat('Body', PV.to_bl(v), f[:, ::-1].copy(), nb, mi)
for nm in ('M_Paint', 'M_PaintNavy', 'M_BodyDark'):
    ob.data.materials.append(bpy.data.materials[nm])
mcheck = np.empty(len(ob.data.polygons), np.int32); ob.data.polygons.foreach_get('material_index', mcheck)
print('material counts', np.bincount(mcheck))
# ---------- lettering (evaluated on the Mac, already in world space) ----------
L = np.load('/home/claude/tank/build/web/lettering_eval.npz')  # evaluated Lettering_Drivers mesh exported from the .blend
lo = PV.make_mesh('Lettering_Drivers', L['v'].astype(np.float64), L['f'].astype(np.int64), None)
try:
    lo.data.set_sharp_from_angle(angle=math.radians(35))
except Exception as e:
    print('sharp from angle n/a', e)
lo.data.materials.append(bpy.data.materials['M_Lettering'])
# ---------- strip unused UV maps (only gauge faces use a texture) ----------
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    uses_tex = any(s.material is not None and s.material.name == 'M_GaugeFace' for s in o.material_slots)
    if not uses_tex:
        while o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers[0])
tri = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); tri += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
print('objects', len(bpy.data.objects), 'total tris', tri)
kw = dict(filepath=OUT, export_format='GLB', export_apply=True, export_yup=True, export_cameras=False,
          export_lights=False, export_extras=False, export_animations=False, export_texcoords=True,
          export_normals=True, export_tangents=False, export_materials='EXPORT', export_image_format='AUTO')
bpy.ops.export_scene.gltf(**kw)
import os
print('exported', OUT, round(os.path.getsize(OUT)/1e6, 2), 'MB')
if len(args) > 1:
    bpy.ops.wm.save_as_mainfile(filepath=args[1], compress=True)
