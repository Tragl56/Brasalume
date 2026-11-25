# Kit de arte do Brasalume no Blender: base comum (cena, cores, materiais, primitivas, luz, câmera e render).
# As medidas seguem o desenho do jogo: 1 unidade do Canvas = 2 cm (o herói tem cerca de 85 unidades = 1,7 m).
# Eixos: o personagem olha para +X, Z é para cima, Y é a lateral (esquerda do personagem = +Y).
import bpy, bmesh, math
from mathutils import Vector, Euler, Matrix

U = 0.02


def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()


# ---------- cores ----------
def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h, a=1.0):
    r, g, b = hex_rgb(h)
    return (lin(r), lin(g), lin(b), a)


def to_hex(r, g, b):
    return '#%02x%02x%02x' % tuple(max(0, min(255, round(v * 255))) for v in (r, g, b))


def shade(h, f):
    """Mesmo critério do jogo: f < 0 escurece, f > 0 clareia."""
    r, g, b = hex_rgb(h)
    if f < 0:
        return to_hex(r * (1 + f), g * (1 + f), b * (1 + f))
    return to_hex(r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f)


def mix(a, b, t):
    ra, ga, ba = hex_rgb(a); rb, gb, bb = hex_rgb(b)
    return to_hex(ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t)


# ---------- materiais ----------
_MATS = {}
ROUGH = {'cloth': .86, 'fur': .95, 'leather': .55, 'metal': .3, 'skin': .5, 'wood': .72, 'bone': .58, 'stone': .88,
         'gloss': .16, 'glass': .04, 'emit': .5, 'paper': .9, 'gold': .25}
# Acabamento dos monstros (gerar.py liga ao renderizar inimigos): manchas largas de cor, sombra nas dobras e brilho menos
# plástico. Heróis, retratos e cenário continuam com o material de antes.
ACAB = False
MANCHA = {'fur': (.56, 1.12), 'cloth': (.62, 1.1), 'skin': (.58, 1.12), 'gloss': (.62, 1.1), 'stone': (.55, 1.15), 'wood': (.58, 1.12),
          'bone': (.66, 1.08), 'leather': (.6, 1.1), 'metal': (.76, 1.06), 'gold': (.8, 1.05), 'paper': (.8, 1.04), 'gosma': (.6, 1.12),
          'escama': (.5, 1.14)}
ROUGH.update({'gosma': .22, 'escama': .46})


