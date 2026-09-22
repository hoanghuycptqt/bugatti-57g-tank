
import bpy, numpy as np
def load_body5(D=None):
    D = D or bpy.path.abspath("//data/body_5mm/")
    vn = np.load(D + 'body_vn.npz'); at = np.load(D + 'body_attr.npz')
    f = np.concatenate([np.load(D + 'body_f0.npz')['f'], np.load(D + 'body_f1.npz')['f']]).astype(np.int64)
    v = vn['v'].astype(np.float64); n = vn['n'].astype(np.float32)
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
        a = me.attributes.new(k, 'FLOAT', 'POINT'); a.data.foreach_set('value', at[k].astype(np.float32))
    ob = bpy.data.objects['Body']
    old = ob.data; mats = [m for m in old.materials]
    ob.data = me
    for m in mats: me.materials.append(m)
    bpy.data.meshes.remove(old); me.name = 'Body'
    return len(vb)
