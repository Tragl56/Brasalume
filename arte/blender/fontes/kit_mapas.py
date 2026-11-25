# Kit de mapas do Brasalume no Blender: peças de cenário (as mesmas do desenho do jogo, em 3D), cena de região
# (losango isométrico como o mapa do jogo, com toca do chefe, portal e entrada de masmorra) e cena de masmorra
# (sala com piso de lajotas, paredes do fundo, tochas e a decoração do tema). Desenhos originais.
import math
import random
import bpy
from mathutils import Vector
from kit_base import mat, shade, mix, sph, cyl, caps, box, torus, tubo, poly, raiz, luz_ponto, V, U, hex_lin, _link
import bmesh
from kit_heroi import grupo
from kit_monstros import rocha, chama, relevo, pelo, espalhar, olhos
import kit_base as KB


def _monstro_polido(KM, *args, **kw):
    """Monstro de cena com o acabamento dos sprites do jogo (manchas, sombra nas dobras, pelo); o resto da cena fica como está."""
    antes = KB.ACAB
    KB.ACAB = True
    try:
        return KM.construir(*args, **kw)
    finally:
        KB.ACAB = antes

ESC_PECA = 1.0


# ---------------- materiais de chão ----------------
def mat_chao(a, b, escala=6.0, rugo=.92, nome='chao'):
    """Chão com manchas: ruído mistura as duas cores do jogo; relevo leve."""
    m = bpy.data.materials.new('%s_%s_%s' % (nome, a, b))
    if hasattr(m, 'use_nodes'):
        m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = rugo
    tex = nt.nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = escala
    tex.inputs['Detail'].default_value = 8
    rampa = nt.nodes.new('ShaderNodeValToRGB')
    rampa.color_ramp.elements[0].position, rampa.color_ramp.elements[1].position = .35, .65
    rampa.color_ramp.elements[0].color = hex_lin(a)
    rampa.color_ramp.elements[1].color = hex_lin(b)
    nt.links.new(tex.outputs['Fac'], rampa.inputs['Fac'])
    nt.links.new(rampa.outputs['Color'], bsdf.inputs['Base Color'])
    tex2 = nt.nodes.new('ShaderNodeTexNoise')
    tex2.inputs['Scale'].default_value = escala * 9
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .35
    nt.links.new(tex2.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_agua(cor):
    return mat('gloss', cor, rough=.08)


# ---------------- peças de cenário (origem no chão, olham para a câmera em qualquer giro) ----------------
VERDES = ('trees', 'reeds', 'ruins', 'dawn', 'rocks', 'pale')   # regiões de chão com mato


def capim(g, c, r, n=None, alt=3.0, rnd=None):
    """Capim baixo num anel em volta da base da peça, nas regiões de chão com mato. Só os fios aparecem: o anel que os
    carrega some no render, para não virar uma mancha de outra cor sobre o chão do jogo."""
    if c['decor'] not in VERDES:
        return
    ri, ro, segs = r * .72, r * 1.18, 28
    me = bpy.data.meshes.new('capim')
    bm = bmesh.new()
    dentro = [bm.verts.new(V((math.cos(k / segs * math.tau) * ri, math.sin(k / segs * math.tau) * ri, .2))) for k in range(segs)]
    fora = [bm.verts.new(V((math.cos(k / segs * math.tau) * ro, math.sin(k / segs * math.tau) * ro, .2))) for k in range(segs)]
    for k in range(segs):
        bm.faces.new((dentro[k], fora[k], fora[(k + 1) % segs], dentro[(k + 1) % segs]))
    bm.to_mesh(me)
    bm.free()
    base = bpy.data.objects.new('capim', me)
    bpy.context.collection.objects.link(base)
    base.data.materials.append(mat('cloth', '#2a3a2a'))
    _link(base, g)
    n = n or max(40, min(220, int(.22 * math.pi * (ro * ro - ri * ri))))
    cor = '#aeb8a6' if c['decor'] == 'pale' else shade(c['folha'], .1)
    pelo(base, cor, comp=alt, n=n, pente=(0, 0, 1), solto=2.4, raio=.55, filhos=4)
    try:
        base.show_instancer_for_render = False   # no Blender 5 o disco que emite os fios some do render por aqui
    except Exception as e:
        print('capim', e)


def musgo_fios(p, r, c, g, achatado=.3):
    """Manta de musgo (fios curtos e densos) por cima de uma pedra ou coluna."""
    m = sph(p, r, mat('fur', '#4f6a3a'), scale=(1.2, 1, achatado), parent=g)
    pelo(m, '#6f8f48', comp=1.4, n=int(60 * r), pente=(0, 0, 1), solto=1.6, raio=.4, filhos=4)
    return m


def pedrinhas(g, c, r, rnd, n=5, cor=None):
    """Cascalho solto em volta da base."""
    m = mat('stone', cor or shade(c['pedra'], -.25))
    for k in range(n):
        a = rnd.random() * math.tau
        d = r * rnd.uniform(.9, 1.4)
        rocha((math.cos(a) * d, math.sin(a) * d, .8), rnd.uniform(1.6, 3.2), m, semente=rnd.randint(0, 300), parent=g)


def _cores(decor, dados):
    g = dados['GROUND'].get(decor, dados['GROUND']['trees'])
    folha = dados['FOLIAGE'].get(decor, '#3f7048')
    pedra = shade(g[1], .22)
    return {'folha': folha, 'pedra': pedra, 'chao': g, 'decor': decor}


def _estrela(o, rnd, fundo=.7, caida=.12):
    """Base do cone em estrela: pontas de galho (um pouco caídas) e reentrâncias, como um pinheiro desenhado."""
    me = o.data
    zs = [v.co.z for v in me.vertices]
    zmin, alt = min(zs), max(zs) - min(zs)
    anel = sorted((v for v in me.vertices if abs(v.co.z - zmin) < 1e-7), key=lambda v: math.atan2(v.co.y, v.co.x))
    for k, v in enumerate(anel):
        if k % 2:
            v.co.x *= fundo
            v.co.y *= fundo
            v.co.z += alt * .07
        else:
            v.co.z -= alt * caida * (.4 + .6 * rnd.random())
    me.update()


def P_pine(g, c, rnd, neve=False):
    madeira = mat('wood', '#3a2a1c')
    cyl((0, 0, 0), (0, 0, 34), 5, 3.4, madeira, verts=10, parent=g)
    for k in range(3):   # raízes aparentes
        a = k / 3 * math.tau + rnd.random()
        tubo([(0, 0, 4), (math.cos(a) * 7, math.sin(a) * 7, 1), (math.cos(a) * 11, math.sin(a) * 11, 0)], 1.8, madeira, radii=[1, .6, .2], parent=g)
    base = '#2d5242' if neve else shade(c['folha'], -.1)
    for i, (z0, z1, r) in enumerate(((22, 74, 36), (52, 102, 29), (82, 128, 22), (108, 152, 14))):
        m = mat('fur', shade(base, i * .05))
        o = cyl((0, 0, z0), (0, 0, z1), r, .6, m, verts=18, parent=g)
        o.rotation_mode = 'XYZ'
        o.rotation_euler[2] = rnd.random() * 3
        _estrela(o, rnd)   # pontas de galho em estrela, um pouco caídas
        b = cyl((0, 0, z0 - 2), (0, 0, z0 + 6), r * 1.02, r * .86, mat('fur', shade(base, -.2)), verts=18, parent=g)   # borda escura do galho
        _estrela(b, rnd)
        b.rotation_mode = 'XYZ'
        b.rotation_euler[2] = o.rotation_euler[2]
        if neve:
            nv = cyl((0, 0, z1 - (z1 - z0) * .42), (0, 0, z1 + .5), r * .46, .4, mat('cloth', '#eef4f8'), verts=14, parent=g)
            relevo(nv, forca=2.4, escala=4, sub=2, semente=rnd.randint(0, 99))
    capim(g, c, 14)
    return 152


def P_snowpine(g, c, rnd):
    return P_pine(g, c, rnd, neve=True)


def P_round(g, c, rnd):
    madeira = mat('wood', '#3a2a1c')
    tubo([(0, 0, 0), (2, 1, 26), (-1, 0, 52), (1, 0, 70)], 5.2, madeira, radii=[1.3, 1, .85, .7], parent=g)
    for s in (-1, 1):
        tubo([(0, 0, 50), (6, s * 12, 64), (10, s * 18, 76)], 2.2, madeira, radii=[1, .7, .3], parent=g)
    folha, escura = mat('fur', c['folha']), mat('fur', shade(c['folha'], -.18))
    sem = rnd.randint(0, 99)
    for k, (x, y, z, r) in enumerate(((-10, -12, 74, 24), (10, 12, 76, 24), (0, 0, 96, 28), (-4, 14, 92, 18), (8, -10, 98, 17))):
        cacho = rocha((x, y, z), r, folha if k >= 2 else escura, semente=sem + k, aspereza=.28, sub=3, liso=True, parent=g)
        relevo(cacho, forca=4.5, escala=4.5, sub=1, semente=sem + k)   # cachos de folhas
    capim(g, c, 12)
    return 124


def P_bush(g, c, rnd):
    folha, escura = mat('fur', c['folha']), mat('fur', shade(c['folha'], -.15))
    sem = rnd.randint(0, 99)
    for k, (x, y, z, r) in enumerate(((-8, 0, 10, 13), (8, 2, 10, 13), (0, -2, 18, 15))):
        cacho = rocha((x, y, z), r, folha if k == 2 else escura, semente=sem + k, aspereza=.3, sub=3, liso=True, parent=g)
        relevo(cacho, forca=3.4, escala=3.5, sub=1, semente=sem + k)
    for k in range(4):
        sph((rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(14, 26)), 1.8, mat('cloth', '#b84a4a' if c['decor'] != 'pale' else '#e8e0f0'), parent=g)
    return 32


def P_birch(g, c, rnd):
    casca_m = mat('wood', '#d9dde0')
    tubo([(0, 0, 0), (2, 0, 40), (-2, 1, 84), (1, 0, 118)], 4.4, casca_m, radii=[1.2, 1, .85, .6], parent=g)
    for i in range(7):
        z = 10 + i * 15
        box((rnd.uniform(-.5, .5), 0, z), (9, 9.6, 1.4 + rnd.random()), mat('wood', '#2b2f35'), rot=(0, 0, rnd.random() * 3), bevel=.3, parent=g)
    for s in (-1, 1):
        tubo([(0, 0, 76), (6, s * 14, 92), (8, s * 22, 104)], 1.4, casca_m, radii=[1, .6, .2], parent=g)
    copa = mat('fur', '#c8d4c8')
    for k in range(7):
        a = k / 7 * math.tau
        cacho = rocha((math.cos(a) * 14, math.sin(a) * 14, 112 + (k % 3) * 8), 11, copa, semente=k + rnd.randint(0, 50), aspereza=.3, sub=2, liso=True, parent=g)
        relevo(cacho, forca=3, escala=3.5, sub=1, semente=k)
    capim(g, c, 9)
    return 136


def P_dead(g, c, rnd):
    m = mat('wood', shade(c['pedra'], -.45))
    tubo([(0, 0, 0), (2, 0, 30), (-2, 0, 60), (2, 1, 86)], 5, m, radii=[1.3, 1, .7, .3], parent=g)
    for (z, a, comp) in ((40, 2.6, 26), (54, -.4, 22), (68, 1.4, 18), (30, -2.2, 14)):
        p = (0, 0, z)
        q = (math.cos(a) * comp, math.sin(a) * comp, z + comp * .6)
        r_ = (math.cos(a + .4) * comp * 1.4, math.sin(a + .4) * comp * 1.4, z + comp * 1.1)
        tubo([p, q, r_], 2.2, m, radii=[1, .6, .15], parent=g)
    for k in range(3):
        a = k / 3 * math.tau
        tubo([(0, 0, 6), (math.cos(a) * 10, math.sin(a) * 10, 2), (math.cos(a) * 16, math.sin(a) * 16, 0)], 2.4, m, radii=[1, .6, .2], parent=g)
    return 100


def P_rock(g, c, rnd, grande=False):
    r = 26 if grande else 16
    pedra = mat('stone', shade(c['pedra'], -.2))
    rocha((0, 0, r * .5), r, pedra, escala=(1.2, 1, .75), semente=rnd.randint(0, 200), parent=g)
    if grande:
        for k in range(3):
            a = rnd.random() * math.tau
            rocha((math.cos(a) * r * 1.2, math.sin(a) * r * 1.2, 4), 7, pedra, semente=rnd.randint(0, 200), parent=g)
    if c['decor'] == 'peaks':
        rocha((0, 0, r * .95), r * .7, mat('cloth', '#eef4f8'), escala=(1.1, .9, .35), semente=7, aspereza=.2, parent=g)
    if c['decor'] in ('trees', 'reeds', 'ruins', 'dawn'):
        musgo_fios((r * .1, 0, r * .88), r * .55, c, g)   # musgo no topo
    pedrinhas(g, c, r * 1.05, rnd, n=4 if not grande else 6)
    return r * 1.3


def P_boulder(g, c, rnd):
    return P_rock(g, c, rnd, grande=True)


def P_reeds(g, c, rnd):
    caule = mat('cloth', shade(c['folha'], .1))
    for i in range(9):
        x, y = rnd.uniform(-8, 8), rnd.uniform(-8, 8)
        h = rnd.uniform(34, 56)
        tubo([(x, y, 0), (x + rnd.uniform(-2, 2), y, h * .5), (x + rnd.uniform(-5, 5), y + rnd.uniform(-3, 3), h)], .9, caule, radii=[1, .8, .3], parent=g)
        if i % 3 == 0:
            sph((x + rnd.uniform(-2, 2), y, h * .82), 2, mat('fur', '#4a3523'), scale=(1, 1, 2.6), parent=g)
    for i in range(4):
        poly([(0, 0, 0), (rnd.uniform(-16, 16), rnd.uniform(-16, 16), rnd.uniform(10, 18)), (rnd.uniform(-4, 4), rnd.uniform(-4, 4), 0)], caule, esp=.4, parent=g)
    return 56


def P_pond(g, c, rnd):
    cyl((0, 0, 0), (0, 0, 1.2), 40, 40, mat_agua(shade(c['chao'][0], -.25)), verts=32, parent=g).scale = (1, .8, 1)
    for k in range(9):
        a = k / 9 * math.tau
        rocha((math.cos(a) * 40, math.sin(a) * 32, 2), 5 + rnd.random() * 3, mat('stone', shade(c['pedra'], -.25)), semente=k, parent=g)
    return 8


def P_column(g, c, rnd):
    pedra = mat('stone', shade(c['pedra'], .05))
    h = rnd.uniform(64, 90)
    box((0, 0, 4), (30, 30, 8), pedra, bevel=1.2, parent=g)
    cyl((0, 0, 8), (0, 0, h), 11, 10, pedra, verts=16, parent=g)
    for k in range(8):
        a = k / 8 * math.tau
        box((math.cos(a) * 10.6, math.sin(a) * 10.6, 8 + (h - 8) / 2), (1.4, 1.4, h - 10), mat('stone', shade(c['pedra'], -.15)), rot=(0, 0, a), bevel=.3, parent=g)
    rocha((1, 0, h + 2), 10, pedra, escala=(1, 1, .6), semente=rnd.randint(0, 99), parent=g)   # topo quebrado
    rocha((26, 10, 4), 8, pedra, semente=rnd.randint(0, 99), parent=g)                           # pedaço caído
    escura = mat('gloss', '#14110e')
    for k in range(3):   # rachaduras na pedra
        a = -.9 + k * .7
        z = h * rnd.uniform(.3, .8)
        tubo([(math.cos(a) * 11.2, math.sin(a) * 11.2, z), (math.cos(a + .1) * 11.2, math.sin(a + .1) * 11.2, z - 7), (math.cos(a - .05) * 11, math.sin(a - .05) * 11, z - 13)],
             .45, escura, radii=[1, .7, .2], parent=g)
    if c['decor'] in ('ruins', 'dawn', 'sunken', 'trees'):   # trepadeira subindo pela coluna
        folha = mat('fur', '#4f7a44' if c['decor'] != 'sunken' else '#2f5a50')
        pts = [(math.cos(-.6 + u * 2.4) * 11.4, math.sin(-.6 + u * 2.4) * 11.4, 6 + u * h * .8) for u in (0, .25, .5, .75, 1)]
        tubo(pts, .9, folha, parent=g)
        for (x, y, z) in pts[1:]:
            sph((x * 1.05, y * 1.05, z), 2.4, folha, scale=(1, 1, .6), parent=g)
    capim(g, c, 17, alt=1.8)
    if c['decor'] == 'ruins':
        box((10.4, 0, h * .55), (1, 4, 14), mat('emit', '#7ed2d2', strength=3), bevel=.2, parent=g)
        luz_ponto((16, 0, h * .55), 8, '#7ed2d2', parent=g)
    return h + 8


def P_glass(g, c, rnd):
    vid = mat('glass', '#8cdcdc')
    for i in range(4):
        x, y = (i - 1.5) * 9, rnd.uniform(-6, 6)
        h = 24 + i % 2 * 16 + rnd.random() * 8
        o = cyl((x, y, 0), (x + rnd.uniform(-4, 4), y, h), 4.6, .3, vid, verts=4, parent=g)
    luz_ponto((0, 0, 20), 10, '#8cdcdc', parent=g)
    return 48


def P_obelisk(g, c, rnd):
    arenito = mat('stone', '#9a7a4a')
    box((0, 0, 3), (30, 30, 6), arenito, bevel=1, parent=g)
    o = cyl((0, 0, 6), (0, 0, 104), 13, 8, arenito, verts=4, parent=g)
    o.rotation_mode = 'QUATERNION'
    cyl((0, 0, 104), (0, 0, 118), 8, .3, mat('gold', '#c8a050'), verts=4, parent=g)
    for i in range(6):
        box((9.4 - i * .4, 0, 20 + i * 13), (1, 5, 6), mat('gloss', '#3a2a14'), rot=(0, .06, 0), bevel=.2, parent=g)
    for k in range(4):   # areia acumulada na base
        sph((math.cos(k * 1.6) * 16, math.sin(k * 1.6) * 16, 0), 10, mat('stone', '#c8a46a'), scale=(1.4, 1, .35), parent=g)
    return 118


def P_bones(g, c, rnd):
    osso = mat('bone', '#d8d2c0')
    sph((0, 0, 0), 26, mat('stone', '#b08a54'), scale=(1.2, 1, .18), parent=g)
    sph((6, 2, 9), 7, osso, parent=g)
    for y in (-2.4, 2.4):
        sph((12, 2 + y, 10), 1.8, mat('gloss', '#1a1410'), parent=g)
    for i in range(5):   # costelas de uma fera enorme
        x = -14 + i * 5
        tubo([(x, -8, 2), (x - 2, -12, 18), (x - 1, -4, 28)], 1.6, osso, radii=[1, .8, .3], parent=g)
    caps((-4, 10, 2), (16, 16, 3), 1.8, osso, parent=g)
    return 32


def P_shard(g, c, rnd):
    """Cristal do Abismo: flutua sozinho a uns 27 de altura (no jogo ele sobe e desce em código; no chão fica só a sombra).
    Casca de vidro violeta com um núcleo aceso dentro, e três lascas menores em volta."""
    vidro = mat('glass', '#7a5aa8')
    nucleo = mat('emit', '#c8a8ff', strength=6)
    cyl((0, 0, 27), (1.2, .4, 47), 7, .25, vidro, verts=6, parent=g, smooth=False)      # bipirâmide de seis faces, levemente torta
    cyl((0, 0, 27), (-.6, -.2, 11), 7, .25, vidro, verts=6, parent=g, smooth=False)
    cyl((0, 0, 27), (.7, .2, 40), 3.2, .2, nucleo, verts=6, parent=g, smooth=False)
    cyl((0, 0, 27), (-.3, -.1, 17), 3.2, .2, nucleo, verts=6, parent=g, smooth=False)
    for k, (a, z, h) in enumerate(((.6, 34, 9), (2.7, 21, 7), (4.4, 29, 6))):
        x, y = math.cos(a) * 13, math.sin(a) * 13
        inc = rnd.uniform(-1.6, 1.6)
        cyl((x, y, z), (x + inc, y, z + h / 2), 2.3, .15, vidro, verts=5, parent=g, smooth=False)
        cyl((x, y, z), (x - inc, y, z - h / 2), 2.3, .15, vidro, verts=5, parent=g, smooth=False)
        sph((x, y, z), 1.0, nucleo, parent=g)
    luz_ponto((0, 0, 27), 22, '#aa82dc', parent=g)
    return 48


def P_wreck(g, c, rnd):
    madeira = mat('wood', '#3a2e24')
    escura = mat('wood', '#2a221c')
    for i in range(6):   # costado partido
        a = -1.1 + i * .44
        box((math.cos(a) * 20, math.sin(a) * 26, 6 + abs(i - 2.5) * 2), (3.6, 13, 18 - abs(i - 2.5) * 2.2), escura, rot=(0, .3 * (1 if i < 3 else -1), a), bevel=.6, parent=g)
    box((0, 0, 3), (40, 26, 4), escura, bevel=.8, parent=g)
    cyl((0, 0, 0), (10, 2, 104), 2.6, 2, madeira, verts=10, parent=g)
    cyl((5, -16, 64), (7, 20, 66), 1.2, 1, madeira, verts=8, parent=g)
    poly([(6, -14, 62), (8, 4, 92), (9, 18, 64), (7, 6, 48)], mat('cloth', '#b4aa96', alpha=.85), esp=.4, parent=g)
    for k in range(5):
        sph((rnd.uniform(-20, 20), rnd.uniform(-20, 20), 0), rnd.uniform(5, 9), mat('gloss', '#101418'), scale=(1.6, 1.3, .2), parent=g)   # poças de piche
    return 104


def P_crystal(g, c, rnd):
    for i in range(5):
        a = i / 5 * math.tau
        x, y = math.cos(a) * 7 * (i > 0), math.sin(a) * 7 * (i > 0)
        h = (54 if i == 0 else 22 + rnd.random() * 18)
        cyl((x, y, 0), (x * 1.5, y * 1.5, h), 6 if i == 0 else 4, .4, mat('glass', shade('#6a4a9a', -.2 + i * .08)), verts=6, parent=g)
    sph((0, 0, 20), 6, mat('emit', '#c8a8ff', strength=4), parent=g)
    luz_ponto((0, 0, 24), 26, '#b890f0', parent=g)
    for k in range(3):
        rocha((rnd.uniform(-12, 12), rnd.uniform(-12, 12), 2), 5, mat('stone', '#2a2238'), semente=k, parent=g)
    return 56


def P_tower(g, c, rnd):
    pedra = mat('stone', shade(c['pedra'], -.1))
    box((0, 0, 70), (40, 40, 140), pedra, bevel=2, parent=g)
    for z in (36, 72, 108):
        box((0, 0, z), (42, 42, 3), mat('stone', shade(c['pedra'], -.3)), bevel=.8, parent=g)
    o = cyl((0, 0, 140), (0, 0, 166), 30, .5, mat('stone', shade(c['pedra'], -.35)), verts=4, parent=g)
    o.rotation_mode = 'XYZ'
    o.rotation_euler[2] = math.pi / 4
    for i in range(4):
        for f in (-1, 1):
            box((20.4, f * 9, 22 + i * 30), (1, 6, 10), mat('emit', '#7ed2c8', strength=3), bevel=.2, parent=g)
            box((f * 9, 20.4, 22 + i * 30), (6, 1, 10), mat('emit', '#7ed2c8', strength=3), bevel=.2, parent=g)
    for k in range(5):   # algas penduradas
        tubo([(20.6, -16 + k * 8, 50), (21, -16 + k * 8, 36), (20.8, -15 + k * 8, 20)], 1, mat('cloth', '#2f5a50'), parent=g)
    luz_ponto((30, 0, 80), 20, '#7ed2c8', parent=g)
    return 166


def P_vent(g, c, rnd):
    """Fenda de lava da Forja: anel de basalto em volta de uma poça de lava com placas de crosta.
    A fumaça e o pulsar do brilho ficam em código no jogo (aqui seriam bolas paradas)."""
    basalto = mat('stone', '#2a1510')
    for k in range(12):   # as pedras do lado da câmera (y < 0) são mais baixas para a lava aparecer no ângulo do jogo
        a = k / 12 * math.tau + rnd.uniform(-.1, .1)
        perto = .7 if math.sin(a) < -.3 else 1.0
        rocha((math.cos(a) * 17, math.sin(a) * 11, 1.4), rnd.uniform(3.6, 5) * perto, basalto, semente=k, parent=g)
    sph((0, 0, 0), 12, mat('emit', '#ff5a10', strength=1.5), scale=(1.2, .75, .22), parent=g)     # lava
    sph((0, 0, 2.3), 5, mat('emit', '#ff9a30', strength=2.6), scale=(1.3, .8, .2), parent=g)        # miolo mais quente
    crosta = mat('stone', '#1c0e0a')
    for k in range(5):   # placas de crosta boiando
        a, r = rnd.uniform(0, math.tau), rnd.uniform(4, 9)
        sph((math.cos(a) * r * 1.1, math.sin(a) * r * .65, 2.5), rnd.uniform(1.6, 2.8), crosta, scale=(1.4, 1, .3), parent=g)
    luz_ponto((0, 0, 6), 16, '#ff6a20', raio=.4, parent=g)
    return 14


def P_pillar(g, c, rnd):
    pedra = mat('stone', '#d8d2c4')
    box((0, 0, 4), (24, 24, 8), pedra, bevel=1, parent=g)
    cyl((0, 0, 8), (0, 0, 100), 9, 8, pedra, verts=16, parent=g)
    for z in (20, 60, 96):
        torus((0, 0, z), 9, 1.2, mat('gold', '#d8b450'), parent=g)
    sph((0, 0, 108), 6, mat('emit', '#ffdc96', strength=12), parent=g)
    luz_ponto((0, 0, 108), 40, '#ffdc96', raio=.2, parent=g)
    return 114


def P_torch(g, c, rnd):
    cyl((0, 0, 0), (0, 0, 44), 1.8, 1.4, mat('wood', '#3a2a1c'), verts=8, parent=g)
    cyl((0, 0, 40), (0, 0, 46), 4, 3, mat('metal', '#3a3634', rough=.6), verts=10, parent=g)
    chama(None, (0, 0, 46), 14, '#ffaa3c', r=3, n=4, parent=g)
    luz_ponto((0, 0, 54), 60, '#ffaa3c', raio=.1, parent=g)
    return 60


def P_shroomprop(g, c, rnd):
    """Moita de cogumelos acesos: pés tortos e fibrosos, chapéus irregulares de borda grossa, lamelas escuras e verrugas claras."""
    pe = mat('skin', '#d6c8a8')
    for i in range(3):
        x, y = (i - 1) * 9, (i % 2) * 2 - 1
        h = 14 + (i % 2) * 10
        haste = cyl((x, y, 0), (x + rnd.uniform(-1.5, 1.5), y, h), 2.8, 2, pe, verts=14, parent=g)
        relevo(haste, forca=.8, escala=2, sub=1, semente=i)
        cor = '#aa78e6' if i % 2 else '#78dcaa'
        chapeu = sph((x, y, h), 9, mat('emit', cor, strength=1.4), scale=(1, 1, .5), parent=g)
        relevo(chapeu, forca=1.6, escala=3, sub=1, semente=i + 3)
        torus((x, y, h - .5), 8.6, 1.2, mat('emit', shade(cor, -.25), strength=1.0), scale=(1, 1, .6), parent=g)   # borda enrolada
        sph((x, y, h - 1.6), 8, mat('cloth', shade(cor, -.65)), scale=(1, 1, .12), parent=g)                           # lamelas
        for (p, nn) in espalhar((x, y, h), 9, (1, 1, .5), 5, semente=i + 7, zmin=h + 1.5):
            sph(p, 1.2, mat('skin', '#f0e8d8'), scale=(1, 1, .5), parent=g)                                            # verrugas
    luz_ponto((0, 0, 20), 12, '#aa78e6', parent=g)
    return 30


def P_bonepile(g, c, rnd):
    osso = mat('bone', '#d8d2c0')
    sph((0, 0, 7), 7, osso, parent=g)
    for y in (-2.4, 2.4):
        sph((5.6, y, 8), 1.8, mat('gloss', '#2a2622'), parent=g)
    for i in range(6):
        a = rnd.random() * math.tau
        caps((math.cos(a) * 4, math.sin(a) * 4, 2), (math.cos(a) * 16, math.sin(a) * 16, 2 + rnd.random() * 3), 1.4, osso, parent=g)
    return 16


def P_honey(g, c, rnd):
    o = cyl((0, 0, 0), (0, 0, 36), 16, 16, mat('gloss', '#b07a2a'), verts=6, parent=g)
    cyl((0, 0, 36), (0, 0, 38), 15, 15, mat('gloss', '#e0a63a'), verts=6, parent=g)
    for k in range(4):
        a = k / 4 * math.tau + .3
        tubo([(math.cos(a) * 15, math.sin(a) * 15, 36), (math.cos(a) * 16, math.sin(a) * 16, 26 - k * 3)], 1.6, mat('gloss', '#e8a838'), radii=[1, .5], parent=g)
    luz_ponto((0, 0, 42), 10, '#ffc050', parent=g)
    return 40


def P_icicle(g, c, rnd):
    for i in range(4):
        x, y = (i - 1.5) * 7, rnd.uniform(-5, 5)
        cyl((x, y, 0), (x, y, 30 + (i % 2) * 22), 5, .2, mat('glass', '#c8ebff' if i % 2 else '#96c8eb'), verts=5, parent=g)
    return 54


def P_crate(g, c, rnd):
    madeira = mat('wood', '#6a4a2a')
    box((0, 0, 12), (24, 24, 24), madeira, bevel=1, parent=g)
    for z in (2, 22):
        box((0, 0, z), (25, 25, 2.4), mat('wood', '#3a2616'), bevel=.3, parent=g)
    box((12.4, 0, 12), (.8, 3, 26), mat('wood', '#3a2616'), rot=(.78, 0, 0), bevel=.2, parent=g)
    box((6, 6, 30), (14, 14, 12), madeira, rot=(0, 0, .4), bevel=.8, parent=g)
    fresta = mat('wood', '#22160c')
    for s in (-1, 1):   # frestas entre as tábuas, nos quatro lados
        for z in (8.5, 15.5):
            box((s * 12.1, 0, z), (.5, 23, .5), fresta, bevel=0, parent=g)
            box((0, s * 12.1, z), (23, .5, .5), fresta, bevel=0, parent=g)
    for (x, y) in ((12.3, -9), (12.3, 9), (-9, -12.3), (9, -12.3)):   # pregos
        sph((x, y, 22), .7, mat('metal', '#5a5048', rough=.5), parent=g)
    return 36


def P_coins(g, c, rnd):
    ouro = mat('gold', '#e0b850')
    sph((0, 0, 0), 18, ouro, scale=(1.2, 1, .4), parent=g)
    for i in range(14):
        a = rnd.random() * math.tau
        r = rnd.random() * 20
        o = cyl((math.cos(a) * r, math.sin(a) * r, 4 + rnd.random() * 2), (math.cos(a) * r, math.sin(a) * r, 5 + rnd.random() * 2), 2.4, 2.4, ouro, parent=g)
        o.rotation_mode = 'XYZ'
        o.rotation_euler = (rnd.random(), rnd.random(), 0)
    luz_ponto((0, 0, 12), 8, '#ffe8a0', parent=g)
    return 12


def P_cart(g, c, rnd):
    trilho = mat('metal', '#5a5048', rough=.6)
    for y in (-8, 8):
        box((0, y, 1), (90, 1.6, 2), trilho, bevel=.3, parent=g)
    for x in range(-40, 44, 12):
        box((x, 0, .4), (4, 24, 1.4), mat('wood', '#3a2a1c'), bevel=.3, parent=g)
    madeira = mat('wood', '#4a3a2a')
    o = cyl((0, 0, 6), (0, 0, 24), 20, 25, madeira, verts=4, parent=g)
    o.rotation_mode = 'XYZ'
    o.rotation_euler[2] = math.pi / 4
    for k in range(5):
        rocha((rnd.uniform(-10, 10), rnd.uniform(-6, 6), 25), 6, mat('stone', '#6a6460'), semente=k, parent=g)
    sph((2, 2, 30), 2, mat('emit', '#dcbe64', strength=4), parent=g)
    for x in (-10, 10):
        for y in (-12, 12):
            cyl((x, y, 5), (x, y * 1.06, 5), 5, 5, mat('metal', '#2a2420', rough=.5), parent=g)
    return 32


def P_bookshelf(g, c, rnd):
    madeira = mat('wood', '#4a3222')
    box((0, 0, 40), (12, 40, 80), madeira, bevel=1, parent=g)
    cores = ['#8a3a3a', '#3a5a8a', '#5a7a3a', '#8a7a3a', '#5a3a7a']
    for r in range(3):
        z = 8 + r * 24
        box((2, 0, z - 1.6), (10, 38, 1.6), mat('wood', '#2e1e14'), bevel=.2, parent=g)
        y = -17
        while y < 16:
            w = rnd.uniform(2.4, 4)
            h = rnd.uniform(14, 20)
            box((3, y + w / 2, z + h / 2), (8, w, h), mat('leather', cores[rnd.randint(0, 4)]), rot=(rnd.uniform(-.08, .08), 0, 0), bevel=.3, parent=g)
            y += w + .4
    for k in range(3):
        box((rnd.uniform(6, 14), rnd.uniform(-16, 16), .3), (6, 8, .4), mat('paper', '#ece2c8'), rot=(0, 0, rnd.random() * 3), bevel=0, parent=g)
    return 80


def P_menhir(g, c, rnd):
    rocha((0, 0, 22), 11, mat('stone', '#5a5248'), escala=(.7, .6, 2.1), semente=rnd.randint(0, 99), aspereza=.18, parent=g)
    for i in range(3):
        box((6.6, 0, 16 + i * 9), (1, 4, 3), mat('emit', '#e8c45a', strength=1.5), bevel=.2, parent=g)
    return 46


def P_portal(g, c, rnd, aceso=True):
    pedra = mat('stone', '#5a5248')
    for s in (-1, 1):
        for k in range(4):
            rocha((0, s * 22, 6 + k * 13), 8, pedra, escala=(1, 1, .9), semente=k + (s + 1) * 5, aspereza=.15, parent=g)
    pts = [(0, -22, 52), (0, -14, 70), (0, 0, 76), (0, 14, 70), (0, 22, 52)]
    tubo(pts, 6.4, pedra, parent=g)
    if aceso:
        luz = mat('emit', '#96d7f0', strength=3, alpha=.55)
        poly([(0, -16, 2), (0, -16, 50), (0, -10, 64), (0, 0, 68), (0, 10, 64), (0, 16, 50), (0, 16, 2)], luz, esp=.3, parent=g)
        luz_ponto((8, 0, 36), 50, '#96d7f0', raio=.3, parent=g)
    return 82


def P_gate(g, c, rnd):
    """Entrada de masmorra no mapa da região: arco de pedra, degraus que descem e duas tochas."""
    pedra = mat('stone', '#4a4238')
    box((0, 0, -1), (40, 48, 3), mat('gloss', '#0c0908'), bevel=.4, parent=g)
    for i in range(3):
        box((-4 - i * 6, 0, -2 - i * 3), (6, 36 - i * 6, 3), mat('stone', '#6a6050'), bevel=.4, parent=g)
    for s in (-1, 1):
        box((0, s * 24, 22), (10, 8, 44), pedra, bevel=1.2, parent=g)
        tubo([(4, s * 30, 30), (6, s * 32, 40)], .8, mat('metal', '#3a3634'), parent=g)
        chama(None, (6, s * 32, 42), 9, '#ffaa3c', r=2, n=3, parent=g)
        luz_ponto((8, s * 32, 46), 30, '#ffaa3c', parent=g)
    tubo([(0, -24, 44), (0, -12, 56), (0, 0, 60), (0, 12, 56), (0, 24, 44)], 5, pedra, parent=g)
    return 66


PECAS = {n[2:]: f for n, f in globals().items() if n.startswith('P_')}


def peca(tipo, c, rnd, loc=(0, 0, 0), rot=0.0, esc=1.0, parent=None):
    g = grupo(loc, rot=(0, 0, rot), parent=parent, nome=tipo)
    g.scale = (esc, esc, esc)
    alt = PECAS.get(tipo, P_rock)(g, c, rnd)
    return g, alt


# ---------------- chão em losango ----------------
CASA_CENA = 92   # uma casa do mapa na cena de região (em unidades U): a proporção entre casa e pinheiro do jogo


def _brilho_chao(decor):
    """Brilho do chão do jogo medido pelo integrar.py (renders_2d/chao/brilho.json); 1 sem a medição."""
    import json
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'renders_2d', 'chao', 'brilho.json')
    try:
        return float(json.load(open(p, encoding='utf-8')).get(decor, 1.0))
    except (OSError, ValueError):
        return 1.0


