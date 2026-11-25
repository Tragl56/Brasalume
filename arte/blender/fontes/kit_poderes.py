# Catálogo dos poderes do Brasalume: as peças da biblioteca de efeitos das habilidades e como cada uma se mexe.
# Cada entrada de EFEITOS diz o gerador (kit_efeitos ou daqui), a câmera, o tamanho do quadro em unidades do jogo,
# a resolução (u = unidades por pixel), quantos quadros, a duração no jogo e se é luz (o jogo pinta e soma na tela).
# O jogo combina essas peças por habilidade (receitas no src/gameEngine.js): projétil, efeito no alvo, marca, prisão, aura.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, Quaternion
import kit_base as K
import kit_efeitos as KE
from kit_efeitos import (V3, TAU, suave, lerp, env, chega, cai, Nos, mat_luz, mat_espectral, mat_nat, acender, objeto,
                         m_esfera, m_plana, m_cilindro, m_rocha, malha, curva, circulo, de_frente, apontar, estrela_pts)

U = K.U


def raiz(nome='raiz'):
    o = bpy.data.objects.new(nome, None)
    bpy.context.collection.objects.link(o)
    return o


def set_w(m, x):
    for nd in m.node_tree.nodes:
        if nd.type == 'VALUE' and nd.label in ('', 'w'):
            nd.outputs[0].default_value = x


def filhos(o):
    for f in o.children:
        yield f
        yield from filhos(f)


# =============================================================================================
# peças de luz próprias
# =============================================================================================
def g_impacto(E):
    """Estouro de golpe: riscos de luz saindo do centro e um clarão redondo que acende e some."""
    rnd = random.Random(E.get('semente', 4))
    m = mat_luz('imp', base=1.0, borda=.55)
    nucleo = objeto(m_esfera(10, 18, 12), 'nucleo', mat_luz('nuc', base=.95, borda=.15, cobre=.9, blend=.65))
    riscos = []
    me = m_esfera(1.6, 8, 6, esc=(7, 1, 1))
    me.materials.append(m)
    for i in range(E.get('quant', 14)):
        o = bpy.data.objects.new('r', me)
        bpy.context.collection.objects.link(o)
        a = i / E.get('quant', 14) * TAU + rnd.uniform(-.2, .2)
        riscos.append((o, a, rnd.uniform(.7, 1.1), rnd.uniform(.6, 1.2)))
    R = E.get('raio', 36.0)

    def quadro(t):
        k = chega(t, 0, .6)
        s = (.5 + 1.1 * chega(t, 0, .25)) * (1 - .3 * t)
        nucleo.scale = (s, s, s)
        nucleo.color = (1 - suave(.1, .55, t), 1, 1, 1)
        for o, a, v, e in riscos:
            d = Vector((math.cos(a), 0, math.sin(a)))
            o.location = V3(*(d * R * (.15 + .85 * k * v)))
            apontar(o, d)
            o.scale = (e * (1 - .6 * t), 1, 1)
            o.color = (1 - suave(.35, 1, t), 1, .6, 1)
    return quadro


def g_clarao(E):
    """Clarão em estrela: raios finos de tamanhos diferentes e um miolo branco."""
    rnd = random.Random(E.get('semente', 9))
    raios = []
    for i in range(E.get('quant', 12)):
        a = i / E.get('quant', 12) * TAU + rnd.uniform(-.1, .1)
        L = rnd.uniform(.55, 1.0) * E.get('raio', 60.0)
        pts = [(0, -2.2), (L * .25, -1.4), (L, 0), (L * .25, 1.4), (0, 2.2)]
        o = objeto(m_plana([(x, y) for x, y in pts]), 'raio', mat_luz('cl', base=1.0, borda=1.0))
        o.rotation_mode = 'XYZ'
        o.rotation_euler = (math.pi / 2, -a, 0)   # no plano XZ, de frente para a câmera de lado
        raios.append((o, rnd.uniform(.7, 1.3)))
    nuc = objeto(m_esfera(12, 18, 12), 'nucleo', mat_luz('nuc', base=1.0, borda=.1, cobre=.9, blend=.7))

    def quadro(t):
        k = chega(t, 0, .22)
        f = 1 - suave(.3, 1, t)
        for o, e in raios:
            s = k * e * (1 + .25 * t)
            o.scale = (s, max(.05, 1 - .7 * t), 1)
            o.color = (f, 1, .8, 1)
        nuc.scale = (.4 + k,) * 3
        nuc.color = (f, 1, 1, 1)
    return quadro


def g_orbe(E):
    """Orbe que voa (laço): miolo vivo, energia girando e um rastro curto para trás."""
    m = mat_espectral('orbe', base=.55, borda=1.0, a0=.55, a1=1.0, fluxo=3.0)
    nuc = objeto(m_esfera(E.get('raio', 7.0), 20, 14), 'orbe', m)
    halo = objeto(m_esfera(E.get('raio', 7.0) * 2.1, 20, 14), 'halo', mat_luz('halo', base=.7, borda=.05, cobre=.55, blend=.8))
    rastro = []
    me = m_esfera(E.get('raio', 7.0) * .8, 12, 8)
    me.materials.append(mat_luz('rastro', base=.8, borda=.2, cobre=.8, blend=.6))
    for i in range(6):
        o = bpy.data.objects.new('r', me)
        bpy.context.collection.objects.link(o)
        rastro.append(o)

    def quadro(t):
        set_w(m, math.cos(t * TAU) * .8)
        nuc.rotation_euler = (t * TAU, 0, t * TAU)
        for i, o in enumerate(rastro):
            k = (i + 1) / 6
            o.location = V3(-k * E.get('cauda', 26.0), 0, math.sin(t * TAU * 2 + i) * 1.5 * k)
            s = 1 - k * .8
            o.scale = (s * 1.4, s, s)
            o.color = ((1 - k) * .9, 1, 0, 1)
        halo.color = (.8 + .2 * math.sin(t * TAU), 1, 0, 1)
    return quadro


def g_feixe(E):
    """Feixe reto (laço) ao longo de X, de -L/2 a L/2: o jogo estica entre quem lança e o alvo."""
    L = E.get('comp', 100.0)
    r = E.get('raio', 4.0)
    N = Nos('feixe')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    a, b = N.valor('a', 0.0), N.valor('b', 1.0)
    # o cilindro é feito em pé e deitado em X: ao longo do feixe é o z do objeto
    rn = N.ruido(N.vet(N.mul(x, 30.0), N.mul(y, 30.0), N.soma(N.mul(z, 18.0), a)), escala=1.0, w=b, det=3.0)
    f = N.facing(.35)
    fio = N.faixa(rn, .38, .66, .55, 1.15)
    I = N.soma(N.faixa(f, 0, 1, 1.0, .45), N.mul(fio, .15))
    A = N.mul(N.faixa(f, 0, 1, 1.0, 0), fio, N.obj_cor()[0], clamp=True)
    m = N.luz(I, A)
    corpo = objeto(m_cilindro(r * .6, L, 24), 'feixe', m)
    corpo.rotation_euler = (0, math.pi / 2, 0)
    halo = objeto(m_cilindro(r * 2.0, L, 24), 'halo', mat_luz('halo', base=.6, borda=.2, cobre=.42, blend=.75, borda_a=0))
    halo.rotation_euler = (0, math.pi / 2, 0)
    halo.color = (1, 1, 0, 1)
    fora = objeto(m_cilindro(r * 3.8, L, 24), 'fora', mat_luz('fora', base=.42, borda=.1, cobre=.16, blend=.8, borda_a=0))
    fora.rotation_euler = (0, math.pi / 2, 0)
    fora.color = (1, 1, 0, 1)

    def quadro(t):
        N.v['a'].default_value = math.sin(t * TAU) * 1.2
        N.v['b'].default_value = math.cos(t * TAU) * 1.2
        corpo.color = (1, 1, 0, 1)
    return quadro


def g_pilar(E):
    """Coluna de luz que desce do céu sobre o alvo, alarga e some."""
    H, r = E.get('altura', 300.0), E.get('raio', 16.0)
    N = Nos('pilar')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    topo = N.valor('topo', 1.0)
    fade = N.valor('fade', 1.0)
    w = N.valor('w', 0.0)
    zz = N.math('DIVIDE', z, H * U)          # 0 no chão, 1 no alto
    desce = N.faixa(zz, N.math('SUBTRACT', topo, .02), topo, 1, 0)
    grad = N.faixa(zz, 0, 1, 1, .25)
    rn = N.ruido(N.vet(N.mul(x, 4.0), N.mul(y, 4.0), N.mul(z, .6)), escala=1.0 / U * .05, w=w, det=2.0)
    risco = N.faixa(rn, .35, .65, .5, 1.1)
    f = N.facing(.3)
    A = N.mul(desce, grad, risco, fade, N.faixa(f, 0, 1, .95, .05), clamp=True)
    I = N.soma(N.faixa(f, 0, 1, 1.0, .4), N.mul(risco, .1))
    m = N.luz(I, A)
    me = malha('pilar', lambda bm: bmesh.ops.create_cone(bm, cap_ends=False, segments=28, radius1=r * U, radius2=r * U * 1.3, depth=H * U))
    for v in me.vertices:
        v.co.z += H * U / 2
    col = objeto(me, 'pilar', m)
    nuc = objeto(m_cilindro(r * .35, H, 16), 'nucleo', m)
    nuc.location.z = H * U / 2
    disco = objeto(m_esfera(r * 2.4, 24, 12, esc=(1, 1, .18)), 'chao', mat_luz('disco', base=.9, borda=.2, cobre=.8, blend=.7))

    def quadro(t):
        desce_k = chega(t, 0, .18)   # a luz desce do alto até o chão
        col.scale = (1 + .5 * t, 1 + .5 * t, desce_k)
        col.location.z = H * U * (1 - desce_k)
        nuc.scale = (1 - .5 * t, 1 - .5 * t, desce_k)
        nuc.location.z = H * U / 2 * desce_k + H * U * (1 - desce_k)
        N.v['fade'].default_value = 1 - suave(.45, 1, t)
        N.v['w'].default_value = t * 2
        disco.color = ((1 - suave(.4, 1, t)) * desce_k, 1, 0, 1)
        disco.scale = (1 + t, 1 + t, 1)
    return quadro


def g_aura(E):
    """Aura de reforço em volta do herói (laço): línguas de luz subindo num cilindro e um anel no chão."""
    r, H = E.get('raio', 28.0), E.get('altura', 100.0)
    N = Nos('aura')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    ang = N.math('ARCTAN2', y, x)
    zz = N.math('DIVIDE', z, H * U)
    a, b = N.valor('a', 0.0), N.valor('b', 0.0)
    rn = N.ruido(N.vet(N.mul(N.math('COSINE', ang), 1.6), N.mul(N.math('SINE', ang), 1.6), N.soma(N.mul(zz, 2.2), a)), escala=1.0, w=b, det=3.0)
    lingua = N.faixa(N.soma(rn, N.mul(zz, -.3)), .28, .5, 0, 1)
    A = N.mul(lingua, N.faixa(zz, 0, 1, 1, 0), N.obj_cor()[0], clamp=True)
    I = N.faixa(zz, 0, 1, 1.0, .45)
    m = N.luz(I, A)
    me = malha('aura', lambda bm: bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=r * U, radius2=r * .72 * U, depth=H * U))
    for v in me.vertices:
        v.co.z += H * U / 2
    o = objeto(me, 'aura', m)
    anel = objeto(m_esfera(r * 1.25, 28, 10, esc=(1, 1, .08)), 'anel', mat_luz('anel', base=.9, borda=.3, cobre=.6, blend=.5))

    def quadro(t):
        N.v['a'].default_value = math.sin(t * TAU) * .9 - t * 0
        N.v['b'].default_value = math.cos(t * TAU) * .9
        o.color = (1, 1, 0, 1)
        anel.color = (.55 + .2 * math.sin(t * TAU), 1, 0, 1)
    return quadro


