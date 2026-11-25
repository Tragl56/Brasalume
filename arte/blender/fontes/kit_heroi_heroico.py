# Corpo heroico dos heróis do Brasalume (remodelagem de 2026-11-25: dark fantasy, ~6,5 cabeças de altura).
# Esqueleto novo, em unidades do jogo (pés em z=0, o herói olha para +X):
#   tornozelo 6, joelho 25, quadril 45, cinto 51, peito 65, ombros 73 (y = ±13), pescoço 78, centro da cabeça ~83.
# Pernas, tronco e braços são esculpidos aqui. Cabeças, armas, costas e auras continuam vindo do kit_heroi:
#   - a cabeça antiga é montada dentro de uma parte com escala ESC_CAB, presa no pescoço novo;
#   - os enfeites do tronco, as costas e as auras são remapeados na vertical por deformar() (pernas mais longas, mesmo tronco).
import math
import bpy
from mathutils import Vector, Matrix
from kit_base import (mat, shade, mix, sph, cyl, caps, box, torus, tubo, poly, casca, raiz, luz_ponto, V, U, parte)
import kit_heroi as KH
from kit_heroi import (SKIN, METAL, grupo, tm, _goldish, AIM, CABECAS, H_hood, arma, braco_anim, lanterna, costas, aura, companheiro)

# ---------- esqueleto ----------
TORN, JOELHO, QUADRIL, CINTO, PEITO, OMBRO_Z, PESCOCO = 6, 25, 45, 51, 65, 73, 78
OMBRO_Y = 13.2
ESC_CAB = .6                    # a cabeça antiga (raio 12) fica com raio ~7
PIVO_CAB_ANTIGO = (0, 0, 64)     # onde a cabeça antiga gira (pescoço no desenho antigo)
PIVO_CAB = (0, 0, 77.6)
OMBROS = {-1: (0, -OMBRO_Y, OMBRO_Z), 1: (0, OMBRO_Y, OMBRO_Z)}
LARG = 1.08                      # o tronco antigo fica 8% mais largo (ombros heroicos)


def Z(z):
    """Altura antiga (corpo de boneco, ~85 de altura) -> altura nova. Abaixo do cinto antigo (36,5) as pernas esticam;
    do cinto ao pescoço o tronco só sobe; acima do pescoço tudo encolhe com a cabeça."""
    if z <= 36.5:
        return z * CINTO / 36.5
    if z <= 64:
        return CINTO + (z - 36.5) * (PIVO_CAB[2] - CINTO) / (64 - 36.5)
    return PIVO_CAB[2] + (z - 64) * ESC_CAB


def _f(w):
    return Vector((w.x, w.y * LARG, Z(w.z / U) * U))


def deformar(objs):
    """Leva peças montadas nas medidas antigas para o corpo novo (vértice a vértice, no espaço da raiz)."""
    bpy.context.view_layer.update()
    for o in objs:
        M = o.matrix_world.copy()
        Mi = M.inverted()
        if o.type == 'MESH':
            for v in o.data.vertices:
                v.co = Mi @ _f(M @ v.co)
        elif o.type == 'CURVE':
            for sp in o.data.splines:
                for bp in sp.bezier_points:
                    bp.co = Mi @ _f(M @ bp.co)
                    bp.handle_left = Mi @ _f(M @ bp.handle_left)
                    bp.handle_right = Mi @ _f(M @ bp.handle_right)
        elif o.type == 'LIGHT':
            t = M.translation
            o.matrix_world = Matrix.Translation(_f(t) - t) @ M


class novos:
    """Guarda os objetos criados dentro do bloco (para deformar só esses)."""
    def __enter__(self):
        self.antes = set(bpy.data.objects)
        self.objs = []
        return self

    def __exit__(self, *a):
        self.objs[:] = [o for o in bpy.data.objects if o not in self.antes]
        return False


# ---------- materiais do corpo ----------
def _principal(L, B):
    mt = L.get('mt', METAL)
    if B.get('armor'):
        return mat('metal', mt if L.get('tabard') else L['c1'])
    if B.get('apron') or L.get('body') == 'leather':
        return mat('leather', L['c1'])
    return mat('cloth', L['c1'])