def chao_losango(lado, cores, sem=1, falesia=70, rocha_cor='#2a2420', decor=None):
    """Placa quadrada (vira losango com a câmera a 45°): topo ondulado e laterais de terra e pedra. Com o cenário
    (decor), o topo usa o mesmo chão do jogo (kit_chao) na escala da cena; sem ele, manchas das duas cores."""
    n = 48
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=lado * U)
    o = bpy.context.object
    from mathutils import noise as _n
    for v in o.data.vertices:
        p = v.co / (lado * U) * 4
        v.co.z = _n.noise(Vector((p.x + sem, p.y - sem, 0))) * 2.5 * U
    if decor:
        import kit_chao as KC
        o.data.materials.append(KC.material_chao(decor, cores, casa=CASA_CENA * U, deslocar=False, brilho=_brilho_chao(decor)))
    else:
        o.data.materials.append(mat_chao(cores[0], cores[1], escala=3.0))
    for p in o.data.polygons:
        p.use_smooth = True
    terra = mat('stone', rocha_cor)
    for k in range(4):   # laterais
        a = k * math.pi / 2
        cx, cy = math.cos(a) * lado / 2, math.sin(a) * lado / 2
        box((cx, cy, -falesia / 2), (6 if k % 2 == 0 else lado + 6, lado + 6 if k % 2 == 0 else 6, falesia), terra, bevel=1, parent=None)
    rnd = random.Random(sem)
    for k in range(40):   # pedras soltas na borda
        lado_k = rnd.randint(0, 3)
        t = rnd.uniform(-.5, .5) * lado
        x, y = ((lado / 2, t), (t, lado / 2), (-lado / 2, t), (t, -lado / 2))[lado_k]
        rocha((x, y, -rnd.uniform(4, falesia - 10)), rnd.uniform(8, 16), terra, semente=k, parent=None)
    return o