def g_ciclone(E):
    """Redemoinho de vento (laço): funil de faixas em espiral girando."""
    r0, r1, H = E.get('raio0', 10.0), E.get('raio', 46.0), E.get('altura', 110.0)
    N = Nos('ciclone')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    ang = N.math('ARCTAN2', y, x)
    zz = N.math('DIVIDE', z, H * U)
    faixa = N.math('SINE', N.soma(N.mul(ang, 3.0), N.mul(zz, 9.0)))
    rn = N.ruido(N.vet(N.mul(x, 30.0), N.mul(y, 30.0), N.mul(z, 12.0)), escala=1.0, det=2.0)
    A = N.mul(N.faixa(N.soma(faixa, N.mul(rn, .9)), .35, .95, 0, 1), N.faixa(zz, 0, 1, .7, 1), N.faixa(zz, .85, 1, 1, 0), N.obj_cor()[0], clamp=True)
    I = N.faixa(zz, 0, 1, .55, 1.0)
    m = N.luz(I, A)
    me = malha('funil', lambda bm: bmesh.ops.create_cone(bm, cap_ends=False, segments=40, radius1=r0 * U, radius2=r1 * U, depth=H * U))
    for v in me.vertices:
        v.co.z += H * U / 2
    o = objeto(me, 'funil', m)
    o2 = objeto(me.copy(), 'funil2', m)
    o2.scale = (.7, .7, .92)

    def quadro(t):
        o.rotation_euler = (0, 0, -t * TAU / 3)
        o2.rotation_euler = (0, 0, -t * TAU / 3 * 2 + 1.0)
        o.color = (1, 1, 0, 1)
        o2.color = (.7, 1, 0, 1)
    return quadro


def g_cupula(E):
    """Cúpula de proteção (laço): rede de células de luz numa meia esfera, com a borda acesa."""
    R = E.get('raio', 55.0)
    N = Nos('cupula')
    co = N.coord('Object')
    a, b = N.valor('a', 0.0), N.valor('b', 0.0)
    vo = N.no('ShaderNodeTexVoronoi')
    vo.feature = 'DISTANCE_TO_EDGE'
    N.liga(N.vmath('SCALE', co, escala=1.0 / (R * U) * 3.2), vo.inputs['Vector'])
    vo.inputs['Scale'].default_value = 1.0
    borda = N.faixa(vo.outputs['Distance'], 0, .07, 1, 0)
    rn = N.ruido(N.vmath('SCALE', co, escala=1.0 / (R * U) * 2.0), escala=1.0, w=a, det=2.0)
    brilho = N.faixa(rn, .35, .7, .25, 1.0)
    f = N.facing(.3)
    A = N.mul(N.soma(N.mul(borda, brilho, .9), N.mul(N.faixa(f, 0, 1, 0, 1), .75), .06), N.obj_cor()[0], clamp=True)
    I = N.soma(.55, N.mul(borda, .45))
    m = N.luz(I, A)

    def fn(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=R * U)
        for v in [v for v in bm.verts if v.co.z < -1e-6]:
            bm.verts.remove(v)
    o = objeto(malha('cupula', fn), 'cupula', m)
    o.scale = (1, 1, .92)

    def quadro(t):
        N.v['a'].default_value = math.cos(t * TAU) * .6
        o.color = (.85 + .15 * math.sin(t * TAU), 1, 0, 1)
    return quadro


def g_som(E):
    """Ondas de som: arcos ")))" que saem de quem canta (ou uiva) e correm para +X, abrindo."""
    m = mat_luz('som', base=.95, borda=.5, cobre=1.0, blend=.35)
    arcos = []
    for i in range(E.get('quant', 5)):
        r = 12 + i * 5.5
        pts = [(r * math.cos(a), r * math.sin(a)) for a in [math.radians(-58 + 116 * k / 24) for k in range(25)]]
        o = curva([[(x - r, z) for x, z in pts]], 1.5, 'arco', m, plano='XZ')
        halo = curva([[(x - r, z) for x, z in pts]], 4.5, 'halo', m, plano='XZ', z=.5)
        halo.color = (1, .3, 0, 1)
        arcos.append((o, halo, i))
    L = E.get('comp', 100.0)

    def quadro(t):
        for o, halo, i in arcos:
            tt = max(0.0, min(1.0, (t - i * .1) / .6))
            x = -L / 2 + L * chega(tt, 0, 1)
            f = (1 - suave(.5, 1, tt)) * (1 if t >= i * .1 else 0)
            for q, g in ((o, 1.0), (halo, .3)):
                q.location = V3(x, 0, 0)
                q.color = (f, g, 0, 1)
    return quadro


def g_runa_flutua(E):
    """Runa de pé que pulsa (laço): marca em cima do alvo."""
    E2 = dict(E, plano='XZ', forma='runa', laco=True, pulso=1)
    return KE.g_traco(E2)


# =============================================================================================
# corpos de luz (armas, mãos, astros) e como se mexem
# =============================================================================================
def esp_escudo(m, R):
    K.box((0, 0, 32), (44, 6, 64), m, bevel=6, parent=R)
    K.sph((0, -4, 36), 8, m, scale=(1, .5, 1), parent=R)
    K.box((0, -3.5, 32), (6, 2, 52), m, bevel=1, parent=R)
    K.box((0, -3.5, 40), (34, 2, 6), m, bevel=1, parent=R)


def esp_espada(m, R):
    K.cyl((0, 0, -2), (0, 0, 104), .4, 8.5, m, verts=4, parent=R)
    K.box((0, 0, 106), (36, 5, 5), m, bevel=1.5, parent=R)
    K.cyl((0, 0, 108), (0, 0, 128), 2.2, 2.2, m, verts=10, parent=R)
    K.sph((0, 0, 131), 4.2, m, parent=R)


def esp_martelo(m, R):
    K.cyl((0, 0, 0), (0, 0, 92), 2.6, 2.6, m, verts=10, parent=R)
    K.box((0, 0, 98), (48, 20, 24), m, bevel=3, parent=R)
    K.box((0, 0, 98), (54, 14, 16), m, bevel=2, parent=R)


def esp_foice(m, R):
    K.cyl((0, 0, 0), (0, 0, 120), 2.0, 2.0, m, verts=10, parent=R)
    pts = [(0, 0, 118), (-14, 0, 126), (-42, 0, 122), (-64, 0, 104), (-70, 0, 86), (-56, 0, 100), (-36, 0, 110), (-14, 0, 112), (0, 0, 108)]
    K.poly(pts, m, esp=2.5, parent=R)


def esp_pendulo(m, R):
    K.cyl((0, 0, 0), (0, 0, -120), 1.6, 1.6, m, verts=8, parent=R)
    K.sph((0, 0, 0), 4, m, parent=R)
    pts = [(-40, 0, -112), (-20, 0, -126), (0, 0, -130), (20, 0, -126), (40, 0, -112), (24, 0, -120), (0, 0, -122), (-24, 0, -120)]
    K.poly(pts, m, esp=3.0, parent=R)


def g_arma(E):
    """Arma de luz: escudo e espada caem do céu, martelo desce num golpe, foice varre e pêndulo balança."""
    m = mat_espectral('arma', base=.42, borda=1.0, a0=.38, a1=1.0, fluxo=2.6)   # armas de luz encorpadas (de longe quase sumiam)
    R = raiz('arma')
    E['peca'](m, R)
    mov = E.get('mov', 'cai')
    esc = E.get('escala', 1.0)

    def quadro(t):
        set_w(m, t * 1.6)
        flash = max(0.0, 1 - abs(t - E.get('bate', .3)) / .12)
        fade = 1 - suave(E.get('apaga', .6), 1, t)
        if mov == 'cai':
            k = cai(t, 0, E.get('bate', .3))
            R.location = V3(0, 0, E.get('alto', 160.0) * (1 - k) + E.get('crava', 0.0) * k)
            R.rotation_euler = (0, math.radians(E.get('inclina', 0.0)), 0)
            s = 1 + .08 * flash
            R.scale = (s * esc, s * esc, (1 - .06 * flash) * esc)
        elif mov == 'golpe':
            k = cai(t, .02, E.get('bate', .3))
            R.location = V3(*E.get('pivo', (-96, 0, 14)))
            R.rotation_euler = (0, math.radians(lerp(E.get('de', -40.0), E.get('ate', 90.0), k)), 0)
        elif mov == 'varre':
            k = chega(t, 0, E.get('bate', .45))
            R.location = V3(*E.get('pivo', (0, 26, 0)))
            R.rotation_euler = (math.radians(E.get('inclina', 0.0)), 0, math.radians(lerp(E.get('de', -110.0), E.get('ate', 70.0), k)))
        elif mov == 'balanca':
            k = suave(0, E.get('bate', .6), t)
            R.location = V3(*E.get('pivo', (0, 0, 170)))
            R.rotation_euler = (0, math.radians(lerp(E.get('de', -70.0), E.get('ate', 70.0), k)), 0)
        acender(R, fade, 1.0, flash * .8)
    return quadro


def esp_mao(m, R, x0=0.0, z0=0.0):
    K.box((x0, 0, z0), (14, 5, 12), m, bevel=2.5, parent=R)
    for k, z in enumerate((-4.2, -1.4, 1.4, 4.2)):
        L = (9, 11, 10.5, 8)[k]
        K.caps((x0 + 6, 0, z0 + z), (x0 + 6 + L, 0, z0 + z * 1.05), 1.55, m, parent=R)
    K.caps((x0 + 2, 0, z0 - 6), (x0 + 9, 0, z0 - 9.5), 1.7, m, parent=R)


def g_maos(E):
    """Mãos de luz que golpeiam para +X, uma atrás da outra."""
    m = mat_espectral('mao', base=.35, borda=1.0, a0=.22, a1=.95)
    rnd = random.Random(E.get('semente', 2))
    maos = []
    for i in range(E.get('quant', 4)):
        R = raiz('mao')
        esp_mao(m, R)
        z = rnd.uniform(-18, 18)
        s = rnd.uniform(.85, 1.25)
        R.scale = (s, s, s)
        maos.append((R, i * .13, z, rnd.uniform(-.25, .25)))
    L = E.get('comp', 90.0)

    def quadro(t):
        set_w(m, t * 2)
        for R, atraso, z, inc in maos:
            tt = max(0.0, min(1.0, (t - atraso) / .5))
            R.location = V3(-L / 2 + L * chega(tt, 0, .55) - 10, 0, z)
            R.rotation_euler = (0, inc, 0)
            acender(R, (1 if t >= atraso else 0) * (1 - suave(.5, 1, tt)), 1.0, max(0.0, 1 - abs(tt - .55) / .15) * .6)
    return quadro


def g_palma(E):
    """Palma de luz chapada de frente (marca de mão), que cresce e estala."""
    m = mat_espectral('palma', base=.6, borda=1.0, a0=.55, a1=1.0, fluxo=3.0)
    R = raiz('palma')
    K.poly([(-11, 0, -16), (11, 0, -16), (13, 0, 6), (-13, 0, 6)], m, esp=1.5, parent=R)
    for x, L in ((-10, 15), (-3.5, 19), (3.5, 18), (10, 14)):
        K.caps((x, 0, 6), (x * 1.06, 0, 6 + L), 2.8, m, parent=R)
    K.caps((-13, 0, -6), (-22, 0, 3), 3.0, m, parent=R)
    R.location = V3(0, 0, 0)

    def quadro(t):
        set_w(m, t * 2)
        k = chega(t, 0, .25)
        s = (.4 + .9 * k) * (1 + .15 * suave(.25, .4, t))
        R.scale = (s, s, s)
        acender(R, 1 - suave(.45, 1, t), 1.0, max(0.0, 1 - abs(t - .27) / .12))
    return quadro