def _inp(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    return None


def mat(kind, color, strength=5.0, alpha=1.0, rough=None):
    key = (kind, color, strength, alpha, rough, ACAB)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new('%s_%s' % (kind, color))
    if hasattr(m, 'use_nodes'):
        m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = hex_lin(color)
    b.inputs['Roughness'].default_value = ROUGH.get(kind, .6) if rough is None else rough
    if kind in ('metal', 'gold'):
        b.inputs['Metallic'].default_value = 1.0
    if kind == 'gloss':
        _inp(b, 'Coat Weight').default_value = .7
    if kind == 'skin':
        _inp(b, 'Subsurface Weight').default_value = .18
    if kind == 'gosma':   # geleia viva: a luz entra e espalha por dentro, com uma película molhada por cima
        _inp(b, 'Subsurface Weight').default_value = .6
        _inp(b, 'Subsurface Radius').default_value = (1.0, .8, .6)
        _inp(b, 'Subsurface Scale').default_value = .09
        _inp(b, 'Coat Weight').default_value = .45
        _inp(b, 'Coat Roughness').default_value = .08
    if kind == 'escama':   # couro de serpente: escamas em células, com a borda funda
        vo = nt.nodes.new('ShaderNodeTexVoronoi')
        vo.feature = 'DISTANCE_TO_EDGE'
        vo.inputs['Scale'].default_value = 70
        geo_e = nt.nodes.new('ShaderNodeNewGeometry')
        mp_e = nt.nodes.new('ShaderNodeMapping')
        mp_e.inputs['Scale'].default_value = (1.0, 1.0, .6)
        nt.links.new(geo_e.outputs['Position'], mp_e.inputs['Vector'])
        nt.links.new(mp_e.outputs['Vector'], vo.inputs['Vector'])
        bp_e = nt.nodes.new('ShaderNodeBump')
        bp_e.inputs['Strength'].default_value = .55
        bp_e.inputs['Distance'].default_value = .01
        nt.links.new(vo.outputs['Distance'], bp_e.inputs['Height'])
        nt.links.new(bp_e.outputs['Normal'], b.inputs['Normal'])
        rp_e = nt.nodes.new('ShaderNodeMapRange')   # a borda de cada escama brilha menos
        rp_e.inputs['From Max'].default_value = .12
        rp_e.inputs['To Min'].default_value, rp_e.inputs['To Max'].default_value = .8, .34
        nt.links.new(vo.outputs['Distance'], rp_e.inputs['Value'])
        nt.links.new(rp_e.outputs['Result'], b.inputs['Roughness'])
    if kind in ('cloth', 'fur'):
        _inp(b, 'Sheen Weight').default_value = .5
    if kind == 'glass':
        _inp(b, 'Transmission Weight').default_value = .9
    if kind == 'emit':
        _inp(b, 'Emission Color').default_value = hex_lin(color)
        _inp(b, 'Emission Strength').default_value = strength
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    # relevo sutil para o material não parecer plástico liso
    if kind in ('cloth', 'fur', 'leather', 'metal', 'gold', 'stone', 'wood', 'bone', 'paper'):
        tex = nt.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = {'metal': 55, 'gold': 55, 'stone': 18, 'wood': 6, 'fur': 90, 'paper': 30}.get(kind, 38)
        tex.inputs['Detail'].default_value = 7
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = {'metal': .12, 'gold': .1, 'stone': .55, 'wood': .4, 'fur': .5}.get(kind, .22)
        bump.inputs['Distance'].default_value = .02
        nt.links.new(tex.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
        if kind in ('metal', 'gold', 'leather', 'stone'):
            # desgaste: a rugosidade varia com o mesmo ruído
            mr = nt.nodes.new('ShaderNodeMapRange')
            base = b.inputs['Roughness'].default_value
            mr.inputs['To Min'].default_value = max(0, base - .14)
            mr.inputs['To Max'].default_value = min(1, base + .22)
            nt.links.new(tex.outputs['Fac'], mr.inputs['Value'])
            nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
        if kind in ('metal', 'gold', 'bone', 'leather'):
            # bordas gastas mais claras (curvatura da malha) e cavidades mais escuras
            try:
                geo = nt.nodes.new('ShaderNodeNewGeometry')
                rampa = nt.nodes.new('ShaderNodeValToRGB')
                rampa.color_ramp.elements[0].position, rampa.color_ramp.elements[1].position = .47, .56
                mix_n = nt.nodes.new('ShaderNodeMix')
                mix_n.data_type = 'RGBA'
                mix_n.inputs[6].default_value = hex_lin(shade(color, -.35))
                mix_n.inputs[7].default_value = hex_lin(shade(color, .35))
                nt.links.new(geo.outputs['Pointiness'], rampa.inputs['Fac'])
                nt.links.new(rampa.outputs['Color'], mix_n.inputs[0])
                nt.links.new(mix_n.outputs[2], b.inputs['Base Color'])
            except Exception as e:
                print('borda', e)
    if kind in ('cloth', 'leather', 'fur'):
        # sujeira: tudo o que fica perto do chão escurece (vale para qualquer peça, pela altura no mundo)
        try:
            geo = nt.nodes.new('ShaderNodeNewGeometry')
            sep = nt.nodes.new('ShaderNodeSeparateXYZ')
            mr = nt.nodes.new('ShaderNodeMapRange')
            mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 0.0, 0.55
            mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = .45, 1.0
            mx = nt.nodes.new('ShaderNodeMix')
            mx.data_type = 'RGBA'
            mx.blend_type = 'MULTIPLY'
            mx.inputs[0].default_value = 1.0
            mx.inputs[6].default_value = hex_lin(color)
            comb = nt.nodes.new('ShaderNodeCombineXYZ')
            nt.links.new(geo.outputs['Position'], sep.inputs[0])
            nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
            for k in ('X', 'Y', 'Z'):
                nt.links.new(mr.outputs['Result'], comb.inputs[k])
            nt.links.new(comb.outputs[0], mx.inputs[7])
            nt.links.new(mx.outputs[2], b.inputs['Base Color'])
        except Exception as e:
            print('sujeira', e)
    if ACAB:
        try:
            _acabamento(nt, b, kind, color)
        except Exception as e:
            print('acabamento', kind, e)
    _MATS[key] = m
    return m


def _acabamento(nt, b, kind, color):
    """Monstros: a cor ganha manchas largas (ruído pela posição no mundo) e escurece nas dobras e encontros de peças (oclusão),
    o brilho molhado fica menos de plástico e pele e casca ganham relevo. Vidro e luz ficam como estão."""
    if kind in ('emit', 'glass'):
        return
    N = nt.nodes
    geo = N.new('ShaderNodeNewGeometry')
    cor = b.inputs['Base Color']
    if cor.is_linked:   # bordas gastas ou sujeira já ligadas: o acabamento vai por cima delas
        src = cor.links[0].from_socket
    else:
        rgb = N.new('ShaderNodeRGB')
        rgb.outputs[0].default_value = hex_lin(color)
        src = rgb.outputs[0]
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 4.2
    nz.inputs['Detail'].default_value = 4
    nz.inputs['Roughness'].default_value = .6
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = .3, .7
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = MANCHA.get(kind, (.75, 1.06))
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.samples = 8
    ao.inputs['Distance'].default_value = .14
    mo = N.new('ShaderNodeMapRange')
    mo.inputs['To Min'].default_value, mo.inputs['To Max'].default_value = .3, 1.0
    nt.links.new(ao.outputs['AO'], mo.inputs['Value'])
    fator = N.new('ShaderNodeMath')
    fator.operation = 'MULTIPLY'
    nt.links.new(mr.outputs['Result'], fator.inputs[0])
    nt.links.new(mo.outputs['Result'], fator.inputs[1])
    mx = N.new('ShaderNodeMix')
    mx.data_type = 'RGBA'
    mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    nt.links.new(src, mx.inputs[6])
    nt.links.new(fator.outputs[0], mx.inputs[7])
    nt.links.new(mx.outputs[2], cor)
    if kind == 'gloss':   # molhado, mas sem cara de brinquedo: menos verniz e brilho que varia
        _inp(b, 'Coat Weight').default_value = .3
    if kind in ('gloss', 'skin', 'gosma') and not b.inputs['Roughness'].is_linked:
        base = b.inputs['Roughness'].default_value
        rr = N.new('ShaderNodeMapRange')
        rr.inputs['To Min'].default_value, rr.inputs['To Max'].default_value = base + .04, base + .24
        nt.links.new(nz.outputs['Fac'], rr.inputs['Value'])
        nt.links.new(rr.outputs['Result'], b.inputs['Roughness'])
    if kind in ('gloss', 'skin', 'gosma') and not b.inputs['Normal'].is_linked:
        tx = N.new('ShaderNodeTexNoise')
        tx.inputs['Scale'].default_value = 26 if kind == 'skin' else 11
        tx.inputs['Detail'].default_value = 6
        bp = N.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = .22 if kind == 'skin' else .1
        bp.inputs['Distance'].default_value = .02
        nt.links.new(tx.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])


# ---------- primitivas (coordenadas em unidades do jogo) ----------
def V(p):
    return Vector((p[0] * U, p[1] * U, p[2] * U))


def _link(o, parent):
    if _PARTES and parent is not None and parent is _PARTES[-1][0]:
        e = _PARTES[-1][1]
        o.parent = e
        o.matrix_parent_inverse = Matrix.Translation(-e.location)   # o vazio está no pivô; a peça não sai do lugar
        return o
    if parent is not None:
        o.parent = parent
    return o


# ---------- partes animáveis ----------
# As peças criadas dentro de "with parte(R, 'perna', pivo, ...)" com pai R ficam presas a um vazio no pivô.
# A pose de cada quadro gira ou desloca esse vazio (kit_monstros.pose); sem pose, nada muda no desenho.
# Os dados extras viram propriedades anim_<nome> do vazio (fase, amp, eixo, s, atk...).
_PARTES = []


class parte:
    def __init__(self, pai, tipo, pivo=(0, 0, 0), **dados):
        self.pai, self.tipo, self.pivo, self.dados = pai, tipo, pivo, dados

    def __enter__(self):
        e = bpy.data.objects.new('parte_' + self.tipo, None)
        bpy.context.collection.objects.link(e)
        e.location = V(self.pivo)
        _link(e, self.pai)   # dentro de outra parte, o vazio novo fica preso a ela
        e['anim'] = self.tipo
        for k, v in self.dados.items():
            e['anim_' + k] = v
        _PARTES.append((self.pai, e))
        return e

    def __exit__(self, *a):
        _PARTES.pop()
        return False


def _fin(o, m, smooth=True, parent=None):
    if m is not None:
        o.data.materials.append(m)
    if smooth and hasattr(o.data, 'polygons'):
        for p in o.data.polygons:
            p.use_smooth = True
    return _link(o, parent)


def raiz(nome='raiz'):
    o = bpy.data.objects.new(nome, None)
    bpy.context.collection.objects.link(o)
    return o


def sph(loc, r, m, scale=(1, 1, 1), rot=(0, 0, 0), seg=28, ring=18, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r * U, location=V(loc), rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return _fin(o, m, parent=parent)


def cyl(p1, p2, r1, r2, m, verts=24, parent=None, smooth=True):
    a, b = Vector(p1), Vector(p2)
    d = b - a
    L = max(d.length, 1e-4)
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=max(r1, .01) * U, radius2=max(r2, .01) * U, depth=L * U, location=V((a + b) / 2))
    o = bpy.context.object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return _fin(o, m, smooth=smooth, parent=parent)


def caps(p1, p2, r, m, parent=None, r2=None):
    r2 = r if r2 is None else r2
    o = cyl(p1, p2, r, r2, m, parent=parent)
    sph(p1, r, m, parent=parent, seg=16, ring=10)
    sph(p2, r2, m, parent=parent, seg=16, ring=10)
    return o


def box(loc, size, m, rot=(0, 0, 0), bevel=.6, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=V(loc), rotation=rot)
    o = bpy.context.object
    o.scale = (size[0] * U, size[1] * U, size[2] * U)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        bv = o.modifiers.new('chanfro', 'BEVEL')
        bv.width = min(bevel, min(size) * .45) * U
        bv.segments = 3
    return _fin(o, m, smooth=bool(bevel), parent=parent)


def torus(loc, R, r, m, rot=(0, 0, 0), scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R * U, minor_radius=r * U, location=V(loc), rotation=rot, major_segments=36, minor_segments=12)
    o = bpy.context.object
    o.scale = scale
    return _fin(o, m, parent=parent)


def tubo(pts, r, m, radii=None, parent=None, res=5):
    """Curva com espessura (chifres, cachecóis, correntes, cordas). radii afina ponto a ponto."""
    cu = bpy.data.curves.new('tubo', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r * U
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for i, (bp, p) in enumerate(zip(sp.bezier_points, pts)):
        bp.co = V(p)
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
        if radii:
            bp.radius = radii[i]
    o = bpy.data.objects.new('tubo', cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    return _link(o, parent)


def poly(pts, m, esp=.8, parent=None, subdiv=0):
    """Placa plana a partir de um contorno (lâminas, penas, bandeiras), com espessura."""
    me = bpy.data.meshes.new('placa')
    bm = bmesh.new()
    vs = [bm.verts.new(V(p)) for p in pts]
    bm.faces.new(vs)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('placa', me)
    bpy.context.collection.objects.link(o)
    sd = o.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = esp * U
    sd.offset = 0
    if subdiv:
        ss = o.modifiers.new('suave', 'SUBSURF')
        ss.levels = ss.render_levels = subdiv
    return _fin(o, m, smooth=bool(subdiv), parent=parent)


def casca(z0, z1, r0, r1, a0, a1, m, xs=1.0, esp=1.2, segs=18, rings=10, cx=0.0, cy=0.0, dobras=0.0, onda=0.0, parent=None, rasgos=0.0):
    """Superfície de cone parcial entre os ângulos a0..a1 (0 = frente, +X): capas, saias, mantos, capuzes.
    rasgos: a barra (a borda em z1) fica esfarrapada, com pontas de comprimentos diferentes (em unidades do jogo)."""
    me = bpy.data.meshes.new('casca')
    bm = bmesh.new()
    grid = []
    for j in range(rings + 1):
        t = j / rings
        z = z0 + (z1 - z0) * t
        r = r0 + (r1 - r0) * t
        row = []
        for i in range(segs + 1):
            a = a0 + (a1 - a0) * i / segs
            rr = r + math.sin(i * 1.7 + j * .3) * dobras * t + math.sin(a * 3) * onda * t
            zz = z
            faixa = max(2, rings // 3)
            if rasgos and j > rings - faixa:   # pontas esfarrapadas: cada coluna termina numa altura (as últimas fileiras sobem juntas)
                k = ((i * 7919 + 13) % 11) / 10
                zz = z + math.copysign(rasgos * k * (j - (rings - faixa)) / faixa, z0 - z1)
            row.append(bm.verts.new(V((cx + math.cos(a) * rr * xs, cy + math.sin(a) * rr, zz))))
        grid.append(row)
    for j in range(rings):
        for i in range(segs):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('casca', me)
    bpy.context.collection.objects.link(o)
    sd = o.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = esp * U
    ss = o.modifiers.new('suave', 'SUBSURF')
    ss.levels = ss.render_levels = 1
    return _fin(o, m, parent=parent)


def capuz(loc, r, m, abertura=.38, parent=None, ponta=None):
    """Esfera com a frente aberta para o rosto; ponta opcional (x, z) para trás."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=18, radius=r * U, location=V(loc))
    o = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    corte = [v for v in bm.verts if v.co.x > r * U * abertura and v.co.z < r * U * .62]
    bmesh.ops.delete(bm, geom=corte, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    sd = o.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = 1.4 * U
    _fin(o, m, parent=parent)
    if ponta and ponta[1] > abs(ponta[0]):
        # capuz pontudo (penitente): cone para cima
        cyl((loc[0] - r * .55, loc[1], loc[2] + r * .55), (loc[0] + ponta[0], loc[1], loc[2] + ponta[1]), r * .42, .4, m, parent=parent)
    elif ponta:
        # cauda do capuz caída nas costas; de 3/4 não parece orelha
        k = abs(ponta[0]) / 15
        x, y, z = loc
        tubo([(x - r * .5, y, z + r * .6), (x - r * 1.0 * k, y, z + r * .42), (x - r * 1.22 * k, y, z - r * .2), (x - r * 1.12 * k, y, z - r * .95 * k)],
             r * .34, m, radii=[1, .72, .48, .22], parent=parent)
    return o


def cupula(loc, r, m, corte=.05, frente=-.25, parent=None):
    """Elmo: esfera sem a parte de baixo da frente (onde fica o rosto); atrás desce até a nuca."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=36, ring_count=20, radius=r * U, location=V(loc))
    o = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    fora = [v for v in bm.verts if v.co.z < r * U * corte and (v.co.x > r * U * frente or v.co.z < -r * U * .45)]
    bmesh.ops.delete(bm, geom=fora, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    sd = o.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = 1.6 * U
    return _fin(o, m, parent=parent)


# ---------- luz, mundo, câmera e render ----------
def mirar(o, alvo):
    d = Vector(alvo) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def luz_area(nome, loc, energia, cor, tam, alvo):
    L = bpy.data.lights.new(nome, 'AREA')
    L.energy = energia
    L.color = cor
    L.size = tam
    o = bpy.data.objects.new(nome, L)
    bpy.context.collection.objects.link(o)
    o.location = loc
    mirar(o, alvo)
    return o


def luz_ponto(loc, energia, cor_hex, raio=.05, parent=None):
    L = bpy.data.lights.new('brilho', 'POINT')
    L.energy = energia
    L.color = hex_lin(cor_hex)[:3]
    L.shadow_soft_size = raio
    o = bpy.data.objects.new('brilho', L)
    bpy.context.collection.objects.link(o)
    o.location = V(loc)
    return _link(o, parent)


def mundo(cor=(.012, .014, .018), forca=1.0):
    w = bpy.data.worlds.new('mundo')
    bpy.context.scene.world = w
    if hasattr(w, 'use_nodes'):
        w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (*cor, 1)
    bg.inputs['Strength'].default_value = forca


def estudio(alvo_z=1.0, aro='#9fb8d8', quente=(1.0, .91, .8), forte=1.0):
    """Luz dramática de retrato: chave levemente quente pela frente-direita, contraluz na cor do efeito (misturada com branco,
    para não tingir a paleta da classe) e preenchimento fraco."""
    alvo = (0, 0, alvo_z)
    aro = mix(aro, '#ffffff', .45)
    luz_area('chave', (2.4, -2.8, 3.8), 300 * forte, quente, .9, alvo)
    luz_area('preench', (-3.4, -2.4, 1.2), 38 * forte, (.55, .62, .85), 2.4, alvo)
    r, g, b, _ = hex_lin(aro)
    luz_area('aro', (-1.8, 3.0, 3.4), 1300 * forte, (r, g, b), 1.0, alvo)
    luz_area('aro2', (2.4, 2.4, 2.4), 520 * forte, (r, g, b), .8, alvo)
    luz_area('topo', (0, 0, 5), 60 * forte, (.7, .75, .9), 1.5, (0, 0, 0))


def camera(elev_graus=6.0, alvo_z=.95, escala=2.4, dist=12.0):
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = escala
    o = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(o)
    e = math.radians(elev_graus)
    o.location = (0, -dist * math.cos(e), alvo_z + dist * math.sin(e))
    mirar(o, (0, 0, alvo_z))
    bpy.context.scene.camera = o
    return o


_GPU = None


def _gpu():
    """Liga a placa de vídeo quando a variável BRASALUME_GPU pede (CUDA ou OPTIX); sem ela, CPU."""
    global _GPU
    if _GPU is not None:
        return _GPU
    _GPU = False
    import os
    tipo = os.environ.get('BRASALUME_GPU', '').upper()
    if not tipo:
        return False
    try:
        pref = bpy.context.preferences.addons['cycles'].preferences
        pref.compute_device_type = tipo
        (getattr(pref, 'refresh_devices', None) or pref.get_devices)()
        n = 0
        for d in pref.devices:
            d.use = d.type == tipo
            n += d.use
        _GPU = n > 0
        print('GPU', tipo, 'dispositivos:', n, flush=True)
    except Exception as e:
        print('GPU indisponível:', e, flush=True)
    return _GPU


def config_render(w, h, amostras=64, transparente=True):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        sc.cycles.device = 'GPU' if _gpu() else 'CPU'
    except Exception:
        pass
    import os
    if os.environ.get('BRASALUME_PREVIA'):
        # prévia rápida para conferir modelagem: metade da resolução e poucas amostras
        w, h, amostras = w // 2, h // 2, min(amostras, 16)
        sc.cycles.samples = amostras
    if os.environ.get('BRASALUME_THREADS'):
        # deixa núcleos livres quando outro Blender usa a placa de vídeo ao mesmo tempo
        sc.render.threads_mode = 'FIXED'
        sc.render.threads = int(os.environ['BRASALUME_THREADS'])
    sc.cycles.samples = amostras
    sc.cycles.use_denoising = True
    try:
        sc.cycles.max_bounces = 6
        sc.cycles.transparent_max_bounces = 8
    except Exception:
        pass
    sc.render.film_transparent = transparente
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Punchy'
    except Exception:
        try:
            sc.view_settings.look = 'Punchy'
        except Exception:
            pass


def render(caminho):
    import os
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    bpy.context.scene.render.filepath = caminho
    bpy.ops.render.render(write_still=True)