def manga(L, B):
    if B.get('bare'):
        return mat('skin', L.get('sk', SKIN))
    if B.get('armor'):
        return mat('metal', L.get('mt', METAL))
    return mat('cloth' if L.get('body') != 'leather' else 'leather', L['c1'])


# ---------- pernas ----------
def pernas(L, B, R):
    mt = L.get('mt', METAL)
    armor = B.get('armor')
    if armor:
        calca, bota = mat('metal', shade(mt, -.25)), mat('metal', shade(mt, -.45))
    elif B.get('bare'):
        calca, bota = mat('cloth', shade(L['c2'], -.1)), mat('leather', '#2a1e16')
    else:
        calca, bota = mat('cloth', '#2c241e'), mat('leather', '#221912')
    couro = mat('leather', '#3a2a1c')
    for s in (-1, 1):
        y = s * 4.9
        with parte(R, 'perna', (0, y, QUADRIL), fase=.5 if s > 0 else 0, amp=.28):
            # coxa (larga em cima, afina no joelho) e panturrilha
            cyl((0, y, QUADRIL), (.9, y * 1.02, JOELHO + 1), 4.5, 3.3, calca, parent=R)
            sph((.3, y, QUADRIL - 3), 4.6, calca, scale=(1, .95, 1.3), parent=R)
            sph((.9, y * 1.02, JOELHO), 3.4, calca, parent=R)
            cyl((.9, y * 1.02, JOELHO), (0, y * 1.02, TORN + 4), 3.2, 2.5, calca, parent=R)
            sph((-.6, y * 1.02, 18.5), 3.2, calca, scale=(1, .9, 1.7), parent=R)   # panturrilha
            # bota: cano alto com dobra, pé alongado com bico
            cyl((.2, y * 1.02, 2.5), (.3, y * 1.02, 17), 3.5, 3.4, bota, parent=R)
            torus((.3, y * 1.02, 17), 3.5, .9, bota if armor else mat('leather', '#3a2818'), parent=R)
            box((2.8, y * 1.03, 2.2), (11, 5.2, 4.4), bota, bevel=1.8, parent=R)
            sph((7.8, y * 1.03, 2.2), 2.6, bota, scale=(1.3, 1, .85), parent=R)
            box((.3, y * 1.03, .5), (12, 5.6, 1.2), mat('leather', '#140f0b'), bevel=.4, parent=R)   # sola
            if armor:
                # grevas, joelheira com aba e escarpe em lâminas
                sph((1.6, y * 1.02, 15), 3.6, mat('metal', shade(mt, -.15)), scale=(.75, 1, 2.4), parent=R)
                sph((2.2, y * 1.02, JOELHO), 3.6, mat('metal', mt), scale=(.9, 1.05, 1), parent=R)
                sph((3.6, y * 1.02, JOELHO), 2.1, mat('metal', shade(mt, .15)), scale=(.5, 1.5, 1.4), parent=R)
                for k in range(3):   # escarpe: lâminas sobrepostas em cima do pé
                    box((3.2 + k * 1.8, y * 1.03, 4.5 - k * .55), (3.6, 5.5, 1.3), mat('metal', shade(mt, -.2 + k * .07)), rot=(0, -.22, 0), bevel=.45, parent=R)
                sph((.4, y * 1.02, 38), 4.4, mat('metal', shade(mt, -.1)), scale=(.9, .95, 1.6), parent=R)   # coxote
            else:
                # correias da bota e joelheira de couro
                for z in (7, 12):
                    torus((.3, y * 1.02, z), 3.55, .45, couro, parent=R)
                    box((3.6, y * 1.02, z), (.8, 1.4, 1.2), mat('metal', '#8a7a5a'), bevel=.2, parent=R)
                sph((2.4, y * 1.02, JOELHO), 2.6, couro, scale=(.7, 1.1, 1.1), parent=R)


# ---------- tronco ----------
def _anatomia(R, m, costas_m=None):
    """Tronco em V: quadril, abdômen, peito largo, dorsais e trapézio."""
    costas_m = costas_m or m
    sph((0, 0, QUADRIL + 2.5), 8.6, m, scale=(.8, 1.16, .62), parent=R)
    sph((.3, 0, 55.5), 8.2, m, scale=(.82, 1.26, 1.0), parent=R)
    sph((-1.6, 0, 63), 9, costas_m, scale=(.72, 1.42, 1.0), parent=R)
    sph((.9, 0, PEITO + .5), 10, m, scale=(.8, 1.36, .9), parent=R)
    sph((-1, 0, OMBRO_Z), 7, costas_m, scale=(.78, 1.6, .5), parent=R)