def g_caveira(E):
    """Caveira de alma que voa (laço), com o rastro de névoa para trás."""
    m = mat_espectral('caveira', base=.4, borda=1.0, a0=.35, a1=1.0, fluxo=3.0)
    R = raiz('caveira')
    K.sph((0, 0, 1), 8, m, scale=(1.08, .95, 1), parent=R)
    K.box((3.5, 0, -6.5), (9, 8, 4.5), m, bevel=1.5, parent=R)
    for s in (-1, 1):
        K.sph((6.5, s * 3.2, 2), 2.4, m, parent=R)
    cauda = []
    for i, (x, r) in enumerate(((-9, 6.4), (-15, 5), (-21, 3.8), (-26, 2.6), (-30, 1.6))):
        o = K.sph((x, 0, 0), r, m, scale=(1.5, 1, 1), parent=R)
        cauda.append((o, x, i))

    def quadro(t):
        set_w(m, math.cos(t * TAU))
        for o, x, i in cauda:
            o.location = V3(x, 0, math.sin(t * TAU + i * .9) * 2.2)
        acender(R, 1.0, 1.0, 0)
    return quadro


def g_olho(E):
    """Olho enorme (laço): a íris gira devagar e brilha; as pálpebras são arcos de luz."""
    m = mat_espectral('olho', base=.3, borda=.95, a0=.15, a1=.85)
    mi = mat_espectral('iris', base=.8, borda=1.0, a0=.7, a1=1.0, fluxo=4.0)
    R = raiz('olho')
    K.sph((0, 0, 0), 24, m, scale=(1.6, .35, .7), parent=R)
    iris = K.torus((0, -7, 0), 9.5, 2.6, mi, rot=(math.pi / 2, 0, 0), parent=R)
    K.torus((0, -7.5, 0), 4.2, 1.2, mi, rot=(math.pi / 2, 0, 0), parent=R)
    for s in (-1, 1):
        pts = [(-40 + 80 * i / 24, s * (17 * math.sin(math.pi * i / 24)) + 0) for i in range(25)]
        o = curva([pts], 1.4, 'palpebra', m, plano='XZ', z=-9)
        o.parent = R

    def quadro(t):
        set_w(m, math.cos(t * TAU) * .5)
        set_w(mi, math.sin(t * TAU) * .8)
        iris.rotation_euler = (math.pi / 2, t * TAU / 8, 0)
        acender(R, 1.0, 1.0, .25 + .25 * math.sin(t * TAU))
    return quadro


def g_relogio(E):
    """Mostrador de relógio de luz: surge, os ponteiros disparam e ele some."""
    m = mat_espectral('relogio', base=.4, borda=1.0, a0=.3, a1=.95)
    R = raiz('relogio')
    K.torus((0, 0, 0), 36, 2.4, m, rot=(math.pi / 2, 0, 0), parent=R)
    K.torus((0, 0, 0), 31, 1.0, m, rot=(math.pi / 2, 0, 0), parent=R)
    for i in range(12):
        a = i / 12 * TAU
        L = 7 if i % 3 == 0 else 4
        K.box((math.cos(a) * (31 - L / 2 - 2), 0, math.sin(a) * (31 - L / 2 - 2)), (L, 1.5, 2.2 if i % 3 else 3.2), m, rot=(0, -a, 0), bevel=.4, parent=R)
    ph = raiz('hora')
    ph.parent = R
    K.box((0, -1.5, 9), (3.4, 1.2, 18), m, bevel=.5, parent=ph)
    pm = raiz('minuto')
    pm.parent = R
    K.box((0, -2, 13), (2.2, 1.2, 26), m, bevel=.4, parent=pm)
    K.sph((0, -2, 0), 3, m, parent=R)

    def quadro(t):
        set_w(m, t * 2)
        k = chega(t, 0, .22)
        s = .3 + .7 * k
        R.scale = (s, s, s)
        gira = chega(t, .1, .8)
        pm.rotation_euler = (0, gira * TAU * 3, 0)
        ph.rotation_euler = (0, gira * TAU * .25 + .8, 0)
        acender(R, 1 - suave(.65, 1, t), 1.0, max(0.0, 1 - abs(t - .8) / .1) * .7)
    return quadro


def g_portal(E):
    """Portal de luz: o anel abre, o miolo gira em espiral e fecha com um estalo."""
    m = mat_espectral('portal', base=.45, borda=1.0, a0=.4, a1=1.0)
    R = raiz('portal')
    K.torus((0, 0, 0), 36, 3.4, m, rot=(math.pi / 2, 0, 0), parent=R)
    N = Nos('miolo')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    r = N.math('DIVIDE', N.vmath('LENGTH', N.vet(x, z, 0)), 34 * U)
    ang = N.math('ARCTAN2', z, x)
    gira = N.valor('gira', 0.0)
    espiral = N.math('SINE', N.soma(N.mul(ang, 3.0), N.mul(r, 9.0), gira))
    A = N.mul(N.faixa(espiral, -.2, 1.0, 0, 1), N.faixa(r, .2, 1.0, .3, 1.0), N.faixa(r, .92, 1.0, 1, 0), N.obj_cor()[0], clamp=True)
    I = N.faixa(r, 0, 1, 1.0, .5)
    disco = objeto(m_esfera(34, 36, 10, esc=(1, .04, 1)), 'miolo', N.luz(I, A))
    disco.parent = R

    def quadro(t):
        set_w(m, t * 2)
        k = chega(t, 0, .25) * (1 - chega(t, .75, 1.0))
        s = max(.02, k)
        R.scale = (s, s, s)
        N.v['gira'].default_value = -t * TAU * 2
        acender(R, 1.0 if t < .97 else 0.0, 1.0, max(0.0, 1 - abs(t - .82) / .1))
    return quadro


def g_sol(E):
    """Sol (laço): miolo branco, coroa de raios girando devagar e um halo que pulsa."""
    m = mat_luz('sol', base=1.0, borda=.6, cobre=1.0, blend=.5)
    R = raiz('sol')
    nuc = objeto(m_esfera(16, 24, 16), 'nucleo', m)
    nuc.parent = R
    halo = objeto(m_esfera(30, 24, 16), 'halo', mat_luz('halo', base=.8, borda=.05, cobre=.65, blend=.8))
    halo.parent = R
    raios = raiz('raios')
    raios.parent = R
    for i in range(16):
        a = i / 16 * TAU
        L = 44 if i % 2 == 0 else 32
        pts = [(18, -2.6), (L, 0), (18, 2.6)]
        o = objeto(m_plana(pts), 'raio', m)
        o.rotation_mode = 'XYZ'
        o.rotation_euler = (math.pi / 2, -a, 0)
        o.parent = raios

    def quadro(t):
        raios.rotation_euler = (0, t * TAU / 8, 0)
        s = 1 + .06 * math.sin(t * TAU)
        halo.scale = (s * 1.05, s, s * 1.05)
        acender(R, 1.0, 1.0, 0)
        halo.color = (.85 + .15 * math.sin(t * TAU), 1, 0, 1)
    return quadro


def g_lua_cheia(E):
    """Lua cheia de luz (laço curto): crateras em relevo de luz e um halo."""
    N = Nos('lua')
    co = N.coord('Object')
    vo = N.no('ShaderNodeTexVoronoi')
    N.liga(N.vmath('SCALE', co, escala=1.0 / (20 * U) * 2.2), vo.inputs['Vector'])
    cr = N.faixa(vo.outputs['Distance'], .05, .35, .55, 1.0)
    f = N.facing(.4)
    w = N.valor('w', 0.0)
    rn = N.ruido(N.vmath('SCALE', co, escala=1.0 / (20 * U) * 1.5), escala=1.0, w=w, det=3.0)
    I = N.mul(cr, N.faixa(rn, .3, .7, .8, 1.05))
    A = N.mul(N.faixa(f, 0, 1, 1.0, .6), N.obj_cor()[0], clamp=True)
    lua = objeto(m_esfera(20, 32, 20), 'lua', N.luz(I, A))
    halo = objeto(m_esfera(32, 24, 16), 'halo', mat_luz('halo', base=.75, borda=.05, cobre=.55, blend=.8))

    def quadro(t):
        N.v['w'].default_value = math.cos(t * TAU) * .2
        lua.rotation_euler = (0, 0, t * .3)
        lua.color = (1, 1, 0, 1)
        halo.color = (.8 + .2 * math.sin(t * TAU), 1, 0, 1)
    return quadro


def g_lua(E):
    """Lua crescente de luz (projétil em laço)."""
    m = mat_espectral('crescente', base=.6, borda=1.0, a0=.6, a1=1.0, fluxo=3.0)
    R = raiz('lua')
    pts = [(14 * math.cos(a), 0, 14 * math.sin(a)) for a in [math.radians(60 + 240 * i / 20) for i in range(21)]]
    pts += [(5 + 10.5 * math.cos(a), 0, 10.5 * math.sin(a)) for a in [math.radians(300 - 240 * i / 20) for i in range(21)]]
    K.poly(pts, m, esp=4.0, parent=R)
    halo = objeto(m_esfera(11, 20, 12, esc=(1, .3, 1)), 'halo', mat_luz('halo', base=.6, borda=.05, cobre=.22, blend=.8))
    halo.parent = R

    def quadro(t):
        set_w(m, math.cos(t * TAU))
        acender(R, 1.0, 1.0, 0)
    return quadro


def g_eclipse(E):
    """Eclipse (laço): coroa de luz em volta de um disco escuro (o jogo pinta o escuro), com labaredas girando."""
    m = mat_luz('coroa', base=1.0, borda=.5, cobre=1.0, blend=.4)
    R = raiz('eclipse')
    K.torus((0, 0, 0), 24, 2.2, m, rot=(math.pi / 2, 0, 0), parent=R)
    halo = K.torus((0, 0, 0), 26, 6.5, mat_luz('halo', base=.6, borda=.15, cobre=.45, blend=.75), rot=(math.pi / 2, 0, 0), parent=R)
    lab = raiz('labaredas')
    lab.parent = R
    rnd = random.Random(8)
    for i in range(10):
        a = i / 10 * TAU + rnd.uniform(-.15, .15)
        L = rnd.uniform(34, 46)
        o = objeto(m_plana([(24, -3.2), (L, 0), (24, 3.2)]), 'lab', m)
        o.rotation_mode = 'XYZ'
        o.rotation_euler = (math.pi / 2, -a, 0)
        o.parent = lab

    def quadro(t):
        lab.rotation_euler = (0, t * TAU / 10, 0)
        acender(R, 1.0, 1.0, 0)
        halo.color = (.7 + .3 * math.sin(t * TAU), 1, 0, 1)
    return quadro


def g_espelhos(E):
    """Salão de espelhos: placas de luz sobem em roda, brilham e se partem."""
    m = mat_espectral('espelho', base=.35, borda=1.0, a0=.28, a1=.95)
    placas = []
    for i in range(6):
        a = i / 6 * TAU
        R = raiz('placa')
        K.box((0, 0, 26), (26, 2.4, 50), m, bevel=1.2, parent=R)
        R.location = V3(math.cos(a) * 46, math.sin(a) * 46, 0)
        R.rotation_euler = (0, 0, a + math.pi / 2)
        placas.append((R, i * .04))
    KE.CAM and None
    cacos = KE.g_particulas({'tipo': 'caco', 'tam': 4.0, 'quant': 30, 'mov': 'explode', 'raio': 70.0, 'z0': 26.0, 'gravidade': 30.0,
                             'espalha': .0, 'semente': 4})

    def quadro(t):
        set_w(m, t * 2)
        for R, atraso in placas:
            k = chega(t, atraso, atraso + .25)
            R.scale = (1, 1, max(.01, k))
            acender(R, 1 - suave(.55, .7, t), 1.0, max(0.0, 1 - abs(t - .5) / .1))
        cacos(max(0.0, (t - .58) / .42))
    return quadro


def g_fragmento(E):
    """Caco de cristal de luz (projétil parado; o jogo gira)."""
    m = mat_espectral('frag', base=.5, borda=1.0, a0=.5, a1=1.0)
    R = raiz('frag')
    K.cyl((-9, 0, 0), (9, 0, 0), 3.4, .2, m, verts=5, parent=R)
    K.cyl((-9, 0, 0), (-12, 0, 0), 3.4, .5, m, verts=5, parent=R)
    return lambda t: acender(R, 1.0, 1.0, 0)


