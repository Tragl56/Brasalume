# Construtor de monstros do Brasalume no Blender: uma base por família visual do jogo (KINDS) e traços por nome,
# para que inimigos da mesma família continuem distinguíveis. Desenhos originais. O monstro olha para +X.
# Cavaleiros usam as peças de armadura do kit dos heróis (mesmo mundo, mesma escala); golens são rocha lascada;
# voadores, feras, serpentes, espectros, esqueletos e treants têm anatomia própria.
import math
import json
import os
import unicodedata
import bpy
from mathutils import Vector, Quaternion, noise as _noise
from kit_base import mat, shade, mix, sph, cyl, caps, box, torus, tubo, poly, casca, cupula, raiz, luz_ponto, V, U, _link, parte, hex_lin, _inp
import kit_base as K
from kit_heroi import grupo

AQUI = os.path.dirname(os.path.abspath(__file__))


def _sem_acento(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii').lower()


def _semente(nome):
    return sum(ord(c) * (i + 1) for i, c in enumerate(nome)) % 997


TEMAS = [  # palavra no nome → tema de material e efeito
    (('gelo', 'gelid', 'nevasca', 'inverno', 'degelo', 'branco'), 'gelo'),
    (('vitral', 'prism', 'espelh', 'cristal', 'vidro', 'quartzo'), 'vidro'),
    (('obsidiana',), 'obsidiana'),
    (('piche', 'breu', 'lodo', 'lama'), 'piche'),
    (('ambar', 'solar', 'dourad', 'tesouro', 'mel', 'colmeia', 'zangao'), 'ambar'),
    (('brasa', 'escoria', 'fagulha', 'forj', 'ferreiro', 'salamandra', 'carvao', 'cinzas', 'fuligem', 'fume'), 'brasa'),
    (('nevoa', 'espectro', 'eco', 'sombra', 'vazio', 'fatuo', 'noite', 'crepusculo', 'apagador'), 'sombra'),
    (('musgo', 'raiz', 'broto', 'esporo', 'casca', 'alvorada'), 'musgo'),
    (('ossud', 'esqueleto', 'osso', 'cripta', 'catacumba'), 'osso'),
    (('afogad', 'marujo', 'capitao', 'coral', 'medusa', 'polvo', 'enguia', 'imediato', 'naufragio', 'leviata'), 'mar'),
    (('granito', 'cascalho', 'pedra', 'colosso'), 'pedra'),
]


def tema(nome):
    n = _sem_acento(nome)
    for chaves, t in TEMAS:
        if any(k in n for k in chaves):
            return t
    return ''


def pele(cor, t, base='cloth'):
    """Material principal do monstro conforme o tema do nome."""
    if t == 'gelo':
        return mat('glass', mix(cor, '#e8f6ff', .35))
    if t == 'vidro':
        return mat('glass', cor)
    if t == 'obsidiana':
        return mat('gloss', shade(cor, -.35))
    if t == 'piche':
        return mat('gloss', shade(cor, -.25))
    if t == 'ambar':
        return mat('gloss', cor)
    if t == 'osso':
        return mat('bone', cor)
    if t == 'pedra':
        return mat('stone', cor)
    if t == 'sombra':   # quase opaco, com a borda acesa
        return espectral(cor, forca=1.1, a_centro=.82, a_borda=1.0)
    return mat(base, cor)


def olhos(R, pos, r, cor='#ffd24a', brilho=True, n=2, sep=None):
    sep = sep if sep is not None else r * 2.4
    for i in range(n):
        y = (i - (n - 1) / 2) * sep
        p = (pos[0], pos[1] + y, pos[2])
        if brilho:
            sph(p, r, mat('emit', cor, strength=14), parent=R)
        else:   # olho de bicho: bola escura e molhada, íris acesa e um ponto de luz (no lugar do olho branco de desenho animado)
            sph(p, r, mat('gloss', '#17110d'), parent=R)
            sph((p[0] + r * .66, p[1], p[2]), r * .56, mat('emit', cor, strength=4), scale=(.42, 1, 1), parent=R)
            sph((p[0] + r * .86, p[1] - r * .22, p[2] + r * .3), r * .15, mat('emit', '#fff6e0', strength=10), parent=R)


# ---------------- acabamento: superfície irregular, pelo de fios e corpo de fantasma ----------------
def relevo(o, forca=2.0, escala=8.0, sub=2, semente=0):
    """Superfície irregular (carne, gosma, chapéu de cogumelo, casco): subdivide a malha e empurra os vértices com um ruído preso
    à própria peça, que não escorrega quando a peça se mexe na animação. forca e escala em unidades do jogo."""
    if o.type != 'MESH':
        return o
    if sub:
        ss = o.modifiers.new('sub', 'SUBSURF')
        ss.levels = ss.render_levels = sub
    tx = bpy.data.textures.new('relevo', 'CLOUDS')
    tx.noise_scale = max(.01, escala * U * (1 + .09 * (semente % 5)))
    tx.noise_depth = 2
    try:
        tx.noise_basis = 'IMPROVED_PERLIN'
    except Exception:
        pass
    d = o.modifiers.new('relevo', 'DISPLACE')
    d.texture = tx
    d.texture_coords = 'LOCAL'
    d.strength = forca * U
    d.mid_level = .5
    return o


def mat_pelo(cor, nevoa=False):
    """Fios: raiz escura e ponta clara, cada fio num tom; com nevoa a ponta acende e some no ar (lobos de névoa)."""
    key = ('pelo', cor, nevoa)
    if key in K._MATS:
        return K._MATS[key]
    m = bpy.data.materials.new('pelo_' + cor)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    hi = nt.nodes.new('ShaderNodeHairInfo')
    grad = nt.nodes.new('ShaderNodeMix')
    grad.data_type = 'RGBA'
    grad.inputs[6].default_value = hex_lin(shade(cor, -.55))
    grad.inputs[7].default_value = hex_lin(mix(cor, '#ffffff', .1))
    nt.links.new(hi.outputs['Intercept'], grad.inputs[0])
    tom = nt.nodes.new('ShaderNodeMapRange')
    tom.inputs['To Min'].default_value, tom.inputs['To Max'].default_value = .74, 1.14
    nt.links.new(hi.outputs['Random'], tom.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs[0].default_value = 1.0
    nt.links.new(grad.outputs[2], mul.inputs[6])
    nt.links.new(tom.outputs['Result'], mul.inputs[7])
    nt.links.new(mul.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .55   # sem brilho acetinado: no Cycles 5.3 ele derruba o render de fios com transparência
    if nevoa:
        nt.links.new(mul.outputs[2], _inp(b, 'Emission Color'))
        fs = nt.nodes.new('ShaderNodeMapRange')
        fs.inputs['To Min'].default_value, fs.inputs['To Max'].default_value = .1, 1.6
        nt.links.new(hi.outputs['Intercept'], fs.inputs['Value'])
        nt.links.new(fs.outputs['Result'], _inp(b, 'Emission Strength'))
        al = nt.nodes.new('ShaderNodeMapRange')
        al.inputs['To Min'].default_value, al.inputs['To Max'].default_value = 1.0, .15
        nt.links.new(hi.outputs['Intercept'], al.inputs['Value'])
        nt.links.new(al.outputs['Result'], b.inputs['Alpha'])
    K._MATS[key] = m
    return m


def pelo(o, cor, comp=5.0, n=600, pente=(-1, 0, -.5), nevoa=False, raio=.45, solto=1.0, filhos=5):
    """Pelagem de fios de verdade (partículas de cabelo) numa peça de malha. comp: comprimento em unidades do jogo;
    pente: para onde o pelo deita, no espaço do monstro (+X é a frente, Z para cima)."""
    if o.type != 'MESH':
        return o
    o.data.materials.append(mat_pelo(cor, nevoa))
    ps = o.modifiers.new('pelo', 'PARTICLE_SYSTEM').particle_system
    st = ps.settings
    st.type = 'HAIR'
    st.count = n
    st.use_advanced_hair = True
    # no Blender o comprimento do fio é a soma das "velocidades" (em metros): um pouco na direção da normal e o resto deitado
    # na direção do pente (que vai para o espaço da peça); hair_length não entra, porque ele só reescreve a parte da normal
    L = comp * U
    q = o.rotation_quaternion if o.rotation_mode == 'QUATERNION' else o.rotation_euler.to_quaternion()
    d = q.inverted() @ Vector(pente)
    if d.length > 1e-6:
        d.normalize()
    st.normal_factor = L * .25   # pouco para fora: o pelo deita sobre o corpo e a silhueta continua a do bicho
    st.object_align_factor = d * L * .95
    st.factor_random = L * .14
    st.use_modifier_stack = True
    st.child_type = 'INTERPOLATED'
    st.rendered_child_count = filhos
    st.child_percent = 1
    st.clump_factor = .25
    st.roughness_1 = .012 * solto
    st.roughness_endpoint = .006 * solto
    st.root_radius, st.tip_radius, st.radius_scale = 1.0, 0.0, raio * U
    st.material = len(o.data.materials)
    return o


def espectral(cor, centro=None, forca=1.6, a_centro=.4, a_borda=.95):
    """Corpo de fantasma: no miolo o fundo aparece através dele, na borda ele acende (pela inclinação da superfície);
    um pouco de luz difusa por baixo para a forma não ficar chapada."""
    key = ('espectral', cor, centro, forca, a_centro, a_borda)
    if key in K._MATS:
        return K._MATS[key]
    m = bpy.data.materials.new('espectral_' + cor)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = .45
    cm = nt.nodes.new('ShaderNodeMix')
    cm.data_type = 'RGBA'
    cm.inputs[6].default_value = hex_lin(centro or shade(cor, -.2))
    cm.inputs[7].default_value = hex_lin(mix(cor, '#ffffff', .3))
    nt.links.new(lw.outputs['Facing'], cm.inputs[0])
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(cm.outputs[2], em.inputs['Color'])
    fs = nt.nodes.new('ShaderNodeMapRange')
    fs.inputs['To Min'].default_value, fs.inputs['To Max'].default_value = forca * .45, forca * 1.7
    nt.links.new(lw.outputs['Facing'], fs.inputs['Value'])
    nt.links.new(fs.outputs['Result'], em.inputs['Strength'])
    df = nt.nodes.new('ShaderNodeBsdfPrincipled')
    df.inputs['Base Color'].default_value = hex_lin(shade(centro or cor, -.3))
    df.inputs['Roughness'].default_value = .6
    ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(em.outputs[0], ad.inputs[0])
    nt.links.new(df.outputs[0], ad.inputs[1])
    al = nt.nodes.new('ShaderNodeMapRange')
    al.inputs['To Min'].default_value, al.inputs['To Max'].default_value = a_centro, a_borda
    nt.links.new(lw.outputs['Facing'], al.inputs['Value'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    ms = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(al.outputs['Result'], ms.inputs[0])
    nt.links.new(tr.outputs[0], ms.inputs[1])
    nt.links.new(ad.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs['Surface'])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    K._MATS[key] = m
    return m


def esclera(base='#ece2cc', veia='#b8342a'):
    """Branco do olho úmido com veias vermelhas finas e tortas: bordas de células distorcidas por ruído, que aparecem nos lados
    e no fundo do olho e somem perto da íris (a íris fica em +X)."""
    key = ('esclera', base, veia)
    if key in K._MATS:
        return K._MATS[key]
    m = bpy.data.materials.new('esclera')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9
    nz.inputs['Detail'].default_value = 4
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sm = nt.nodes.new('ShaderNodeVectorMath')   # posição torta pelo ruído: as veias serpenteiam
    sm.operation = 'MULTIPLY_ADD'
    sm.inputs[1].default_value = (.06, .06, .06)
    nt.links.new(nz.outputs['Color'], sm.inputs[0])
    nt.links.new(tc.outputs['Object'], sm.inputs[2])
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    vo.feature = 'DISTANCE_TO_EDGE'
    vo.inputs['Scale'].default_value = 9
    nt.links.new(sm.outputs[0], vo.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeMapRange')
    rp.inputs['From Min'].default_value, rp.inputs['From Max'].default_value = .004, .016
    rp.inputs['To Min'].default_value, rp.inputs['To Max'].default_value = .85, 0.0
    nt.links.new(vo.outputs['Distance'], rp.inputs['Value'])
    sx = nt.nodes.new('ShaderNodeSeparateXYZ')   # perto da íris (+X) não há veia
    nt.links.new(tc.outputs['Object'], sx.inputs[0])
    mk = nt.nodes.new('ShaderNodeMapRange')
    mk.inputs['From Min'].default_value, mk.inputs['From Max'].default_value = .02, .2
    mk.inputs['To Min'].default_value, mk.inputs['To Max'].default_value = 1.0, 0.0
    nt.links.new(sx.outputs['X'], mk.inputs['Value'])
    vm = nt.nodes.new('ShaderNodeMath')
    vm.operation = 'MULTIPLY'
    nt.links.new(rp.outputs['Result'], vm.inputs[0])
    nt.links.new(mk.outputs['Result'], vm.inputs[1])
    cm = nt.nodes.new('ShaderNodeMix')
    cm.data_type = 'RGBA'
    cm.inputs[6].default_value = hex_lin(base)
    cm.inputs[7].default_value = hex_lin(veia)
    nt.links.new(vm.outputs[0], cm.inputs[0])
    nt.links.new(cm.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .25
    _inp(b, 'Coat Weight').default_value = .7
    _inp(b, 'Coat Roughness').default_value = .05
    _inp(b, 'Subsurface Weight').default_value = .25
    K._MATS[key] = m
    return m


def vitral(cor):
    """Vitral: cacos de vidro colorido (cada um num tom em volta da cor) acesos por dentro, presos por filetes de chumbo escuro."""
    key = ('vitral', cor)
    if key in K._MATS:
        return K._MATS[key]
    m = bpy.data.materials.new('vitral')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vc = nt.nodes.new('ShaderNodeTexVoronoi')   # um tom por caco
    vc.inputs['Scale'].default_value = 9
    ve = nt.nodes.new('ShaderNodeTexVoronoi')   # distância até a borda do caco: o chumbo
    ve.feature = 'DISTANCE_TO_EDGE'
    ve.inputs['Scale'].default_value = 9
    nt.links.new(tc.outputs['Object'], vc.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], ve.inputs['Vector'])
    hs = nt.nodes.new('ShaderNodeHueSaturation')   # cada caco gira um pouco o matiz e muda o brilho da cor base
    hs.inputs['Color'].default_value = hex_lin(cor)
    hs.inputs['Saturation'].default_value = 1.25
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(vc.outputs['Color'], sep.inputs['Color'])
    mh = nt.nodes.new('ShaderNodeMapRange')
    mh.inputs['To Min'].default_value, mh.inputs['To Max'].default_value = .4, .6
    nt.links.new(sep.outputs[0], mh.inputs['Value'])
    nt.links.new(mh.outputs['Result'], hs.inputs['Hue'])
    mv = nt.nodes.new('ShaderNodeMapRange')
    mv.inputs['To Min'].default_value, mv.inputs['To Max'].default_value = .55, 1.35
    nt.links.new(sep.outputs[1], mv.inputs['Value'])
    nt.links.new(mv.outputs['Result'], hs.inputs['Value'])
    tom = hs
    chumbo = nt.nodes.new('ShaderNodeMapRange')
    chumbo.inputs['From Min'].default_value, chumbo.inputs['From Max'].default_value = .025, .05
    chumbo.inputs['To Min'].default_value, chumbo.inputs['To Max'].default_value = 1.0, 0.0
    nt.links.new(ve.outputs['Distance'], chumbo.inputs['Value'])
    cb = nt.nodes.new('ShaderNodeMix')
    cb.data_type = 'RGBA'
    nt.links.new(chumbo.outputs['Result'], cb.inputs[0])
    nt.links.new(tom.outputs[0], cb.inputs[6])
    cb.inputs[7].default_value = hex_lin('#16161a')
    nt.links.new(cb.outputs[2], b.inputs['Base Color'])
    nt.links.new(tom.outputs[0], _inp(b, 'Emission Color'))
    fe = nt.nodes.new('ShaderNodeMapRange')
    fe.inputs['To Min'].default_value, fe.inputs['To Max'].default_value = .75, 0.0
    nt.links.new(chumbo.outputs['Result'], fe.inputs['Value'])
    nt.links.new(fe.outputs['Result'], _inp(b, 'Emission Strength'))
    nt.links.new(chumbo.outputs['Result'], b.inputs['Metallic'])
    b.inputs['Roughness'].default_value = .12
    _inp(b, 'Coat Weight').default_value = .6
    K._MATS[key] = m
    return m


def tubo_malha(pts, r, m, radii=None, parent=None):
    """Tubo de malha (cones encadeados, com juntas redondas) por uma linha de pontos: como tubo(), mas recebe pelo.
    Devolve os cones. (Converter curva em malha pelo Blender derruba o programa sem janela depois de limpar a cena.)"""
    radii = radii or [1] * len(pts)
    cones = []
    for i in range(len(pts) - 1):
        r0, r1 = r * radii[i], r * radii[i + 1]
        cones.append(cyl(pts[i], pts[i + 1], r0, r1, m, verts=20, parent=parent))
        if 0 < i + 1 < len(pts) - 1:
            sph(pts[i + 1], r1, m, seg=16, ring=10, parent=parent)
    return cones


def espalhar(c, r, esc, n, semente=0, zmin=None, zmax=None, frente=None):
    """n pontos (posição e normal, em unidades do jogo) sobre a superfície de um elipsoide de centro c, raio r e escala esc
    (os mesmos números passados a sph): verrugas, bolhas, entulho, pintas. frente: só onde a normal aponta para +X acima disso."""
    import random
    rg = random.Random(semente)
    c = Vector(c)
    sx, sy, sz = esc
    pts = []
    tent = 0
    while len(pts) < n and tent < n * 60:
        tent += 1
        z = rg.uniform(-1, 1)
        a = rg.uniform(0, math.tau)
        s = math.sqrt(1 - z * z)
        nrm = Vector((s * math.cos(a), s * math.sin(a), z))
        p = Vector((nrm.x * r * sx, nrm.y * r * sy, nrm.z * r * sz)) + c
        if zmin is not None and p.z < zmin or zmax is not None and p.z > zmax or frente is not None and nrm.x < frente:
            continue
        nn = Vector((nrm.x / max(1e-6, sx), nrm.y / max(1e-6, sy), nrm.z / max(1e-6, sz))).normalized()
        pts.append((tuple(p), tuple(nn)))
    return pts


# ---------------- formas orgânicas ----------------
def rocha(loc, r, m, escala=(1, 1, 1), semente=0, aspereza=.3, sub=2, rot=(0, 0, 0), parent=None, liso=False):
    """Pedra irregular: icosfera deformada por ruído, facetada como rocha lascada."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r * U, location=V(loc), rotation=rot)
    o = bpy.context.object
    off = Vector((semente * 1.731 + .3, semente * 2.417 + .7, semente * 3.119 + .1))
    for v in o.data.vertices:
        d = _noise.fractal(v.co.normalized() * 1.8 + off, .7, 2.0, 3)
        v.co *= 1 + aspereza * max(-1.0, min(1.0, d))
    o.scale = escala
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = liso
    bv = o.modifiers.new('chanfro', 'BEVEL')
    bv.width = r * U * .05
    bv.segments = 2
    return _link(o, parent)


def tufo(p, d, m, r=2.2, parent=None):
    """Mecha de pelo ou fiapo: sai de p na direção d (vetor em unidades do jogo), afinando."""
    a = Vector(p)
    b = a + Vector(d) * .55 + Vector((0, 0, -abs(d[2]) * .15))
    c = a + Vector(d)
    tubo([tuple(a), tuple(b), tuple(c)], r, m, radii=[1, .6, .08], parent=parent, res=3)


def chama(R, base, alt, cor, r=6, n=5, parent=None, forca=8):
    """Língua de fogo: cones finos e torcidos que sobem da base."""
    e = mat('emit', cor, strength=forca, alpha=.85)
    for i in range(n):
        a = i / n * math.tau
        x, y = base[0] + math.cos(a) * r * .5, base[1] + math.sin(a) * r * .5
        h = alt * (.6 + .4 * ((i * 7) % 5) / 4)
        tubo([(x, y, base[2]), (x + math.cos(a + 1) * 2, y + math.sin(a + 1) * 2, base[2] + h * .5), (x - math.cos(a) * 1.5, y, base[2] + h)],
             r * .55, e, radii=[1, .6, .05], parent=parent or R, res=3)


def marca(R, papel, raio):
    """Círculo de runas no chão para chefes (ouro), errantes (roxo), subchefes (prata) e chefes de masmorra (brasa)."""
    if not papel:
        return
    cor = {'boss': '#e8c45a', 'field': '#c792ee', 'mini': '#c8d0d8', 'dboss': '#ff8a4a'}[papel]
    e = mat('emit', cor, strength=3.2 if papel != 'mini' else 2.2)
    torus((0, 0, .3), raio, .5, e, scale=(1, 1, .25), parent=R)
    torus((0, 0, .3), raio * .84, .32, e, scale=(1, 1, .25), parent=R)
    for i in range(16):
        a = i / 16 * math.tau
        comp = 4.5 if i % 4 == 0 else 2.2
        box((math.cos(a) * raio * .92, math.sin(a) * raio * .92, .3), (comp, 1.1, .25), e, rot=(0, 0, a + math.pi / 2), bevel=0, parent=R)
    if papel != 'mini':
        luz_ponto((0, 0, 5), 50, cor, raio=.8, parent=R)


def efeitos(R, nome, cor, t, topo):
    """Traços do tema para as famílias simples: espinhos de gelo, cristais, rachaduras em brasa, musgo, algas, gotas."""
    if t == 'gelo':
        g = mat('glass', '#d8f2ff')
        for i in range(5):
            a = i / 5 * math.tau
            cyl((math.cos(a) * 10, math.sin(a) * 10, topo * .75), (math.cos(a) * 13, math.sin(a) * 13, topo * .75 + 9), 2.2, .1, g, parent=R)
        luz_ponto((10, 0, topo * .7), 12, '#a8e4ff', parent=R)
    elif t in ('vidro', 'obsidiana'):
        g = mat('glass', '#c8b8ff' if t == 'obsidiana' else '#bff0f0')
        for i in range(4):
            a = i / 4 * math.tau + .4
            cyl((math.cos(a) * 9, math.sin(a) * 9, topo * .8), (math.cos(a) * 11, math.sin(a) * 11, topo * .8 + 11), 2.4, .1, g, parent=R)
    elif t == 'brasa':
        e = mat('emit', '#ff7a30', strength=10)
        for i in range(3):
            a = i * 2.1
            tubo([(math.cos(a) * 12, math.sin(a) * 12, topo * .3), (math.cos(a) * 13, math.sin(a) * 13, topo * .5), (math.cos(a + .3) * 12, math.sin(a + .3) * 12, topo * .7)], .5, e, parent=R)
        luz_ponto((8, 0, topo * .5), 30, '#ff7a30', raio=.2, parent=R)
    elif t == 'musgo':
        m = mat('fur', '#5f8a4a')
        for i in range(6):
            a = i / 6 * math.tau
            sph((math.cos(a) * 9, math.sin(a) * 9, topo * .85), 4, m, scale=(1, 1, .45), parent=R)
    elif t == 'mar':
        alga = mat('cloth', '#3f6a4a')
        for i in range(3):
            a = i * 2.2 + .3
            tubo([(math.cos(a) * 11, math.sin(a) * 11, topo * .7), (math.cos(a) * 13, math.sin(a) * 13, topo * .45), (math.cos(a) * 12, math.sin(a) * 12, topo * .25)], .9, alga, parent=R)
        for i in range(4):
            a = i * 1.6
            sph((math.cos(a) * 10, math.sin(a) * 10, topo * .55), 1.6, mat('stone', '#cfc8b0'), parent=R)   # cracas
    elif t == 'piche':
        p = mat('gloss', '#14181e')
        for i in range(5):
            a = i / 5 * math.tau
            sph((math.cos(a) * 14, math.sin(a) * 14, 1.5), 3.4, p, scale=(1, 1, .4), parent=R)
    elif t == 'ambar':
        luz_ponto((8, 0, topo * .6), 14, '#ffc050', parent=R)
    elif t == 'sombra':
        luz_ponto((6, 0, topo * .55), 18, cor, raio=.3, parent=R)


# ---------------- famílias simples (gosmas, águas-vivas, olhos, baús...) ----------------
def _na_casca(c, r, esc, z, a, fora=0.0):
    """Ponto na superfície do elipsoide (centro c, raio r, escala esc) na altura z e no ângulo a; fora afasta da superfície."""
    k = max(0.0, 1 - ((z - c[2]) / (r * esc[2])) ** 2) ** .5
    return (c[0] + math.cos(a) * (r * esc[0] * k + fora), c[1] + math.sin(a) * (r * esc[1] * k + fora), z)


def cranio(p, nrm, r, osso, escuro, parent):
    """Crânio pequeno meio afundado (na gosma, no lodo), olhando para fora na direção nrm."""
    nv = Vector(nrm).normalized()
    c = Vector(p) - nv * r * .3
    sph(tuple(c), r, osso, scale=(1, .92, .95), parent=parent)
    lado = nv.cross(Vector((0, 0, 1)))
    lado = lado.normalized() if lado.length > .1 else Vector((0, 1, 0))
    for s in (-1, 1):
        sph(tuple(c + nv * r * .76 + lado * s * r * .38 + Vector((0, 0, r * .12))), r * .3, escuro, parent=parent)
    sph(tuple(c + nv * r * .86 - Vector((0, 0, r * .28))), r * .13, escuro, parent=parent)
    for k in range(4):   # dentes de cima
        q = c + nv * r * .8 + lado * (k - 1.5) * r * .2 - Vector((0, 0, r * .55))
        cyl(tuple(q), tuple(q - Vector((0, 0, r * .25))), r * .07, r * .05, osso, parent=parent)


def osso_solto(p, d, comp, r, osso, parent):
    """Osso comprido saindo de p na direção d, com as duas cabeças."""
    a = Vector(p)
    b = a + Vector(d).normalized() * comp
    cyl(tuple(a), tuple(b), r, r * .85, osso, parent=parent)
    lado = Vector(d).normalized().cross(Vector((0, 0, 1)))
    lado = lado.normalized() if lado.length > .1 else Vector((0, 1, 0))
    for q in (a, b):
        for s in (-1, 1):
            sph(tuple(q + lado * s * r * .7), r * 1.05, osso, parent=parent)


def F_blob(R, nome, cor, t):
    """Gosmas, lodos, sapos e o polvo de lama: geleia viva de superfície irregular sobre uma poça, escorrendo pelos lados,
    com o que ela engoliu meio afundado (ossos, pedras, um crânio) ou coberta de musgo."""
    n = _sem_acento(nome)
    sem = _semente(n)
    sapo, musgo, polvo = 'sapo' in n, ('musgo' in n or 'brotinho' in n), 'polvo' in n
    mae = 'mae' in n or 'rainha' in n
    base_cor = shade(cor, -.12) if t == 'piche' else cor
    corpo = mat('gosma', base_cor)
    escuro = mat('gloss', '#100a08')
    osso = mat('bone', '#d8ccb0')
    c, rc = (0, 0, 26), 30
    esc = (1.16, 1.0, .84) if not sapo else (1.1, 1.0, .9)
    o = sph(c, rc, corpo, scale=esc, parent=R)
    relevo(o, forca=5.5, escala=15, semente=sem)
    saia = sph((0, 0, 8), rc * 1.02, corpo, scale=(1.26, 1.14, .3), parent=R)   # a base cede com o peso e se esparrama
    relevo(saia, forca=3.5, escala=10, semente=sem + 7)
    poca = sph((0, 0, 1.0), 33, mat('skin', shade(base_cor, -.62)), scale=(1.16, 1.06, .04), parent=R)   # mancha úmida e fosca no chão
    relevo(poca, forca=3, escala=11, semente=sem + 1)
    for i in range(8):   # escorridos descendo pelo corpo até a base
        a = i / 8 * math.tau + (sem % 7) * .3
        z0, z1 = c[2] + 2 - (i % 3) * 4, c[2] - 12 - (i % 2) * 2
        p0, p1 = _na_casca(c, rc, esc, z0, a, -.4), _na_casca(c, rc, esc, z1, a, .2)
        pm = _na_casca(c, rc, esc, (z0 + z1) / 2, a, .9)
        tubo([p0, pm, p1], 1.8 + (i % 3) * .5, corpo, radii=[.5, .9, 1.2], parent=R)
    for (p, nn) in espalhar(c, rc, esc, 9, semente=sem + 2, zmin=c[2] - 6):   # bolhas presas na película
        sph(tuple(Vector(p) + Vector(nn) * .6), 1.4 + (sem + int(p[1])) % 3 * .7, mat('glass', mix(cor, '#ffffff', .6)), parent=R)
    # rosto: olhos miúdos e úmidos, boca larga e escura de onde pinga baba
    zo = c[2] + 9
    for s in (-1, 1):
        p = _na_casca(c, rc, esc, zo, s * .3, -1.2)
        olhos(R, p, 3.2 if not mae else 3.8, cor='#e8d05a' if t != 'piche' else '#c8f070', brilho=False, n=1)
    pb = _na_casca(c, rc, esc, c[2] - 3, 0, -1.6)
    sph(pb, 6.4, escuro, scale=(.34, 1.7, .42), parent=R)
    for y in (-5, 0, 4):
        q = (pb[0] + .6, y, pb[2] - 1.6)
        tubo([q, (q[0] + 1.6, y * 1.05, q[2] - 5), (q[0] + 1.2, y, q[2] - 9 - abs(y) * .4)], .55, corpo, radii=[1, .5, .9], parent=R)
    if not sapo and not musgo and not polvo:   # o que o lodo engoliu: ossos, pedras e um crânio
        pts = espalhar(c, rc, esc, 7, semente=sem + 3, zmin=c[2] - 2, frente=-.2)
        for k, (p, nn) in enumerate(pts):
            if k == 0:
                cranio(p, nn, 5.6, osso, escuro, R)
            elif k < 4:
                osso_solto(tuple(Vector(p) - Vector(nn) * 3), (nn[0] + .6, nn[1], nn[2] + .3), 11, 1.1, osso, R)
            else:
                rocha(p, 3.2, mat('stone', '#5a5248'), semente=sem + k, parent=R)
        if mae:   # a mãe: lâmina enferrujada atravessada e três filhotes em volta
            box((-6, -14, 50), (2, 5, 30), mat('metal', '#6a5a4a', rough=.75), rot=(.5, .3, .2), bevel=.4, parent=R)
            box((-10, -18, 37), (3, 14, 2.4), mat('metal', '#4a3e34', rough=.7), rot=(.5, .3, .2), bevel=.4, parent=R)
            for k in range(3):
                a = 2.2 + k * .9
                pf = (math.cos(a) * 46, math.sin(a) * 40, 7)
                f = sph(pf, 7.5, corpo, scale=(1.1, 1, .8), parent=R)
                relevo(f, forca=2, escala=7, semente=sem + 10 + k)
                olhos(R, (pf[0] + 7, pf[1], pf[2] + 2), 1.4, cor='#c8f070', brilho=False, sep=4)
    if sapo:   # sapo: olhos no alto da cabeça, beiço largo, verrugas e barbilhões
        for y in (-12, 12):
            sph((14, y, 50), 6.4, corpo, parent=R)
            olhos(R, (19.5, y, 52), 3.4, cor='#e8c45a', brilho=False, n=1)
        sph((24, 0, 27), 18, escuro, scale=(.18, 1.3, .1), rot=(0, -.2, 0), parent=R)   # risca da boca larga
        for (p, nn) in espalhar(c, rc, esc, 16, semente=sem + 4, zmin=c[2] + 2):
            sph(tuple(Vector(p) + Vector(nn) * .4), 1.6 + (int(p[0] * 7) % 3) * .5, mat('gosma', shade(base_cor, -.3)), scale=(1, 1, .6), parent=R)
        if 'velho' in n:
            for y in (-6, 6):   # barbilhões de bagre velho
                tubo([(30, y, 22), (34, y * 1.3, 14), (32, y * 1.5, 6)], .8, corpo, radii=[1, .7, .2], parent=R)
            for (p, nn) in espalhar(c, rc, esc, 4, semente=sem + 5, zmin=c[2] + 8, frente=-.6):
                m = sph(p, 7, mat('fur', '#4f6a3a'), scale=(1, 1, .3), parent=R)
                pelo(m, '#6a8a44', comp=1.6, n=260, pente=(0, 0, 1))
        else:
            sph((-4, 0, 58), 4, mat('emit', '#ffd96a', strength=12), parent=R)         # lampião na cabeça
            cyl((-4, 0, 50), (-4, 0, 56), .6, .6, mat('wood', '#4a3a2a'), parent=R)
            torus((-4, 0, 58), 4.2, .4, mat('metal', '#4a3e30', rough=.6), rot=(math.pi / 2, 0, 0), parent=R)
            luz_ponto((-4, 0, 60), 20, '#ffd96a', parent=R)
    if polvo:
        for i in range(6):
            a = i / 6 * math.tau
            with parte(R, 'tent', (math.cos(a) * 20, math.sin(a) * 20, 8), ang=a, fase=i / 6, amp=.16):
                tb = tubo([(math.cos(a) * 20, math.sin(a) * 20, 8), (math.cos(a) * 32, math.sin(a) * 32, 4), (math.cos(a + .4) * 38, math.sin(a + .4) * 38, 1)], 3.4, corpo, radii=[1, .7, .3], parent=R)
                for k in range(4):   # ventosas
                    u = .25 + k * .17
                    sph((math.cos(a + u * .4) * (20 + 18 * u), math.sin(a + u * .4) * (20 + 18 * u), 8 - 7 * u - 1.6), 1.1 - k * .15, mat('skin', mix(cor, '#e8c0b0', .5)), parent=R)
    if musgo:   # tapete de musgo no alto, brotos e florzinhas
        tampa = sph((0, 0, c[2] + 13), rc * .86, mat('fur', '#4f6a3a'), scale=(1.12, 1, .42), parent=R)
        relevo(tampa, forca=3, escala=9, semente=sem + 6)
        pelo(tampa, '#7a9a4a', comp=1.7 if not mae else 2.1, n=1600 if mae else 1100, pente=(0, 0, 1), solto=1.6)
        for i in range(6 if not mae else 9):
            a = i / (6 if not mae else 9) * math.tau + .4
            b0 = (math.cos(a) * 12, math.sin(a) * 11, c[2] + 22)
            tubo([b0, (b0[0] * 1.2, b0[1] * 1.2, b0[2] + 8), (b0[0] * 1.5, b0[1] * 1.5, b0[2] + 12)], 1.1, mat('cloth', '#6a9a4a'), radii=[1, .8, .3], parent=R)
            poly([(b0[0] * 1.5, b0[1] * 1.5, b0[2] + 12), (b0[0] * 1.9, b0[1] * 1.6 + 2, b0[2] + 14), (b0[0] * 1.7, b0[1] * 1.9, b0[2] + 11)], mat('cloth', '#7aaa50'), esp=.3, parent=R)
        for i in range(5 if not mae else 10):
            a = i * 2.39
            sph((math.cos(a) * 18, math.sin(a) * 16, c[2] + 20 - (i % 3) * 2), 1.5, mat('emit', '#f0e0a0' if mae else '#e8f0c0', strength=3), parent=R)
        if mae:   # rainha: coroa de cogumelos e esporos acesos
            for i in range(7):
                a = i / 7 * math.tau
                bc = (math.cos(a) * 9, math.sin(a) * 8, c[2] + 24)
                cyl(bc, (bc[0], bc[1], bc[2] + 7 + (i % 2) * 3), 1.4, 1.1, mat('skin', '#e8dcc0'), parent=R)
                sph((bc[0], bc[1], bc[2] + 8 + (i % 2) * 3), 3.4, mat('cloth', '#c86a4a'), scale=(1, 1, .5), parent=R)
            luz_ponto((0, 0, c[2] + 30), 25, '#f0e0a0', parent=R)
    return 60


def F_jelly(R, nome, cor, t):
    n = _sem_acento(nome)
    z = 70
    sino = espectral(cor, forca=1.6, a_centro=.3, a_borda=.95) if t not in ('piche',) else espectral(cor, centro=shade(cor, -.6), forca=1.0, a_centro=.8, a_borda=1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=26 * U, location=V((0, 0, z)))
    o = bpy.context.object
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(o.data)
    _bm.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -2 * U], context='VERTS')
    bm.to_mesh(o.data); bm.free()
    sd = o.modifiers.new('esp', 'SOLIDIFY'); sd.thickness = 2 * U
    o.data.materials.append(sino)
    o.parent = R
    for p in o.data.polygons:
        p.use_smooth = True
    sph((0, 0, z + 7), 7, mat('emit', mix(cor, '#ffffff', .25), strength=5 if 'lanterna' in n else 2.5), scale=(1, 1, .7), parent=R)   # núcleo aceso, pequeno
    for i in range(10):
        a = i / 10 * math.tau
        r = 18 + (i % 2) * 4
        with parte(R, 'tent', (math.cos(a) * r, math.sin(a) * r, z), ang=a, fase=(i * .3) % 1, amp=.2):
            tubo([(math.cos(a) * r, math.sin(a) * r, z), (math.cos(a) * r * 1.1, math.sin(a) * r * 1.1, z - 18), (math.cos(a + .3) * r, math.sin(a + .3) * r, z - 38), (math.cos(a) * r * .9, math.sin(a) * r * .9, z - 56)],
                 1.2, espectral(shade(cor, -.1), forca=1.3, a_centro=.35, a_borda=.85), radii=[1, .8, .5, .15], parent=R)
    for i in range(4):   # braços orais franzidos, no meio do sino
        a = i / 4 * math.tau + .4
        with parte(R, 'tent', (math.cos(a) * 5, math.sin(a) * 5, z - 1), ang=a, fase=(i * .37) % 1, amp=.12):
            tubo([(math.cos(a) * 5, math.sin(a) * 5, z - 1), (math.cos(a + .5) * 8, math.sin(a + .5) * 8, z - 14), (math.cos(a + 1.1) * 6, math.sin(a + 1.1) * 6, z - 26),
                  (math.cos(a + 1.6) * 8, math.sin(a + 1.6) * 8, z - 36)], 2.4, espectral(mix(cor, '#ffffff', .2), forca=1.4, a_centro=.25, a_borda=.8), radii=[1, .8, .6, .1], parent=R)
    if 'rainha' in n or 'profundezas' in n:
        for i in range(5):
            a = i / 5 * math.tau
            with parte(R, 'tent', (math.cos(a) * 8, math.sin(a) * 8, z - 2), ang=a, fase=i / 5, amp=.14):
                tubo([(math.cos(a) * 8, math.sin(a) * 8, z - 2), (math.cos(a) * 10, math.sin(a) * 10, z - 30), (math.cos(a + .6) * 6, math.sin(a + .6) * 6, z - 64)], 3, espectral(shade(cor, .3), forca=2.0, a_centro=.4, a_borda=.9), radii=[1, .7, .1], parent=R)
    olhos(R, (22, 0, z + 6), 2.6, brilho=False, sep=10)
    luz_ponto((0, 0, z), 40, cor, raio=.4, parent=R)
    return 96


def F_spider(R, nome, cor, t):
    n = _sem_acento(nome)
    sem = _semente(n)
    corpo = pele(cor, t, 'gloss')
    if t == 'obsidiana':   # vidro vulcânico: o abdome é lascado em facetas
        rocha((-14, 0, 30), 20, corpo, escala=(1.2, 1, .85), semente=sem, aspereza=.14, sub=2, parent=R)
        rocha((10, 0, 28), 12, corpo, semente=sem + 1, aspereza=.12, sub=2, parent=R)
        e = mat('emit', '#c86aff', strength=5)
        for (dy, dz) in ((-8, 6), (7, 9), (-2, -6)):   # veios acesos entre as facetas
            tubo([(-2, 0, 34), (-10, dy * .6, 34 + dz * .6), (-20, dy, 34 + dz)], .5, e, radii=[1, .6, .15], parent=R)
    else:
        abd = sph((-14, 0, 30), 20, corpo, scale=(1.2, 1, .85), parent=R)
        cef = sph((10, 0, 28), 12, corpo, parent=R)
        relevo(abd, forca=1.6, escala=7, sub=1, semente=sem)
        if t != 'vidro':   # cerdas pelo corpo
            pelo(abd, shade(cor, -.2), comp=1.5, n=900, pente=(-1, 0, .1), raio=.35, solto=1.4)
            pelo(cef, shade(cor, -.2), comp=1.2, n=360, pente=(-1, 0, .3), raio=.35)
            for d in (6, 0, -6, -12):   # listras claras em volta do abdome
                k = (1 - (d / 24) ** 2) ** .5
                torus((-14 + d, 0, 30), 20 * k + .2, 1.1, mat('fur', mix(cor, '#e8dcc0', .45)), rot=(0, math.pi / 2, 0), scale=(.85, 1, 1.6), parent=R)
    if 'viuva' in n:
        sph((-14, 0, 47), 4, mat('emit', '#ff3a4a', strength=10), scale=(1, .6, 1.6), parent=R)
    if 'rainha' in n or 'matriarca' in n:
        for i in range(5):
            a = -1 + i * .5
            cyl((-14 + math.cos(a) * 12, math.sin(a) * 14, 44), (-16 + math.cos(a) * 14, math.sin(a) * 18, 58), 3, .1, mat('glass', '#d8b8ff'), parent=R)
    for i in range(4):
        for s in (-1, 1):
            x = 8 - i * 6
            with parte(R, 'perna', (x, s * 8, 28), eixo='Z', amp=.26, fase=.5 * ((i + (s > 0)) % 2)):
                joelho = (x + 4 - i * 3, s * (24 + i * 4), 50 - i * 4)
                tubo([(x, s * 8, 28), joelho, (x + 8 - i * 6, s * (36 + i * 5), 1)], 2.2, mat('gloss', shade(cor, -.4)), radii=[1, .8, .4], parent=R)
                sph(joelho, 2.6, mat('gloss', shade(cor, -.25)), parent=R)   # junta
    for (x, y, z) in ((21, -3, 31), (21, 3, 31), (20, -6, 27), (20, 6, 27)):
        sph((x, y, z), 1.6, mat('emit', '#ff4a3a', strength=14), parent=R)
    for s in (-1, 1):
        cyl((20, s * 3, 22), (24, s * 2, 15), 1.4, .1, mat('bone', '#e8dcc0'), parent=R)
    return 58


def F_mushroom(R, nome, cor, t):
    """Cogumelos que andam: pé grosso e torto com o rosto (visível de cima, abaixo da aba), saia esfarrapada, chapéu irregular
    de borda grossa com lamelas escuras por baixo e verrugas por cima."""
    n = _sem_acento(nome)
    sem = _semente(n)
    cristal, venenoso, guardiao = 'cristal' in n, 'venenoso' in n, 'guardiao' in n
    carne = mat('skin', '#d4c4a2')
    escuro = mat('gloss', '#120c08')
    pe = cyl((0, 0, 3), (1.5, 0, 31), 13.5, 10.5, carne, verts=28, parent=R)
    relevo(pe, forca=1.8, escala=5, semente=sem)
    bulbo = sph((0, 0, 7), 15.5, carne, scale=(1.08, 1, .55), parent=R)
    relevo(bulbo, forca=2.2, escala=7, semente=sem + 1)
    for i in range(7):   # raízes finas entrando no chão
        a = i / 7 * math.tau + .3
        tubo([(math.cos(a) * 12, math.sin(a) * 12, 4), (math.cos(a) * 18, math.sin(a) * 18, 2), (math.cos(a + .25) * 24, math.sin(a + .25) * 24, 0)],
             1.2, carne, radii=[1, .6, .2], parent=R)
    casca(31, 23, 10.6, 15.5, -math.pi, math.pi, mat('cloth', '#e6d8b8'), esp=.7, segs=30, rings=4, dobras=1.1, rasgos=3.4, parent=R)   # saia
    # chapéu: meia esfera achatada e irregular, um pouco inclinada para a frente
    chapeu = mat('glass', cor) if cristal else mat('cloth', cor)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=26 * U, location=V((1, 0, 31)), rotation=(0, .12, 0))
    o = bpy.context.object
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(o.data)
    _bm.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1 * U], context='VERTS')
    bm.to_mesh(o.data); bm.free()
    o.scale = (1, 1, .74)
    sd = o.modifiers.new('esp', 'SOLIDIFY'); sd.thickness = 3 * U
    o.data.materials.append(chapeu)
    o.parent = R
    for p in o.data.polygons:
        p.use_smooth = True
    relevo(o, forca=2.8, escala=9, sub=1, semente=sem + 2)
    torus((1, 0, 31), 25.6, 2.4, chapeu, rot=(0, .12, 0), scale=(1, 1, .7), parent=R)                  # borda grossa, enrolada
    gl = grupo((1, 0, 31), rot=(0, .12, 0), parent=R)   # lamelas, com a mesma inclinação do chapéu
    casca(.5, -1.5, 24.5, 10.5, -math.pi, math.pi, mat('cloth', shade(cor, -.55)), esp=.6, segs=40, rings=2, dobras=.9, parent=gl)
    if cristal:   # núcleo aceso dentro do chapéu de vidro e lascas no topo
        sph((1, 0, 38), 12, mat('emit', mix(cor, '#ffffff', .4), strength=6), scale=(1, 1, .6), parent=R)
        for i in range(5):
            a = i / 5 * math.tau + .5
            cyl((math.cos(a) * 9, math.sin(a) * 9, 44), (math.cos(a) * 13, math.sin(a) * 13, 55 + (i % 2) * 5), 2.6, .1, mat('glass', mix(cor, '#ffffff', .5)), parent=R)
        luz_ponto((1, 0, 40), 30, mix(cor, '#ffffff', .4), raio=.3, parent=R)
    else:
        pinta = mat('emit', '#b46ae8', strength=5) if venenoso else mat('skin', '#efe4cc')
        for (p, nn) in espalhar((1, 0, 31), 26, (1, 1, .74), 13 if venenoso else 10, semente=sem + 3, zmin=38):
            pp = Vector(p) + Vector(nn) * .8
            v = sph(tuple(pp), 3.2 + (int(p[0] * 3 + p[1]) % 3) * .8, pinta, scale=(1, 1, .45), parent=R)
            v.rotation_mode = 'QUATERNION'
            v.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(nn))
            relevo(v, forca=.8, escala=2.5, sub=1, semente=sem + int(p[1]))
    if venenoso:   # veneno pingando da aba
        gota = mat('emit', '#a8e05a', strength=4)
        for i in range(6):
            a = i / 6 * math.tau + .2
            x, y = 1 + math.cos(a) * 25, math.sin(a) * 25
            tubo([(x, y, 29.5), (x * 1.02, y * 1.02, 26), (x * 1.02, y * 1.02, 23 - (i % 3) * 2)], .7, gota, radii=[1, .5, .9], parent=R)
        luz_ponto((6, 0, 22), 14, '#a8e05a', parent=R)
    # rosto no pé, abaixo da aba: sobrancelha, olhos miúdos e boca rasgada
    rocha((12.2, 0, 22.5), 4, carne, escala=(.5, 2.1, .45), semente=sem + 4, parent=R)
    olhos(R, (11.6, 0, 18.5), 2.3, cor='#f0b040' if not venenoso else '#c8f070', brilho=False, sep=7.4)
    sph((12.6, 0, 11), 4.6, escuro, scale=(.3, 1.25, .42), parent=R)
    if guardiao or venenoso:
        for k in range(5):
            y = -3.6 + k * 1.8
            cyl((13.6, y, 12.6), (13.8, y, 10.8), .55, .1, mat('bone', '#efe4cc'), parent=R)
    for s in (-1, 1):
        with parte(R, 'braco', (0, s * 11, 18), fase=.5 if s > 0 else 0, amp=.35, atk=-.9):
            caps((0, s * 11, 18), (5, s * 16, 8), 2.8, carne, parent=R)   # bracinhos com dedos de raiz
            for k in range(3):
                tubo([(5, s * 16, 8), (7 + k, s * (15 + k * 1.6), 4), (8 + k, s * (15 + k * 1.8), 1.6)], .7, carne, radii=[1, .6, .2], parent=R)
    if guardiao:   # escudo de casca e lança
        with parte(R, 'braco', (0, 11, 18), fase=.5, amp=.35, atk=-.9):
            g = grupo((8, 19, 12), rot=(0, math.pi / 2 - .15, .35), parent=R)
            cyl((0, 0, -1.2), (0, 0, 1.2), 11, 10.4, mat('wood', '#5a4026'), parent=g)
            torus((0, 0, 1.2), 10.4, .9, mat('metal', '#6a6258', rough=.6), parent=g)
            sph((0, 0, 1.4), 3, mat('metal', '#7a7268', rough=.5), scale=(1, 1, .5), parent=g)
        with parte(R, 'braco', (0, -11, 18), fase=0, amp=.35, atk=-.9):
            cyl((6, -17, -2), (8, -17, 52), 1.2, 1.1, mat('wood', '#4a3622'), parent=R)
            cyl((8, -17, 52), (8.4, -17, 60), 2.2, .1, mat('metal', '#8a8478', rough=.4), parent=R)
    if 'saltitante' in n:   # broto teimoso no alto do chapéu
        tubo([(2, 0, 49), (4, 1, 55), (7, 2, 58)], .7, mat('cloth', '#6a9a4a'), parent=R)
        poly([(7, 2, 58), (12, 5, 61), (11, 0, 59)], mat('cloth', '#7aaa50'), esp=.3, parent=R)
    return 58


def F_imp(R, nome, cor, t):
    n = _sem_acento(nome)
    corpo = pele(cor, t, 'skin')
    z = 40
    sph((0, 0, z), 10, corpo, scale=(.9, .9, 1.3), parent=R)
    sph((2, 0, z + 18), 10, corpo, parent=R)
    for s in (-1, 1):
        cyl((-2, s * 6, z + 25), (-6, s * 9, z + 36), 2.4, .1, mat('bone', '#f3e6c8'), parent=R)
        with parte(R, 'asa', (-2, s * 4, z + 10), s=s, amp=.6):
            poly([(-2, s * 4, z + 10), (-10, s * 26, z + 24), (-6, s * 20, z + 4)], mat('leather', shade(cor, -.35)), esp=.6, parent=R)
        with parte(R, 'perna', (0, s * 5, z - 10), fase=.5 if s > 0 else 0, amp=.16):
            caps((0, s * 5, z - 10), (2, s * 6, 18), 2.4, corpo, parent=R)
        with parte(R, 'braco', (2, s * 9, z + 6), fase=.5 if s > 0 else 0, amp=.25, atk=-1.0):
            caps((2, s * 9, z + 6), (8, s * 12, z - 4), 1.8, corpo, parent=R)
    with parte(R, 'cauda', (-8, 0, z - 4), amp=.3):
        tubo([(-8, 0, z - 4), (-20, 0, z - 10), (-24, 0, z + 2)], 1.4, corpo, parent=R)
        cyl((-24, 0, z + 2), (-27, 0, z + 6), 2.4, .1, corpo, parent=R)
    olhos(R, (10.6, 0, z + 20), 2, cor='#ffe07a', sep=6)
    box((11, 0, z + 13), (1, 6, 1), mat('gloss', '#1a0a08'), bevel=.3, parent=R)
    if 'colmeia' in n or 'rainha' in n:
        for x in (-4, 0, 4):
            torus((x, 0, z - 2), 9, 1.4, mat('cloth', '#1a1410'), rot=(0, math.pi / 2, 0), parent=R)
        sph((-12, 0, z - 8), 9, mat('gloss', cor), scale=(1.3, .9, .9), parent=R)
        for s in (-1, 1):
            with parte(R, 'asa', (-2, s * 4, z + 12), s=s, amp=.6, fase=.1):
                poly([(-2, s * 4, z + 12), (-14, s * 30, z + 30), (-22, s * 22, z + 12)], mat('glass', '#f0e6c8'), esp=.3, parent=R)
    if 'brasa' in n:
        chama(R, (2, 0, z + 27), 12, '#ff9a3a', r=5, n=4)
        luz_ponto((2, 0, z + 34), 20, '#ff8a3a', parent=R)
    if 'areia' in n:
        for i in range(6):
            a = i / 6 * math.tau
            sph((math.cos(a) * 14, math.sin(a) * 14, 4 + i), 1.2, mat('stone', '#c8a870'), parent=R)
    return 72


def F_plant(R, nome, cor, t):
    n = _sem_acento(nome)
    escuro = mat('cloth', shade(cor, -.35))
    for s in (-1, 1):
        poly([(0, 0, 2), (s * 6, s * 30, 6), (s * 2, s * 40, 2), (0, s * 8, 1)], escuro, esp=.8, parent=R)
        poly([(0, 0, 2), (s * -26, s * 8, 5), (s * -38, s * 2, 2), (0, s * 2, 1)], escuro, esp=.8, parent=R)
    with parte(R, 'caule', (0, 0, 0), amp=.07, atk=.3):   # o caule balança e dá o bote
        tubo([(0, 0, 0), (8, 0, 24), (-2, 0, 46), (-6, 0, 58)], 4, mat('cloth', shade(cor, -.15)), parent=R)
        for s in (-1, 1):   # cipós laterais com espinhos
            tubo([(2, s * 4, 30), (6, s * 18, 38), (12, s * 24, 32)], 1.4, mat('cloth', shade(cor, -.2)), radii=[1, .7, .3], parent=R)
        with parte(R, 'cabeca', (-4, 0, 56), amp=.12, fase=.25, atk=.25):
            cab = mat('cloth', cor)
            bulbo = sph((-6, 0, 64), 14, cab, scale=(1.1, 1, .8), parent=R)
            relevo(bulbo, forca=2.2, escala=7, sub=1, semente=_semente(n))
            sph((4, 0, 62), 9, mat('gloss', '#3a0f12'), scale=(.9, 1, .6), parent=R)
            for i in range(6):
                cyl((6 + (i % 3) * 3, -6 + i * 2.4, 66), (8 + (i % 3) * 3, -6 + i * 2.4, 61), 1, .1, mat('bone', '#f4ecd8'), parent=R)
            if 'melifera' in n or 'alvorada' in n:
                for i in range(5):
                    a = i / 5 * math.tau
                    sph((-6 + math.cos(a) * 14, math.sin(a) * 14, 72), 4, mat('emit', '#ffd070' if 'alvorada' in n else '#e0a030', strength=4), scale=(1, 1, .4), parent=R)
                luz_ponto((-6, 0, 80), 20, '#ffd070', parent=R)
    if 'esporo' in n:
        for i in range(8):
            a = i / 8 * math.tau
            sph((math.cos(a) * 26, math.sin(a) * 26, 60 + (i % 3) * 10), 1.4, mat('emit', '#c8a0f0', strength=10), parent=R)
    return 80


def F_crab(R, nome, cor, t):
    n = _sem_acento(nome)
    casco = pele(cor, t, 'gloss')
    if 'besouro' in n:
        casco = mat('wood', cor)
    sem = _semente(n)
    carapaca = sph((0, 0, 18), 22, casco, scale=(1, 1.1, .55), parent=R)
    relevo(carapaca, forca=2.2, escala=8, semente=sem)
    for (p, nn) in espalhar((0, 0, 18), 22, (1, 1.1, .55), 9, semente=sem + 1, zmin=22):   # cravos na carapaça
        q = Vector(p)
        cyl(tuple(q - Vector(nn) * .8), tuple(q + Vector(nn) * 3.4), 1.6, .15, mat('gloss', shade(cor, -.3)) if t not in ('gelo', 'vidro') else casco, parent=R)
    torus((2, 0, 16), 21.5, 1.4, mat('gloss', shade(cor, -.4)) if t not in ('gelo', 'vidro') else casco, scale=(1, 1.1, .5), parent=R)   # borda da carapaça
    for i in range(3):
        for s in (-1, 1):
            with parte(R, 'perna', (-4 + i * 6, s * 18, 14), eixo='Z', amp=.24, fase=.5 * ((i + (s > 0)) % 2)):
                tubo([(-4 + i * 6, s * 18, 14), (-6 + i * 6, s * 28, 18), (-8 + i * 6, s * 34, 1)], 1.8, mat('gloss', shade(cor, -.35)), parent=R)
    for s in (-1, 1):
        with parte(R, 'garra', (14, s * 14, 16), amp=.1, fase=.5 if s > 0 else 0, atk=-.5):   # pinças sobem no ataque
            tubo([(14, s * 14, 16), (26, s * 22, 22), (34, s * 18, 26)], 3, casco, parent=R)
            big = 1.35 if ('rei' in n and s < 0) else 1
            sph((38, s * 18, 27), 7 * big, casco, scale=(1.4, .8, .8), parent=R)
            cyl((44, s * 18, 31), (52, s * 18, 31), 2.4 * big, .3, casco, parent=R)
        cyl((10, s * 4, 26), (10, s * 4, 34), .8, .8, casco, parent=R)
        sph((10, s * 4, 35), 2.4, mat('bone', '#f3efe4'), parent=R)
        sph((12, s * 4, 35.4), 1.1, mat('gloss', '#14100c'), parent=R)
    if 'cascalho' in n:
        for i in range(5):
            rocha((-6 + i * 3, (i % 2 - .5) * 10, 28), 5, mat('stone', '#6a625a'), semente=i, parent=R)
    return 48


def F_eye(R, nome, cor, t):
    n = _sem_acento(nome)
    z = 58
    carne = sph((0, 0, z), 20, pele(cor, t, 'skin'), parent=R)
    relevo(carne, forca=2.6, escala=8, semente=_semente(n))
    sph((7, 0, z), 15, esclera(), scale=(1, 1.05, 1), parent=R)
    iris = '#c0392b' if t not in ('gelo',) else '#3a9ac0'
    if 'tesouro' in n:
        iris = '#e8c45a'
    with parte(R, 'pupila', (7, 0, z), eixo='Z', amp=.22, atk=0.0):   # a íris corre de um lado a outro
        sph((19, 0, z), 7, mat('emit', iris, strength=3), scale=(.4, 1, 1), parent=R)
        torus((20.4, 0, z), 6.4, .9, mat('gloss', shade(iris, -.7)), rot=(0, math.pi / 2, 0), parent=R)   # aro escuro da íris
        sph((21.6, 0, z), 3.4, mat('gloss', '#0d0a0a'), scale=(.3, 1, 1.2), parent=R)
        sph((22.2, -1.6, z + 2), .9, mat('emit', '#ffffff', strength=8), parent=R)   # reflexo molhado
    for s in (-1, 1):   # pálpebras
        casca(z + s * 6, z + s * 21, 21, 4, math.radians(-60), math.radians(60), mat('skin', shade(cor, -.2)), esp=1.6, parent=R)
    for i in range(6):
        a = i / 6 * math.tau
        with parte(R, 'tent', (math.cos(a) * 8, math.sin(a) * 8, z - 14), ang=a, fase=i / 6, amp=.22):
            tubo([(math.cos(a) * 8, math.sin(a) * 8, z - 14), (math.cos(a) * 12, math.sin(a) * 12, z - 30), (math.cos(a + .5) * 10, math.sin(a + .5) * 10, z - 46)], 1.6, mat('gloss', shade(cor, -.4)), radii=[1, .6, .15], parent=R)
    if 'bibliotec' in n:
        torus((20, 9, z + 2), 4, .5, mat('gold', '#c9a54a'), rot=(0, math.pi / 2, 0), parent=R)
    if 'cripta' in n:
        for i in range(5):
            a = -1 + i * .5
            cyl((math.cos(a) * 18, math.sin(a) * 18, z + 12), (math.cos(a) * 20, math.sin(a) * 20, z + 22), 1.6, .1, mat('bone', '#e8dcc0'), parent=R)
    if 'tesouro' in n:
        for i in range(7):
            a = i / 7 * math.tau
            cyl((math.cos(a) * 14, math.sin(a) * 14, 3), (math.cos(a) * 14, math.sin(a) * 14, 4.2), 3, 3, mat('gold', '#e0b850'), parent=R)
    luz_ponto((24, 0, z), 12, iris, parent=R)
    return 82


def F_mimic(R, nome, cor, t):
    n = _sem_acento(nome)
    madeira = mat('gold', cor) if 'dourado' in n else mat('wood', cor)
    ouro = mat('gold', '#d9b85a')
    box((0, 0, 13), (40, 52, 26), madeira, bevel=2, parent=R)
    for x in (-19, 19):
        box((x, 0, 13), (3, 53, 27), ouro, bevel=.6, parent=R)
    box((0, 0, 1), (40.6, 52.6, 3), ouro, bevel=.4, parent=R)
    g = grupo((-20, 0, 26), rot=(0, -.75, 0), parent=R, nome='tampa')
    g['anim'], g['anim_amp'], g['anim_atk'] = 'tampa', .12, -.45   # a tampa abre e fecha; no ataque escancara
    box((20, 0, 7), (40, 52, 14), madeira, bevel=2, parent=g)
    box((40, 0, 7), (3, 53, 15), ouro, bevel=.6, parent=g)
    for i in range(9):
        y = -22 + i * 5.5
        cyl((40, y, 0), (40, y, -5), 1.6, .1, mat('bone', '#f2ead6'), parent=g)
    box((14, 0, 13), (36, 46, 2), mat('gloss', '#2a0b0e'), bevel=.4, parent=R)
    for i in range(9):
        y = -22 + i * 5.5
        cyl((19, y, 26), (19, y, 31), 1.6, .1, mat('bone', '#f2ead6'), parent=R)
    with parte(R, 'lingua', (10, 0, 24), amp=.3, atk=.5):
        tubo([(10, 0, 24), (24, 0, 22), (34, 0, 12), (38, 2, 4)], 3, mat('skin', '#c0485a'), radii=[1, .9, .7, .3], parent=R)
    olhos(R, (6, -8, 40), 2.6, cor='#ffd24a', sep=14)
    for s in (-1, 1):   # perninhas de inseto saindo de baixo
        for k in range(2):
            with parte(R, 'perna', (-8 + k * 16, s * 24, 4), eixo='Z', amp=.35, fase=.5 * ((k + (s > 0)) % 2)):
                tubo([(-8 + k * 16, s * 24, 4), (-6 + k * 16, s * 32, 8), (-4 + k * 16, s * 36, 0)], 1.4, mat('gloss', '#2a1a12'), radii=[1, .7, .3], parent=R)
    if 'anciao' in n:
        for i in range(6):
            a = i / 6 * math.tau
            sph((math.cos(a) * 18, math.sin(a) * 22, 27), 4, mat('fur', '#5f7a4a'), scale=(1, 1, .4), parent=R)
    if 'dourado' in n:
        for i in range(9):
            a = i / 9 * math.tau
            cyl((math.cos(a) * 30, math.sin(a) * 32, .5), (math.cos(a) * 30, math.sin(a) * 32, 1.6), 3, 3, ouro, parent=R)
        luz_ponto((12, 0, 30), 30, '#ffd870', parent=R)
    return 60


def F_worm(R, nome, cor, t):
    corpo = pele(cor, t, 'gloss')
    rocha((4, 0, 0), 26, mat('stone', '#3a2e22'), escala=(1.2, 1.2, .3), semente=3, parent=R)
    for i in range(6):
        a = i / 6 * math.tau
        rocha((math.cos(a) * 26, math.sin(a) * 26, 3), 5, mat('stone', '#4a3e32'), semente=i + 9, parent=R)
    pts = [(0, 0, 0), (2, 0, 24), (-2, 0, 48), (6, 0, 70), (14, 0, 84)]
    with parte(R, 'caule', (0, 0, 0), amp=.09, atk=.38):   # o corpo sai da terra balançando e dá o bote
        tubo(pts, 13, corpo, radii=[1.1, 1, .9, .85, .8], parent=R, res=6)
        for k in range(1, 4):
            x, y, z = pts[k]
            torus((x, y, z), 12, 1.8, mat('gloss', shade(cor, -.3)), rot=(0, .25, 0), parent=R)
        if 'devorador' in _sem_acento(nome):
            for k in range(5):
                cyl((-8, 0, 20 + k * 14), (-16, 0, 24 + k * 14), 3, .1, mat('bone', '#d8c8a0'), parent=R)
        with parte(R, 'cabeca', (12, 0, 80), amp=.1, fase=.3, atk=.2):
            sph((16, 0, 86), 12, mat('gloss', shade(cor, .2)), scale=(.7, 1, 1), parent=R)
            sph((22, 0, 86), 8, mat('gloss', '#2a0e10'), scale=(.4, 1, 1), parent=R)
            for i in range(10):
                a = i / 10 * math.tau
                cyl((22, math.cos(a) * 8, 86 + math.sin(a) * 8), (24, math.cos(a) * 4, 86 + math.sin(a) * 4), 1.2, .1, mat('bone', '#f2ead6'), parent=R)
    return 92


def F_tome(R, nome, cor, t):
    n = _sem_acento(nome)
    z = 56
    capa = mat('glass', cor) if 'vidro' in n else mat('leather', cor)
    for s in (-1, 1):
        g = grupo((0, 0, z), rot=(s * .45, 0, 0), parent=R, nome='capa')
        g['anim'], g['anim_s'], g['anim_amp'], g['anim_atk'] = 'capa', s, .3, .55   # as capas batem como asas; no ataque abrem
        box((0, s * 13, 0), (30, 26, 2.4), capa, bevel=.6, parent=g)
        box((0, s * 12, 2.2), (28, 22, 2), mat('paper', '#efe6cc'), bevel=.3, parent=g)
        for k in range(4):   # cantoneiras de metal
            box((-14 + (k % 2) * 28, s * (2 + (k // 2) * 22), 1.4), (3, 3, .6), mat('gold', '#b89a4a'), bevel=.3, parent=g)
    cyl((-15, 0, z - 2), (15, 0, z - 2), 2.4, 2.4, mat('leather', shade(cor, -.4)), parent=R)
    sph((0, 0, z + 8), 5, mat('bone', '#f6f1e4'), scale=(1, 1, .7), parent=R)
    sph((4, 0, z + 8), 2.6, mat('emit', '#c0392b', strength=4), parent=R)
    if 'mordedor' in n:
        for i in range(8):
            cyl((-12 + i * 3.4, -2, z + 3), (-12 + i * 3.4, -2, z + 7), .8, .1, mat('bone', '#f2ead6'), parent=R)
    if 'grimorio' in n:
        for i in range(4):
            a = i / 4 * math.tau
            torus((math.cos(a) * 26, math.sin(a) * 26, z + 10), 3, .4, mat('emit', '#b070f0', strength=10), rot=(math.pi / 2, 0, a), parent=R)
        elo = mat('metal', '#8a8a90')
        for i in range(6):
            torus((-14 + i * 5, 14, z - 6), 1.6, .5, elo, rot=(0, 0, (i % 2) * math.pi / 2), parent=R)
        luz_ponto((0, 0, z + 16), 30, '#b070f0', parent=R)
    for i in range(3):
        box((-10 + i * 10, 10 - i * 8, z + 24 + i * 6), (5, 6, .4), mat('paper', '#efe6cc'), rot=(i, i * .7, i * .3), bevel=.1, parent=R)
    return 88


def F_maw(R, nome, cor, t):
    n = _sem_acento(nome)
    z = 42
    corpo = pele(cor, t, 'gloss')
    massa = sph((0, 0, z), 28, corpo, scale=(1, 1, .8), parent=R)
    relevo(massa, forca=5, escala=12, semente=_semente(n))
    sph((12, 0, z + 2), 18, mat('gloss', '#12060c'), scale=(.6, 1, .75), parent=R)
    labio = torus((19.5, 0, z + 2), 15, 3, mat('skin', shade(cor, -.25)), rot=(0, math.pi / 2, 0), scale=(.9, 1.2, 1), parent=R)   # beiço carnudo
    relevo(labio, forca=1.4, escala=4, sub=1, semente=_semente(n) + 1)
    sph((15, 0, z + 1), 9, mat('emit', '#7a2a5a', strength=2.5), scale=(.4, 1, .8), parent=R)   # garganta acesa lá no fundo
    for s, (z0, z1) in ((1, (z + 13, z + 6)), (-1, (z - 9, z - 2))):   # fileiras de dentes tortos que mastigam
        with parte(R, 'dentes', (21, 0, (z0 + z1) / 2), s=s, amp=1.4, atk=4.0):
            for i in range(9):
                y = -17 + i * 4.25
                k = .7 + ((i * 7 + (s > 0) * 3) % 5) * .14
                cyl((21, y, z0), (22.4 + (i % 2), y + (i % 3 - 1) * .8, z0 + (z1 - z0) * k * 1.25), 1.5 + (i % 3) * .35, .1, mat('bone', '#e8dcc4'), parent=R)
    sph((14, 0, z + 2), 4, mat('emit', '#b06ad0', strength=10), parent=R)
    for i in range(6):
        a = i / 6 * math.tau
        with parte(R, 'tent', (math.cos(a) * 14, math.sin(a) * 14, z - 18), ang=a, fase=i / 6, amp=.22):
            tubo([(math.cos(a) * 14, math.sin(a) * 14, z - 18), (math.cos(a) * 20, math.sin(a) * 20, z - 32), (math.cos(a + .4) * 16, math.sin(a + .4) * 16, z - 44)], 2.4, mat('gloss', shade(cor, -.45)), radii=[1, .6, .15], parent=R)
    n_olhos = 6 if 'devorador' in n else 3
    for i in range(n_olhos):
        a = -1 + i * (2 / max(1, n_olhos - 1))
        p = (math.cos(a) * 18, math.sin(a) * 18, z + 18)
        sph(p, 2.6, mat('bone', '#f6f1e4'), parent=R)
        sph((p[0] + 1.6, p[1], p[2]), 1.2, mat('emit', '#ffe07a', strength=12), parent=R)
    luz_ponto((22, 0, z), 18, '#b06ad0', parent=R)
    return 78


# ---------------- voadores ----------------
def asa_morcego(R, s, z, membrana, osso, env=1.0):
    ombro = (0, s * 6, z + 4)
    punho = (-2, s * 22 * env, z + 18)
    tubo([ombro, (-1, s * 14 * env, z + 15), punho], 1.5, osso, radii=[1, .8, .6], parent=R)
    dedos = [(-4, s * 42 * env, z + 22), (-12, s * 40 * env, z + 6), (-14, s * 28 * env, z - 6)]
    for d in dedos:
        tubo([punho, d], .7, osso, radii=[1, .25], parent=R)
    cutuc = (-1, s * 24 * env, z + 22)    # garrinha do polegar
    cyl(punho, cutuc, .8, .1, osso, parent=R)
    m1 = (-9, s * 36 * env, z + 12)
    m2 = (-12, s * 30 * env, z + 2)
    m3 = (-10, s * 14 * env, z - 4)
    poly([ombro, punho, dedos[0], m1, dedos[1], m2, dedos[2], m3, (-4, s * 7, z - 2)], membrana, esp=.5, parent=R)


def asa_penas(R, s, z, cor, n=8, env=1.0):
    base = mat('cloth', shade(cor, -.05))
    escura = mat('gloss', shade(cor, -.3))
    tubo([(0, s * 6, z + 4), (-2, s * 16 * env, z + 13), (-6, s * 27 * env, z + 12)], 3, base, radii=[1, .8, .55], parent=R)
    for i in range(n):
        u = i / (n - 1)
        r0 = (-3 - u * 5, s * (12 + u * 15) * env, z + 12 - u * 1.5)
        comp = 13 + u * 16
        ang = .25 + u * .95                       # as penas da ponta abrem para fora
        tip = (r0[0] - comp * math.cos(ang) * .9, r0[1] + s * comp * math.sin(ang) * env, r0[2] - 4 - u * 3)
        lar = 2.4 + u * .6
        mid = ((r0[0] + tip[0]) / 2, (r0[1] + tip[1]) / 2, (r0[2] + tip[2]) / 2)
        poly([r0, (mid[0] + lar, mid[1], mid[2] + .4), tip, (mid[0] - lar, mid[1], mid[2] - .4)], escura if i % 2 else base, esp=.4, parent=R)
    for i in range(5):   # coberteiras curtas sobre a base das penas
        u = i / 4
        r0 = (-1 - u * 4, s * (8 + u * 16) * env, z + 13)
        tip = (r0[0] - 9, r0[1] + s * 2, r0[2] - 3)
        poly([r0, (r0[0] - 4, r0[1] + 2.4, r0[2]), tip, (r0[0] - 4, r0[1] - 2.4, r0[2])], base, esp=.4, parent=R)


def asa_inseto(R, s, z, cor_m, lob=1.0, frente=True):
    """Asa arredondada (mariposa, borboleta noturna): contorno de elipse com lóbulo."""
    pts = []
    for k in range(13):
        a = k / 12 * math.pi
        rx = 12 * lob if frente else 9 * lob
        ry = 30 * lob if frente else 20 * lob
        x = (4 if frente else -8) - math.cos(a) * rx * (1.1 if frente else 1)
        y = s * (4 + math.sin(a) * ry)
        zz = z + (10 if frente else 4) + math.sin(a) * (14 if frente else 6) * lob
        pts.append((x - (6 if not frente else 0) * math.sin(a), y, zz))
    poly(pts, cor_m, esp=.4, parent=R)
    return pts


def F_flyer(R, nome, cor, t):
    n = _sem_acento(nome)
    z = 62
    if 'corvo' in n:
        pena = mat('cloth', cor)
        sph((0, 0, z), 11, pena, scale=(1.35, .85, .9), parent=R)
        sph((13, 0, z + 6), 7.4, pena, parent=R)
        cyl((18, 0, z + 6), (29, 0, z + 3), 2.4, .2, mat('gloss', '#2a241e'), parent=R)
        cyl((18, 0, z + 3.6), (26, 0, z + 2.6), 1.6, .2, mat('gloss', '#2a241e'), parent=R)
        olhos(R, (17.4, 0, z + 9), 1.4, cor='#ff5a4a', sep=7)
        for s in (-1, 1):
            with parte(R, 'asa', (0, s * 6, z + 4), s=s, amp=.5):
                asa_penas(R, s, z, cor, n=9 if 'mil' in n else 8, env=1.15 if 'mil' in n else 1)
            caps((2, s * 4, z - 8), (4, s * 5, z - 18), 1, mat('gloss', '#2a241e'), parent=R)
        for i in range(5):   # cauda em leque
            a = (i - 2) * .22
            poly([(-12, 0, z - 2), (-30 * math.cos(a) - 10, 30 * math.sin(a), z - 7), (-30 * math.cos(a + .12) - 10, 30 * math.sin(a + .12), z - 7)], mat('cloth', shade(cor, -.2)), esp=.4, parent=R)
        if 'mil' in n:   # corvo das mil penas: penas soltas girando em volta
            for i in range(10):
                a = i / 10 * math.tau
                poly([(math.cos(a) * 28, math.sin(a) * 28, z + 10 + (i % 3) * 8), (math.cos(a) * 33, math.sin(a) * 33, z + 14 + (i % 3) * 8), (math.cos(a) * 31, math.sin(a) * 31, z + 8 + (i % 3) * 8)],
                     mat('cloth', cor), esp=.3, parent=R)
        return 88
    if 'besouro' in n or 'zangao' in n or 'vagalume' in n:
        casco = mat('gloss', cor) if 'zangao' not in n else mat('fur', cor)
        tronco = sph((0, 0, z), 12, casco, scale=(1.4, 1, .9), parent=R)
        if 'zangao' in n:
            pelo(tronco, cor, comp=1.3, n=800, pente=(-1, 0, .2), solto=1.4, raio=.4)
        sph((15, 0, z + 2), 7, mat('gloss', shade(cor, -.3)), parent=R)
        if 'zangao' in n:
            for x in (-8, -2, 4):
                faixa = cyl((x, 0, z), (x + 2.4, 0, z), 11.8, 11.8, mat('fur', '#1a1410'), parent=R)
                pelo(faixa, '#2a2018', comp=1.4, n=220, pente=(-1, 0, .2), solto=1.4, raio=.4)
            cyl((-17, 0, z - 1), (-25, 0, z - 4), 2, .1, mat('gloss', '#1a1410'), parent=R)
        if 'besouro' in n:
            for s in (-1, 1):   # élitros abertos
                g = grupo((4, s * 3, z + 8), rot=(s * .5, -.25, 0), parent=R)
                casca(0, -16, 9, 12, math.radians(-60 if s < 0 else 60), math.radians(0), mat('gloss', shade(cor, .1)), esp=1.4, parent=g)
            cyl((20, 0, z + 6), (28, 0, z + 16), 2.4, .3, mat('gloss', shade(cor, -.2)), parent=R)   # chifre
            luz_ponto((0, 0, z + 14), 25, '#ffd060', parent=R)
        if 'vagalume' in n:
            sph((-15, 0, z - 2), 8, mat('emit', '#f0e070', strength=14), scale=(1.2, 1, 1), parent=R)
            luz_ponto((-18, 0, z - 2), 40, '#f0e070', parent=R)
            for y in (-3, 3):   # mandíbulas famintas
                cyl((20, y, z + 1), (25, y * .3, z - 2), 1.2, .1, mat('bone', '#e8dcc0'), parent=R)
        for s in (-1, 1):
            asa = mat('glass', '#e8f4ff')
            with parte(R, 'asa', (1, s * 4, z + 7), s=s, amp=.55):
                poly([(2, s * 4, z + 8), (-6, s * 28, z + 24), (-18, s * 24, z + 14), (-6, s * 8, z + 8)], asa, esp=.3, parent=R)
                poly([(0, s * 4, z + 6), (-12, s * 20, z + 8), (-20, s * 14, z + 4)], asa, esp=.3, parent=R)
            for k in range(3):   # pernas
                tubo([(4 - k * 6, s * 6, z - 6), (2 - k * 6, s * 13, z - 9), (-4 - k * 6, s * 15, z - 14)], .7, mat('gloss', '#1a1410'), radii=[1, .8, .3], parent=R)
        olhos(R, (20, 0, z + 4), 2.2, cor='#ff8a3a', sep=6)
        return 84
    if 'mariposa' in n:
        corpo = mat('fur', shade(cor, -.1))
        tronco = sph((0, 0, z), 8, corpo, scale=(1.8, .9, .9), parent=R)
        cabeca = sph((12, 0, z + 2), 6.4, corpo, parent=R)
        pelo(tronco, shade(cor, -.1), comp=2.3, n=700, pente=(-1, 0, -.2), solto=1.8, raio=.4)
        pelo(cabeca, shade(cor, -.1), comp=1.8, n=260, pente=(0, 0, 1), solto=1.8, raio=.4)
        asa1 = mat('cloth', shade(cor, .12))
        asa2 = mat('cloth', shade(cor, -.15))
        for s in (-1, 1):
            with parte(R, 'asa', (2, s * 4, z + 8), s=s, amp=.35, vies=.5):   # bate mais para cima: abaixo da linha a asa some de lado
                asa_inseto(R, s, z, asa1, 1.1, True)
                asa_inseto(R, s, z - 2, asa2, 1.0, False)
                sph((-2, s * 24, z + 19.8), 4.4, mat('emit', '#ffb060', strength=3), scale=(1, 1, .25), rot=(s * .44, 0, 0), parent=R)    # olho falso na asa
                sph((-2, s * 24, z + 20.4), 2, mat('gloss', '#1a1008'), scale=(1, 1, .25), rot=(s * .44, 0, 0), parent=R)
            tubo([(15, s * 2, z + 7), (20, s * 7, z + 17), (24, s * 11, z + 20)], .5, corpo, parent=R)
            for k in range(4):   # antena plumosa
                cyl((17 + k * 2, s * (4 + k * 1.6), z + 10 + k * 2.4), (18 + k * 2, s * (6 + k * 1.6), z + 12 + k * 2.4), .3, .1, corpo, parent=R)
        for i in range(8):   # fuligem caindo das asas
            a = i / 8 * math.tau
            sph((math.cos(a) * 20 - 6, math.sin(a) * 26, z - 12 - (i % 3) * 6), 1.2, mat('stone', '#2a2622'), parent=R)
        olhos(R, (16, 0, z + 3), 2.6, cor='#ffe07a', sep=6)
        return 90
    if 'fatuo' in n:   # fogo-fátuo negro: chama escura com núcleo violeta
        sph((0, 0, z), 12, mat('gloss', '#0e0b12'), parent=R)
        sph((0, 0, z), 15, mat('emit', '#7a4ab0', strength=1.5, alpha=.35), parent=R)
        with parte(R, 'caule', (0, 0, z), amp=.14, atk=.25):   # a chama dança
            chama(R, (0, 0, z + 6), 26, '#6a3aa0', r=12, n=6)
        sph((2, 0, z), 5, mat('emit', '#e0c8ff', strength=18), parent=R)
        for i in range(7):
            a = i / 7 * math.tau
            sph((math.cos(a) * 22, math.sin(a) * 22, z - 10 + (i % 3) * 10), 1.4, mat('emit', '#b890f0', strength=10), parent=R)
        olhos(R, (12, 0, z + 3), 1.6, cor='#f0e0ff', sep=6)
        luz_ponto((0, 0, z), 40, '#9a6ad8', raio=.3, parent=R)
        return 96
    # morcegos (padrão): quartzo, ancião, ossudo, de mina
    osso = mat('bone', '#d8ccb8') if 'ossudo' in n else mat('leather', shade(cor, -.35))
    corpo = pele(cor, t, 'fur') if 'ossudo' not in n else mat('bone', '#e0d6c4')
    membrana = mat('leather', shade(cor, -.2)) if 'ossudo' not in n else mat('emit', '#7ab0a0', strength=.8, alpha=.45)
    tronco = sph((0, 0, z), 11, corpo, scale=(1.05, .9, 1.05), parent=R)
    cabeca = sph((7, 0, z + 10), 8, corpo, parent=R)
    if 'ossudo' not in n and t not in ('vidro', 'gelo'):   # morcego de pelo de verdade
        pelo(tronco, cor, comp=1.4, n=800, pente=(-.4, 0, -1), solto=1.4, raio=.4)
        pelo(cabeca, cor, comp=1.1, n=320, pente=(-1, 0, .2), solto=1.2, raio=.4)
    for s in (-1, 1):
        cyl((6, s * 5, z + 15), (3, s * 9, z + 27), 3.4, .2, corpo, parent=R)     # orelhas grandes
        with parte(R, 'asa', (0, s * 6, z + 4), s=s, amp=.62):
            asa_morcego(R, s, z, membrana, osso, env=1.25 if 'anciao' in n else 1)
        caps((0, s * 4, z - 9), (2, s * 5, z - 16), 1.2, osso, parent=R)
    sph((14, 0, z + 9), 3, mat('skin', shade(cor, -.2)), scale=(.8, 1.1, .8), parent=R)   # focinho
    olhos(R, (12.5, 0, z + 13), 1.8, cor='#ff6a5a', sep=7)
    for y in (-2, 2):
        cyl((14, y, z + 5), (14, y, z + 1), .8, .05, mat('bone', '#f4ecd8'), parent=R)
    if 'quartzo' in n:
        for i in range(5 if 'anciao' in n else 3):
            a = -.8 + i * .4
            cyl((-2 + math.cos(a) * 4, math.sin(a) * 8, z + 8), (-6 + math.cos(a) * 6, math.sin(a) * 12, z + 22 + (i % 2) * 6), 2.6, .1, mat('glass', '#d8c0f0'), parent=R)
        luz_ponto((0, 0, z + 20), 20, '#c8a0f0', parent=R)
    if 'mina' in n:   # capacete de mineiro torto com lamparina
        cupula((6, 0, z + 14), 8.6, mat('metal', '#8a7a4a'), parent=R)
        sph((14, 0, z + 18), 2, mat('emit', '#ffe09a', strength=14), parent=R)
        luz_ponto((16, 0, z + 18), 14, '#ffd08a', parent=R)
    return 84


# ---------------- feras ----------------
CAB_FERA = dict(amp=.06, fase=.25, atk=.22)   # a cabeça acena no passo e avança na mordida


def quadrupede(R, corpo, escuro, comp=1.0, alt=1.0, pesc=1.0, perna=3.6, pelagem=None):
    """Esqueleto genérico de quadrúpede (peito maior que o quadril), devolve a posição da cabeça.
    pelagem = dict(cor, comp, nevoa, juba): pelo de fios no peito, quadril, barriga, pescoço (mais longo com juba) e coxas."""
    zc = 36 * alt
    peito = sph((14 * comp, 0, zc + 2), 16, corpo, scale=(1.15, .95, 1.05), parent=R)       # peito
    quadril = sph((-14 * comp, 0, zc), 14, corpo, scale=(1.2, .9, .95), parent=R)          # quadril
    barriga = cyl((-14 * comp, 0, zc), (14 * comp, 0, zc + 2), 13, 14, corpo, parent=R)    # barriga
    cab = (32 * comp, 0, zc + 16 * pesc)
    if pelagem:   # pescoço de malha, para receber pelo
        pescoco = cyl((16 * comp, 0, zc + 5), cab, 9.4, 6.8, corpo, parent=R)
        P = pelagem
        L, nev = P['comp'], P.get('nevoa', False)
        pelo(peito, P['cor'], comp=L * (1.5 if P.get('juba') else 1.1), n=800, pente=(-1, 0, -.5), nevoa=nev)
        pelo(quadril, P['cor'], comp=L, n=650, pente=(-1, 0, -.45), nevoa=nev)
        pelo(barriga, P['cor'], comp=L * .6, n=550, pente=(-1, 0, -.4), nevoa=nev)
        pelo(pescoco, P['cor'], comp=L * (2.0 if P.get('juba') else 1.15), n=500, pente=(-1, 0, -.4), nevoa=nev)
    else:
        tubo([(18 * comp, 0, zc + 6), (26 * comp, 0, zc + 12 * pesc), cab], 8, corpo, radii=[1.1, .9, .8], parent=R)
    for x, k in ((14 * comp, 1), (-15 * comp, -1)):
        for y in (-7, 7):
            joelho = (x + k * 2, y, zc * .5)
            with parte(R, 'perna', (x, y, zc - 4), fase=.5 if (k > 0) != (y > 0) else 0, amp=.42):   # patas em diagonal andam juntas
                coxa = caps((x, y, zc - 4), joelho, perna + 1, corpo if k > 0 else escuro, parent=R, r2=perna)
                caps(joelho, (x + k * 3, y, 3), perna, escuro, parent=R, r2=perna * .8)
                sph((x + k * 3 + 2, y, 2.2), perna * 1.15, escuro, scale=(1.4, 1, .6), parent=R)   # pata
                if pelagem:
                    pelo(coxa, pelagem['cor'], comp=pelagem['comp'] * .35, n=160, pente=(0, 0, -1), nevoa=pelagem.get('nevoa', False))
                    for j in range(3):   # garras
                        cyl((x + k * 3 + 4.4, y + (j - 1) * 1.6, 2), (x + k * 3 + 6.6, y + (j - 1) * 1.8, .4), .6, .1, mat('bone', '#2a221c'), parent=R)
    return cab


def F_beast(R, nome, cor, t):
    n = _sem_acento(nome)
    nevoa = t == 'sombra'
    if t in ('gelo', 'vidro', 'sombra'):   # feras de gelo e de névoa também têm pelo: o gelo fica nos espinhos, a névoa na ponta dos fios
        cor_pelo = mix(cor, '#e8f6ff', .3) if not nevoa else cor
        corpo = mat('fur', cor_pelo)
    else:
        cor_pelo = cor
        corpo = pele(cor, t, 'fur')
    escuro = mat('fur', shade(cor_pelo, -.3))
    if 'escorpiao' in n:
        casco = mat('gloss', cor)
        for i in range(4):   # placas do corpo
            sph((8 - i * 8, 0, 14), 13 - i, casco, scale=(.75, 1, .6), parent=R)
        for s in (-1, 1):
            for i in range(4):
                with parte(R, 'perna', (6 - i * 6, s * 10, 12), eixo='Z', amp=.24, fase=.5 * ((i + (s > 0)) % 2)):
                    tubo([(6 - i * 6, s * 10, 12), (4 - i * 7, s * 20, 13), (2 - i * 8, s * 26, 0)], 1.6, mat('gloss', shade(cor, -.3)), radii=[1, .8, .4], parent=R)
            with parte(R, 'garra', (12, s * 8, 14), amp=.1, fase=.5 if s > 0 else 0, atk=-.45):
                tubo([(12, s * 8, 14), (22, s * 16, 16), (30, s * 13, 16)], 2.6, casco, parent=R)
                sph((34, s * 12, 16), 5, casco, scale=(1.4, .8, .7), parent=R)
                cyl((37, s * 10, 18), (44, s * 6, 18), 1.6, .2, casco, parent=R)
                cyl((37, s * 14, 16), (44, s * 11, 15), 1.6, .2, casco, parent=R)
        pts = [(-20, 0, 14), (-32, 0, 24), (-32, 0, 40), (-20, 0, 52), (-8, 0, 50)]
        with parte(R, 'cauda', (-20, 0, 14), eixo='Y', amp=.08, atk=.5):   # o ferrão arqueia para a frente no ataque
            for k in range(1, 5):
                x, y, z = pts[k]
                sph((x, y, z), 5.4 - k * .4, casco, parent=R)
            tubo(pts, 3.6, casco, radii=[1, .9, .8, .7, .5], parent=R)
            cyl((-8, 0, 50), (0, 0, 42), 2.6, .1, mat('emit', '#ffb040', strength=6), parent=R)
            luz_ponto((-4, 0, 48), 12, '#ffb040', parent=R)
        olhos(R, (18, 0, 20), 1.6, cor='#ff5a3a', sep=4)
        return 56
    if 'escavador' in n:   # toupeira cega, de pelo curto e aveludado
        tronco = sph((0, 0, 26), 22, corpo, scale=(1.4, 1, .95), parent=R)
        cabeca = sph((26, 0, 26), 12, corpo, parent=R)
        pelo(tronco, cor_pelo, comp=1.0, n=1800, pente=(-1, 0, -.3), raio=.4, filhos=4)
        pelo(cabeca, cor_pelo, comp=.8, n=500, pente=(-1, 0, 0), raio=.4, filhos=4)
        sph((37, 0, 25), 5, mat('skin', '#d8909a'), scale=(.8, 1, 1), parent=R)
        for i in range(8):
            a = i / 8 * math.tau
            cyl((40, math.cos(a) * 3, 25 + math.sin(a) * 3), (43, math.cos(a) * 5.4, 25 + math.sin(a) * 5.4), 1, .3, mat('skin', '#e8a0aa'), parent=R)
        for s in (-1, 1):
            with parte(R, 'braco', (14, s * 16, 18), fase=.5 if s > 0 else 0, amp=.3, atk=-.6):   # patas de cavar
                sph((16, s * 18, 12), 7, mat('skin', '#c88a8a'), scale=(1, .6, 1), parent=R)
                for k in range(4):
                    cyl((20, s * (15 + k * 2.4), 8), (28, s * (16 + k * 2.6), 2), 1.2, .1, mat('bone', '#efe4c8'), parent=R)
            sph((-14, s * 12, 8), 6, escuro, scale=(1.3, 1, .6), parent=R)
        with parte(R, 'cauda', (-28, 0, 22), amp=.3):
            tubo([(-28, 0, 22), (-36, 0, 18), (-40, 0, 14)], 1.6, mat('skin', '#c88a8a'), radii=[1, .6, .2], parent=R)
        return 52
    if 'javali' in n:
        cab = quadrupede(R, corpo, escuro, comp=1.0, alt=.9, pesc=.5, perna=3.8, pelagem=dict(cor=cor_pelo, comp=2.4))
        corcova = sph((4, 0, 50), 16, corpo, scale=(1.3, .9, .7), parent=R)    # corcova de cerdas grossas
        pelo(corcova, shade(cor_pelo, -.15), comp=3.6, n=700, pente=(-1, 0, .6), solto=2.2, raio=.6)
        pc = (cab[0] - 8, 0, cab[2] - 4)
        with parte(R, 'cabeca', pc, **CAB_FERA):
            cabeca = sph(cab, 12, corpo, scale=(1.1, .9, .95), parent=R)
            pelo(cabeca, cor_pelo, comp=1.5, n=380, pente=(-1, 0, .2), solto=1.6)
            cyl((cab[0] + 6, 0, cab[2] - 2), (cab[0] + 15, 0, cab[2] - 4), 7, 5.6, corpo, parent=R)
            cyl((cab[0] + 15, 0, cab[2] - 4), (cab[0] + 16, 0, cab[2] - 4), 5.6, 5.6, mat('skin', '#6a4a42'), parent=R)
            for y in (-5, 5):
                tubo([(cab[0] + 12, y, cab[2] - 6), (cab[0] + 18, y * 1.5, cab[2] - 2), (cab[0] + 17, y * 1.7, cab[2] + 6)], 1.6, mat('bone', '#f0e6d0'), radii=[1, .8, .2], parent=R)
        crina = mat('fur', shade(cor, -.5))
        for i in range(11):
            x = 24 - i * 4.6
            tufo((x, 0, 54 - abs(i - 4) * 1.4), (-3, (i % 2 - .5) * 3, 9), crina, r=2.2, parent=R)
        with parte(R, 'cabeca', pc, **CAB_FERA):
            for y in (-6, 6):
                cyl((cab[0] - 2, y, cab[2] + 8), (cab[0] - 4, y * 1.3, cab[2] + 15), 3, .3, escuro, parent=R)
            olhos(R, (cab[0] + 8, 0, cab[2] + 4), 1.6, cor='#ff7a3a' if 'fuligem' in n or 'fume' in n else '#ffd98a', sep=9)
        with parte(R, 'cauda', (-30, 0, 38), amp=.4):
            tubo([(-30, 0, 38), (-36, 0, 42), (-38, 2, 36)], 1.2, corpo, parent=R)
        if 'fume' in n or 'fuligem' in n:   # fumaça saindo do lombo
            fum = mat('emit', '#5a524c', strength=.4, alpha=.45)
            for i in range(5):
                sph((10 - i * 8, (i % 2 - .5) * 6, 64 + i * 4 + (i % 2) * 5), 5 + i * 1.4, fum, parent=R)
            if 'rei' in n:
                with parte(R, 'cabeca', pc, **CAB_FERA):
                    for i in range(6):
                        a = i / 6 * math.tau
                        cyl((cab[0] - 2 + math.cos(a) * 6, math.sin(a) * 6, cab[2] + 12), (cab[0] - 2 + math.cos(a) * 7, math.sin(a) * 7, cab[2] + 20), 1.6, .2, mat('stone', '#2a2420'), parent=R)
                    luz_ponto((cab[0], 0, cab[2]), 20, '#ff7a3a', parent=R)
        return 66
    if 'cervo' in n:
        cab = quadrupede(R, corpo, escuro, comp=.9, alt=1.25, pesc=1.5, perna=2.4, pelagem=dict(cor=cor_pelo, comp=1.3))
        pc = (cab[0] - 6, 0, cab[2] - 4)
        luz = mat('emit', '#fff0c0', strength=5)
        with parte(R, 'cabeca', pc, **CAB_FERA):
            cabeca = sph(cab, 8.5, corpo, scale=(1.2, .85, .9), parent=R)
            pelo(cabeca, cor_pelo, comp=1.0, n=260, pente=(-1, 0, .2))
            cyl((cab[0] + 6, 0, cab[2] - 2), (cab[0] + 13, 0, cab[2] - 4), 5, 3.4, corpo, parent=R)
            sph((cab[0] + 13.4, 0, cab[2] - 4), 1.6, mat('gloss', '#14100c'), parent=R)
            for y in (-1, 1):
                base = (cab[0] - 2, y * 4, cab[2] + 7)
                tubo([base, (cab[0] - 4, y * 10, cab[2] + 18), (cab[0] - 2, y * 15, cab[2] + 30), (cab[0] - 7, y * 18, cab[2] + 40)], 1.3, luz, radii=[1, .8, .6, .2], parent=R)
                for k, (dx, dy, dz) in enumerate(((2, 4, 6), (-3, 3, 8), (2, 2, 7))):
                    p = (cab[0] - 4 + k * 1, y * (10 + k * 3), cab[2] + 18 + k * 8)
                    tubo([p, (p[0] + dx, p[1] + y * dy, p[2] + dz)], .8, luz, radii=[1, .2], parent=R)
                cyl((cab[0] - 1, y * 5, cab[2] + 3), (cab[0] - 4, y * 11, cab[2] + 6), 2.2, .3, corpo, parent=R)
        for i in range(9):   # pintas de luz
            a = i * 1.3
            sph((-12 + i * 3.4, math.cos(a) * 12, 56 + math.sin(a) * 3), 1.3, luz, parent=R)
        with parte(R, 'cabeca', pc, **CAB_FERA):
            olhos(R, (cab[0] + 5, 0, cab[2] + 2), 1.5, cor='#fff4d0', sep=8)
            luz_ponto((cab[0], 0, cab[2] + 28), 30, '#fff0c0', parent=R)
        with parte(R, 'cauda', (-28, 0, 48), amp=.4):
            tubo([(-28, 0, 48), (-32, 0, 52)], 2.4, mat('fur', '#f6f0e0'), radii=[1, .3], parent=R)
        return 92
    # lobos e linces (padrão)
    lince = 'lince' in n
    alfa = 'alfa' in n or 'ancestral' in n
    cab = quadrupede(R, corpo, escuro, comp=1.0, alt=1.0, pesc=1.0, perna=3.2 if not alfa else 3.8,
                     pelagem=dict(cor=cor_pelo, comp=1.8 if lince else 2.3 if not alfa else 2.8, nevoa=nevoa, juba=not lince))
    pc = (cab[0] - 8, 0, cab[2] - 4)
    foc = 10 if not lince else 6
    with parte(R, 'cabeca', pc, **CAB_FERA):
        cabeca = sph(cab, 10.5, corpo, scale=(1.1, .95, .95), parent=R)
        pelo(cabeca, cor_pelo, comp=1.4, n=420, pente=(-1, 0, .25), nevoa=nevoa)
        cyl((cab[0] + 5, 0, cab[2] - 1), (cab[0] + 5 + foc, 0, cab[2] - 4), 6, 3.2, corpo, parent=R)
        sph((cab[0] + 5.4 + foc, 0, cab[2] - 3.6), 2, mat('gloss', '#14100c'), parent=R)
        for y in (-1, 1):
            cyl((cab[0] + 1, y * 5, cab[2] + 7), (cab[0] - 1, y * 7, cab[2] + 17), 3.4, .3, escuro, parent=R)
            if lince:
                cyl((cab[0] - 1, y * 7, cab[2] + 17), (cab[0] - 1.6, y * 7.6, cab[2] + 22), .5, .05, mat('fur', '#1a1410'), parent=R)
            cyl((cab[0] + 3 + foc * .7, y * 2.4, cab[2] - 6), (cab[0] + 3 + foc * .7, y * 2.2, cab[2] - 9), .7, .05, mat('bone', '#f4ecd8'), parent=R)
        olhos(R, (cab[0] + 7, 0, cab[2] + 3), 1.6, cor='#a8e4ff' if t in ('gelo', 'sombra') else '#ffd98a', sep=8)
    pelo_m = mat('fur', shade(cor_pelo, -.12))
    if not lince:   # cauda volumosa (a juba agora é o pelo comprido do pescoço e do peito)
        with parte(R, 'cauda', (-26, 0, 40), amp=.3):
            for seg in tubo_malha([(-26, 0, 40), (-36, 0, 42), (-46, 0, 36), (-52, 0, 30)], 3.4, pelo_m, radii=[.8, 1, .8, .25], parent=R):
                pelo(seg, cor_pelo, comp=4 if not alfa else 4.8, n=200, pente=(-1, 0, -.5), nevoa=nevoa, solto=1.4)
    else:
        with parte(R, 'cauda', (-26, 0, 40), amp=.4):
            for seg in tubo_malha([(-26, 0, 40), (-31, 0, 43)], 2.4, pelo_m, radii=[1, .6], parent=R):
                pelo(seg, cor_pelo, comp=2, n=160, pente=(-1, 0, .4))
            sph((-31.6, 0, 43.4), 2.6, mat('fur', '#1a1410'), parent=R)   # ponta escura da cauda curta
        for i in range(10):   # pintas
            a = i * 1.7
            sph((-14 + i * 3.6, math.cos(a) * 12.4, 40 + math.sin(a) * 5), 2.2, mat('fur', shade(cor_pelo, -.5)), scale=(1, 1, .6), parent=R)
        with parte(R, 'cabeca', pc, **CAB_FERA):
            for y in (-1, 1):
                tufo((cab[0] + 2, y * 9, cab[2] - 5), (-2, y * 5, -4), pelo_m, r=2, parent=R)   # costeletas
    if alfa:   # cicatriz e névoa em volta do líder
        with parte(R, 'cabeca', pc, **CAB_FERA):
            box((cab[0] + 6, -6.8, cab[2] + 3), (6, .6, 1), mat('skin', '#c87a7a'), rot=(0, .4, 0), bevel=.2, parent=R)
    if t == 'gelo':
        g = mat('glass', '#d8f2ff')
        for i in range(3):
            cyl((6 - i * 9, 0, 50), (5 - i * 9, (i % 2 - .5) * 3, 56), 1.8, .1, g, parent=R)
    if t == 'sombra':
        luz_ponto((10, 0, 40), 30, '#c8dcff', raio=.4, parent=R)
    return 70 if not alfa else 76


# ---------------- golens (rocha lascada) ----------------
GOLEM_BRACO = {-1: dict(fase=0, amp=.12, atk=-.8), 1: dict(fase=.5, amp=.12, atk=-.8)}
GOLEM_CAB = dict(amp=.05, fase=.25, atk=.15)


def F_golem(R, nome, cor, t):
    n = _sem_acento(nome)
    sem = _semente(n)
    nucleo = '#ffb050'
    if t == 'gelo':
        nucleo = '#a8e4ff'
    elif t == 'brasa' or 'carvao' in n:
        nucleo = '#ff7a30'
    elif t == 'vidro':
        nucleo = '#bff0ff'
    elif 'escaravelho' in n:
        nucleo = '#ffd060'
    elif 'coral' in n:
        nucleo = '#ff9a8a'
    if 'yeti' in n:
        return _yeti(R, n, cor)
    if 'espelhado' in n:
        corpo, escuro = mat('metal', cor, rough=.08), mat('metal', shade(cor, -.35), rough=.18)
    elif 'escaravelho' in n:
        corpo, escuro = mat('gloss', cor), mat('gloss', shade(cor, -.45))
    elif t == 'gelo':
        corpo, escuro = mat('glass', mix(cor, '#e8f6ff', .3)), mat('stone', shade(cor, -.35))
    elif 'carvao' in n:
        corpo, escuro = mat('stone', '#2a2624'), mat('stone', '#1a1716')
    else:
        corpo, escuro = mat('stone', cor), mat('stone', shade(cor, -.3))
    for s in (-1, 1):
        with parte(R, 'perna', (0, s * 11, 22), fase=.5 if s > 0 else 0, amp=.14):
            rocha((0, s * 11, 12), 10, escuro, escala=(1.1, 1, 1.3), semente=sem + s, parent=R)
    rocha((-1, 0, 30), 15, escuro, escala=(1, 1.3, .7), semente=sem + 3, parent=R)
    rocha((0, 0, 54), 24, corpo, escala=(.95, 1.2, 1.0), semente=sem + 4, parent=R)
    sph((18, 0, 56), 5, mat('emit', nucleo, strength=12), parent=R)     # núcleo aceso no peito
    luz_ponto((24, 0, 56), 30, nucleo, raio=.3, parent=R)
    e = mat('emit', nucleo, strength=6)
    for (dy, dz) in ((-9, 10), (8, 12), (-4, -10), (10, -6)):      # rachaduras saindo do núcleo
        tubo([(19, 0, 56), (20, dy * .5, 56 + dz * .5), (18.5, dy, 56 + dz)], .5, e, radii=[1, .7, .2], parent=R)
    for s in (-1, 1):
        with parte(R, 'braco', (0, s * 27, 70), **GOLEM_BRACO[s]):   # os braços de pedra balançam e esmagam no ataque
            rocha((0, s * 27, 70), 12, corpo, semente=sem + 5 + s, parent=R)                         # ombro
            rocha((2, s * 33, 54), 9, escuro, escala=(1, 1, 1.4), semente=sem + 7 + s, parent=R)     # braço
            rocha((6, s * 35, 35), 9, corpo, escala=(1, 1, 1.4), semente=sem + 9 + s, parent=R)      # antebraço
            rocha((9, s * 36, 16), 12, corpo, semente=sem + 11 + s, parent=R)                        # punho perto do chão
    with parte(R, 'cabeca', (6, 0, 74), **GOLEM_CAB):
        rocha((10, 0, 80), 10, corpo, escala=(1.15, 1, .85), semente=sem + 13, parent=R)              # cabeça baixa
        rocha((17, 0, 84), 6.5, escuro, escala=(.6, 1.7, .5), semente=sem + 14, parent=R)            # sobrancelha
        olhos(R, (19.5, 0, 80), 2, cor=nucleo, sep=8)
    if t in ('musgo', 'pedra') or 'colosso' in n or 'granito' in n:
        musgo = mat('fur', '#5a7a44')
        for (x, y, z, r) in ((0, -26, 80, 8), (0, 24, 80, 7), (4, 0, 76, 9), (-6, 8, 70, 10), (-8, -10, 64, 8)):
            sph((x, y, z), r, musgo, scale=(1, 1, .35), parent=R)
        for i in range(5):
            tufo((-4 + i * 2, -20 + i * 9, 78), (0, 0, 7), mat('fur', '#7a9a52'), r=1, parent=R)
    if t == 'gelo':
        g = mat('glass', '#d8f2ff')
        for s in (-1, 1):
            for k in range(3):
                cyl((-2, s * (24 + k * 3), 76), (-4 - k, s * (28 + k * 5), 88 + k * 3), 3, .1, g, parent=R)
    if 'escaravelho' in n:
        casca(80, 34, 22, 30, math.radians(100), math.radians(260), mat('gloss', shade(cor, -.15)), esp=2.4, parent=R)
        with parte(R, 'cabeca', (6, 0, 74), **GOLEM_CAB):
            tubo([(18, 0, 86), (24, 0, 96), (22, 0, 108), (14, 0, 112)], 3.4, mat('gloss', shade(cor, -.3)), radii=[1, .8, .5, .1], parent=R)
            for y in (-5, 5):
                cyl((20, y, 74), (27, y * .4, 70), 1.8, .2, mat('gloss', '#2a1a0a'), parent=R)
    if 'coral' in n:
        cm = mat('stone', '#e07a6a')
        for i in range(6):
            a = i / 6 * math.tau
            p0 = (math.cos(a) * 10 - 4, math.sin(a) * 20, 72)
            tubo([p0, (p0[0] - 2, p0[1] * 1.3, 88), (p0[0] + 2, p0[1] * 1.5, 100)], 2.2, cm, radii=[1, .7, .3], parent=R)
            tubo([(p0[0] - 2, p0[1] * 1.3, 88), (p0[0] - 6, p0[1] * 1.6, 96)], 1.4, cm, radii=[1, .3], parent=R)
    if 'forj' in n or 'ferreiro' in n or 'capataz' in n:
        with parte(R, 'braco', (0, -27, 70), **GOLEM_BRACO[-1]):   # o martelo acompanha o braço direito
            g = grupo((10, -38, 20), rot=(0, .3, 0), parent=R)
        cyl((0, 0, -6), (0, 0, 40), 2, 2, mat('wood', '#3a2a1a'), parent=g)
        box((0, 0, 44), (14, 22, 13), mat('metal', '#2a2624', rough=.6), bevel=1.6, parent=g)
        box((14, 0, 40), (3, 26, 30), mat('leather', '#4a3222'), bevel=.8, parent=R)    # avental de couro
        luz_ponto((12, -36, 30), 25, '#ff8a3a', parent=R)
        if 'primeiro' in n:
            for i in range(7):
                a = i / 7 * math.tau
                cyl((10 + math.cos(a) * 7, math.sin(a) * 7, 86), (10 + math.cos(a) * 8, math.sin(a) * 8, 94 + (i % 2) * 4), 1.6, .2, mat('metal', '#2a2624'), parent=R)
    if t == 'vidro' or 'quartzo' in n or 'cristal' in n:
        for i in range(6):
            a = i * 1.1
            cyl((math.cos(a) * 8 - 6, math.sin(a) * 16, 72), (math.cos(a) * 10 - 10, math.sin(a) * 20, 90 + (i % 3) * 6), 3.2, .1, mat('glass', '#d8c8f0' if 'quartzo' in n else '#bff0f0'), parent=R)
    return 96


def _yeti(R, n, cor):
    corpo = mat('fur', cor)
    escuro = mat('fur', shade(cor, -.25))
    pele_m = mat('skin', '#8aa8c0')
    for s in (-1, 1):
        with parte(R, 'perna', (0, s * 10, 26), fase=.5 if s > 0 else 0, amp=.2):
            caps((0, s * 10, 26), (2, s * 11, 6), 8, corpo, parent=R)
            sph((5, s * 11, 4), 7, pele_m, scale=(1.5, 1, .55), parent=R)
    tronco = sph((0, 0, 52), 24, corpo, scale=(.95, 1.15, 1.05), parent=R)
    pelo(tronco, cor, comp=4.4, n=1500, pente=(-.3, 0, -1), solto=1.8, raio=.55)
    sph((6, 0, 46), 16, mat('fur', shade(cor, .1)), scale=(.6, 1, 1.1), parent=R)
    for s in (-1, 1):
        ombro = sph((0, s * 26, 68), 12, corpo, parent=R)
        pelo(ombro, cor, comp=4, n=300, pente=(0, s * .3, -1), solto=1.8, raio=.55)
        with parte(R, 'braco', (0, s * 28, 66), fase=.5 if s > 0 else 0, amp=.15, atk=-.9):
            b1 = caps((0, s * 30, 64), (6, s * 36, 38), 8, corpo, parent=R, r2=7)
            b2 = caps((6, s * 36, 38), (10, s * 37, 16), 7, corpo, parent=R, r2=6)
            pelo(b1, cor, comp=3.6, n=260, pente=(0, 0, -1), solto=1.8, raio=.55)
            pelo(b2, cor, comp=3, n=220, pente=(0, 0, -1), solto=1.8, raio=.55)
            sph((11, s * 37, 12), 7, pele_m, scale=(1.2, 1, .9), parent=R)
            for k in range(3):
                cyl((15, s * (34 + k * 2.6), 10), (19, s * (34 + k * 2.6), 6), 1.2, .1, mat('bone', '#efe4c8'), parent=R)
    with parte(R, 'cabeca', (6, 0, 70), **GOLEM_CAB):
        cabeca = sph((10, 0, 78), 12, corpo, scale=(1.05, 1, .95), parent=R)
        pelo(cabeca, cor, comp=3, n=380, pente=(-.6, 0, -.6), solto=1.8, raio=.55)
        sph((18, 0, 76), 8, pele_m, scale=(.6, 1, .9), parent=R)
        olhos(R, (21.5, 0, 78), 1.8, cor='#a8e4ff', sep=7)
        box((22, 0, 71.5), (1, 7, 1.4), mat('gloss', '#1a1418'), bevel=.3, parent=R)
        for y in (-2.6, 2.6):
            cyl((22.4, y, 71), (22.6, y, 68.4), .7, .05, mat('bone', '#f4ecd8'), parent=R)
        for y in (-1, 1):
            tubo([(6, y * 9, 86), (2, y * 16, 94), (8, y * 21, 102)], 2.4, mat('bone', '#e8dcc0'), radii=[1, .7, .15], parent=R)
    for i in range(24):   # pelagem desgrenhada
        a = i / 24 * math.tau
        z = 34 + (i % 4) * 10
        tufo((math.cos(a) * 18, math.sin(a) * 22, z), (math.cos(a) * 5 - 2, math.sin(a) * 6, -7), escuro if i % 3 else corpo, r=2.6, parent=R)
    for i in range(5):
        cyl((-4 - i * 3, (i % 2 - .5) * 20, 70 + i * 2), (-6 - i * 3, (i % 2 - .5) * 24, 78 + i * 3), 2.4, .1, mat('glass', '#d8f2ff'), parent=R)
    return 96


# ---------------- espectros ----------------
ESPECTRO_BRACO = {-1: dict(fase=0, amp=.25, atk=-.7), 1: dict(fase=.5, amp=.25, atk=-.7)}


def F_wisp(R, nome, cor, t):
    n = _sem_acento(nome)
    escuro = any(k in n for k in ('sombra', 'noite'))
    if escuro:   # miolo negro e opaco, só a borda acesa na cor do espectro
        corpo = mat('gloss', '#0e0b12')
        veu = espectral(cor, forca=.8, a_centro=.03, a_borda=.42)
        olho = '#ff5a4a' if 'sombra' in n else '#fff2c8'
    else:   # translúcido no meio, aceso na borda
        corpo = espectral(cor, forca=1.5, a_centro=.42, a_borda=.97)
        veu = espectral(shade(cor, .3), forca=1.0, a_centro=.03, a_borda=.55)
        olho = '#1a1418'
    if 'degelo' in n:
        corpo = mat('glass', '#bfe6ff')
    if 'vitral' in n:
        corpo = vitral(cor)
    pts = []
    for k in range(9):   # cauda em espiral que sobe do chão até o tronco
        u = k / 8
        a = u * 2.4 * math.pi
        rr = 12 * (1 - u) + 2
        pts.append((math.cos(a) * rr - 4, math.sin(a) * rr, 6 + u * 44))
    with parte(R, 'cauda', (-4, 0, 50), amp=.22):   # a cauda em espiral gira devagar
        tubo(pts, 13, corpo, radii=[.06 + .94 * (k / 8) ** 1.4 for k in range(9)], parent=R, res=5)
        if 'djinn' not in n:   # fiapos que se desprendem da cauda e somem no ar
            for k, s in ((2, -1), (3, 1), (5, -1)):
                p = Vector(pts[k])
                tubo([tuple(p), tuple(p + Vector((-7, s * 9, -1))), tuple(p + Vector((-15, s * 13, 4))), tuple(p + Vector((-19, s * 11, 10)))],
                     2.2, veu, radii=[1, .7, .35, .05], parent=R)
    sph((0, 0, 58), 15, corpo, scale=(.85, 1.05, 1.1), parent=R)                 # tronco
    sph((3, 0, 80), 11.5, corpo, parent=R)                                       # cabeça
    if escuro:
        sph((0, 0, 60), 19, veu, scale=(.9, 1.1, 1.3), parent=R)                 # véu
    maos = []
    for s in (-1, 1):
        mao = (16, s * 22, 60) if 'djinn' not in n else (10, s * 8, 62)
        maos.append(mao)
        with parte(R, 'braco', (0, s * 13, 68), **ESPECTRO_BRACO[s]):
            tubo([(0, s * 13, 68), (8, s * 22, 66), mao], 3.6, corpo, radii=[1, .8, .45], parent=R)
            for k in range(3):   # dedos longos
                cyl(mao, (mao[0] + 6, mao[1] + s * (k - 1) * 2.2, mao[2] - 3 - k), .8, .1, corpo, parent=R)
    if not escuro and 'djinn' not in n:   # órbitas fundas com um ponto aceso no fundo e a boca aberta num lamento
        for y in (-3.6, 3.6):
            sph((13.2, y, 81), 2.7, mat('gloss', '#0a080c'), scale=(.4, 1, 1.4), parent=R)
            sph((14, y, 80.4), .8, mat('emit', mix(cor, '#ffffff', .55), strength=16), parent=R)
        sph((13.6, 0, 74.6), 2.4, mat('gloss', '#0a080c'), scale=(.4, 1.05, 1.7), parent=R)
    else:
        olhos(R, (13.4, 0, 81), 1.8, cor=olho, sep=7)
    if any(k in n for k in ('espectro', 'espirito', 'eco')):   # capuz e manto esfarrapados, por trás e pelos lados
        casca(90, 30, 8, 20, math.radians(95), math.radians(265), veu, esp=.6, segs=18, rings=9, dobras=1.8, onda=1.2, rasgos=12, cx=-1, parent=R)
        casca(94, 76, 9.5, 13.5, math.radians(110), math.radians(250), corpo, esp=.8, segs=14, rings=4, dobras=.6, cx=1, parent=R)
    luz_ponto((10, 0, 64), 50 if not escuro else 25, cor, raio=.5, parent=R)
    if 'sombra' in n:   # boca faminta cheia de dentes
        sph((13, 0, 72), 5, mat('emit', '#ff3a2a', strength=3), scale=(.3, 1.4, .6), parent=R)
        for i in range(7):
            y = -6 + i * 2
            cyl((13.6, y, 74), (14, y, 71), .6, .05, mat('bone', '#f4ecd8'), parent=R)
        for s in (-1, 1):
            with parte(R, 'braco', (0, s * 13, 68), **ESPECTRO_BRACO[s]):   # garras acompanham as mãos
                for k in range(3):
                    cyl(maos[(s + 1) // 2], (maos[(s + 1) // 2][0] + 14, maos[(s + 1) // 2][1] + s * (k - 1) * 3, maos[(s + 1) // 2][2] - 6 - k * 2), 1, .05, mat('gloss', '#0a080c'), parent=R)
    if 'galho' in n:
        madeira = mat('wood', '#5a4a3a')
        for s in (-1, 1):
            tubo([(0, s * 6, 88), (-2, s * 14, 100), (2, s * 22, 108)], 1.6, madeira, radii=[1, .7, .3], parent=R)
            tubo([(-2, s * 14, 100), (-8, s * 18, 106)], 1, madeira, radii=[1, .2], parent=R)
    if 'eco' in n:
        vid = mat('glass', '#bff0ff')
        for i in range(8):
            a = i * .8
            box((math.cos(a) * 26, math.sin(a) * 26, 44 + i * 6), (5, 1, 7), vid, rot=(a, a * .7, 0), bevel=.2, parent=R)
        if 'primeira' in n:
            for i in range(12):
                a = i / 12 * math.tau
                cyl((3, 0, 80), (3 + math.cos(a) * 26, math.sin(a) * 26, 80 + math.sin(a) * 6), .5, .05, mat('emit', '#fff0b0', strength=8), parent=R)
            torus((-2, 0, 90), 12, .8, mat('emit', '#fff0b0', strength=10), rot=(0, .3, 0), parent=R)
    if 'djinn' in n:
        ouro = mat('gold', '#e0b06a')
        tubo([(-2, 0, 90), (-4, 0, 98), (-12, 0, 102), (-20, 0, 96)], 3.2, corpo, radii=[1, .8, .5, .1], parent=R)   # rabo de cavalo
        torus((-1, 0, 90), 5, 1.2, ouro, parent=R)
        for s in (-1, 1):
            torus((8, s * 16, 64), 3.4, 1, ouro, rot=(0, math.pi / 2, .6), parent=R)
        torus((0, 0, 50), 14, 1.6, mat('cloth', '#c84a3a'), scale=(.9, 1.1, .4), parent=R)       # faixa
        areia = mat('stone', '#d0b080')
        for i in range(14):
            a = i / 14 * math.tau * 2
            sph((math.cos(a) * (18 - i * .6), math.sin(a) * (18 - i * .6), 4 + i * 3), 1.3, areia, parent=R)
        olhos(R, (13.6, 0, 81), 1.6, cor='#fff0a0', sep=7)
        if 'simum' in n:
            for i in range(3):
                torus((-4, 0, 14 + i * 12), 20 - i * 4, 1, mat('emit', '#e8c890', strength=1, alpha=.5), rot=(.2, .1 * i, 0), parent=R)
    if 'nevasca' in n:
        g = mat('glass', '#d8f2ff')
        for i in range(6):
            a = i / 6 * math.tau
            cyl((3 + math.cos(a) * 9, math.sin(a) * 9, 88), (3 + math.cos(a) * 11, math.sin(a) * 11, 98 + (i % 2) * 5), 1.8, .1, g, parent=R)
        for i in range(12):
            a = i / 12 * math.tau
            sph((math.cos(a) * 30, math.sin(a) * 30, 30 + (i % 4) * 14), 1, mat('emit', '#ffffff', strength=6), parent=R)
    if 'fada' in n:
        asa = mat('glass', '#e8d8ff')
        for s in (-1, 1):
            with parte(R, 'asa', (-4, s * 8, 66), s=s, amp=.5):
                poly([(-4, s * 8, 70), (-10, s * 30, 92), (-16, s * 26, 74)], asa, esp=.3, parent=R)
                if s < 0:   # só um lado tem a asa de baixo: a outra está partida
                    poly([(-6, s * 8, 62), (-16, s * 22, 50), (-12, s * 30, 60)], asa, esp=.3, parent=R)
        for i in range(5):
            sph((-20 + i * 2, 24 + i * 3, 40 - i * 7), 1.2, asa, parent=R)
    if 'fagulha' in n:
        chama(R, (3, 0, 84), 22, '#ffb04a', r=10, n=6)
        luz_ponto((3, 0, 96), 30, '#ff9a3a', parent=R)
    if 'noite' in n:
        for i in range(14):
            a = i / 14 * math.tau
            sph((math.cos(a) * 12, math.sin(a) * 14, 40 + (i * 7) % 36), 1, mat('emit', '#fff6d0', strength=16), parent=R)
        tubo([(4, -6, 96), (8, 0, 100), (4, 6, 96)], 1.6, mat('emit', '#f0e6c0', strength=6), parent=R)        # lua crescente
        casca(86, 14, 13, 30, math.radians(120), math.radians(240), mat('cloth', '#0e0b14'), dobras=2, parent=R)  # manto
    if 'vitral' in n:   # bibliotecária: livro aberto e óculos
        with parte(R, 'braco', (0, 13, 68), **ESPECTRO_BRACO[1]):   # o livro vai na mão esquerda
            g = grupo((maos[1][0], 8, 60), rot=(0, -.6, 0), parent=R)
        box((0, -5, 0), (12, 10, 1.2), mat('leather', '#5a2a2a'), rot=(.25, 0, 0), bevel=.3, parent=g)
        box((0, 5, 0), (12, 10, 1.2), mat('leather', '#5a2a2a'), rot=(-.25, 0, 0), bevel=.3, parent=g)
        for y in (-3.6, 3.6):
            torus((13.8, y, 81), 2.4, .3, mat('gold', '#c9a54a'), rot=(0, math.pi / 2, 0), parent=R)
    return 100


# ---------------- serpentes ----------------
def F_serpent(R, nome, cor, t):
    n = _sem_acento(nome)
    corpo = pele(cor, t, 'escama') if t not in ('piche', 'ambar', 'obsidiana') else pele(cor, t, 'gloss')
    if t == 'brasa':
        corpo = mat('escama', cor)
    if 'vitral' in n:
        corpo = vitral(cor)
    if 'salamandra' in n:
        return _salamandra(R, n, cor, corpo)
    grande = 'leviata' in n or 'wyrm' in n
    r0 = 13 if grande else 9.5
    pts = []
    for k in range(12):   # espiral enrolada no chão
        u = k / 11
        a = u * 1.7 * math.tau + 1.2
        rr = 26 - u * 10
        pts.append((math.cos(a) * rr - 6, math.sin(a) * rr, r0 * .85 + u * 3))
    hx = 14 if grande else 12
    pts += [(4, 0, r0 + 10), (8, 0, 34 + (10 if grande else 0)), (hx, 0, 52 + (16 if grande else 0))]   # pescoço erguido
    m = len(pts)
    cobra = tubo(pts, r0, corpo, radii=[.12 + .88 * min(1, (k / (m - 1)) * 1.6) for k in range(m)], parent=R, res=6)
    cobra['anim'], cobra['anim_curva'], cobra['anim_n'] = 'curva', 'pescoco', 3   # o pescoço (3 últimos pontos) segue a cabeça
    barriga = mat('gloss', mix(cor, '#e8dcc0', .5)) if t not in ('vidro', 'gelo') else corpo
    hx, hy, hz = pts[-1]
    with parte(R, 'pescoco', (hx, hy, hz)):   # a cabeça balança e dá o bote; tudo que está nela vem junto
        sph((hx + 5, hy, hz + 2), r0 * 1.05, corpo, scale=(1.55, .95, .75), parent=R)          # cabeça em cunha
        sph((hx + 9, hy, hz - 3), r0 * .8, barriga, scale=(1.4, .85, .4), parent=R)            # queixo
        olhos(R, (hx + 12, hy, hz + 7), 1.8, cor='#fff2c0' if t != 'brasa' else '#ffcf5a', sep=r0 * 1.1)
        tubo([(hx + 20, hy, hz - 3), (hx + 27, hy, hz - 5), (hx + 31, hy + 2, hz - 3)], .6, mat('cloth', '#d85a5a'), parent=R)
        for y in (-1, 1):
            cyl((hx + 16, y * 3, hz - 2), (hx + 16.4, y * 3, hz - 6), .8, .05, mat('bone', '#f4ecd8'), parent=R)
        if 'prismatica' in n or 'vitral' in n:   # capuz de cobra translúcido
            casca(hz + 4, hz - 18, r0 * 1.1, r0 * 2.2, math.radians(110), math.radians(250), mat('glass', mix(cor, '#ffffff', .3)), esp=1, cx=hx - 4, parent=R)
            for k in range(4):
                sph((hx - 6, (k - 1.5) * 6, hz - 6 - k * 2), 1.6, mat('emit', '#c8f0ff', strength=8), parent=R)
        if grande:
            for s in (-1, 1):
                tubo([(hx, hy + s * 6, hz + 10), (hx - 8, hy + s * 11, hz + 20), (hx - 18, hy + s * 10, hz + 28)], 2.6, mat('bone', '#e8e0d0'), radii=[1, .6, .1], parent=R)
            if 'wyrm' in n:
                g = mat('glass', '#d8f2ff')
                for s in (-1, 1):
                    poly([(hx - 10, s * 6, hz - 8), (hx - 24, s * 30, hz + 8), (hx - 30, s * 24, hz - 12)], mat('leather', shade(cor, -.2)), esp=.5, parent=R)
                for i in range(5):
                    cyl((hx - 4 - i * 4, 0, hz + 10 - i * 4), (hx - 6 - i * 4, 0, hz + 18 - i * 4), 2, .1, g, parent=R)
            if 'leviata' in n:
                for s in (-1, 1):
                    poly([(hx - 6, s * 8, hz - 4), (hx - 16, s * 22, hz + 4), (hx - 20, s * 16, hz - 10)], mat('gloss', shade(cor, -.3)), esp=.6, parent=R)
        if 'enguia' in n:
            poly([(hx - 2, 0, hz + 8), (hx - 14, 0, hz + 14), (hx - 22, 0, hz)], mat('glass', '#8ae0f0'), esp=.4, parent=R)
            luz_ponto((hx, 0, hz), 20, '#8ae0f0', parent=R)
    if grande:   # espinhos e sombras ficam no corpo enrolado, que não se mexe
        for k in range(2, m - 3, 2):
            px, py, pz = pts[k]
            cyl((px, py, pz + r0 * .8), (px - 2, py, pz + r0 * 1.6), 3, .1, mat('bone', shade(cor, .3)), parent=R)
        if 'leviata' in n:
            for i in range(5):
                sph((pts[i * 2][0], pts[i * 2][1], 1), 6, mat('gloss', '#101418'), scale=(1.6, 1.6, .25), parent=R)
    if 'enguia' in n:
        for k in range(2, m - 3, 2):
            px, py, pz = pts[k]
            sph((px, py, pz + r0 * .8), 1.6, mat('emit', '#8ae0f0', strength=8), parent=R)
    return 78 if grande else 66


def _salamandra(R, n, cor, corpo):
    """Salamandra: lagarto de fogo com quatro patas, cauda longa e chamas nas costas."""
    pts = [(28, 0, 24), (14, 0, 20), (0, 0, 18), (-14, 0, 17), (-28, 4, 12), (-40, 10, 7), (-50, 6, 4)]
    corpo_t = tubo(pts, 10, corpo, radii=[1, 1.1, 1.05, .9, .6, .35, .1], parent=R, res=6)
    corpo_t['anim'], corpo_t['anim_curva'] = 'curva', 'cauda'   # a cauda ondula de um lado para o outro
    with parte(R, 'cabeca', (26, 0, 22), eixo='Z', amp=.08, fase=.25, atk=0.0):
        sph((32, 0, 26), 9, corpo, scale=(1.4, .9, .75), parent=R)
        olhos(R, (40, 0, 30), 1.6, cor='#ffcf5a', sep=8)
    for x in (16, -10):
        for s in (-1, 1):
            with parte(R, 'perna', (x, s * 8, 16), eixo='Z', amp=.3, fase=.5 if (x > 0) != (s > 0) else 0):
                caps((x, s * 8, 16), (x + 4, s * 18, 10), 3, corpo, parent=R)
                caps((x + 4, s * 18, 10), (x + 6, s * 20, 2), 2.6, corpo, parent=R)
                sph((x + 8, s * 20, 1.6), 3.2, corpo, scale=(1.4, 1.2, .5), parent=R)
    for k, (x, y, z) in enumerate(pts[:5]):
        chama(R, (x, y, z + 8), 10 + (4 if 'imperatriz' in n else 0) - k, '#ff5a10', r=4, n=3, forca=3.5)
    luz_ponto((0, 0, 36), 40, '#ff7a30', raio=.4, parent=R)
    if 'imperatriz' in n:
        with parte(R, 'cabeca', (26, 0, 22), eixo='Z', amp=.08, fase=.25, atk=0.0):   # coroa acompanha a cabeça
            for i in range(5):
                a = -1 + i * .5
                cyl((28 + math.cos(a) * 5, math.sin(a) * 6, 32), (26 + math.cos(a) * 6, math.sin(a) * 7, 40 + (i % 2) * 4), 1.6, .2, mat('gold', '#e8c45a'), parent=R)
    return 44


# ---------------- cavaleiros (peças de armadura do kit dos heróis) ----------------
_BODY = None


def _corpo(nome):
    global _BODY
    if _BODY is None:
        _BODY = json.load(open(os.path.join(AQUI, 'dados_jogo.json'), encoding='utf-8'))['BODY']
    return dict(_BODY[nome])


CAVALEIROS = {
    'sentinela_de_vitral':    dict(body='plate', head='greathelm', wpn='sword', off='tower', mt='#6fb0b8', c1='#2c5a60', c2='#183236', tr='#c8ffff', slit='#a8f4ff', fx='#a8f4ff', shield='#3a7a82', aura='prisms'),
    'guardiao_estilhacado':   dict(body='plate', head='greathelm', wpn='greatsword', back='cape', mt='#8fc8cf', c1='#2f5d64', c2='#183034', tr='#e0ffff', slit='#d0ffff', fx='#bff0f0', aura='mirrors'),
    'cavaleiro_oco':          dict(body='plate', head='greathelm', wpn='sword', off='round', back='cape', mt='#4a4658', c1='#2a2632', c2='#15121a', tr='#7a6a8a', slit='#c8a8ff', fx='#c8a8ff', aura='smoke'),
    'o_apagador':             dict(body='plate', cracks=1, head='horned', wpn='flamberge', back='cape', mt='#2a2630', c1='#1c1820', c2='#0e0c10', tr='#5a4a6a', fx='#ff5a4a', aura='shadow', sk='#3a3440'),
    'marinheiro_afogado':     dict(body='coat', head='tricorn', wpn='scimitar', c1='#2f4a4a', c2='#1c2e30', tr='#a89a6a', sk='#8fa89c', fx='#8affd0', aura='droplets', morto=1),
    'guarda_afogado':         dict(body='plate', head='kettle', wpn='spear', off='round', mt='#6a7a74', c1='#2a3c3a', c2='#18262a', tr='#8a8060', sk='#8fa89c', fx='#8affd0', aura='bubbles', morto=1),
    'arquiduque_afogado':     dict(body='coat', head='crown', crown='shells', wpn='rapier', back='cape', c1='#1f4a52', c2='#122e34', tr='#d8c070', sk='#7f9a90', hair='#3a4a44', fx='#8affd0', aura='droplets', morto=1),
    'sentinela_dourada':      dict(body='plate', head='crest', wpn='spear', off='tower', mt='#d8b450', c1='#8a6a2a', c2='#5a441a', tr='#f0d070', shield='#a07a2a', fx='#ffe08a', sk='#c8a070'),
    'cavaleiro_sem_nome':     dict(body='plate', head='gladhelm', wpn='greatsword', back='cape', mt='#5a5a5e', c1='#2e2c2e', c2='#18171a', tr='#7a6a50', fx='#d8d0c0', aura='ash'),
    'arauto_do_crepusculo':   dict(body='plate', tabard=1, head='crest', wpn='sunhammer', back='banner', mt='#6a5a8a', c1='#3a2f5a', c2='#22193a', tr='#e8c45a', fx='#c792ee', aura='halo', crestCol='#c792ee', sk='#b8a0c8'),
    'imediato_afogado':       dict(body='coat', head='tricorn', wpn='sword', off='dagger', c1='#3a4a42', c2='#202c28', tr='#b8a070', sk='#8fa89c', beard='#4a5a52', fx='#8affd0', aura='bubbles', morto=1),
    'guarda_do_cofre':        dict(body='plate', head='kettle', wpn='maul', off='tower', mt='#a08a5a', c1='#5a4a2a', c2='#3a2e1a', tr='#e8c45a', shield='#6a5a3a', fx='#ffd870', sk='#c8a070'),
    'sentinela_de_leitura':   dict(body='plate', head='greathelm', wpn='tome', off='tower', mt='#8a8270', c1='#4a4236', c2='#2c271f', tr='#d8c8a0', slit='#ffe0a0', shield='#5a4a36', fx='#ffe0a0', aura='runes'),
    'carcereiro_oco':         dict(body='plate', chainsBody=1, head='greathelm', wpn='chain', mt='#5a5662', c1='#2e2a34', c2='#18151c', tr='#7a6a5a', slit='#c8a8ff', fx='#c8a8ff', aura='chains'),
    'guarda_do_crepusculo':   dict(body='plate', head='visor', wpn='spear', off='round', mt='#5a5278', c1='#2e2848', c2='#1a162c', tr='#c8a0e8', fx='#c792ee', aura='stars'),
    'o_rei_sem_aurora':       dict(body='plate', cracks=1, head='greathelm', wpn='flamberge', back='cape', mt='#3a3448', c1='#241e30', c2='#120e18', tr='#d8b450', slit='#ff8a5a', fx='#ff8a5a', aura='shadow', coroa=1),
}


def F_knight(R, nome, cor, t):
    import kit_heroi as KH
    import re
    s = re.sub(r'[^a-z0-9]+', '_', _sem_acento(nome)).strip('_')
    L = dict(CAVALEIROS.get(s) or dict(body='plate', head='greathelm', wpn='sword', back='cape', mt=cor, c1=shade(cor, -.2), c2=shade(cor, -.5),
                                        tr='#8a7a5a', slit='#a0f0ff', fx='#a0f0ff'))
    L['semLanterna'] = 1
    H = KH.construir(L, _corpo(L['body']))
    H.parent = R
    H.scale = (1.15, 1.15, 1.15)
    if L.get('morto'):   # olhos de afogado acesos por cima dos olhos do rosto
        for y in (-3.6, 3.6):
            sph((10.4, y, 73.6), .9, mat('emit', '#8affd0', strength=16), parent=H)
        for i in range(5):   # algas e cracas pela roupa
            a = i * 1.3
            tubo([(math.cos(a) * 12, math.sin(a) * 12, 50), (math.cos(a) * 13, math.sin(a) * 13, 40), (math.cos(a) * 12.5, math.sin(a) * 12.5, 30)], .8, mat('cloth', '#3f6a4a'), parent=H)
            sph((math.cos(a + .5) * 12, math.sin(a + .5) * 12, 56), 1.4, mat('stone', '#cfc8b0'), parent=H)
    if L.get('coroa'):   # coroa partida por cima do elmo do rei sem aurora
        ouro = mat('gold', L['tr'])
        torus((0, 0, 88), 11, 1.4, ouro, parent=H)
        for i in range(7):
            a = i / 7 * math.tau
            if i == 2:
                continue   # ponta quebrada
            cyl((math.cos(a) * 11, math.sin(a) * 11, 88), (math.cos(a) * 11.6, math.sin(a) * 11.6, 96 + (i % 2) * 3), 1.6, .2, ouro, parent=H)
    return 104


# ---------------- esqueletos ----------------
OSSO_BRACO = {-1: dict(fase=0, amp=.22, atk=-1.1), 1: dict(fase=.5, amp=.22, atk=-.3)}   # o braço da arma golpeia
OSSO_CAB = dict(amp=.05, fase=.25, atk=.15)


def F_skeleton(R, nome, cor, t):
    n = _sem_acento(nome)
    osso = mat('bone', cor) if t != 'vidro' else vitral(cor) if 'vitral' in n else mat('glass', cor)
    gasto = mat('bone', shade(cor, -.25)) if t != 'vidro' else osso
    olho = '#8affc0' if ('afogad' in n or 'marujo' in n or 'capitao' in n) else '#78e6ff'
    if 'rei' in n:
        olho = '#ff8a4a'
    for y in (-6, 6):   # pernas
        with parte(R, 'perna', (0, y, 34), fase=.5 if y > 0 else 0, amp=.35):
            caps((0, y, 34), (1, y * 1.1, 18), 2.2, osso, parent=R)
            sph((1, y * 1.1, 18), 2.8, gasto, parent=R)
            caps((1, y * 1.1, 18), (0, y * 1.2, 4), 1.9, osso, parent=R)
            box((3, y * 1.2, 2), (8, 4, 3), osso, bevel=1, parent=R)
    torus((0, 0, 36), 7, 2.4, osso, scale=(.8, 1, .7), parent=R)                    # bacia
    for k in range(7):   # coluna
        sph((-2, 0, 38 + k * 4), 2.2, gasto, scale=(1, 1, .7), parent=R)
    for i in range(5):   # costelas
        r = 10 - abs(i - 1.5) * 1.1
        torus((1, 0, 48 + i * 4), r, 1.2, osso, scale=(.75, 1, .45), rot=(0, .12, 0), parent=R)
    box((8, 0, 52), (2, 3, 12), osso, bevel=.6, parent=R)                           # esterno
    for s in (-1, 1):   # clavículas e braços
        caps((2, s * 3, 66), (0, s * 12, 66), 1.4, osso, parent=R)
        with parte(R, 'braco', (0, s * 12, 66), **OSSO_BRACO[s]):
            caps((0, s * 12, 66), (4, s * 15, 52), 1.8, osso, parent=R)
            caps((4, s * 15, 52), (11, s * 14, 42), 1.6, osso, parent=R)
            sph((12, s * 14, 41), 2.4, osso, parent=R)
    with parte(R, 'cabeca', (0, 0, 68), **OSSO_CAB):
        sph((2, 0, 79), 11.5, osso, scale=(1.05, .95, 1), parent=R)                     # crânio grande
        with parte(R, 'boca', (4, 0, 73), amp=.1, atk=.35):   # a mandíbula bate os dentes
            box((9, 0, 70), (8, 10, 5), osso, bevel=1.6, parent=R)                      # mandíbula
            for i in range(6):
                cyl((12.6, -4 + i * 1.6, 72.4), (12.6, -4 + i * 1.6, 70.6), .6, .5, osso, parent=R)
        for y in (-3.8, 3.8):
            sph((10.6, y, 79), 3.8, mat('gloss', '#0d0a08'), scale=(.6, 1, 1.15), parent=R)
            sph((12, y, 79), 1.2, mat('emit', olho, strength=16), parent=R)
        sph((12.4, 0, 74.6), 1.4, mat('gloss', '#0d0a08'), scale=(.5, 1, 1), parent=R)
        luz_ponto((16, 0, 79), 8, olho, parent=R)
    tanga = mat('cloth', '#3a3028')
    casca(40, 22, 9, 13, math.radians(-60), math.radians(60), tanga, dobras=2, parent=R)
    # arma enferrujada na mão direita e escudo partido na esquerda
    with parte(R, 'braco', (0, -12, 66), **OSSO_BRACO[-1]):   # a arma acompanha o braço direito
        g = grupo((12, -14, 41), rot=(.35, .1, 0), parent=R)
    ferrugem = mat('metal', '#7a6a5a', rough=.7)
    if 'vigia' in n or 'arauto' in n:
        cyl((0, 0, -30), (0, 0, 48), 1, 1, mat('wood', '#4a3a2a'), parent=g)
        cyl((0, 0, 48), (0, 0, 60), 2.6, .1, ferrugem, parent=g)
    elif 'rei' in n:
        box((0, 0, 26), (2, 6, 48), mat('metal', '#5a5048', rough=.5), bevel=.3, parent=g)
        box((0, 0, 1), (2.6, 16, 2.6), mat('gold', '#b89a4a'), bevel=.4, parent=g)
    else:
        box((0, 0, 16), (1.6, 4, 28), ferrugem, bevel=.3, parent=g)
        box((0, 0, 1), (2.4, 11, 2), mat('wood', '#4a3a2a'), bevel=.3, parent=g)
    if 'marujo' not in n and 'capitao' not in n and 'vigia' not in n:
        with parte(R, 'braco', (0, 12, 66), **OSSO_BRACO[1]):   # o escudo acompanha o braço esquerdo
            g2 = grupo((10, 15, 44), rot=(0, math.pi / 2 - .2, .4), parent=R)
        cyl((0, 0, -1), (0, 0, 1.4), 10, 9.5, mat('wood', '#5a4026'), parent=g2)
        torus((0, 0, 1), 9.5, .8, ferrugem, parent=g2)
    if 'vigia' in n:   # elmo amassado e lanterna pendurada
        with parte(R, 'cabeca', (0, 0, 68), **OSSO_CAB):
            cupula((1, 0, 81), 12.4, ferrugem, parent=R)
        with parte(R, 'braco', (0, 12, 66), **OSSO_BRACO[1]):
            g3 = grupo((12, 15, 34), parent=R)
            box((0, 0, 0), (5, 5, 7), mat('glass', '#ffd9a0'), bevel=.4, parent=g3)
            sph((0, 0, 0), 1.6, mat('emit', '#ffbe5a', strength=14), parent=g3)
            cyl((0, 0, 3.6), (0, 0, 8), .3, .3, ferrugem, parent=g3)
            luz_ponto((12, 15, 34), 14, '#ffb25a', parent=R)
    if 'rei' in n:
        casca(66, 8, 12, 22, math.radians(115), math.radians(245), mat('cloth', '#5a1a2a'), dobras=1.6, parent=R)
        ouro = mat('gold', '#d8b450')
        with parte(R, 'cabeca', (0, 0, 68), **OSSO_CAB):
            torus((1, 0, 89), 9.6, 1.2, ouro, parent=R)
            for i in range(6):
                a = i / 6 * math.tau
                cyl((1 + math.cos(a) * 9.6, math.sin(a) * 9.6, 89), (1 + math.cos(a) * 10.2, math.sin(a) * 10.2, 96 + (i % 2) * 3), 1.4, .2, ouro, parent=R)
        for i in range(8):   # gola de pele
            a = i / 8 * math.tau
            sph((math.cos(a) * 9 - 2, math.sin(a) * 11, 66), 4, mat('fur', '#3a2e28'), parent=R)
    if 'capitao' in n or 'marujo' in n:
        chapeu = mat('cloth', '#2a2622')
        with parte(R, 'cabeca', (0, 0, 68), **OSSO_CAB):
            cyl((1, 0, 88), (1, 0, 90), 17, 17, chapeu, verts=3, parent=R)
            sph((1, 0, 90), 10, chapeu, scale=(1, 1, .6), parent=R)
            if 'capitao' in n:
                tubo([(-2, 4, 94), (-10, 10, 104), (-20, 12, 106)], 2, mat('cloth', '#d8d0c0'), radii=[1, .8, .2], parent=R)
            else:
                torus((2, 0, 84), 11, 1.6, mat('cloth', '#8a2a2a'), scale=(1, 1, .4), parent=R)        # bandana
        if 'capitao' in n:
            casca(64, 14, 12, 18, math.radians(110), math.radians(250), mat('cloth', '#1e3a3a'), dobras=1.4, parent=R)
            with parte(R, 'braco', (0, 12, 66), **OSSO_BRACO[1]):
                torus((12, 14, 41), 3, .6, mat('metal', '#9aa2a0'), rot=(math.pi / 2, 0, 0), parent=R)   # gancho
        for i in range(4):
            a = i * 1.5
            sph((math.cos(a) * 9, math.sin(a) * 10, 50 + i * 4), 1.4, mat('stone', '#cfc8b0'), parent=R)
    if 'arauto' in n:
        tubo([(-6, 10, 66), (-8, 14, 102)], 1, mat('wood', '#5a4026'), parent=R)
        poly([(-8, 14, 100), (-24, 14, 98), (-26, 14, 82), (-16, 14, 86), (-8, 14, 84)], mat('cloth', '#6a5a8a'), esp=.5, parent=R)
    if t == 'vidro':
        for i in range(5):
            a = i * 1.25
            cyl((math.cos(a) * 8, math.sin(a) * 8, 70), (math.cos(a) * 10, math.sin(a) * 10, 80), 1.6, .1, mat('glass', '#bff0f0'), parent=R)
    return 92


# ---------------- treants ----------------
def F_treant(R, nome, cor, t):
    n = _sem_acento(nome)
    sem = _semente(n)
    casca_m = mat('wood', '#5a4630')
    escura = mat('wood', '#3a2c1e')
    toco = 'toco' in n
    alto = 54 if toco else 84
    for s in (-1, 1):   # raízes que servem de pés
        for k in range(3):
            a = s * (.5 + k * .45)
            tubo([(0, s * 6, 22), (math.cos(a) * 14, math.sin(a) * 16, 10), (math.cos(a) * 24, math.sin(a) * 26, 1)], 4.2 - k * .8, escura, radii=[1, .7, .3], parent=R)
    for i in range(5):   # tronco feito de fibras torcidas
        a = i / 5 * math.tau
        pts = [(math.cos(a + u * 1.6) * (12 - u * 3), math.sin(a + u * 1.6) * (13 - u * 3), 6 + u * (alto - 6)) for u in (0, .3, .6, 1)]
        tubo(pts, 7.4 if not toco else 9.4, casca_m, radii=[1.1, 1, .9, .8], parent=R)
    cyl((0, 0, 10), (0, 0, alto - 4), 12 if not toco else 15, 9 if not toco else 14, escura, verts=14, parent=R)
    zf = alto * .62
    for y in (-4.6, 4.6):   # rosto entalhado na casca
        sph((11, y, zf), 3.2, mat('gloss', '#0e0a06'), scale=(.6, 1, .8), parent=R)
        sph((12, y, zf), 1.6, mat('emit', '#c8f06a', strength=14), parent=R)
    box((13.5, 0, zf - 10), (1.6, 9, 3.6), mat('gloss', '#0e0a06'), bevel=.6, parent=R)
    rocha((14, 0, zf + 4), 5, casca_m, escala=(.5, 2, .5), semente=sem, parent=R)   # sobrancelha grossa
    luz_ponto((18, 0, zf), 10, '#c8f06a', parent=R)
    for s in (-1, 1):   # braços de galho com dedos de graveto
        ombro = (0, s * 12, alto - 16)
        cot = (6, s * 26, alto - 26)
        mao = (12, s * 30, alto - 44)
        with parte(R, 'braco', ombro, fase=.5 if s > 0 else 0, amp=.16, atk=-.7):
            tubo([ombro, cot, mao], 4, casca_m, radii=[1, .8, .5], parent=R)
            for k in range(4):
                tubo([mao, (mao[0] + 6 + k, mao[1] + s * (k - 1.5) * 3, mao[2] - 8 - k * 1.4)], 1, escura, radii=[1, .1], parent=R)
    musgo = mat('fur', '#5f8a4a')
    for i in range(6):   # musgo pendurado
        a = i / 6 * math.tau
        tubo([(math.cos(a) * 12, math.sin(a) * 13, alto - 8), (math.cos(a) * 14, math.sin(a) * 15, alto - 18), (math.cos(a) * 13, math.sin(a) * 14, alto - 28)], 1.6, musgo, radii=[1, .7, .2], parent=R)
    if not toco:
        copa = mat('fur', cor)
        copa2 = mat('fur', shade(cor, -.25))
        with parte(R, 'caule', (0, 0, alto - 6), amp=.05, atk=.08):   # a copa balança com o vento
            for (x, y, z, r) in ((0, 0, alto + 14, 20), (-6, -16, alto + 4, 15), (-6, 16, alto + 4, 15), (6, 0, alto + 2, 13), (-12, 0, alto + 10, 16),
                                 (4, -12, alto + 16, 12), (4, 12, alto + 16, 12)):
                rocha((x, y, z), r, copa if (x + y) % 2 == 0 else copa2, semente=sem + int(x + y + z), aspereza=.35, sub=3, parent=R, liso=True)
            for s in (-1, 1):
                tubo([(0, s * 8, alto - 4), (-2, s * 16, alto + 6), (-6, s * 24, alto + 14)], 2.4, casca_m, radii=[1, .7, .3], parent=R)
            if 'avo' in n:
                flor = mat('cloth', '#f0b8d8')
                for i in range(12):
                    a = i / 12 * math.tau
                    sph((math.cos(a) * 18, math.sin(a) * 20, alto + 10 + (i % 3) * 6), 2.4, flor, parent=R)
                for i in range(4):
                    sph((math.cos(i * 1.6) * 16, math.sin(i * 1.6) * 16, alto - 2), 2.6, mat('emit', '#f6d070', strength=6), parent=R)
                luz_ponto((0, 0, alto + 4), 30, '#f6d070', parent=R)
        return alto + 32
    # toco ranzinza: topo cortado com anéis, cogumelos e uma folhinha teimosa
    cyl((0, 0, alto - 2), (0, 0, alto), 14.6, 14.6, mat('wood', '#c8a878'), verts=16, parent=R)
    for k in range(3):
        torus((0, 0, alto + .1), 4 + k * 3.6, .35, mat('wood', '#8a6a48'), scale=(1, 1, .2), parent=R)
    for i in range(3):
        a = i * 2.2
        cyl((math.cos(a) * 15, math.sin(a) * 15, 14 + i * 8), (math.cos(a) * 18, math.sin(a) * 18, 14 + i * 8), 4, 4, mat('cloth', '#d0804a'), parent=R).scale = (1, 1, .4)
    tubo([(2, 0, alto), (4, 2, alto + 8), (8, 4, alto + 12)], .5, musgo, parent=R)
    poly([(8, 4, alto + 12), (14, 8, alto + 16), (12, 2, alto + 14)], mat('cloth', '#7aa85a'), esp=.3, parent=R)
    return alto + 14


FAMILIAS = {n[2:]: f for n, f in globals().items() if n.startswith('F_')}
SIMPLES = {'jelly', 'spider', 'imp', 'plant', 'crab', 'eye', 'mimic', 'worm', 'tome', 'maw'}   # gosmas e cogumelos cuidam do próprio tema
RAIO = {'beast': 46, 'spider': 44, 'crab': 44, 'serpent': 40, 'mimic': 40, 'worm': 34, 'plant': 38, 'flyer': 34, 'tome': 32,
        'golem': 46, 'knight': 36, 'treant': 40, 'wisp': 34, 'jelly': 34, 'skeleton': 30, 'eye': 30, 'imp': 28, 'blob': 40, 'mushroom': 34, 'maw': 36}


def construir(nome, kind, cor, papel=None, marcador=True):
    """papel: None (comum), 'boss' (chefe de região), 'field' (errante), 'mini' (subchefe), 'dboss' (chefe de masmorra).
    marcador: desenha o círculo de runas do papel no chão (só no conceito; o sprite do jogo fica limpo)."""
    R = raiz('monstro')
    t = tema(nome)
    topo = FAMILIAS.get(kind, F_blob)(R, nome, cor, t)
    if kind in SIMPLES:
        efeitos(R, nome, cor, t, topo)
    if marcador:
        marca(R, papel, RAIO.get(kind, 36))
    return R, topo


# ---------------- animação: pose de cada quadro do sprite do jogo ----------------
# Cada parte marcada com "with parte(...)" tem um tipo; aqui o tipo vira movimento.
# f vai de 0 a 1 ao longo do ciclo de QUADROS quadros; ataque=True dá a pose do golpe, renderizada num quadro à parte.
QUADROS = 6
AMP = {'perna': .42, 'asa': .55, 'cauda': .28, 'tent': .2, 'braco': .2, 'cabeca': .06, 'boca': .1, 'tampa': .12, 'capa': .3,
       'garra': .1, 'caule': .07, 'pupila': .22, 'dentes': 1.4, 'lingua': .3}
EIXO = {'asa': 0, 'capa': 0, 'cauda': 2, 'pupila': 2, 'lingua': 2}   # as outras partes giram em Y (para a frente e para trás)
ATAQUE = {'asa': 1.2, 'braco': -1.0, 'cabeca': .2, 'boca': .35, 'tampa': -.45, 'capa': .55, 'garra': -.5, 'caule': .3, 'lingua': .5}
ANDAM = {'beast', 'spider', 'crab', 'skeleton', 'knight', 'golem', 'mimic'}
VOAM = {'flyer', 'imp'}


def _partes(o):
    for c in o.children:
        if 'anim' in c:
            yield c
        yield from _partes(c)


def _curva(e, d, f, ataque):
    """Curvas que mudam de forma: 'pescoco' leva os últimos pontos junto com a cabeça; 'cauda' ondula do ponto 4 em diante."""
    sp = e.data.splines[0]
    if 'rest_pts' not in e:
        e['rest_pts'] = [tuple(p.co) for p in sp.bezier_points]
    rest = [Vector(p) for p in e['rest_pts']]
    m = len(rest)
    for i, p in enumerate(sp.bezier_points):
        p.co = rest[i]
    if e['anim_curva'] == 'pescoco':
        n = e.get('anim_n', 3)
        for j in range(n):
            sp.bezier_points[m - n + j].co = rest[m - n + j] + d * ((j + 1) / n)
    else:
        for j in range(4, m):
            peso = (j - 3) / (m - 4)
            dy = 0 if ataque else math.sin(math.tau * f - j * .9) * 7 * peso
            sp.bezier_points[j].co = rest[j] + Vector((0, dy * U, 0))
    e.data.update_tag()


def pose(R, kind, f, ataque=False):
    if 'rot_z' not in R:
        R['rot_z'] = R.rotation_euler.z
    w = math.tau * f
    # pescoço das serpentes enroladas (unidades do jogo): balança no ciclo e dá o bote no ataque
    pesc = Vector((12, 0, -6)) if ataque else Vector((math.sin(w) * 3, math.cos(w) * 3, math.sin(2 * w) * 1.5))
    for e in _partes(R):
        tipo = e['anim']
        if tipo == 'curva':
            _curva(e, pesc * U, f, ataque)
            continue
        if 'rest_loc' not in e:
            e['rest_loc'] = tuple(e.location)
            e['rest_rot'] = tuple(e.rotation_euler)
        loc, rot = Vector(e['rest_loc']), list(e['rest_rot'])
        amp = e.get('anim_amp', AMP.get(tipo, .2))
        s = e.get('anim_s', 1)
        x = math.sin(w + e.get('anim_fase', 0.0) * math.tau)
        if tipo == 'pescoco':
            e.location = loc + pesc * U
            continue
        if tipo == 'dentes':   # fileiras de dentes se afastam (s = +1 em cima, -1 embaixo)
            e.location = loc + Vector((0, 0, s * (e.get('anim_atk', 4.0) if ataque else amp * (.5 + .5 * x)) * U))
            continue
        if tipo == 'tent':     # balança para fora e para dentro, em volta do eixo perpendicular à direção do tentáculo
            a = e.get('anim_ang', 0.0)
            e.rotation_mode = 'QUATERNION'
            e.rotation_quaternion = Quaternion((-math.sin(a), math.cos(a), 0), amp * (1.5 if ataque else x))
            continue
        eixo = 'XYZ'.index(e['anim_eixo']) if 'anim_eixo' in e else EIXO.get(tipo, 1)
        if ataque:
            v = e.get('anim_atk', ATAQUE.get(tipo, 0.0))
        elif tipo == 'boca':
            v = amp * (.5 + .5 * x)   # só abre: fechar mais entraria no crânio
        else:
            v = amp * (x + e.get('anim_vies', 0.0))   # vies desloca o balanço para um dos lados
        if tipo in ('asa', 'capa'):
            v *= s
        rot[eixo] += v
        e.rotation_euler = rot
        e.location = loc
    # o corpo inteiro: respira, pula, flutua ou se inclina para o golpe
    dz, lean, sx, sz = 0.0, 0.0, 1.0, 1.0
    if ataque:
        lean = .08 if kind in ('jelly', 'eye', 'tome', 'mimic', 'maw') else .16
        if kind == 'blob':
            sx, sz = 1.08, .9
    elif kind in ('blob', 'jelly'):
        k = math.sin(w) * (.06 if kind == 'blob' else .05)
        sx, sz = 1 + k * .5, 1 - k
    elif kind == 'mushroom':
        dz = abs(math.sin(w)) * 4
        k = math.cos(2 * w) * .04
        sx, sz = 1 + k, 1 - k
    elif kind in VOAM:
        dz = math.sin(w + math.pi) * 2.5   # sobe quando as asas descem
    elif kind in ANDAM:
        dz = abs(math.sin(2 * w)) * (1.2 if kind == 'golem' else .6)
    elif kind == 'wisp':
        lean = math.sin(w) * .05
    R.location = (0, 0, dz * U)
    R.scale = (sx, sx, sz)
    R.rotation_euler = (0, lean, R['rot_z'])