def _frente(y, z):
    """Onde fica a frente do tronco (x) numa altura e lateral: a maior entre o peito e a barriga de _anatomia."""
    melhor = 0.0
    for (cx, cz, r, sx, sy, sz) in ((.9, PEITO + .5, 10, .8, 1.36, .9), (.3, 55.5, 8.2, .82, 1.26, 1.0), (0, QUADRIL + 2.5, 8.6, .8, 1.16, .62)):
        q = 1 - (y / (r * sy)) ** 2 - ((z - cz) / (r * sz)) ** 2
        if q > 0:
            melhor = max(melhor, cx + r * sx * math.sqrt(q))
    return melhor


def _pescoco(L, R):
    sk = L.get('sk', SKIN)
    cyl((-.5, 0, 71), (-.2, 0, 80), 3.9, 3.3, mat('skin', sk), parent=R)


def _saia(L, B, R, m, hem_novo, fl):
    """Saia/aba da roupa, do cinto até a barra, com dobras; em 'split' a frente fica aberta."""
    if hem_novo >= CINTO - 3:
        return
    dobras = .7 + max(0, fl - 13) * .1
    if B.get('split'):
        for a0, a1 in ((math.radians(22), math.radians(180)), (math.radians(-180), math.radians(-22))):
            casca(CINTO + 1, hem_novo, 10.6, fl * 1.02, a0, a1, m, xs=.8, esp=1.4, segs=24, rings=10, dobras=dobras, parent=R)
    elif hem_novo > 18:
        # saia curta em quatro abas (frente, trás e lados) com frestas: as pernas aparecem e a silhueta ganha recortes
        for k in range(4):
            a = k * math.pi / 2
            casca(CINTO + 1, hem_novo - (2 if k % 2 == 0 else 0), 10.6, fl * 1.06, a - .68, a + .68, m, xs=.8, esp=1.4, segs=12, rings=8,
                  dobras=dobras * .6, parent=R)
    else:
        longa = hem_novo < 15   # túnicas e mantos até o chão abrem mais na barra
        casca(CINTO + 1, hem_novo, 10.6, fl * (1.2 if longa else 1.02), 0, math.tau, m, xs=.8, esp=1.4, segs=40, rings=12,
              dobras=dobras * (1.6 if longa else 1),
              rasgos=5 if (B.get('tat') or L.get('tat')) else 0, parent=R)


def _placas(L, B, R):
    """Armadura de placas: peitoral com quilha, placa da barriga, faldas, escarcelas, gorjal e rebites."""
    mt = L.get('mt', METAL)
    peito = mat('metal', mt)
    esc = mat('metal', shade(mt, -.25))
    ouro = mat('gold', L['tr']) if _goldish(L['tr']) else mat('metal', shade(mt, .2))
    sph((1.6, 0, PEITO), 10.6, peito, scale=(.82, 1.36, .94), parent=R)
    box((9.4, 0, 63.5), (1.6, 1.4, 16), mat('metal', shade(mt, .12)), rot=(0, .12, 0), bevel=.6, parent=R)   # quilha
    sph((2.4, 0, 55.5), 8.8, peito, scale=(.84, 1.28, .62), parent=R)
    # gola do peitoral (debrum)
    torus((1.6, 0, 70.5), 9.4, .8, ouro, scale=(.8, 1.3, .5), rot=(0, .25, 0), parent=R)
    # faldas: lâminas sobrepostas que abrem para baixo
    for k, z in enumerate((50.5, 47.8, 45.1)):
        b = cyl((0, 0, z + 1.4), (0, 0, z - 1.6), 10.8 + k * .7, 11.6 + k * .7, mat('metal', shade(mt, -.05 - k * .07)), verts=32, parent=R)
        b.scale = (.8, 1, 1)
    # escarcelas sobre as coxas
    for s in (-1, 1):
        g = grupo((4.2, s * 6.2, 39.5), rot=(s * .12, -.18, 0), parent=R)
        for k in range(3):
            box((0, 0, -k * 3.2), (1.6, 8.4 - k * .4, 4.4), mat('metal', shade(mt, -.08 - k * .06)), bevel=.6, parent=g)
        box((.9, 0, 1.8), (.4, 8, .8), ouro, bevel=.15, parent=g)
    # gorjal
    for k in range(3):
        cyl((0, 0, 72.5 + k * 1.6), (0, 0, 74 + k * 1.6), 7.6 - k * 1.1, 7 - k * 1.1, mat('metal', shade(mt, -.1 * k)), verts=28, parent=R)
    # rebites no peitoral
    reb = mat('metal', shade(mt, .35))
    for s in (-1, 1):
        for z in (58, 62, 66):
            sph((8.4 - abs(z - 62) * .1, s * 9.8, z), .55, reb, parent=R)