def g_lanca_luz(E):
    """Lança (ou flecha) de luz voando para +X (laço curto)."""
    m = mat_espectral('lanca', base=.55, borda=1.0, a0=.55, a1=1.0, fluxo=3.0)
    R = raiz('lanca')
    L = E.get('comp', 60.0)
    K.cyl((-L / 2, 0, 0), (L / 2 - 10, 0, 0), 1.3, 1.3, m, verts=10, parent=R)
    K.cyl((L / 2 - 12, 0, 0), (L / 2, 0, 0), 4.0, .2, m, verts=4, parent=R)
    if E.get('penas'):
        for s in (-1, 1):
            K.poly([(-L / 2, 0, 0), (-L / 2 + 9, 0, 0), (-L / 2 + 6, 0, s * 4.5), (-L / 2 - 1, 0, s * 5)], m, esp=.8, parent=R)
    halo = objeto(m_esfera(L * .55, 24, 12, esc=(1, .12, .12)), 'halo', mat_luz('halo', base=.75, borda=.05, cobre=.5, blend=.8))
    halo.parent = R

    def quadro(t):
        set_w(m, math.cos(t * TAU) * .8)
        acender(R, 1.0, 1.0, 0)
    return quadro


def g_lobo(E):
    """Lobo de luz correndo para +X (laço): as peças do lobo dos monstros, com corpo de energia."""
    import kit_monstros as KM
    R, topo = KM.construir('Lobo de Névoa', 'beast', '#b9c3cf', marcador=False)
    m = mat_espectral('lobo', base=.32, borda=1.0, a0=.2, a1=.95, fluxo=2.0)
    KE.trocar_material(R, m)
    pendurar(R, E.get('escala', 1.0), chao=True)

    def quadro(t):
        set_w(m, t * 2)
        KM.pose(R, 'beast', t)
        acender(R, 1.0, 1.0, 0)
    return quadro


def pendurar(R, s=1.0, chao=False):
    """Pendura o bicho num vazio (a pose dos monstros mexe na raiz): escala e põe o meio na origem (chao=True: os pés)."""
    P = raiz('suporte')
    R.parent = P
    P.scale = (s, s, s)
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in filhos(R):
        if o.type in ('MESH', 'CURVE'):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
    if lo.x < 1e8:
        c = (lo + hi) / 2
        if chao:
            c.z = lo.z
        P.location = -c
    return P


def centrar(R):
    """Põe o meio da caixa de tudo sob R na origem (quem voa é montado no alto)."""
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in filhos(R):
        if o.type in ('MESH', 'CURVE'):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
    if lo.x < 1e8:
        R.location -= (lo + hi) / 2


def g_ave(E):
    """Ave voando para +X (laço): falcão ou corvo, com as asas dos monstros voadores."""
    import kit_monstros as KM
    R, topo = KM.construir('Corvo Agourento', 'flyer', E.get('cor', '#59606e'), marcador=False)
    pendurar(R, E.get('escala', 1.0))

    def quadro(t):
        KM.pose(R, 'flyer', t)
    return quadro


# =============================================================================================
# objetos de verdade (projéteis e armadilhas)
# =============================================================================================
def mn(kind, cor, **kw):
    return mat_nat(kind, cor, **kw)


def obj_flecha(E, pena='#d9d0bf', ponta='#c8ccd0', haste='#8a6a42', L=44.0):
    R = raiz('flecha')
    madeira, metal, pen = mn('wood', haste), mn('metal', ponta), mn('cloth', pena)
    K.cyl((-L / 2, 0, 0), (L / 2 - 6, 0, 0), .85, .85, madeira, verts=10, parent=R)
    K.cyl((L / 2 - 7, 0, 0), (L / 2 + 1, 0, 0), 2.3, .05, metal, verts=4, parent=R)
    for a in (0, 2.094, 4.189):
        pts = [(-L / 2 + 1, 4.2 * math.sin(a) * .0, 0), (-L / 2 + 9, 0, 0), (-L / 2 + 7, 0, 3.6), (-L / 2, 0, 4.2)]
        pts = [(x, -z * math.sin(a), z * math.cos(a)) for x, _, z in pts]
        K.poly(pts, pen, esp=.4, parent=R)
    return R


def obj_virote(E):
    R = raiz('virote')
    madeira, metal, cou = mn('wood', '#5a4630'), mn('metal', '#9aa0a6'), mn('leather', '#6a4a2a')
    K.cyl((-17, 0, 0), (10, 0, 0), 1.2, 1.2, madeira, verts=10, parent=R)
    K.cyl((9, 0, 0), (17, 0, 0), 2.6, .1, metal, verts=4, parent=R)
    for s in (-1, 1):
        K.poly([(-17, 0, 0), (-9, 0, 0), (-11, 0, s * 3.6), (-17.5, 0, s * 3.8)], cou, esp=.5, parent=R)
    return R


def obj_lanca(E):
    R = raiz('lanca')
    madeira, metal = mn('wood', '#7a5a38'), mn('metal', '#c0c6cc')
    K.cyl((-42, 0, 0), (26, 0, 0), 1.3, 1.3, madeira, verts=10, parent=R)
    K.cyl((24, 0, 0), (29, 0, 0), 1.9, 1.6, metal, verts=10, parent=R)
    K.poly([(28, 0, 0), (34, 0, 3.4), (44, 0, 0), (34, 0, -3.4)], metal, esp=1.2, parent=R)
    return R


def obj_adaga(E):
    R = raiz('adaga')
    metal, cou, ouro = mn('metal', '#d0d6dc'), mn('leather', '#3a2a22'), mn('gold', '#c8a050')
    K.poly([(0, 0, -1.8), (12, 0, -1.2), (17, 0, 0), (12, 0, 1.2), (0, 0, 1.8)], metal, esp=.9, parent=R)
    K.box((-.5, 0, 0), (1.6, 2.4, 8.5), ouro, bevel=.4, parent=R)
    K.cyl((-8, 0, 0), (-1, 0, 0), 1.15, 1.15, cou, verts=8, parent=R)
    K.sph((-8.6, 0, 0), 1.8, ouro, parent=R)
    return R


def obj_machado(E):
    R = raiz('machado')
    madeira, metal = mn('wood', '#6a4a2c'), mn('metal', '#b8bec4')
    K.cyl((0, 0, -16), (0, 0, 15), 1.3, 1.3, madeira, verts=8, parent=R)
    K.poly([(0, 0, 15), (7, 0, 19), (13, 0, 15), (13, 0, 4), (7, 0, 7), (0, 0, 8)], metal, esp=1.6, parent=R)
    K.poly([(0, 0, 14), (-5, 0, 15), (-5, 0, 9), (0, 0, 9)], metal, esp=1.4, parent=R)
    return R


def obj_bomba(E):
    R = raiz('bomba')
    ferro, cord = mn('metal', '#2c2a2a', rough=.5), mn('cloth', '#b89a6a')
    K.sph((0, 0, 0), 7, ferro, parent=R)
    K.cyl((0, 0, 6.2), (0, 0, 8), 2.2, 2.2, ferro, verts=12, parent=R)
    K.cyl((0, 0, 8), (2.5, 0, 11.5), .55, .55, cord, verts=6, parent=R)
    fa = objeto(m_esfera(1.6, 12, 8), 'faisca', mat_nat('emit', '#ffd070', emis='#ffc060', forca=40.0))
    fa.location = V3(2.8, 0, 12)
    fa.parent = None
    E['_faisca'] = fa
    return R


def obj_bala(E):
    R = raiz('bala')
    K.sph((0, 0, 0), 8, mn('metal', '#3a3836', rough=.45), parent=R)
    return R


def obj_barril(E):
    R = raiz('barril')
    madeira, ferro, cord = mn('wood', '#7a4e2a'), mn('metal', '#4a4644'), mn('cloth', '#b89a6a')
    K.cyl((0, 0, -13), (0, 0, -4), 9.5, 11, madeira, verts=20, parent=R)
    K.cyl((0, 0, -4), (0, 0, 4), 11, 11, madeira, verts=20, parent=R)
    K.cyl((0, 0, 4), (0, 0, 13), 11, 9.5, madeira, verts=20, parent=R)
    for z in (-9, 0, 9):
        K.torus((0, 0, z), 11.2 - abs(z) * .1, .7, ferro, parent=R)
    K.cyl((0, 0, 13), (3, 0, 17), .6, .6, cord, verts=6, parent=R)
    fa = objeto(m_esfera(1.8, 12, 8), 'faisca', mat_nat('emit', '#ffd070', emis='#ffc060', forca=40.0))
    fa.location = V3(3.3, 0, 17.6)
    E['_faisca'] = fa
    return R


def obj_bolas(E):
    R = raiz('bolas')
    cou, pedra = mn('leather', '#6a4a2c'), mn('stone', '#8a7a64')
    for i in range(3):
        a = i / 3 * TAU + .3
        p = (math.cos(a) * 12, 0, math.sin(a) * 12)
        K.cyl((0, 0, 0), p, .5, .5, cou, verts=6, parent=R)
        K.sph(p, 3.6, pedra, parent=R)
    K.sph((0, 0, 0), 1.4, cou, parent=R)
    return R


def obj_engrenagem(E):
    R = raiz('engrenagem')
    me = KE._malha_part('engrenagem', 8.0)
    o = objeto(me, 'eng', mat_nat('gold', '#d8b060', rough=.42, metal=.55, emis='#a07830', forca=.25))
    o.rotation_euler = (math.pi / 2, 0, 0)
    o.parent = R
    return R


def obj_rocha(E):
    R = raiz('rocha')
    o = objeto(m_rocha(10, 5, .4), 'rocha', mn('stone', '#7a6a58'))
    o.parent = R
    return R


def obj_lanca_gelo(E):
    R = raiz('gelo')
    gelo = mat_nat('glass', '#cdeeff', emis='#7ec8ff', forca=1.2, rough=.08)
    K.cyl((-24, 0, 0), (24, 0, 0), 4.6, .1, gelo, verts=6, parent=R)
    K.cyl((-24, 0, 0), (-28, 0, 0), 4.6, 1.5, gelo, verts=6, parent=R)
    for s, x in ((1, -10), (-1, -2), (1, 8)):
        K.cyl((x, 0, 0), (x + 9, 0, s * 4.5), 1.8, .1, gelo, verts=5, parent=R)
    return R


def obj_corrente(E):
    R = raiz('corrente')
    ferro = mn('metal', '#8a8e92', rough=.35)
    L = E.get('comp', 100.0)
    n = int(L / 6.2)
    for i in range(n):
        x = -L / 2 + i * 6.2
        K.torus((x, 0, 0), 3.0, .85, ferro, rot=((math.pi / 2) if i % 2 else 0, 0, 0), scale=(1.45, 1, 1), parent=R)
    K.cyl((L / 2, 0, 0), (L / 2 + 6, 0, 0), 2.0, 2.0, ferro, verts=8, parent=R)
    K.torus((L / 2 + 9, 0, -3), 4.5, 1.2, ferro, rot=(math.pi / 2, 0, 0), parent=R)
    return R


def g_objeto_simples(E):
    R = E['obj'](E)
    fa = E.get('_faisca')

    def quadro(t):
        if fa:
            s = .7 + .6 * abs(math.sin(t * TAU * 1.5 + .4))
            fa.scale = (s, s, s)
    return quadro


# ---------- coisas que irrompem do chão ----------
def m_espinhos_ferro(E):
    rnd = random.Random(6)
    ferro = mn('metal', '#5a5a5e', rough=.55)
    pecas = []
    for i in range(11):
        a = i / 11 * TAU + rnd.uniform(-.2, .2)
        L = rnd.uniform(36, 58)
        dist = rnd.uniform(6, 20)
        R = raiz('espinho')
        K.cyl((0, 0, 0), (0, 0, L), 4.2, .15, ferro, verts=6, parent=R)
        R.location = V3(math.cos(a) * dist, math.sin(a) * dist, -2)
        R.rotation_euler = (0, math.radians(rnd.uniform(28, 48)), a)
        pecas.append((R, rnd.uniform(0, .1), L))
    return pecas


