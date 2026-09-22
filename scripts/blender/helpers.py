
import bpy, math
def srgb(c):
    def f(x):
        x = x/255.0
        return x/12.92 if x <= 0.04045 else ((x + 0.055)/1.055)**2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)
def setin(node, name, val):
    if name in node.inputs:
        node.inputs[name].default_value = val
def fresh(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes): nt.nodes.remove(nd)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (900, 0)
    return m, nt, out
def principled(name, base=(0.8,0.8,0.8,1), metal=0.0, rough=0.5, coat=0.0, coat_r=0.03, trans=0.0, ior=1.5, spec=0.5, alpha=1.0, extra=None):
    m, nt, out = fresh(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (500, 0)
    setin(b, 'Base Color', base); setin(b, 'Metallic', metal); setin(b, 'Roughness', rough)
    setin(b, 'Coat Weight', coat); setin(b, 'Coat Roughness', coat_r)
    setin(b, 'Transmission Weight', trans); setin(b, 'IOR', ior); setin(b, 'Specular IOR Level', spec); setin(b, 'Alpha', alpha)
    if extra:
        for k, v in extra.items(): setin(b, k, v)
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m, nt, b, out
def node(nt, typ, loc, **kw):
    n = nt.nodes.new(typ); n.location = loc
    for k, v in kw.items():
        if k in n.inputs: n.inputs[k].default_value = v
        else: setattr(n, k, v)
    return n
def link(nt, a, b):
    nt.links.new(a, b)
def maprange(nt, loc, src, fmin, fmax, tmin, tmax, clamp=True):
    mr = node(nt, 'ShaderNodeMapRange', loc)
    mr.inputs['From Min'].default_value = fmin; mr.inputs['From Max'].default_value = fmax
    mr.inputs['To Min'].default_value = tmin; mr.inputs['To Max'].default_value = tmax
    mr.clamp = clamp
    link(nt, src, mr.inputs['Value'])
    return mr.outputs['Result']
def math_op(nt, loc, op, a, b=None, val=None):
    m = node(nt, 'ShaderNodeMath', loc); m.operation = op
    if isinstance(a, (int, float)): m.inputs[0].default_value = a
    else: link(nt, a, m.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): m.inputs[1].default_value = b
        else: link(nt, b, m.inputs[1])
    return m.outputs[0]
def attr(nt, loc, name):
    a = node(nt, 'ShaderNodeAttribute', loc); a.attribute_type = 'GEOMETRY'; a.attribute_name = name
    return a.outputs['Fac']
LIGHT_BLUE = srgb((126, 164, 204))
NAVY = srgb((30, 45, 92))