def _ombreiras(L, B, R):
    """Ombreiras grandes em lâminas: dão a silhueta dos guerreiros."""
    r = B['pld']
    mt = L.get('mt', METAL)
    ouro = mat('gold', L['tr']) if _goldish(L['tr']) else mat('metal', shade(mt, -.3))
    lados = [-1] if B.get('oneP') else [-1, 1]
    for s in lados:
        with parte(R, 'fixo', OMBROS[s], amp=0):   # acompanha o ombro sem balançar
            y = s * (OMBRO_Y + 1.2)
            sph((0, y, OMBRO_Z + 1.6), r * 1.05, mat('metal', mt), scale=(1.12, 1, .78), parent=R)
            torus((0, y, OMBRO_Z - .5), r * 1.0, .75, ouro, scale=(1.12, 1, .45), parent=R)
            for k in range(2):
                sph((0, s * (OMBRO_Y + 2 + k * .8), OMBRO_Z - 3 - k * 2.8), r * (.92 - k * .1), mat('metal', shade(mt, -.12 - k * .08)),
                    scale=(1.15, .95, .42), parent=R)
            if L.get('spikes'):
                for k in range(3):
                    a = (k - 1) * .55
                    cyl((math.sin(a) * r * .5, y, OMBRO_Z + 5), (math.sin(a) * r * 1.0, s * (OMBRO_Y + 3), OMBRO_Z + 13), 1.6, .1, mat('metal', shade(mt, .3)), parent=R)


def tronco(L, B, R):
    w, fl, hem = B['w'], B['fl'], -B['hem']
    sk = L.get('sk', SKIN)
    armor, bare = B.get('armor'), B.get('bare')
    principal = _principal(L, B)
    pele = mat('skin', sk)
    hem_novo = Z(hem)
    _pescoco(L, R)
    if bare:
        _anatomia(R, pele)
        # peitorais e abdômen marcados
        for s in (-1, 1):
            sph((6.4, s * 5.4, 65.5), 5.4, pele, scale=(.55, 1, .78), parent=R)
            for k, z in enumerate((58.5, 55, 51.5)):
                sph((6.6 - k * .2, s * 2.2, z), 2.2, mat('skin', shade(sk, -.04)), scale=(.45, 1, .75), parent=R)
        saia_m = mat('fur' if L.get('body') == 'fur' else 'cloth', L['c1'])
        _saia(L, B, R, saia_m, hem_novo, fl)
    elif armor:
        _anatomia(R, mat('cloth', shade(L['c1'], -.3)))   # gibão por baixo
        malha = mat('metal', shade(L.get('mt', METAL), -.35), rough=.65)
        _saia(L, B, R, malha, hem_novo, fl)   # cota de malha
        _placas(L, B, R)
    else:
        _anatomia(R, principal)
        _saia(L, B, R, principal, hem_novo, fl)
        # gola, abertura da frente com cordões e costura dos ombros
        torus((0, 0, 75), 5.6, 1.3, mat('cloth', shade(L['c1'], -.2)) if L.get('body') != 'leather' else principal, scale=(.9, 1.1, .7), parent=R)
        box((8.6, 0, 66), (.8, 1.6, 12), mat('cloth', shade(L['c1'], -.4)), rot=(0, .2, 0), bevel=.3, parent=R)
        cordao = mat('leather', '#2a1c12')
        for z in (63, 66, 69):
            box((9.1 - (z - 63) * .2, 0, z), (.5, 3.6, .5), cordao, rot=(.5, 0, 0), bevel=.15, parent=R)
            box((9.1 - (z - 63) * .2, 0, z), (.5, 3.6, .5), cordao, rot=(-.5, 0, 0), bevel=.15, parent=R)
        if L.get('body') == 'leather' or B.get('strap'):
            # placas de couro costuradas no peito
            for s in (-1, 1):
                sph((5.6, s * 6, 64), 5.6, mat('leather', shade(L['c1'], -.12)), scale=(.5, 1, .9), parent=R)
    if B.get('pld'):
        _ombreiras(L, B, R)
    # correia diagonal colada ao peito (talabarte): grossa e com fivelas quando o corpo pede 'strap'
    if B.get('strap') or not (bare or L.get('tabard') or armor):
        grossa = bool(B.get('strap'))
        pts = []
        for k in range(7):
            u = k / 6
            y, z = 11 - 21 * u, 73 - 23 * u
            pts.append((_frente(y, z) + .6, y, z))
        tubo(pts, 1.5 if grossa else .9, mat('leather', '#4a3020' if grossa else '#3a2618'), parent=R)
        if grossa:
            for k in (2, 4):
                sph((pts[k][0] + 1, pts[k][1], pts[k][2]), .8, mat('metal', '#b8b0a0'), parent=R)
    # enfeites antigos (cinto, bolsas, faixas, colar, contas, penas, correntes, rachaduras, manto...) remapeados
    with novos() as n:
        extras(L, B, R)
    deformar(n.objs)