def mundo_cena(cor_hex, forca=.5):
    w = bpy.data.worlds.new('mundo')
    bpy.context.scene.world = w
    if hasattr(w, 'use_nodes'):
        w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = hex_lin(cor_hex)
    bg.inputs['Strength'].default_value = forca


def sol(cor_hex, forca, rot):
    L = bpy.data.lights.new('sol', 'SUN')
    L.energy = forca
    L.color = hex_lin(cor_hex)[:3]
    L.angle = math.radians(6)
    o = bpy.data.objects.new('sol', L)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = rot
    return o


def camera_iso(escala, alvo_z=0.0, elev=30.0, dist=40.0):
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = escala * U
    cam.clip_end = 200
    o = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(o)
    e = math.radians(elev)
    o.location = (0, -dist * math.cos(e), alvo_z * U + dist * math.sin(e))
    d = Vector((0, 0, alvo_z * U)) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = o
    return o


# ---------------- clima de luz por cenário ----------------
LUZ = {  # decor/tema → (cor do sol, força, cor ambiente, força ambiente)
    'trees': ('#c8d8ff', 2.2, '#1d2f2a', 1.0), 'reeds': ('#b8d0e0', 1.8, '#1b2c33', 1.0), 'rocks': ('#e0d4c0', 2.2, '#2b2925', .9),
    'pale': ('#d8dce8', 2.0, '#262b36', 1.0), 'ruins': ('#a8e0e0', 1.9, '#1a2d33', 1.0), 'dunes': ('#ffd8a0', 3.0, '#3a2a1b', .9),
    'peaks': ('#d8ecff', 2.6, '#24323f', 1.1), 'void': ('#c8a8e8', 1.5, '#211726', 1.0), 'tar': ('#a8b8d0', 1.3, '#151a22', 1.0),
    'crystals': ('#d0b8ff', 1.6, '#1d1628', 1.0), 'city': ('#a8d8d0', 1.6, '#14262b', 1.0), 'lava': ('#ffb890', 1.8, '#3a1a12', 1.0),
    'dawn': ('#ffd8a8', 3.0, '#232b4a', 1.1),
}
DG_DECO = {'fungus': 'shroomprop', 'bones': 'bonepile', 'amber': 'honey', 'ice': 'icicle', 'wreck': 'crate', 'vault': 'coins', 'forge': 'vent',
           'roots': 'dead', 'mine': 'cart', 'library': 'bookshelf', 'abyss': 'shard', 'mirror': 'glass', 'throne': 'pillar'}
