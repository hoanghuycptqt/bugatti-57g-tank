"""Container-side preview renderer (bpy 4.2, Workbench)."""
import bpy, numpy as np, math, sys, os
from mathutils import Vector

OFF_Y = 1.49  # blender Y = x - 1.49 ; blender X = y ; Z = z

def to_bl(v):
    return np.stack([v[:,1], v[:,0] - OFF_Y, v[:,2]], 1)

def mirror_half(v, f, n):
    # half mesh has y>=0 ; mirror to y<0
    vm = v.copy(); vm[:,1] *= -1
    nm = n.copy(); nm[:,1] *= -1
    fm = f[:, ::-1] + len(v)
    return np.vstack([v, vm]), np.vstack([f, fm]), np.vstack([n, nm])

def make_mesh(name, v, f, n=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v)); me.vertices.foreach_set('co', v.astype(np.float32).ravel())
    nl = len(f)*3
    me.loops.add(nl); me.loops.foreach_set('vertex_index', f.astype(np.int32).ravel())
    me.polygons.add(len(f))
    me.polygons.foreach_set('loop_start', np.arange(0, nl, 3, dtype=np.int32))
    me.update(); me.validate()
    if smooth:
        me.polygons.foreach_set('use_smooth', np.ones(len(f), bool))
    if n is not None:
        me.normals_split_custom_set_from_vertices([tuple(x) for x in n])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def wheel(name, x, z, r, w, y):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=w, location=(y, x - OFF_Y, z), rotation=(0, math.pi/2, 0))
    ob = bpy.context.object; ob.name = name
    bpy.ops.object.shade_smooth()
    return ob

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.62, 0.74, 0.88)
    sh.show_specular_highlight = True
    sc.display.shading.show_cavity = False
    sc.render.film_transparent = False
    sc.world = bpy.data.worlds.new('W'); 
    return sc

def cam(name, loc, look, lens=50, ortho=None, shift=(0,0), rot=None):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.shift_x, cd.shift_y = shift
    cd.clip_end = 200
    ob = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    if rot is not None:
        ob.rotation_euler = rot
    else:
        d = Vector(look) - Vector(loc)
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob

def render(sc, camob, path, rx, ry):
    sc.camera = camob
    sc.render.resolution_x = rx; sc.render.resolution_y = ry
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    npz = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '/home/claude/tank/build/body_half.npz'
    d0 = np.load(npz)
    outdir = '/home/claude/tank/build/prev'; os.makedirs(outdir, exist_ok=True)
    d = np.load(npz)
    v, f, n = mirror_half(d['v'], d['f'], d['n'].astype(np.float32))
    sc = setup_scene()
    ob = make_mesh('Body', to_bl(v), f[:, ::-1].copy(), to_bl(n.astype(np.float32)))
    if 'navy' in d.files:  # VCOL
        navy = np.concatenate([d['navy'], d['navy']]).astype(np.float32)
        gap = np.concatenate([d['gap'], d['gap']]).astype(np.float32)
        well = np.concatenate([d['well'], d['well']]).astype(np.float32)
        light = np.array([0.55, 0.70, 0.88]); dark = np.array([0.07, 0.12, 0.38])
        t = np.clip(0.5 - navy/0.004, 0, 1)[:,None]
        col = light*(1-t) + dark*t
        g = np.clip(1 - (gap - 0.0015)/0.0015, 0, 1)[:,None]
        col = col*(1 - 0.85*g)
        col = col*(1 - 0.8*well[:,None])
        me = ob.data
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        rgba = np.hstack([col, np.ones((len(col),1))]).astype(np.float32)
        ca.data.foreach_set('color', rgba.ravel())
        bpy.context.scene.display.shading.color_type = 'VERTEX'
    for nm, x, z, r in [('WFL', 0.0, 0.385, 0.395), ('WRL', 2.98, 0.39, 0.40)]:
        for s in (1, -1):
            wheel(nm+str(s), x, z, r, 0.15, s*0.675)
    # cameras matched to reference photos (blender coords). front axle at Y=-1.49
    import json
    cams = json.load(open('/home/claude/tank/build/cams.json'))
    for c in cams:
        ob = cam(c['name'], c['loc'], c['look'], lens=c.get('lens', 50), ortho=c.get('ortho'), shift=tuple(c.get('shift', (0,0))), rot=c.get('rot'))
        render(sc, ob, outdir + '/' + c['name'] + '.png', c['res'][0], c['res'][1])
    bpy.ops.wm.save_as_mainfile(filepath='/home/claude/tank/build/prev.blend')