def extras(L, B, R):
    """Os enfeites do tronco do kit antigo, nas medidas antigas (deformar() leva para o corpo novo)."""
    w, fl, hem = B['w'], B['fl'], -B['hem']
    mt = L.get('mt', METAL)
    bare = B.get('bare')
    if not (B.get('tat') or L.get('tat')):
        b = cyl((0, 0, hem), (0, 0, hem + 2.4), fl + .5, fl + .1, tm(L), parent=R)
        b.scale = (.78, 1 / LARG, 1)
    zc = 36.5
    rc = 10.4 / LARG
    if B.get('belt') or B.get('kilt'):
        torus((0, 0, zc), rc + .6, 1.5, mat('leather', '#2b2118'), scale=(.8, 1, 1), parent=R)
        box((rc * .8 + 1.2, 0, zc), (1.4, 4.4, 4.8), mat('gold', L['tr'] if _goldish(L['tr']) else '#c9a54a'), bevel=.4, parent=R)
        box((rc * .8 + 1.8, 0, zc), (.6, 2.2, 2.6), mat('metal', '#2a2420'), bevel=.2, parent=R)
    if B.get('sash'):
        torus((0, 0, zc + 1.5), rc + .8, 1.7, tm(L), scale=(.8, 1, 1), parent=R)
        box((rc * .8 + 1.2, -3, zc - 6), (1, 3, 12), tm(L), rot=(.15, 0, 0), bevel=.4, parent=R)
        box((w * .76 + .2, 0, (58 + hem) / 2), (1, 2.6, 58 - hem), tm(L), bevel=.3, parent=R)
    if not bare:
        box((rc * .5, -rc * .9, zc - 4), (4.4, 2.6, 5.4), mat('leather', '#4a3222'), rot=(0, 0, -.5), bevel=.9, parent=R)
    if L.get('tabard'):
        box((w * .8 + .8, 0, (60 + hem) / 2 - 2), (1.2, 10, 60 - hem + 8), mat('cloth', L['c1']), bevel=.4, parent=R)
        sph((w * .8 + 1.7, 0, 47), 2.6, mat('gold', L['tr']), scale=(.4, 1, 1), parent=R)
    if B.get('apron'):
        box((w * .78 + .8, 0, (52 + hem) / 2), (1.2, 11, 52 - hem), mat('leather', shade(L['c1'], .3)), bevel=.5, parent=R)
    if B.get('collar'):
        torus((0, 0, 60.5), 10.5, 4.2, mat('fur', shade(L['c1'], .14)), scale=(.8, 1, .8), parent=R)
    if L.get('beads'):
        conta = mat('wood', '#6a4a2a')
        for i in range(11):
            a = -1.1 + i / 10 * 2.2
            sph((w * .7 + 1.2 - abs(a) * 2, math.sin(a) * 8, 52 - math.cos(a) * 7), 1.3, conta, parent=R)
        sph((w * .7 + 1.8, 0, 44), 2, mat('gold', L['tr']), parent=R)
    if L.get('feathers'):
        pena = mat('cloth', shade(L['c2'], -.2))
        for row in range(5):
            for i in range(8):
                a = math.pi * .55 + i / 7 * math.pi * .9
                rr = w + (fl - w) * (row / 5)
                sph((math.cos(a) * rr * .78, math.sin(a) * rr, 56 - row * 8), 2.6, pena, scale=(.5, 1, 1.5), parent=R)
    if L.get('chainsBody'):
        elo = mat('metal', shade(mt, -.1))
        for i in range(8):
            u = i / 7
            torus((w * .8 + 1.4, 9 - u * 18, 58 - u * 22), 1.5, .45, elo, rot=(0, math.pi / 2, .9 if i % 2 else 0), parent=R)
    if L.get('cracks'):
        brasa = mat('emit', L['fx'], strength=9)
        for pts in ([(w * .8 + .9, -4, 54), (w * .8 + 1, -1, 49), (w * .8 + .9, -5, 43)], [(w * .8 + .9, 5, 52), (w * .8 + 1, 3, 46), (w * .8 + .9, 7, 40)]):
            tubo(pts, .45, brasa, parent=R)
        luz_ponto((w + 4, 0, 48), 18, L['fx'], parent=R)
    if B.get('drape'):
        pano = mat('cloth', L['c1'])
        cyl((w * .74 + .2, -10, 60), (w * .74 + .9, 10, 33), 2.6, 3.4, pano, parent=R)
        cyl((-w * .74 - .2, -10, 60), (-w * .74 - .9, 10, 33), 2.6, 3.4, pano, parent=R)
    if L.get('pouches'):
        bolsa = mat('leather', '#5a3a22')
        for y in (-7, -1):
            box((rc * .8 + 1.6, y, zc - 3.5), (3, 4.4, 5), bolsa, bevel=.8, parent=R)
        box((w * .78 + 1.4, 6, 47), (.4, 5, 6), mat('paper', '#e8dcc0'), bevel=.1, parent=R)
    if L.get('vials'):
        for y, col in ((-6, '#9ae04a'), (-2, '#b06ad0'), (2, '#9ae04a')):
            cyl((rc * .8 + 1.4, y, zc - 6), (rc * .8 + 1.4, y, zc - 1), 1.3, 1.1, mat('glass', col), parent=R)
            sph((rc * .8 + 1.4, y, zc - 6), 1.4, mat('emit', col, strength=1.5), parent=R)
    if B.get('mantle'):
        casca(61, 12, 12.5, 18, math.radians(105), math.radians(255), mat('cloth', L['c2']), xs=.95, dobras=1.2, parent=R)