def m_cristais(E):
    rnd = random.Random(E.get('semente', 3))
    gelo = mat_nat('glass', '#d6f2ff', emis='#7ec8ff', forca=1.6, rough=.06)
    pecas = []
    for i in range(E.get('quant', 8)):
        a = rnd.uniform(0, TAU)
        d = rnd.uniform(0, E.get('raio', 30.0))
        H = rnd.uniform(.55, 1.0) * E.get('alto', 80.0) * (1.25 - d / max(1, E.get('raio', 30.0)) * .5)
        r = H * rnd.uniform(.13, .18)
        R = raiz('cristal')
        K.cyl((0, 0, 0), (0, 0, H * .8), r, r * .9, gelo, verts=6, parent=R)
        K.cyl((0, 0, H * .8), (0, 0, H), r * .9, .1, gelo, verts=6, parent=R)
        R.location = V3(math.cos(a) * d, math.sin(a) * d, -2)
        R.rotation_euler = (math.radians(rnd.uniform(-22, 22)), math.radians(rnd.uniform(-22, 22)), rnd.uniform(0, TAU))
        pecas.append((R, rnd.uniform(0, .12), H))
    return pecas


def m_pilar_pedra(E):
    rnd = random.Random(2)
    pedra = mn('stone', '#7d7266')
    pecas = []
    R = raiz('pilar')
    for k in range(4):
        o = objeto(m_rocha(18 - k * 2.2, 10 + k, .22), 'bloco', pedra)
        o.location = V3(0, 0, 14 + k * 26)
        o.scale = (1, 1, 1.5)
        o.parent = R
    R.location = V3(0, 0, -4)
    pecas.append((R, 0.0, 100.0))
    for i in range(6):
        a = i / 6 * TAU + rnd.uniform(-.3, .3)
        o = objeto(m_rocha(rnd.uniform(5, 9), 20 + i, .35), 'lasca', pedra)
        o.location = V3(math.cos(a) * 26, math.sin(a) * 26, 2)
        pecas.append((o, .05, 10.0))
    return pecas


def m_vinhas(E):
    rnd = random.Random(E.get('semente', 5))
    caule = mn('wood', '#5c7434', rough=.7)
    folha = mn('cloth', '#74a844')
    pecas = []
    for i in range(E.get('quant', 6)):
        a0 = i / E.get('quant', 6) * TAU + rnd.uniform(-.3, .3)
        rr = E.get('raio', 26.0) * rnd.uniform(.85, 1.15)
        H = E.get('alto', 90.0) * rnd.uniform(.75, 1.05)
        pts = []
        for k in range(28):
            s = k / 27
            a = a0 + s * TAU * rnd.uniform(.5, .8) * (1 if i % 2 else -1)
            r = rr * (1 - .45 * s) + 5 * math.sin(s * 9 + i)
            pts.append((math.cos(a) * r, math.sin(a) * r, H * s))
        cu = bpy.data.curves.new('vinha', 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = 3.6 * U
        cu.bevel_resolution = 2
        cu.use_fill_caps = True
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for p, (x, y, z) in zip(sp.points, pts):
            p.co = (x * U, y * U, z * U, 1)
            p.radius = 1.0
        for j, p in enumerate(sp.points):
            p.radius = 1.0 - .75 * j / len(pts)
        cu.materials.append(caule)
        o = bpy.data.objects.new('vinha', cu)
        bpy.context.collection.objects.link(o)
        cu.bevel_factor_mapping_end = 'SPLINE'
        for k in range(4, 28, 5):
            x, y, z = pts[k]
            fo = objeto(KE._malha_part('folha', 4.5), 'folha', folha)
            fo.location = V3(x, y, z)
            fo.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 6))
            fo['k'] = k / 27
            fo.parent = None
            pecas.append((fo, i * .03 + k / 27 * .3, 0.0))
        o['vinha'] = 1
        pecas.append((o, i * .03, 0.0))
    return pecas


def g_vinhas(E):
    pecas = m_vinhas(E)

    def quadro(t):
        for o, atraso, _ in pecas:
            if o.get('vinha'):
                o.data.bevel_factor_end = max(.001, chega(t, atraso, atraso + .45))
            else:
                k = chega(t, atraso, atraso + .2)
                o.scale = (max(.001, k),) * 3
    return quadro


def g_rede(E):
    """Rede que cai e prende o alvo (fica presa no último quadro)."""
    n = 12
    S = E.get('lado', 74.0)
    me = malha('rede', lambda bm: bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=S * U / 2))
    o = objeto(me, 'rede', mn('cloth', '#b89a6a', rough=.9))
    wf = o.modifiers.new('fios', 'WIREFRAME')
    wf.thickness = 1.3 * U
    wf.use_replace = True
    base = [Vector(v.co) for v in me.vertices]
    Rb, Hb = E.get('raio_alvo', 26.0), E.get('alto_alvo', 56.0)
    rnd = random.Random(1)
    ond = [rnd.uniform(0, TAU) for _ in base]

    def quadro(t):
        k = cai(t, 0, .45)
        assenta = chega(t, .4, .7)
        for v, b, f in zip(me.vertices, base, ond):
            x, y = b.x / U, b.y / U
            r = math.hypot(x, y)
            cola = Hb * math.sqrt(max(0.0, 1 - (r / (Rb * 1.25)) ** 2)) if r < Rb * 1.25 else max(0.0, Hb * .1 - (r - Rb * 1.25) * .3)
            alto = 110 * (1 - k) + Hb * .9
            z = lerp(alto + math.sin(f + t * 8) * 3, cola + 1.5, assenta)
            aperta = 1 - .25 * assenta * min(1, r / (S / 2))
            v.co = Vector((b.x * aperta, b.y * aperta, z * U))
        me.update()
    return quadro


def g_armadilha(E):
    """Armadilha de dentes: aberta no chão, fecha de uma vez e solta faíscas."""
    ferro = mn('metal', '#6a6a6e', rough=.45)
    K.torus((0, 0, 1), 20, 1.3, ferro, scale=(1, 1, .6))
    mand = []
    for s in (-1, 1):
        R = raiz('mand')
        pts = []
        for i in range(17):
            a = math.pi * i / 16
            rr = 20 if i % 2 == 0 else 15.5
            pts.append((rr * math.cos(a), 0, rr * math.sin(a) * .55))
        K.poly([(x, 0, z) for x, _, z in pts], ferro, esp=1.6, parent=R)
        R.rotation_euler = (0, 0, 0)
        R['s'] = s
        mand.append(R)
    fa = KE.g_particulas({'tipo': 'faisca', 'tam': 1.2, 'quant': 16, 'mov': 'explode', 'raio': 40.0, 'z0': 14.0, 'gravidade': 30.0, 'espalha': 0.0,
                          'luz': False, 'kind': 'emit', 'cor': '#ffd27a', 'emis': '#ffb050', 'forca': 30.0})

    def quadro(t):
        k = cai(t, .15, .32)
        for R in mand:
            R.rotation_euler = (math.radians(R['s'] * lerp(84, 4, k)), 0, 0)
        fa(max(0.0, (t - .32) / .68))
    return quadro


def g_correntes(E):
    """Correntes enroladas em volta do alvo (laço): elos numa espiral que gira devagar."""
    ferro = mn('metal', '#8a8e92', rough=.35)
    R = raiz('correntes')
    r, z0, z1 = E.get('raio', 28.0), 8.0, 70.0
    n = 46
    for i in range(n):
        s = i / n
        a = s * TAU * 2.2
        p = (math.cos(a) * r, math.sin(a) * r, lerp(z0, z1, s))
        tang = Vector((-math.sin(a), math.cos(a), (z1 - z0) / (TAU * 2.2 * r)))
        o = K.torus(p, 3.0, .9, ferro, scale=(1.45, 1, 1), parent=R)
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = tang.to_track_quat('X', 'Z') @ Quaternion((1, 0, 0), (math.pi / 2) * (i % 2))

    def quadro(t):
        R.rotation_euler = (0, 0, t * TAU)
    return quadro


def g_grilhoes(E):
    ferro = mn('metal', '#7a7c80', rough=.4)
    R = raiz('grilhao')
    K.torus((0, 0, 0), 11, 2.0, ferro, rot=(math.pi / 2, 0, 0), parent=R)
    K.box((0, 0, -11), (8, 5, 5), ferro, bevel=1, parent=R)
    for i in range(3):
        K.torus((0, 0, 14 + i * 6), 3.0, .9, ferro, rot=(0, 0, (math.pi / 2) * (i % 2)), scale=(1, 1, 1.45), parent=R)

    def quadro(t):
        R.location = V3(0, 0, math.sin(t * TAU) * 3)
        R.rotation_euler = (0, 0, math.sin(t * TAU) * .35)
    return quadro


def g_reliquia(E):
    ouro, gema, mad = mn('gold', '#d0a850'), mat_nat('glass', '#ff6040', emis='#ff5030', forca=6.0), mn('wood', '#5a3a22')
    R = raiz('reliquia')
    K.box((0, 0, 0), (22, 14, 14), ouro, bevel=1.5, parent=R)
    K.cyl((-11, 0, 7), (11, 0, 7), 7, 7, ouro, verts=20, parent=R)
    K.box((0, 0, 0), (23, 15, 3), mad, bevel=.5, parent=R)
    for x in (-6, 0, 6):
        K.sph((x, -7.2, 1), 1.8, gema, parent=R)
    K.cyl((0, 0, 14), (0, 0, 24), 1.0, 1.0, ouro, verts=8, parent=R)
    K.box((0, 0, 21), (8, 1.6, 1.6), ouro, bevel=.3, parent=R)

    def quadro(t):
        R.location = V3(0, 0, 20 + math.sin(t * TAU) * 3)
        R.rotation_euler = (0, 0, t * TAU)
    return quadro


def g_estandarte(E):
    """Estandarte fincado com o pano tremulando (laço)."""
    mad, ouro, pano = mn('wood', '#5a3c22'), mn('gold', '#d8b050'), mn('cloth', E.get('cor', '#8a2a1e'))
    K.cyl((0, 0, -4), (0, 0, 128), 1.8, 1.6, mad, verts=10)
    K.cyl((-2, 0, 122), (34, 0, 122), 1.2, 1.2, mad, verts=8)
    K.sph((0, 0, 131), 3.4, ouro)
    K.cyl((0, 0, 131), (0, 0, 140), 1.4, .1, ouro, verts=8)
    nx, nz = 10, 14
    me = malha('pano', lambda bm: bmesh.ops.create_grid(bm, x_segments=nx, y_segments=nz, size=1.0))
    o = objeto(me, 'pano', pano)
    base = [Vector(v.co) for v in me.vertices]
    emb = mat_nat('emit', '#f0c060', emis='#ffb040', forca=3.0)
    sol = objeto(m_esfera(7, 16, 10, esc=(1, .2, 1)), 'emblema', emb)

    def quadro(t):
        for v, b in zip(me.vertices, base):
            u, w = (b.x + 1) / 2, (b.y + 1) / 2   # u ao longo da barra, w de cima (1) para baixo (0)
            x = 2 + u * 31
            z = 121 - (1 - w) * 62 - (u * 6 if w < .15 else 0)
            y = math.sin(u * 5.5 - t * TAU) * 4.5 * u + math.sin(w * 4 + t * TAU) * 1.2 * u
            v.co = V3(x, y, z)
        me.update()
        sol.location = V3(18, math.sin(.5 * 5.5 - t * TAU) * 2.2 - 2.5, 92)
    return quadro