DG_ACENTO = {'fungus': '#aa78e6', 'bones': '#78e6ff', 'amber': '#ffc050', 'ice': '#a8e4ff', 'wreck': '#8affd0', 'vault': '#ffd870', 'forge': '#ff7828',
             'roots': '#c8f06a', 'mine': '#ffd08a', 'library': '#ffe0a0', 'abyss': '#b06ad0', 'mirror': '#c8b8ff', 'throne': '#e8c45a'}


def _livre(pos, ocupados, raio):
    return all((pos[0] - x) ** 2 + (pos[1] - y) ** 2 > (raio + r) ** 2 for x, y, r in ocupados)


def cena_regiao(z, idx, dados, com_personagens=True):
    """Monta a cena da região idx; devolve a raiz já girada 45° (losango)."""
    import kit_heroi as KH
    import kit_monstros as KM
    c = _cores(z['decor'], dados)
    rnd = random.Random(idx * 97 + 11)
    R = raiz('cena')
    lado = 640
    chao = chao_losango(lado, c['chao'], sem=idx + 1, rocha_cor=shade(z['ground'], .05), decor=z['decor'])
    chao.parent = R
    for o in list(bpy.context.scene.objects):
        if o.parent is None and o is not R and o.type == 'MESH':
            o.parent = R
    ocup = []
    # caminho de terra batida atravessando o mapa (do portal de entrada ao de saída)
    trilha = [(-lado * .42, -lado * .30, 70), (-lado * .15, -lado * .12, 70), (lado * .05, lado * .02, 70), (lado * .22, lado * .18, 70), (lado * .40, lado * .30, 70)]
    o = tubo(trilha, 22, mat_chao(shade(c['chao'][1], .12), shade(c['chao'][0], .05), escala=8, nome='trilha'), parent=R)
    o.scale = (1, 1, .04)
    for p in trilha[1:-1]:
        ocup.append((p[0], p[1], 40))
    # toca do chefe (círculo de menires) num canto e portais nas pontas da trilha
    toca = (-lado * .22, lado * .26)
    for i in range(8):
        a = i / 8 * math.tau
        peca('menhir', c, rnd, (toca[0] + math.cos(a) * 70, toca[1] + math.sin(a) * 50, 0), rot=rnd.random() * 3, parent=R)
    sph((toca[0], toca[1], .5), 60, mat('emit', '#e8c45a', strength=.6, alpha=.35), scale=(1, .72, .02), parent=R)
    ocup.append((toca[0], toca[1], 96))
    peca('portal', c, rnd, (trilha[0][0] - 10, trilha[0][1], 0), rot=math.pi / 4, parent=R)      # de frente para a câmera
    peca('portal', c, rnd, (trilha[-1][0] + 10, trilha[-1][1], 0), rot=math.pi / 4, parent=R)
    ocup += [(trilha[0][0], trilha[0][1], 50), (trilha[-1][0], trilha[-1][1], 50)]
    dg = [g for g in dados['DUNGEONS'] if g['after'] == idx]
    if dg:
        pos = (lado * .26, -lado * .24)
        peca('gate', c, rnd, (pos[0], pos[1], 0), rot=math.pi * 1.25, parent=R)      # degraus descem para longe da câmera
        ocup.append((pos[0], pos[1], 60))
    # vegetação e pedras com o sorteio de tipos do próprio jogo (PROP_SET)
    tipos = dados['PROP_SET'].get(z['decor'], dados['PROP_SET']['trees'])
    feitos = 0
    for tent in range(900):
        if feitos >= 46:
            break
        x, y = rnd.uniform(-lado * .47, lado * .47), rnd.uniform(-lado * .47, lado * .47)
        t = tipos[rnd.randint(0, len(tipos) - 1)]
        raio = {'pond': 46, 'tower': 30, 'wreck': 34, 'boulder': 30}.get(t, 20)
        if not _livre((x, y), ocup, raio):
            continue
        # os altos ficam no fundo (lado de trás do losango) para não esconder o centro
        fundo = (x + y) > 0
        if t in ('pine', 'snowpine', 'round', 'birch', 'tower', 'column', 'obelisk', 'wreck', 'pillar') and not fundo and rnd.random() < .7:
            continue
        peca(t, c, rnd, (x, y, 0), rot=rnd.random() * math.tau, esc=rnd.uniform(.85, 1.15), parent=R)
        ocup.append((x, y, raio))
        feitos += 1
    if com_personagens:
        # o Portador na trilha, encarando os monstros da região
        L = dict(dados['LOOK']['none'])
        H = KH.construir(L, dados['BODY'].get(L.get('body', 'cloak'), dados['BODY']['cloak']))
        H.parent = R
        H.location = V((-20, -30, 0))
        H.rotation_euler = (0, 0, math.radians(50))
        mobs = z['mobs'][:3]
        for i, m in enumerate(mobs):
            Mr, topo = _monstro_polido(KM, m[0], m[1], m[2], None, marcador=False)
            Mr.parent = R
            Mr.location = V((60 + i * 38, 30 - i * 44, 0))
            Mr.rotation_euler = (0, 0, math.radians(200 + i * 15))
        b = z['boss']
        Br, topo = _monstro_polido(KM, b[0], b[1], b[2], 'boss', marcador=False)
        Br.parent = R
        Br.location = V((toca[0], toca[1], 0))
        Br.scale = (1.45, 1.45, 1.45)
        Br.rotation_euler = (0, 0, math.radians(-40))
    # luz: sol frio ou quente conforme o cenário, ambiente na cor do céu do jogo
    sc, sf, ac, af = LUZ.get(z['decor'], LUZ['trees'])
    mundo_cena(ac, af * 1.8)
    sol(sc, sf * 1.9, (math.radians(55), 0, math.radians(-77)))        # luz alta vinda da esquerda e um pouco da frente
    luz_ponto((toca[0], toca[1], 30), 120, '#e8c45a', raio=.5, parent=R)
    R.rotation_euler = (0, 0, math.radians(45))
    return R