# ---------- braços ----------
def bracos(L, B, R):
    """Braço da arma (-Y) e o outro (+Y): bíceps, antebraço, braçadeira e mão fechada. Devolve as mãos."""
    m = manga(L, B)
    armor, bare = B.get('armor'), B.get('bare')
    mt = L.get('mt', METAL)
    luva = mat('metal', shade(mt, -.2)) if armor else mat('leather', '#3a2a1c') if not bare else mat('skin', L.get('sk', SKIN))
    if L['wpn'] in AIM:
        md, cot = (19, -9, 66), (9, -13.5, 68)
    else:
        md, cot = (5, -19.5, 47), (.5, -17.5, 60)
    me, cote = (4, 16.5, 47), (-1.5, 16.5, 60)
    brac = mat('metal', shade(mt, -.15)) if armor else mat('leather', '#3a2a1c')
    for lado, (ombro, cotov, mao) in ((-1, (OMBROS[-1], cot, md)), (1, (OMBROS[1], cote, me))):
        with parte(R, 'braco', ombro, **braco_anim(L, lado)):
            o = Vector(ombro)
            c, h = Vector(cotov), Vector(mao)
            caps(tuple(o), tuple(c), 3.2, m, r2=2.5, parent=R)                                    # braço
            sph(tuple(o + (c - o) * .42 + Vector((.7, 0, 0))), 2.9, m, scale=(1.05, .9, 1.6), parent=R)   # bíceps
            caps(tuple(c), tuple(h), 2.6, m, r2=2.0, parent=R)                                    # antebraço
            p, q = c + (h - c) * .45, c + (h - c) * .9
            cyl(tuple(p), tuple(q), 2.7, 3.2, brac, parent=R)                                    # braçadeira que abre no punho
            if armor:
                sph(tuple(c), 3.6, mat('metal', mt), parent=R)                                    # cotoveleira
                sph(tuple(c + Vector((-1.6, 0, 0))), 2.2, mat('metal', shade(mt, .15)), scale=(.5, 1.2, 1.2), parent=R)
            else:
                for t in (.55, .75):
                    torus(tuple(c + (h - c) * t), 3.25, .35, mat('leather', '#22180f'), rot=(0, math.pi / 2 * 0, 0), parent=R)
            sph(tuple(h), 2.7, luva, scale=(1.15, 1, 1.05), parent=R)                            # mão fechada
            sph(tuple(h + Vector((1.6, 0, .8))), 1.5, luva, scale=(1, 1.5, .8), parent=R)        # dedos
    return md, me