def g_chuva_flechas(E):
    """Saraivada: flechas caem do alto em diagonal e cravam no chão em volta do alvo."""
    rnd = random.Random(E.get('semente', 7))
    modelo = obj_flecha(E)
    pecas = [modelo] + list(filhos(modelo))
    flechas = []
    for i in range(E.get('quant', 14)):
        R = raiz('f%d' % i)
        for p in [modelo] + list(filhos(modelo)):
            if p.type == 'MESH' and p.parent == modelo:
                c = p.copy()
                bpy.context.collection.objects.link(c)
                c.parent = R
        a = rnd.uniform(0, TAU)
        d = math.sqrt(rnd.uniform(0, 1)) * E.get('raio', 42.0)
        flechas.append((R, (math.cos(a) * d, math.sin(a) * d * .9), rnd.uniform(0, .45), rnd.uniform(-.15, .15)))
    for p in pecas:
        p.hide_render = True
    dirv = Vector((.45, .25, -1)).normalized()

    def quadro(t):
        for R, (x, y), atraso, inc in flechas:
            k = cai(t, atraso, atraso + .22)
            fim = Vector((x, y, 8))
            p = fim - dirv * 160 * (1 - k)
            R.location = V3(*p)
            apontar(R, dirv + Vector((inc, 0, 0)))
            vis = 1.0 if t >= atraso else 0.0
            R.hide_render = vis == 0
            fade = 1 - suave(.8, 1, t)
            acender(R, fade)
    return quadro


def g_onda_agua(E):
    """Onda que estoura: uma coroa de água sobe em volta do alvo, abre e cai, com gotas."""
    agua = mat_nat('gloss', '#5cc4e0', emis='#a8ecff', forca=2.4, rough=.12)
    n = 48
    me = malha('coroa', lambda bm: bmesh.ops.create_cone(bm, cap_ends=False, segments=n, radius1=1 * U, radius2=1 * U, depth=1 * U))
    for v in me.vertices:
        v.co.z += .5 * U
    o = objeto(me, 'coroa', agua)
    sd = o.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = 4.5 * U
    sub = o.modifiers.new('suave', 'SUBSURF')
    sub.levels = sub.render_levels = 2
    base = [Vector(v.co) for v in me.vertices]
    rnd = random.Random(3)
    pontas = [rnd.uniform(.7, 1.3) for _ in range(n)]
    espuma = K.torus((0, 0, 1), 30, 5.0, mat_nat('cloth', '#e8faff', emis='#ffffff', forca=.6), scale=(1, 1, .35))
    gotas = KE.g_particulas({'tipo': 'gota', 'tam': 2.2, 'quant': 26, 'mov': 'explode', 'raio': 80.0, 'z0': 40.0, 'gravidade': 70.0,
                             'espalha': .05, 'luz': False, 'kind': 'glass', 'cor': '#9fe4f4', 'emis': '#bff4ff', 'forca': .6, 'el0': .2, 'el1': 1.0})

    def quadro(t):
        sobe = chega(t, 0, .35) * (1 - cai(t, .45, 1.0))
        abre = chega(t, 0, .8)
        for i, (v, b) in enumerate(zip(me.vertices, base)):
            topo = b.z > 0
            a = math.atan2(b.y, b.x)
            j = int((a / TAU % 1) * n) % n
            r = (22 + 20 * abre) + (14 * abre if topo else 0)
            z = (70 * sobe * pontas[j] + 6 * math.sin(a * 5 + t * 6)) if topo else 0
            v.co = V3(math.cos(a) * r, math.sin(a) * r, z)
        me.update()
        acender(o, 1 - suave(.75, 1, t))
        espuma.scale = (.6 + abre, .6 + abre, 1)
        acender(espuma, (1 - suave(.6, 1, t)) * .9)
        gotas(max(0.0, (t - .25) / .75))
    return quadro