def cena_masmorra(dg, idx, dados, com_personagens=True):
    """Sala da masmorra: lajotas nas cores do jogo, paredes atrás, tochas, decoração do tema, chefe e subchefe."""
    import kit_heroi as KH
    import kit_monstros as KM
    fa, fb = dg['floor']
    tema_dg = dg['theme']
    c = {'folha': '#3f7048', 'pedra': shade(fa, .2), 'chao': [fa, fb], 'decor': tema_dg}
    rnd = random.Random(idx * 131 + 7)
    R = raiz('cena')
    lado, n = 560, 14
    t = lado / n
    for i in range(n):   # lajotas com juntas escuras
        for j in range(n):
            x, y = -lado / 2 + (i + .5) * t, -lado / 2 + (j + .5) * t
            cor = mix(fa, fb, round(max(0, min(1, .5 + (rnd.random() - .5) * .8)) * 5) / 5)   # 6 tons: reaproveita materiais
            box((x, y, -2), (t - 1.6, t - 1.6, 4 + rnd.random() * .8), mat('stone', cor), bevel=.8, parent=R)
    box((0, 0, -5), (lado + 4, lado + 4, 4), mat('stone', '#06080a'), bevel=0, parent=R)
    alt = 130
    topo_c, face_e, face_d = shade(fa, .06), shade(fa, -.22), shade(fa, -.12)
    # paredes só nos dois lados do fundo (com o giro de 45°, +Y e +X ficam atrás); a frente fica aberta como no jogo
    for k, (cx, cy, sx, sy, face) in enumerate(((0, lado / 2 + 14, lado + 56, 28, face_e), (lado / 2 + 14, 0, 28, lado + 28, face_d))):
        box((cx, cy, alt / 2 - 4), (sx, sy, alt), mat('stone', face), bevel=1.5, parent=R)
        box((cx, cy, alt - 3), (sx + 4, sy + 4, 6), mat('stone', topo_c), bevel=1, parent=R)
        for m in range(6):   # blocos salientes da parede
            if k == 0:
                box((-lado / 2 + 40 + m * 96, cy - 14.4, 30 + (m % 2) * 40), (40, 1.4, 20), mat('stone', shade(face, -.15)), bevel=.6, parent=R)
            else:
                box((cx - 14.4, -lado / 2 + 40 + m * 96, 30 + (m % 2) * 40), (1.4, 40, 20), mat('stone', shade(face, -.15)), bevel=.6, parent=R)
    for k in range(4):   # tochas nas paredes
        if k < 2:
            pos = (-120 + k * 240, lado / 2 - 2, 70)
        else:
            pos = (lado / 2 - 2, -120 + (k - 2) * 240, 70)
        g = grupo(pos, parent=R)
        cyl((0, 0, -10), (0, 0, 4), 1.6, 2.4, mat('metal', '#3a3634', rough=.6), parent=g)
        chama(None, (0, 0, 4), 12, '#ffaa3c', r=3, n=4, parent=g)
        luz_ponto((0, 0, 14), 160, '#ffaa3c', raio=.1, parent=g)
    deco = DG_DECO.get(tema_dg, 'rock')
    ocup = [(0, 60, 80), (-40, -120, 60)]
    feitos = 0
    for tent in range(400):
        if feitos >= 14:
            break
        x, y = rnd.uniform(-lado * .44, lado * .44), rnd.uniform(-lado * .44, lado * .44)
        if not _livre((x, y), ocup, 30):
            continue
        tipo = deco if rnd.random() < .75 else ('bonepile' if tema_dg in ('bones', 'throne', 'abyss') else 'rock')
        peca(tipo, c, rnd, (x, y, 0), rot=rnd.random() * math.tau, esc=rnd.uniform(.9, 1.2), parent=R)
        ocup.append((x, y, 30))
        feitos += 1
    ac = DG_ACENTO.get(tema_dg, '#ffaa3c')
    for k in range(30):   # detalhes do piso do tema (esporos, moedas, brasas, folhas soltas...)
        x, y = rnd.uniform(-lado * .46, lado * .46), rnd.uniform(-lado * .46, lado * .46)
        sph((x, y, 2.2), 1.6 + rnd.random(), mat('emit', ac, strength=1.5), scale=(1, 1, .4), parent=R)
    if com_personagens:
        L = dict(dados['LOOK']['none'])
        H = KH.construir(L, dados['BODY'].get(L.get('body', 'cloak'), dados['BODY']['cloak']))
        H.parent = R
        H.location = V((-40, -120, 0))
        H.rotation_euler = (0, 0, math.radians(60))
        b = dg['boss']
        Br, topo = _monstro_polido(KM, b[0], b[1], b[2], 'dboss', marcador=True)
        Br.parent = R
        Br.location = V((40, 90, 0))
        Br.scale = (1.45, 1.45, 1.45)
        Br.rotation_euler = (0, 0, math.radians(-120))
        mi = dg['mini']
        Mr, topo = _monstro_polido(KM, mi[0], mi[1], mi[2], 'mini', marcador=False)
        Mr.parent = R
        Mr.location = V((120, -10, 0))
        Mr.rotation_euler = (0, 0, math.radians(-150))
        for i, m in enumerate(dg['mobs'][:2]):
            Or, topo = _monstro_polido(KM, m[0], m[1], m[2], None, marcador=False)
            Or.parent = R
            Or.location = V((-150 + i * 70, 40 - i * 40, 0))
            Or.rotation_euler = (0, 0, math.radians(-90 - i * 30))
    mundo_cena(shade(fa, -.1), 1.3)
    sol(mix(ac, '#ffffff', .6), 1.8, (math.radians(55), 0, math.radians(-77)))
    luz_ponto((40, 90, 80), 260, ac, raio=.6, parent=R)
    luz_ponto((-40, -120, 70), 90, '#ffd8a0', raio=.4, parent=R)   # luz quente no Portador
    R.rotation_euler = (0, 0, math.radians(45))
    return R
