
import bpy, numpy as np, re, time
DATA = bpy.path.abspath("//data/")  # folder "data" next to the .blend
def load_body(npz_name):
    d = np.load(DATA + npz_name)
    v = d['v'].astype(np.float64); f = d['f'].astype(np.int64); n = d['n'].astype(np.float32)
    vb = np.stack([v[:,1], v[:,0] - 1.49, v[:,2]], 1).astype(np.float32)
    nb = np.stack([n[:,1], n[:,0], n[:,2]], 1).astype(np.float32)
    fb = f[:, ::-1].astype(np.int32)
    me = bpy.data.meshes.new('Body_mesh')
    me.vertices.add(len(vb)); me.vertices.foreach_set('co', vb.ravel())
    nl = len(fb)*3
    me.loops.add(nl); me.loops.foreach_set('vertex_index', fb.ravel())
    me.polygons.add(len(fb)); me.polygons.foreach_set('loop_start', np.arange(0, nl, 3, dtype=np.int32))
    me.update(); me.validate(clean_customdata=False); me.shade_smooth()
    nn = nb / (np.linalg.norm(nb, axis=1, keepdims=True) + 1e-12)
    me.normals_split_custom_set_from_vertices(nn)
    for k in ('navy', 'g_seam', 'g_door', 'g_hood', 'g_nose', 'well', 'hole'):
        a = me.attributes.new(k, 'FLOAT', 'POINT'); a.data.foreach_set('value', d[k].astype(np.float32))
    ob = bpy.data.objects['Body']
    old = ob.data
    mats = [m for m in old.materials]
    ob.data = me
    for m in mats: me.materials.append(m)
    bpy.data.meshes.remove(old)
    me.name = 'Body'
    return len(vb)
def reload_parts(blend_name):
    coll = bpy.data.collections['Bugatti_57G_Tank']
    for o in list(coll.objects):
        if o.name != 'Body' and not o.name.startswith('Lettering'):
            bpy.data.objects.remove(o, do_unlink=True)
    with bpy.data.libraries.load(DATA + blend_name, link=False) as (src, dst):
        dst.objects = list(src.objects)
    n = 0
    for o in dst.objects:
        if o is None: continue
        coll.objects.link(o); n += 1
    # remap duplicated materials (M_X.001 -> M_X)
    for o in coll.objects:
        for s in o.material_slots:
            m = s.material
            if m is None: continue
            base = re.sub(r'\.\d{3}$', '', m.name)
            if base != m.name and base in bpy.data.materials:
                s.material = bpy.data.materials[base]
    for m in list(bpy.data.materials):
        if m.users == 0: bpy.data.materials.remove(m)
    for me in list(bpy.data.meshes):
        if me.users == 0: bpy.data.meshes.remove(me)
    for nm in ('Hood_Hinge', 'Hood_Rivets_Louvers'):
        o = bpy.data.objects.get(nm)
        if o: o.data.materials[0] = bpy.data.materials['M_PaintNavy']
    return n