def g_redemoinho(E):
    """Redemoinho de água no chão (laço)."""
    R = E.get('raio', 50.0)
    me = malha('chao', lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=R * U))
    N = Nos('redemoinho')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    rho = N.math('DIVIDE', N.vmath('LENGTH', N.vet(x, y, 0)), R * U)
    ang = N.math('ARCTAN2', y, x)
    gira = N.valor('gira', 0.0)
    braco = N.math('SINE', N.soma(N.mul(ang, 3.0), N.mul(N.math('LOGARITHM', N.math('MAXIMUM', rho, .02), 2.718), 5.0), gira))
    rn = N.ruido(N.vet(N.mul(x, 40.0), N.mul(y, 40.0), 0), escala=1.0, w=N.mul(gira, .2), det=3.0)
    espuma = N.faixa(N.soma(braco, N.mul(rn, .6)), .55, .95, 0, 1)
    disco = N.faixa(rho, .65, 1.0, 1, 0, suave=True)
    cor = N.no('ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = K.hex_lin('#0c3a4a')
    cor.inputs[7].default_value = K.hex_lin('#d8f6ff')
    N.liga(espuma, cor.inputs[0])
    fundo = N.faixa(rho, 0, .35, 1, 0)
    A = N.mul(disco, N.soma(.55, N.mul(espuma, .45)), N.obj_cor()[0], clamp=True)
    m = N.luz_cor(cor.outputs[2], A, forca=1.0)
    o = objeto(me, 'redemoinho', m)
    o.location.z = .4 * U

    def quadro(t):
        N.v['gira'].default_value = -t * TAU
        o.color = (1, 1, 0, 1)
    return quadro


def g_fenda(E):
    """Fenda no chão: rachaduras de brasa se abrem a partir do centro e lascas saltam."""
    rnd = random.Random(E.get('semente', 2))
    tracos = []
    for i in range(E.get('bracos', 5)):
        a = i / E.get('bracos', 5) * TAU + rnd.uniform(-.4, .4)
        L = rnd.uniform(.6, 1.0) * E.get('raio', 70.0)
        p = Vector((0, 0, 0))
        pts = [(0.0, 0.0)]
        for k in range(10):
            a += rnd.uniform(-.45, .45)
            p += Vector((math.cos(a), math.sin(a), 0)) * L / 10
            pts.append((p.x, p.y))
        tracos.append(pts)
        if rnd.random() < .7:
            j = rnd.randrange(3, 8)
            q = Vector((pts[j][0], pts[j][1], 0))
            b = a + rnd.choice((-1, 1)) * rnd.uniform(.6, 1.1)
            sub = [(q.x, q.y)]
            for k in range(5):
                b += rnd.uniform(-.4, .4)
                q += Vector((math.cos(b), math.sin(b), 0)) * L / 14
                sub.append((q.x, q.y))
            tracos.append(sub)
    brasa = mat_nat('emit', '#ff9a40', emis=E.get('cor', '#ff7a2a'), forca=E.get('forca', 14.0))
    escuro = mn('stone', '#1c1612', rough=.95)
    borda = curva(tracos, 3.2, 'borda', escuro, 'XY', .2)
    nuc = curva(tracos, 1.3, 'brasa', brasa, 'XY', .6)
    for o in (borda, nuc):
        o.data.bevel_factor_mapping_end = 'SPLINE'
    lascas = KE.g_particulas({'tipo': 'pedra', 'tam': 3.2, 'quant': 18, 'mov': 'explode', 'raio': 55.0, 'z0': 4.0, 'gravidade': 60.0,
                              'espalha': .1, 'luz': False, 'kind': 'stone', 'cor': '#6a5e52', 'el0': .5, 'el1': 1.3})

    def quadro(t):
        k = chega(t, 0, .3)
        for o in (borda, nuc):
            o.data.bevel_factor_end = max(.001, k)
        acender(nuc, 1 - suave(.6, 1, t))
        acender(borda, 1 - suave(.75, 1, t))
        lascas(t)
    return quadro


def g_prisma(E):
    """Feixe de arco-íris (laço): faixas de cor de um lado ao outro e o miolo branco."""
    L, r = E.get('comp', 100.0), E.get('raio', 6.0)
    N = Nos('prisma')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    a, b = N.valor('a', 0.0), N.valor('b', 0.0)
    f = N.facing(.35)
    hue = N.no('ShaderNodeCombineColor')
    hue.mode = 'HSV'
    N.e(hue.inputs[0], N.math('FRACT', N.soma(N.mul(x, 1.0 / (r * U) * .45), .5, N.mul(a, .08))))
    hue.inputs[1].default_value = .75
    hue.inputs[2].default_value = 1.0
    mx = N.no('ShaderNodeMix', data_type='RGBA')
    N.liga(N.faixa(f, 0, .3, .35, 0), mx.inputs[0])
    N.liga(hue.outputs[0], mx.inputs[6])
    mx.inputs[7].default_value = (1, 1, 1, 1)
    rn = N.ruido(N.vet(N.mul(x, 30.0), N.mul(y, 30.0), N.soma(N.mul(z, 18.0), a)), escala=1.0, w=b, det=3.0)
    A = N.mul(N.faixa(f, 0, 1, .62, 0), N.faixa(rn, .3, .65, .6, 1.1), N.obj_cor()[0], clamp=True)
    m = N.luz_cor(mx.outputs[2], A)
    corpo = objeto(m_cilindro(r * 1.6, L, 24), 'prisma', m)
    corpo.rotation_euler = (0, math.pi / 2, 0)
    halo = objeto(m_cilindro(r * .4, L, 16), 'miolo', mat_luz('miolo', base=1.0, borda=.8, cobre=.9, blend=.4, borda_a=0))
    halo.rotation_euler = (0, math.pi / 2, 0)

    def quadro(t):
        N.v['a'].default_value = math.sin(t * TAU) * 1.0
        N.v['b'].default_value = math.cos(t * TAU) * 1.0
        corpo.color = (1, 1, 0, 1)
        halo.color = (1, 1, 0, 1)
    return quadro


def g_meteoro(E):
    """Meteoro (laço): pedra em brasa com cauda de fogo para trás (-X)."""
    pedra = mat_nat('stone', '#3a2a22', emis='#ff6a20', forca=1.5)
    o = objeto(m_rocha(11, 7, .35), 'pedra', pedra)
    E2 = dict(E, raio=14.0, cauda=4.0, z=0.0, fogo=True, dom=(130, 40, 40), base=-20.0, cx=-40.0, laco=True, densidade=5.0, brilho_fogo=12.0, fofo=2.4,
              curva_r=lambda t: 15.0, curva_z=lambda t: 0.0, curva_d=lambda t: 1.0, curva_c=lambda t: 1.0, grao=2.0)
    fogo = KE.g_volume(E2)

    def quadro(t):
        o.rotation_euler = (t * TAU, t * TAU * .5, 0)
        fogo(t)
    return quadro


def g_erupcao(E):
    """Erupção: o chão racha, sobe uma coluna de fogo e voam pedras em brasa."""
    fenda = g_fenda(dict(E, raio=50.0, bracos=5, semente=4))
    E2 = dict(E, raio=40.0, z=40.0, fogo=True, dom=(110, 110, 230), base=-10.0, densidade=6.0, achata=2.6, brilho_fogo=12.0, fofo=2.6,
              curva_r=lambda t: 40.0 * (.4 + .6 * chega(t, .05, .4)), curva_z=lambda t: 30 + 70 * chega(t, .05, .6),
              curva_d=lambda t: env(t, .08, .45), curva_c=lambda t: 1.2 - .9 * chega(t, .2, 1.0), mexe=1.5, rola=1.6)
    fogo = KE.g_volume(E2)
    pedras = KE.g_particulas({'tipo': 'pedra', 'tam': 4.0, 'quant': 14, 'mov': 'explode', 'raio': 120.0, 'z0': 20.0, 'gravidade': 140.0,
                              'espalha': .15, 'luz': False, 'kind': 'stone', 'cor': '#3a2a22', 'emis': '#ff6a20', 'forca': 3.0, 'el0': .9, 'el1': 1.45,
                              'semente': 9})

    def quadro(t):
        fenda(t)
        fogo(t)
        pedras(t)
    return quadro


def g_nevasca(E):
    """Nevasca (laço): névoa fria girando e flocos de neve em volta."""
    E2 = dict(E, raio=56.0, z=40.0, dom=(150, 150, 120), base=-5.0, cor_fumaca='#dceaf4', densidade=2.2, achata=.7, laco=True, ferve=.8,
              curva_r=lambda t: 56.0, curva_z=lambda t: 36.0, curva_d=lambda t: 1.0, emis='#9fd0ff', forca=.25, fofo=2.4)
    nevoa = KE.g_volume(E2)
    flocos = KE.g_particulas({'tipo': 'floco', 'tam': 2.4, 'quant': 34, 'mov': 'orbita', 'raio': 50.0, 'z0': 30.0, 'voltas': 1, 'ondula': 18.0,
                              'luz': False, 'kind': 'cloth', 'cor': '#ffffff', 'emis': '#e8f6ff', 'forca': 1.5, 'laco': True})

    def quadro(t):
        nevoa(t)
        flocos(t)
    return quadro


def g_explosao(E):
    fogo = KE.g_volume(E)
    brasas = KE.g_particulas({'tipo': 'faisca', 'tam': 1.4, 'quant': 22, 'mov': 'explode', 'raio': E.get('raio', 55.0) * 1.6, 'z0': 30.0,
                              'gravidade': 40.0, 'espalha': .05, 'luz': False, 'kind': 'emit', 'cor': '#ffc070', 'emis': '#ffa040', 'forca': 40.0,
                              'el0': .1, 'el1': 1.3})

    def quadro(t):
        fogo(t)
        brasas(t)
    return quadro


def g_chamas(E):
    E2 = dict(E, raio=24.0, z=50.0, fogo=True, dom=(70, 70, 150), base=-5.0, achata=2.6, densidade=7.0, laco=True, ferve=.9, brilho_fogo=9.0,
              curva_r=lambda t: 24.0, curva_z=lambda t: 45.0, curva_d=lambda t: 1.0, curva_c=lambda t: .95, grao=3.4, miolo=.1, fofo=3.0, det=4.0)
    return KE.g_volume(E2)


def g_bola_fogo(E):
    E2 = dict(E, raio=11.0, cauda=3.2, z=0.0, fogo=True, dom=(80, 30, 30), base=-15.0, cx=-20.0, laco=True, densidade=6.0, brilho_fogo=12.0, fofo=2.4,
              curva_r=lambda t: 11.0, curva_z=lambda t: 0.0, curva_d=lambda t: 1.0, curva_c=lambda t: 1.15, grao=2.2, ferve=.7)
    return KE.g_volume(E2)


# =============================================================================================
# o catálogo
# =============================================================================================
def P(**kw):
    return kw


EFEITOS = {
    # golpes de luz (o jogo gira e espelha)
    'golpe_arco': P(gen=KE.g_rastro, modo='lado', forma='arco', raio=42, largura=24, larg=116, alt=104, u=.8, n=10, dur=.3),
    'golpe_estocada': P(gen=KE.g_rastro, modo='lado', forma='estocada', raio=52, largura=11, larg=120, alt=36, u=.7, n=9, dur=.24, fio=.5),
    'golpe_x': P(gen=KE.g_rastro, modo='lado', forma='x', raio=38, largura=13, larg=100, alt=90, u=.8, n=11, dur=.34, fio=.5),
    'golpe_garra': P(gen=KE.g_rastro, modo='lado', forma='garra', raio=34, largura=12, larg=90, alt=90, u=.8, n=10, dur=.3, fio=.5),
    'impacto': P(gen=g_impacto, modo='lado', larg=100, alt=100, u=.8, n=9, dur=.32),
    'clarao': P(gen=g_clarao, modo='lado', raio=62, larg=140, alt=140, u=1.0, n=9, dur=.38),
    'onda': P(gen=KE.g_onda, modo='iso', raio=70, larg=160, alt=90, u=1.0, n=12, dur=.5, chao=1),
    'sigilo': P(gen=KE.g_traco, modo='iso', forma='sigilo', raio=50, pontas=6, runas=6, simetria=6, laco=True, larg=115, alt=70, u=.65, n=12, dur=2.0, chao=1),
    'sigilo_abre': P(gen=KE.g_traco, modo='iso', forma='sigilo', raio=50, pontas=6, runas=6, giro=.6, larg=115, alt=70, u=.65, n=14, dur=.8, chao=1, apaga=.3),
    'runa': P(gen=g_runa_flutua, modo='lado', raio=18, larg=50, alt=50, u=.45, n=12, dur=1.2, semente=12),
    'mira': P(gen=KE.g_traco, modo='iso', forma='mira', raio=32, simetria=4, laco=True, larg=90, alt=55, u=.6, n=12, dur=1.6, chao=1),
    'pilar_luz': P(gen=g_pilar, modo='iso', altura=300, raio=22, larg=110, alt=330, alvo=120, u=1.2, n=12, dur=.7),
    'feixe': P(gen=g_feixe, modo='lado', comp=100, raio=2.8, larg=106, alt=26, u=.55, n=6, laco=True, dur=.3),
    'orbe': P(gen=g_orbe, modo='lado', raio=6.5, cauda=24, larg=56, alt=28, u=.45, n=6, laco=True, dur=.3),
    'faiscas': P(gen=KE.g_particulas, modo='iso', tipo='faisca', tam=1.3, quant=26, mov='explode', raio=55, z0=30, gravidade=35, espalha=.08,
                 larg=140, alt=130, alvo=30, u=.9, n=10, dur=.45),
    'motas': P(gen=KE.g_particulas, modo='iso', tipo='mota', tam=1.6, quant=22, mov='sobe', raio=30, altura=100, laco=True, base=1.0, borda=.2,
               larg=90, alt=130, alvo=50, u=.8, n=16, dur=1.6),
    'fagulhas': P(gen=KE.g_particulas, modo='iso', tipo='faisca', tam=1.2, quant=34, mov='cai', raio=42, altura=150, vento=30, espalha=.5,
                  larg=130, alt=170, alvo=70, u=.9, n=14, dur=.9),
    'brasas': P(gen=KE.g_particulas, modo='iso', tipo='brasa', tam=1.5, quant=16, mov='gira_sobe', raio=22, altura=70, voltas=1, espalha=.3,
                base=1.0, borda=.25, larg=70, alt=100, alvo=35, u=.7, n=12, dur=.7),
    'notas': P(gen=KE.g_particulas, modo='iso', tipo='nota', tam=7.0, quant=9, mov='sobe', raio=30, altura=110, espalha=.4, base=1.0,
               larg=100, alt=150, alvo=60, u=.8, n=14, dur=1.0),
    'estrelas': P(gen=KE.g_particulas, modo='iso', tipo='estrela', tam=4.2, quant=5, mov='orbita', raio=17, z0=0, voltas=1, ondula=2.5, pisca=1,
                  laco=True, larg=60, alt=40, u=.45, n=12, dur=.9),
    'vortice': P(gen=KE.g_particulas, modo='iso', tipo='risco', tam=1.3, quant=46, mov='espiral', raio=75, altura=60, z0=10, voltas=1.2,
                 espalha=.35, larg=170, alt=130, alvo=35, u=1.0, n=14, dur=.8),
    'estilhacos': P(gen=KE.g_particulas, modo='iso', tipo='caco', tam=4.0, quant=24, mov='explode', raio=60, z0=34, gravidade=40, espalha=.05,
                    larg=140, alt=130, alvo=30, u=.9, n=10, dur=.5),
    'aura': P(gen=g_aura, modo='iso', raio=28, altura=100, larg=100, alt=150, alvo=55, u=.9, n=12, laco=True, dur=1.0),
    'ciclone': P(gen=g_ciclone, modo='iso', raio0=10, raio=46, altura=110, larg=120, alt=150, alvo=55, u=.9, n=10, laco=True, dur=.5),
    'cupula': P(gen=g_cupula, modo='iso', raio=52, larg=130, alt=120, alvo=30, u=.9, n=12, laco=True, dur=1.4),
    'raio': P(gen=KE.g_raio, modo='iso', alto=280, grosso=1.6, galhos=4, larg=110, alt=310, alvo=120, u=1.0, n=8, dur=.42),
    'raio_lado': P(gen=KE.g_raio, modo='lado', comp=120, grosso=1.3, galhos=3, rugo=.18, larg=130, alt=50, u=.7, n=6, laco=True, dur=.24,
                   pisca=[1.0, .8, 1.0, .7, .9, .75]),
    'lanca_luz': P(gen=g_lanca_luz, modo='lado', comp=62, larg=76, alt=24, u=.45, n=4, laco=True, dur=.2),
    'flecha_luz': P(gen=g_lanca_luz, modo='lado', comp=46, penas=1, larg=58, alt=18, u=.4, n=4, laco=True, dur=.2),
    'escudo': P(gen=g_arma, modo='iso', peca=esp_escudo, mov='cai', alto=150, bate=.3, larg=110, alt=190, alvo=60, u=.9, n=12, dur=.55),
    'espada': P(gen=g_arma, modo='iso', peca=esp_espada, mov='cai', alto=220, crava=-14, bate=.32, escala=1.35, larg=110, alt=300, alvo=100, u=1.0, n=12, dur=.6),
    'martelo': P(gen=g_arma, modo='iso', peca=esp_martelo, mov='golpe', pivo=(-96, 0, 14), de=-40, ate=90, bate=.32, larg=170, alt=180, alvo=55,
                 u=1.0, n=12, dur=.5),
    'foice': P(gen=g_arma, modo='iso', peca=esp_foice, mov='varre', pivo=(10, 30, -6), de=-120, ate=70, bate=.45, inclina=12, larg=180, alt=170,
               alvo=60, u=1.0, n=12, dur=.5),
    'pendulo': P(gen=g_arma, modo='iso', peca=esp_pendulo, mov='balanca', pivo=(0, 0, 165), de=-70, ate=70, bate=.62, apaga=.65, larg=180,
                 alt=200, alvo=90, u=1.0, n=12, dur=.6),
    'maos': P(gen=g_maos, modo='lado', quant=4, comp=90, larg=130, alt=70, u=.7, n=10, dur=.38),
    'palma': P(gen=g_palma, modo='lado', larg=80, alt=80, u=.6, n=10, dur=.4),
    'lobo': P(gen=g_lobo, modo='lado', larg=120, alt=90, alvo=34, u=.7, n=6, laco=True, dur=.5),
    'caveira': P(gen=g_caveira, modo='lado', larg=60, alt=30, u=.4, n=6, laco=True, dur=.36),
    'olho': P(gen=g_olho, modo='lado', larg=90, alt=60, u=.55, n=12, laco=True, dur=1.4),
    'relogio': P(gen=g_relogio, modo='lado', larg=90, alt=90, u=.7, n=14, dur=.8),
    'portal': P(gen=g_portal, modo='lado', larg=92, alt=92, u=.75, n=14, dur=.8),
    'sol': P(gen=g_sol, modo='lado', larg=110, alt=110, u=.8, n=12, laco=True, dur=1.4),
    'lua_cheia': P(gen=g_lua_cheia, modo='lado', larg=72, alt=72, u=.55, n=4, laco=True, dur=.6),
    'lua': P(gen=g_lua, modo='lado', larg=40, alt=40, u=.35, n=4, laco=True, dur=.3),
    'eclipse': P(gen=g_eclipse, modo='lado', larg=100, alt=100, u=.7, n=12, laco=True, dur=1.6),
    'som': P(gen=g_som, modo='lado', comp=100, quant=5, larg=130, alt=80, u=.8, n=10, dur=.4),
    'fragmento': P(gen=g_fragmento, modo='lado', larg=30, alt=14, u=.3, n=1, dur=.2),
    'espelhos': P(gen=g_espelhos, modo='iso', larg=170, alt=140, alvo=34, u=1.0, n=14, dur=.8),
    'onda_som': P(gen=KE.g_onda, modo='iso', raio=60, grossura=.6, larg=140, alt=80, u=.9, n=12, dur=.5, chao=1),
    # natureza, fogo, gelo, terra, água
    'bola_fogo': P(gen=g_bola_fogo, modo='lado', luz=False, larg=70, alt=34, u=.45, n=8, laco=True, dur=.32, brilho=.55, amostras=48),
    'explosao': P(gen=g_explosao, modo='iso', luz=False, raio=60, z=40, fogo=True, dom=(160, 160, 200), base=-6, densidade=7.0, brilho_fogo=15.0,
                  sobe=34, miolo=.15, fofo=2.6, grao=2.6, curva_r=lambda t: 60 * (.35 + .65 * chega(t, 0, .45)), curva_c=lambda t: 1.3 - 1.0 * chega(t, .08, 1.0),
                  curva_d=lambda t: env(t, .04, .45), larg=180, alt=200, alvo=60, u=1.0, n=14, dur=.7, brilho=.45, amostras=36),
    'chamas': P(gen=g_chamas, modo='iso', luz=False, larg=80, alt=160, alvo=55, u=.8, n=12, laco=True, dur=.9, brilho=.5, amostras=48),
    'meteoro': P(gen=g_meteoro, modo='lado', luz=False, larg=130, alt=48, u=.6, n=8, laco=True, dur=.4, brilho=.45, amostras=48),
    'erupcao': P(gen=g_erupcao, modo='iso', luz=False, larg=170, alt=240, alvo=85, u=1.0, n=14, dur=.8, brilho=.45, amostras=48),
    'lanca_gelo': P(gen=g_objeto_simples, obj=obj_lanca_gelo, modo='lado', luz=False, larg=62, alt=20, u=.32, n=1, dur=.2, aro='#9fd8ff'),
    'cristais_gelo': P(gen=KE.g_irrompe, monta=m_cristais, modo='iso', luz=False, raio=34, alto=80, quant=9, sobe=.2, afunda=.3, encolhe=.9,
                       larg=130, alt=140, alvo=34, u=.9, n=14, dur=.7, aro='#9fd8ff'),
    'prisao_gelo': P(gen=KE.g_irrompe, monta=lambda E: m_cristais(dict(E, raio=26, alto=84, quant=11, semente=8)), modo='iso', luz=False,
                     sobe=.5, afunda=0.0, t_fixo=.99, larg=110, alt=140, alvo=40, u=.8, n=1, dur=1.0, aro='#9fd8ff'),
    'nevasca': P(gen=g_nevasca, modo='iso', luz=False, larg=170, alt=150, alvo=40, u=1.0, n=12, laco=True, dur=1.2, amostras=40),
    'rocha': P(gen=g_objeto_simples, obj=obj_rocha, modo='lado', luz=False, larg=28, alt=28, u=.28, n=1, dur=.3),
    'pilar_pedra': P(gen=KE.g_irrompe, monta=m_pilar_pedra, modo='iso', luz=False, sobe=.22, afunda=.25, encolhe=.9, larg=120, alt=160, alvo=45,
                     u=.9, n=12, dur=.7),
    'fenda': P(gen=g_fenda, modo='iso', luz=False, raio=72, larg=190, alt=120, alvo=10, u=1.0, n=12, dur=.7, chao=1, brilho=.3),
    'poeira': P(gen=KE.g_volume, modo='iso', luz=False, raio=46, z=14, dom=(170, 170, 70), base=-4, cor_fumaca='#9a8a70', densidade=3.6, achata=.45,
                sobe=8, larg=170, alt=90, alvo=15, u=1.0, n=12, dur=.6, amostras=36),
    'fumaca': P(gen=KE.g_volume, modo='iso', luz=False, raio=48, z=40, dom=(150, 150, 170), base=-4, cor_fumaca='#7a7874', densidade=4.6, sobe=30,
                larg=160, alt=180, alvo=55, u=1.0, n=14, dur=1.0, amostras=36),
    'veneno': P(gen=KE.g_volume, modo='iso', luz=False, raio=44, z=32, dom=(140, 140, 110), base=-4, cor_fumaca='#7fbf3a', absorve='#2a4a10',
                emis='#9ae04a', forca=.8, densidade=2.6, achata=.7, laco=True, ferve=.7, curva_r=lambda t: 44.0, curva_z=lambda t: 30.0,
                curva_d=lambda t: 1.0, larg=150, alt=120, alvo=35, u=1.0, n=12, dur=1.4, amostras=36),
    'sombra': P(gen=KE.g_volume, modo='iso', luz=False, raio=44, z=36, dom=(130, 130, 140), base=-4, cor_fumaca='#2a1a3a', absorve='#100818',
                emis='#6a3a9a', forca=.6, densidade=5.0, sobe=16, larg=140, alt=150, alvo=40, u=1.0, n=12, dur=.5, amostras=36,
                curva_r=lambda t: 44 * (.3 + .7 * chega(t, 0, .45))),
    'incenso': P(gen=KE.g_volume, modo='iso', luz=False, raio=22, z=60, dom=(70, 70, 170), base=-4, cor_fumaca='#b89ad0', emis='#d8a0f0', forca=.6,
                 densidade=2.0, achata=3.0, laco=True, ferve=.9, grao=3.0, miolo=.1, curva_r=lambda t: 24.0, curva_z=lambda t: 60.0,
                 curva_d=lambda t: 1.0, larg=90, alt=170, alvo=60, u=.9, n=12, dur=1.6, amostras=36),
    # objetos de verdade
    'flecha': P(gen=g_objeto_simples, obj=obj_flecha, modo='lado', luz=False, larg=50, alt=12, u=.3, n=1, dur=.2),
    'virote': P(gen=g_objeto_simples, obj=obj_virote, modo='lado', luz=False, larg=38, alt=12, u=.3, n=1, dur=.2),
    'lanca': P(gen=g_objeto_simples, obj=obj_lanca, modo='lado', luz=False, larg=90, alt=12, u=.4, n=1, dur=.3),
    'adaga': P(gen=g_objeto_simples, obj=obj_adaga, modo='lado', luz=False, larg=30, alt=12, u=.25, n=1, dur=.2),
    'machado': P(gen=g_objeto_simples, obj=obj_machado, modo='lado', luz=False, larg=34, alt=38, u=.3, n=1, dur=.3),
    'bomba': P(gen=g_objeto_simples, obj=obj_bomba, modo='lado', luz=False, larg=28, alt=30, alvo=2, u=.28, n=4, laco=True, dur=.3),
    'bala': P(gen=g_objeto_simples, obj=obj_bala, modo='lado', luz=False, larg=20, alt=20, u=.25, n=1, dur=.2),
    'barril': P(gen=g_objeto_simples, obj=obj_barril, modo='lado', luz=False, larg=30, alt=40, alvo=2, u=.3, n=4, laco=True, dur=.4),
    'bolas': P(gen=g_objeto_simples, obj=obj_bolas, modo='lado', luz=False, larg=36, alt=36, u=.3, n=1, dur=.3),
    'engrenagem': P(gen=g_objeto_simples, obj=obj_engrenagem, modo='lado', luz=False, larg=24, alt=24, u=.25, n=1, dur=.3),
    'corrente_lado': P(gen=g_objeto_simples, obj=obj_corrente, modo='lado', luz=False, comp=100, larg=124, alt=22, u=.45, n=1, dur=.3),
    'chuva_flechas': P(gen=g_chuva_flechas, modo='iso', luz=False, raio=42, quant=14, larg=150, alt=210, alvo=60, u=1.0, n=14, dur=.8),
    'rede': P(gen=g_rede, modo='iso', luz=False, larg=110, alt=150, alvo=50, u=.8, n=12, dur=.5),
    'armadilha': P(gen=g_armadilha, modo='iso', luz=False, larg=80, alt=70, alvo=10, u=.55, n=9, dur=.32),
    'correntes': P(gen=g_correntes, modo='iso', luz=False, raio=28, larg=100, alt=130, alvo=40, u=.75, n=12, laco=True, dur=1.4),
    'grilhoes': P(gen=g_grilhoes, modo='iso', luz=False, larg=54, alt=60, alvo=4, u=.45, n=12, laco=True, dur=1.6),
    'espinhos_ferro': P(gen=KE.g_irrompe, monta=m_espinhos_ferro, modo='iso', luz=False, sobe=.16, afunda=.3, encolhe=.9, larg=150, alt=120,
                        alvo=22, u=.9, n=12, dur=.6),
    'vinhas': P(gen=g_vinhas, modo='iso', luz=False, raio=26, alto=92, quant=6, larg=110, alt=150, alvo=45, u=.85, n=14, dur=.8),
    'reliquia': P(gen=g_reliquia, modo='iso', luz=False, larg=70, alt=80, alvo=22, u=.5, n=12, laco=True, dur=2.0, aro='#ffd27a'),
    'estandarte': P(gen=g_estandarte, modo='iso', luz=False, larg=90, alt=160, alvo=62, u=.8, n=12, laco=True, dur=1.2),
    'falcao': P(gen=g_ave, modo='lado', luz=False, cor='#8a6a48', larg=90, alt=70, alvo=20, u=.6, n=6, laco=True, dur=.45),
    'corvo': P(gen=g_ave, modo='lado', luz=False, cor='#2a2a32', escala=.8, larg=72, alt=56, alvo=16, u=.55, n=6, laco=True, dur=.4),
    'moedas': P(gen=KE.g_particulas, modo='iso', luz=False, tipo='moeda', tam=3.2, quant=18, mov='explode', raio=60, z0=30, gravidade=60,
                espalha=.05, kind='gold', cor='#e0b450', el0=.4, el1=1.3, larg=120, alt=120, alvo=30, u=.8, n=12, dur=.6),
    'engrenagens': P(gen=KE.g_particulas, modo='iso', luz=False, tipo='engrenagem', tam=4.0, quant=12, mov='explode', raio=60, z0=34,
                     gravidade=50, espalha=.05, kind='gold', cor='#c8a050', larg=130, alt=130, alvo=34, u=.85, n=12, dur=.6),
    'sangue': P(gen=KE.g_particulas, modo='iso', luz=False, tipo='gota', tam=2.0, quant=22, mov='explode', raio=50, z0=34, gravidade=70,
                espalha=.04, kind='gloss', cor='#7a0c0c', el0=.1, el1=1.2, larg=110, alt=110, alvo=30, u=.8, n=10, dur=.45),
    'folhas': P(gen=KE.g_particulas, modo='iso', luz=False, tipo='folha', tam=4.0, quant=18, mov='gira_sobe', raio=40, altura=110, voltas=1.3,
                espalha=.3, kind='cloth', cor='#6a9a3a', larg=110, alt=150, alvo=50, u=.85, n=16, dur=1.1),
    'gotas': P(gen=KE.g_particulas, modo='iso', luz=False, tipo='gota', tam=2.2, quant=22, mov='explode', raio=56, z0=30, gravidade=60,
               espalha=.04, kind='glass', cor='#9fe4f4', emis='#bff4ff', forca=.6, el0=.2, el1=1.2, larg=120, alt=120, alvo=30, u=.85, n=10, dur=.5),
    'gotas_cura': P(gen=KE.g_particulas, modo='iso', luz=False, tipo='gota', tam=2.0, quant=16, mov='gira_sobe', raio=34, altura=100, voltas=1.2,
                    espalha=.35, kind='glass', cor='#9fe4f4', emis='#bff4ff', forca=1.0, larg=100, alt=140, alvo=50, u=.8, n=14, dur=1.0),
    'contas': P(gen=KE.g_particulas, modo='iso', luz=False, tipo='conta', tam=2.6, quant=14, mov='orbita', raio=34, z0=36, voltas=1, ondula=4.0,
                laco=True, kind='wood', cor='#a8743a', larg=90, alt=70, alvo=34, u=.6, n=12, dur=1.2),
    'onda_agua': P(gen=g_onda_agua, modo='iso', luz=False, larg=180, alt=160, alvo=40, u=1.0, n=14, dur=.7, aro='#9fe4f4'),
    'redemoinho': P(gen=g_redemoinho, modo='iso', luz=True, tinta=False, raio=50, larg=120, alt=70, u=.8, n=12, laco=True, dur=1.2, chao=1),
    'prisma': P(gen=g_prisma, modo='lado', luz=True, tinta=False, comp=100, raio=5.5, larg=106, alt=34, u=.6, n=6, laco=True, dur=.3),
}