def mao_apoio(L, mao, R):
    """Escudos nas posições novas; o resto vem do kit antigo, que já trabalha a partir da mão."""
    off = L.get('off')
    if off == 'tower':
        sc = L.get('shield', L['c1'])
        g = grupo((mao[0] + 7, mao[1] - 2, mao[2] + 6), rot=(0, 0, .35), parent=R)
        box((0, 0, 0), (2.6, 21, 52), mat('metal', sc), bevel=1.4, parent=g)
        box((.9, 0, 0), (1.2, 22, 53), mat('metal', shade(L.get('mt', METAL), -.2)), bevel=.8, parent=g)   # aro
        box((1.8, 0, 0), (.6, 2.8, 46), mat('gold', L['tr']), bevel=.2, parent=g)
        box((1.8, 0, 8), (.6, 16, 2.8), mat('gold', L['tr']), bevel=.2, parent=g)
        sph((2, 0, 8), 2.4, mat('gold', L['tr']), scale=(.4, 1, 1), parent=g)
    elif off == 'round':
        g = grupo((mao[0] + 5, mao[1] - 1, mao[2] + 4), rot=(0, math.pi / 2, .5), parent=R)
        cyl((0, 0, -1), (0, 0, 1.6), 13, 12, mat('metal', L.get('mt', METAL)), parent=g)
        torus((0, 0, 1.4), 12, 1, mat('gold', L['tr']), parent=g)
        sph((0, 0, 2), 4.4, mat('bone', '#f0ead8'), scale=(1.2, .8, .4), parent=g)
        sph((0, 0, 2.8), 2, mat('emit', L['fx'], strength=12), parent=g)
        luz_ponto((0, 0, 5), 10, L['fx'], parent=g)
    else:
        KH.mao_apoio(L, mao, R)


def construir(L, B, mapa=False):
    """Monta o herói heroico completo e devolve a raiz (girar a raiz em Z muda a vista)."""
    R = raiz('heroi')
    with novos() as n:
        costas(L, R)
    deformar(n.objs)
    pernas(L, B, R)
    tronco(L, B, R)
    md, me = bracos(L, B, R)
    with parte(R, 'cabeca', PIVO_CAB_ANTIGO, amp=.04, fase=.25, atk=.12) as cab:
        CABECAS.get(L.get('head', 'hood'), H_hood)(L, R)
    cab.location = V(PIVO_CAB)
    cab.scale = (ESC_CAB,) * 3
    if not L.get('semLanterna'):
        lanterna(R, (-7, -17.5, 40) if mapa else (-2, 16, 40))
    with parte(R, 'braco', OMBROS[-1], **braco_anim(L, -1)):
        arma(L, md, R)
    with parte(R, 'braco', OMBROS[1], **braco_anim(L, 1)):
        mao_apoio(L, me, R)
    if not mapa:
        with novos() as n:
            aura(L, R)
            if L.get('pet') != 'wolf':
                companheiro(L, R)
        deformar(n.objs)
        if L.get('pet') == 'wolf':
            companheiro(L, R)
    return R
