# Construtor de heróis do Brasalume no Blender. Lê a mesma descrição visual que o jogo usa (tabela LOOK) e monta a figura em 3D.
# Proporções do Canvas: pés em z=0, quadril 22, cinto 36, ombros 60, centro da cabeça 73 (raio 12). O herói olha para +X.
import math
from kit_base import (mat, shade, mix, sph, cyl, caps, box, torus, tubo, poly, casca, capuz, cupula, raiz, luz_ponto, V, U, _link, parte)
import bpy

SKIN, METAL = '#e2c7a1', '#a9b1b6'


def grupo(loc=(0, 0, 0), rot=(0, 0, 0), parent=None, nome='grupo'):
    o = bpy.data.objects.new(nome, None)
    bpy.context.collection.objects.link(o)
    o.location = V(loc)
    o.rotation_euler = rot
    return _link(o, parent)   # dentro de uma parte animável, o grupo acompanha a parte


def _goldish(h):
    from kit_base import hex_rgb
    r, g, b = hex_rgb(h)
    return r > .55 and g > .45 and b < .62 and r >= b + .12


def tm(L, metalico=False):
    """Material do detalhe (tr): dourado/latão quando a cor puxa para o ouro, senão tecido."""
    return mat('gold', L['tr']) if (metalico or _goldish(L['tr'])) else mat('cloth', L['tr'])


# ---------------- corpo ----------------
def pernas(L, B, R):
    mt = L.get('mt', METAL)
    if B.get('armor'):
        calca, bota = mat('metal', shade(mt, -.3)), mat('metal', shade(mt, -.5))
    elif B.get('bare'):
        calca, bota = mat('cloth', shade(L['c2'], -.1)), mat('leather', '#221a14')
    else:
        calca, bota = mat('cloth', '#2a221c'), mat('leather', '#1c1612')
    for y in (-5, 5):
        with parte(R, 'perna', (0, y, 21), fase=.5 if y > 0 else 0, amp=.32):   # passada dos cavaleiros (os heróis ficam parados)
            caps((0, y, 21), (.6, y * 1.04, 5), 3.4, calca, parent=R)
            box((2, y * 1.05, 2.3), (9.5, 5.4, 4.6), bota, bevel=1.6, parent=R)
            cyl((.5, y * 1.04, 6), (.5, y * 1.04, 10), 3.9, 3.7, bota, parent=R)          # cano da bota
            torus((.5, y * 1.04, 10), 3.8, .6, bota, parent=R)


def tronco(L, B, R):
    # no Canvas a altura cresce para baixo (hem = -22 quer dizer 22 unidades acima do chão)
    w, fl, hem = B['w'], B['fl'], -B['hem']
    mt = L.get('mt', METAL)
    sk = L.get('sk', SKIN)
    armor, bare = B.get('armor'), B.get('bare')
    if armor:
        principal = mat('metal', mt if L.get('tabard') else L['c1'])
    elif B.get('apron') or 'leather' in L.get('body', '') or L.get('body') == 'leather':
        principal = mat('leather', L['c1'])
    else:
        principal = mat('cloth', L['c1'])
    pele = mat('skin', sk)
    # peito e ombros: elipse que dá volume aos ombros
    sph((0, 0, 56), 12.5, pele if bare else principal, scale=(.72, 1, .62), parent=R)
    if bare:
        t = cyl((0, 0, 30), (0, 0, 58), 10.8, 12.2, pele, parent=R)
        t.scale = (.74, 1, 1)
        box((7.6, 0, 48), (1.2, 12, 1.2), mat('skin', shade(sk, -.12)), bevel=.5, parent=R)   # linha do peito
        saia = cyl((0, 0, 33), (0, 0, hem), 11.6, fl, mat('fur' if L.get('body') == 'fur' else 'cloth', L['c1']), parent=R)
        saia.scale = (.78, 1, 1)
    else:
        # roupa como casca fechada, com dobras que crescem para a barra
        casca(61, hem, w, fl, 0, math.tau, principal, xs=.76, esp=1.6, segs=40, rings=12, dobras=.55 + (fl - w) * .08, parent=R)
        t = cyl((0, 0, 60), (0, 0, hem + 1), w - 1.4, fl - 1.6, mat('cloth', shade(L['c1'], -.45)), parent=R)   # forro escuro por dentro
        t.scale = (.74, 1, 1)
    # barra (não nas roupas rasgadas)
    if not (B.get('tat') or L.get('tat')):
        b = cyl((0, 0, hem), (0, 0, hem + 3.2), fl + .5, fl - .1, tm(L), parent=R)
        b.scale = (.77, 1, 1)
    else:
        trapo = mat('cloth', shade(L['c1'], -.15))
        for i in range(12):
            a = i / 12 * math.tau
            box((math.cos(a) * fl * .74, math.sin(a) * fl, hem - 2.5), (3.6, 3.6, 6 + (i % 3) * 2), trapo, rot=(0, 0, a), bevel=.4, parent=R)
    zc = 36.5
    rc = w + (fl - w) * (60 - zc) / max(1, (60 - hem))
    if B.get('belt') or B.get('kilt'):
        torus((0, 0, zc), rc + .6, 1.4, mat('leather', '#2b2118'), scale=(.77, 1, 1), parent=R)
        box((rc * .77 + 1, 0, zc), (1.4, 4, 4.6), mat('gold', L['tr'] if _goldish(L['tr']) else '#c9a54a'), bevel=.4, parent=R)
    if B.get('sash'):
        torus((0, 0, zc + 1.5), rc + .7, 1.6, tm(L), scale=(.77, 1, 1), parent=R)
        box((rc * .77 + 1.2, -3, zc - 6), (1, 3, 12), tm(L), rot=(.15, 0, 0), bevel=.4, parent=R)
        # abertura do manto na frente, com debrum
        box((w * .76 + .2, 0, (58 + hem) / 2), (1, 2.6, 58 - hem), tm(L), bevel=.3, parent=R)
    if not bare:
        # bolsa e alça de couro, comuns a todos
        box((rc * .5, -rc * .82, zc - 4), (4.4, 2.6, 5.4), mat('leather', '#4a3222'), rot=(0, 0, -.5), bevel=.9, parent=R)
        if not B.get('strap') and not L.get('tabard'):
            cyl((w * .7 + .8, 9.5, 59), (w * .72 + 1, -8, 37), .9, .9, mat('leather', '#3a2618'), parent=R)
    if L.get('tabard'):
        box((w * .76 + .4, 0, (60 + hem) / 2 - 2), (1.2, 11, 60 - hem + 8), mat('cloth', L['c1']), bevel=.4, parent=R)
        sph((w * .76 + 1.3, 0, 46), 2.6, mat('gold', L['tr']), scale=(.4, 1, 1), parent=R)
    if B.get('apron'):
        box((w * .76 + .6, 0, (52 + hem) / 2), (1.2, 12, 52 - hem), mat('leather', shade(L['c1'], .3)), bevel=.5, parent=R)
    if B.get('collar'):
        pelo = mat('fur', shade(L['c1'], .14))
        torus((0, 0, 60), 10.5, 4.2, pelo, scale=(.8, 1, .8), parent=R)
    if B.get('strap'):
        cyl((w * .74 + .6, -9, 59), (w * .74 + .9, 9, 34), 1.4, 1.4, mat('leather', '#4a3020'), parent=R)
    if B.get('pld'):
        r = B['pld']
        pm = mat('metal', mt)
        lados = [-1] if B.get('oneP') else [-1, 1]
        for sgn in lados:
            sph((0, sgn * (w - .5), 57.5), r, pm, scale=(1.05, 1, .8), parent=R)
            torus((0, sgn * (w - .5), 55.4), r * .92, .7, mat('gold', L['tr']) if _goldish(L['tr']) else mat('metal', shade(mt, -.3)), scale=(1.05, 1, .5), parent=R)
            if L.get('spikes'):
                for k in range(3):
                    a = (k - 1) * .55
                    cyl((math.sin(a) * r * .5, sgn * (w - .5), 61), (math.sin(a) * r * 1.0, sgn * (w + 2), 68), 1.4, .1, mat('metal', shade(mt, .3)), parent=R)
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
                z = 56 - row * 8
                sph((math.cos(a) * rr * .78, math.sin(a) * rr, z), 2.6, pena, scale=(.5, 1, 1.5), parent=R)
    if L.get('chainsBody'):
        elo = mat('metal', shade(mt, -.1))
        for i in range(8):
            u = i / 7
            torus((w * .76 + .8, 9 - u * 18, 58 - u * 22), 1.5, .45, elo, rot=(0, math.pi / 2, .9 if i % 2 else 0), parent=R)
    if L.get('cracks'):
        brasa = mat('emit', L['fx'], strength=9)
        for pts in ([(w * .76 + .5, -4, 54), (w * .76 + .6, -1, 49), (w * .76 + .5, -5, 43)], [(w * .76 + .5, 5, 52), (w * .76 + .6, 3, 46), (w * .76 + .5, 7, 40)]):
            tubo(pts, .45, brasa, parent=R)
        luz_ponto((w + 4, 0, 48), 18, L['fx'], parent=R)
    if B.get('drape'):
        pano = mat('cloth', L['c1'])
        cyl((w * .74 + .2, -10, 60), (w * .74 + .9, 10, 33), 2.6, 3.4, pano, parent=R)
        cyl((-w * .74 - .2, -10, 60), (-w * .74 - .9, 10, 33), 2.6, 3.4, pano, parent=R)
    if L.get('pouches'):
        bolsa = mat('leather', '#5a3a22')
        for y in (-7, -1):
            box((rc * .74 + 1.2, y, zc - 3.5), (3, 4.4, 5), bolsa, bevel=.8, parent=R)
        box((w * .74 + 1, 6, 47), (.4, 5, 6), mat('paper', '#e8dcc0'), bevel=.1, parent=R)
    if L.get('vials'):
        for y, col in ((-6, '#9ae04a'), (-2, '#b06ad0'), (2, '#9ae04a')):
            cyl((rc * .74 + 1, y, zc - 6), (rc * .74 + 1, y, zc - 1), 1.3, 1.1, mat('glass', col), parent=R)
            sph((rc * .74 + 1, y, zc - 6), 1.4, mat('emit', col, strength=1.5), parent=R)
    if B.get('mantle'):
        casca(61, 12, 12.5, 18, math.radians(105), math.radians(255), mat('cloth', L['c2']), xs=.95, dobras=1.2, parent=R)


def manga(L, B):
    if B.get('bare'):
        return mat('skin', L.get('sk', SKIN))
    if B.get('armor'):
        return mat('metal', L.get('mt', METAL))
    return mat('cloth' if L.get('body') != 'leather' else 'leather', L['c1'])


AIM = {'bow', 'longbow', 'shortbow', 'recurve', 'crossbow', 'cannon', 'spiritbow'}


def bracos(L, B, R):
    """Braço direito (arma, -Y) e esquerdo (+Y). Devolve as posições das mãos."""
    m = manga(L, B)
    luva = mat('metal', shade(L.get('mt', METAL), -.2)) if B.get('armor') else mat('skin', L.get('sk', SKIN))
    if L['wpn'] in AIM:
        md, cot = (17, -8, 53), (8, -10, 55)
    else:
        # mão da arma afastada do corpo e um pouco recuada: vista de 3/4 (conceito e sprite) a arma passa ao lado da cabeça, não na frente do rosto
        md, cot = (3.5, -17.5, 41), (1.4, -15.8, 49)
    me, cote = (3, 13.5, 40), (-.5, 14, 48)
    # braçadeiras de couro (ou metal) no antebraço
    brac = mat('metal', shade(L.get('mt', METAL), -.15)) if B.get('armor') else mat('leather', '#3a2a1c')
    for lado, (ombro, cotov, mao) in ((-1, ((0, -11.5, 57.5), cot, md)), (1, ((0, 11.5, 57.5), cote, me))):
        with parte(R, 'braco', ombro, **braco_anim(L, lado)):   # cada braço gira inteiro em volta do ombro
            caps(ombro, cotov, 2.9, m, parent=R)
            caps(cotov, mao, 2.6, m, parent=R)
            sph(mao, 2.8, luva, parent=R)
            p = tuple(cotov[i] + (mao[i] - cotov[i]) * .62 for i in range(3))
            q = tuple(cotov[i] + (mao[i] - cotov[i]) * .88 for i in range(3))
            cyl(p, q, 3.0, 3.0, brac, parent=R)
    return md, me


# como os braços se mexem (herói no mapa e cavaleiros inimigos feitos com este kit): o da arma ataca, o do escudo acompanha
BRACO = {-1: dict(fase=.5, amp=.18, atk=-1.05), 1: dict(fase=0, amp=.18, atk=-.35)}
OMBRO = {-1: (0, -11.5, 57.5), 1: (0, 11.5, 57.5)}
# no golpe, arco e besta só recuam (erguer o braço apontaria a arma para o céu); cajados, varinhas e livros sobem para conjurar
CONJURA = ('orbstaff', 'flamewand', 'icestaff', 'stormstaff', 'tome', 'quill', 'palm', 'prism', 'leafstaff', 'bellstaff', 'keystaff',
           'pilgrimstaff', 'eyestaff', 'clockstaff', 'mirror', 'moonstaff', 'tridentstaff', 'censer')
ATK_ARMA = dict({w: -.12 for w in AIM}, **{w: -.75 for w in CONJURA})


def braco_anim(L, lado):
    d = dict(BRACO[lado])
    if lado == -1 and L.get('wpn') in ATK_ARMA:
        d['atk'] = ATK_ARMA[L['wpn']]
    return d


def lanterna(R, pos=(-2, 14.5, 27)):
    """A lanterna do Portador: pendurada no cinto, sempre acesa (no lado esquerdo; no mapa, no quadril direito, um pouco atrás)."""
    escuro = mat('metal', '#3a2b1d')
    g = grupo(pos, parent=R, nome='lanterna')
    tubo([(-0.5, -1.2, 9), (0, 0, 6)], .35, escuro, parent=g)
    box((0, 0, 6), (6.4, 6.4, 1.2), escuro, bevel=.3, parent=g)
    box((0, 0, -5), (6.8, 6.8, 1.4), escuro, bevel=.3, parent=g)
    for x, y in ((-2.8, -2.8), (2.8, -2.8), (-2.8, 2.8), (2.8, 2.8)):
        cyl((x, y, -5), (x, y, 6), .45, .45, escuro, verts=8, parent=g)
    box((0, 0, .5), (5, 5, 9.5), mat('glass', '#ffd9a0'), bevel=.4, parent=g)
    sph((0, 0, .5), 2.1, mat('emit', '#ffbe5a', strength=14), scale=(1, 1, 1.4), parent=g)
    luz_ponto((0, 0, .5), 30, '#ffb25a', raio=.03, parent=g)


# ---------------- cabeças ----------------
def rosto(L, R, z=73, cor=None, olhos=True):
    sk = cor or L.get('sk', SKIN)
    pele = mat('skin', sk)
    sph((0, 0, z), 10.6, pele, parent=R)
    sph((1.2, 0, z - 1), 9.9, pele, scale=(1, .96, 1.04), parent=R)
    sph((10.6, 0, z - 1.6), 1.6, mat('skin', shade(sk, -.08)), parent=R)
    for y in (-10.2, 10.2):
        sph((-.5, y, z - .5), 2.2, pele, scale=(.6, .5, 1), parent=R)
    if olhos:
        for y in (-3.6, 3.6):
            sph((9.4, y, z + .4), 1.35, mat('gloss', '#1b1410'), parent=R)
            box((9.6, y * 1.05, z + 3), (1, 3.4, .8), mat('fur', '#2a1d14'), rot=(y * .03, 0, 0), bevel=.3, parent=R)   # sobrancelha
        box((10.1, 0, z - 5.2), (.8, 3.6, .55), mat('skin', shade(sk, -.35)), bevel=.2, parent=R)   # boca


def cabelo(L, R, z=73, cor=None, longo=False):
    c = mat('fur', cor or L.get('hair', '#5a4030'))
    sph((-1.2, 0, z + 1.2), 11.1, c, scale=(1, 1.02, 1), parent=R)   # calota (o rosto fica na frente)
    sph((4, 0, z + 6), 7.5, c, scale=(1, 1.3, .55), parent=R)          # franja
    if longo:
        for y in (-7, 0, 7):
            tubo([(-6, y, z + 2), (-9, y * 1.2, z - 8), (-8, y * 1.3, z - 20)], 3.2, c, radii=[1, .9, .5], parent=R)


def elmo_base(L, R, z=73):
    mt = mat('metal', L.get('mt', METAL))
    cupula((-.4, 0, z + 1.2), 12.6, mt, parent=R)
    torus((0, 0, z - .6), 12.2, 1.2, mat('metal', shade(L.get('mt', METAL), -.3)), scale=(1, 1, .9), parent=R)
    box((-8.5, 0, z - 6), (5, 19, 9), mt, bevel=1.5, parent=R)
    box((11.6, 0, z - 3), (1.6, 2.4, 8.5), mt, bevel=.4, parent=R)


def H_hood(L, R):
    rosto(L, R)
    capuz((-.6, 0, 74), 12.9, mat('cloth', L['c2']), parent=R, ponta=(-15, 9))


def H_deephood(L, R):
    sph((1.2, 0, 72), 9.9, mat('cloth', '#0b090b'), parent=R)
    capuz((-.4, 0, 73.6), 13.4, mat('cloth', L['c1']), abertura=.48, parent=R, ponta=(-17, 12))
    e = L.get('eyes', '#ffb04a')
    for y in (-3.2, 3.2):
        sph((9.6, y, 73), 1.3, mat('emit', e, strength=18), parent=R)
    luz_ponto((13, 0, 73), 8, e, parent=R)


def H_helm(L, R):
    rosto(L, R)
    elmo_base(L, R)


def H_greathelm(L, R):
    mt = mat('metal', L.get('mt', METAL))
    box((0, 0, 73.5), (24, 23.5, 25), mt, bevel=4, parent=R)
    box((0, 0, 85.6), (24.4, 23.8, 2.2), tm(L, metalico=True), bevel=.8, parent=R)
    sl = L.get('slit')
    box((12, 0, 74.4), (.8, 15, 2.8), mat('emit', sl, strength=16) if sl else mat('gloss', '#0a0c10'), bevel=.2, parent=R)
    if sl:
        luz_ponto((16, 0, 74.4), 14, sl, parent=R)
    for y in (-3, 0, 3):
        sph((12, y, 67), .8, mat('gloss', '#0a0c10'), parent=R)


def H_crest(L, R):
    H_helm(L, R)
    cor = L.get('crestCol', L['tr'])
    tubo([(-11, 0, 80), (-6, 0, 90), (3, 0, 92), (11, 0, 86)], 3.2, mat('fur', cor), radii=[.6, 1, 1, .4], parent=R)


def H_horned(L, R):
    H_helm(L, R)
    osso = mat('bone', '#e8dcc0')
    for s in (-1, 1):
        tubo([(0, s * 9, 80), (0, s * 16, 82), (1, s * 21, 92), (3, s * 19, 101)], 3.2, osso, radii=[1, .85, .55, .1], parent=R)


def H_spiked(L, R):
    H_helm(L, R)
    esp = mat('metal', shade(L.get('mt', METAL), .3))
    for i in range(7):
        a = -1.2 + i / 6 * 2.4
        x0, z0 = math.sin(a) * 11, 75 + math.cos(a) * 11
        cyl((x0, 0, z0), (math.sin(a) * 21, 0, 75 + math.cos(a) * 21), 2.2, .1, esp, parent=R)


def H_gladhelm(L, R):
    mt = mat('metal', L.get('mt', METAL))
    sph((-.4, 0, 74), 12.8, mt, scale=(1, 1, .95), parent=R)
    sph((5, 0, 72), 8, mat('gloss', '#14100c'), scale=(.9, 1, 1.1), parent=R)
    for y in (-4.5, -1.5, 1.5, 4.5):
        cyl((12.2, y, 65), (12.2, y, 79), .55, .55, mt, verts=8, parent=R)
    cyl((0, 0, 75), (0, 0, 76.4), 16, 16, mat('metal', shade(L.get('mt', METAL), -.25)), parent=R)
    pluma = mat('fur', L['tr'])
    for i in range(9):
        a = -1.25 + i / 8 * 2.5
        sph((0, math.sin(a) * 12, 80 + math.cos(a) * 8), 2.6, pluma, scale=(.6, .8, 1.6), parent=R)


def H_wild(L, R):
    rosto(L, R)
    cab = mat('fur', L.get('hair', '#6a3a22'))
    sph((-1.5, 0, 75), 11, cab, scale=(1, 1.05, .9), parent=R)
    for i in range(10):
        a, b = (i / 10) * math.tau, .5 + (i % 3) * .25
        cyl((-1 + math.cos(a) * 5, math.sin(a) * 6, 80), (-3 + math.cos(a) * 13, math.sin(a) * 15, 86 + (i % 2) * 6), 4, .2, cab, parent=R)
    sph((7, 0, 64), 7, cab, scale=(.9, 1.1, 1), parent=R)
    for z in (74.5, 71):
        box((10.4, 0, z), (.5, 9, .9), mat('cloth', L['tr']), bevel=.2, parent=R)


def H_plumehat(L, R):
    rosto(L, R)
    cabelo(L, R)
    chapeu = mat('cloth', L['c2'])
    cyl((1, 0, 80.5), (1, 0, 81.8), 16, 15.5, chapeu, parent=R)
    cyl((0, 0, 81), (0, 0, 90), 8.2, 7, chapeu, parent=R)
    cyl((0, 0, 82), (0, 0, 84.4), 8.3, 8.1, tm(L), parent=R)
    tubo([(0, 3, 88), (-8, 5, 96), (-18, 6, 94), (-24, 6, 86)], 2.6, mat('fur', '#f4ecd8'), radii=[.6, 1, .8, .2], parent=R)


def H_widehat(L, R):
    rosto(L, R)
    cabelo(L, R, cor='#5a4030')
    ch = mat('leather', shade(L['c1'], .12))
    cyl((1, 0, 80), (1, 0, 81.4), 19, 18.4, ch, parent=R)
    sph((0, 0, 81), 9.2, ch, scale=(1, 1, .8), parent=R)
    sph((8.6, 0, 84), 2.6, mat('bone', L['tr']), scale=(.4, 1, 1), parent=R)


def H_kettle(L, R):
    rosto(L, R)
    mt = mat('metal', L.get('mt', METAL))
    sph((0, 0, 77), 11.4, mt, scale=(1, 1, .82), parent=R)
    cyl((1, 0, 77.5), (1, 0, 78.6), 18, 17, mt, parent=R)


def H_tricorn(L, R):
    rosto(L, R)
    cabelo(L, R, cor='#2a2420')
    ch = mat('cloth', L['c2'])
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=17 * U, depth=2.4 * U, location=V((0, 0, 81)))
    o = bpy.context.object
    o.data.materials.append(ch)
    o.parent = R
    o.rotation_euler = (0, 0, math.pi)
    sph((0, 0, 82), 8.4, ch, scale=(1, 1, .8), parent=R)
    if L.get('monocle'):
        torus((10.3, -3.6, 73.4), 2.4, .35, mat('gold', L['tr']), rot=(0, math.pi / 2, 0), parent=R)


def H_pointhat(L, R):
    rosto(L, R)
    if L.get('beard'):
        tubo([(8, 0, 67), (9, 0, 58), (7, 0, 50), (6, 0, 44)], 6.5, mat('fur', L['beard']), radii=[1, .8, .5, .1], parent=R)
    ch = mat('cloth', L['c1'])
    cyl((0, 0, 79.5), (0, 0, 80.8), 16.5, 16, mat('cloth', L['c2']), parent=R)
    tubo([(0, 0, 80), (-2, 0, 92), (-9, 0, 101), (-16, 0, 104)], 9.5, ch, radii=[1, .62, .3, .03], parent=R)
    cyl((0, 0, 81), (0, 0, 83.2), 9.6, 9.1, tm(L), parent=R)
    sph((7.4, 0, 88), 1.6, mat('emit', L['tr'], strength=8), parent=R)


def H_cap(L, R):
    rosto(L, R)
    cabelo(L, R)
    ch = mat('cloth', L['c2'])
    cyl((0, 0, 80), (0, 0, 87), 9.4, 9.4, ch, parent=R)
    box((0, 0, 87.6), (22, 22, 1.4), mat('cloth', shade(L['c2'], -.25)), rot=(0, 0, math.pi / 4), bevel=.3, parent=R)
    tubo([(0, 0, 88.6), (8, -8, 88.6), (9, -9, 80)], .5, tm(L), parent=R)
    sph((9, -9, 79.5), 1.3, tm(L), parent=R)


def H_crown(L, R):
    rosto(L, R)
    cabelo(L, R, longo=True)
    k = L.get('crown')
    if k == 'ice':
        torus((0, 0, 81), 10.6, .9, mat('metal', L['tr']), parent=R)
        gelo = mat('glass', '#cdeeff')
        for i in range(7):
            a = -1.3 + i / 6 * 2.6
            h = 10 if i == 3 else 6 if i % 2 else 4
            cyl((math.cos(a) * 10.4, math.sin(a) * 10.4, 81), (math.cos(a) * 11, math.sin(a) * 11, 81 + h), 1.7, .1, gelo, parent=R)
        luz_ponto((8, 0, 88), 10, '#a8e4ff', parent=R)
    elif k == 'prism':
        torus((0, 0, 81), 10.6, .8, mat('metal', '#e8e4f8'), parent=R)
        for i, col in enumerate(('#ff8ad8', '#8ae8ff', '#ffe88a')):
            a = -.8 + i * .8
            sph((math.cos(a) * 8, math.sin(a) * 8, 92 + (i % 2) * 2), 2.4, mat('emit', col, strength=7), scale=(.6, .6, 1.5), parent=R)
    elif k == 'flowers':
        torus((0, 0, 81), 10.8, 1.1, mat('cloth', '#5a8a3a'), parent=R)
        for i, col in enumerate(('#f0b8d8', '#fff2c0', '#e8c0e0', '#f8f0f0', '#f0b8d8', '#fff2c0')):
            a = -1.4 + i / 5 * 2.8
            sph((math.cos(a) * 10.8, math.sin(a) * 10.8, 81.5), 2.1, mat('cloth', col), parent=R)
    elif k == 'laurel':
        torus((0, 0, 80.5), 10.7, .7, mat('gold', '#d9b85a'), parent=R)
        folha = mat('cloth', '#8aa85a')
        for i in range(12):
            a = i / 12 * math.tau
            sph((math.cos(a) * 11, math.sin(a) * 11, 81.5), 1.4, folha, scale=(1, .5, 2), rot=(0, 0, a), parent=R)
    elif k == 'moon':
        torus((0, 0, 80.5), 10.6, .6, mat('metal', '#c8d0e8'), parent=R)
        torus((11.4, 0, 85), 3.2, .9, mat('emit', '#eef2ff', strength=9), rot=(0, math.pi / 2, 0), scale=(1, 1, 1), parent=R)
        luz_ponto((14, 0, 85), 10, L['fx'], parent=R)
    elif k == 'shells':
        concha = mat('bone', '#e8d8c8')
        for i in range(7):
            a = -1.3 + i / 6 * 2.6
            sph((math.cos(a) * 10.8, math.sin(a) * 10.8, 81.5), 2.2, concha, scale=(1, 1, .6), parent=R)
            sph((math.cos(a + .2) * 10.9, math.sin(a + .2) * 10.9, 80.5), .9, mat('gloss', '#f8f4ff'), parent=R)


def H_feather(L, R):
    rosto(L, R)
    cabelo(L, R)
    torus((0, 0, 79), 10.8, 1.1, tm(L), parent=R)
    poly([(-8, 0, 80), (-11, 0, 92), (-10, 0, 104), (-7, 0, 92)], mat('cloth', '#f0e6d0'), esp=.6, parent=R)
    sph((-10, 0, 103), 1.4, mat('cloth', '#3a2a1a'), scale=(.6, .6, 1.4), parent=R)
    tubo([(-9, 0, 74), (-12, 0, 66), (-11, 0, 58)], 2.6, mat('fur', L.get('hair', '#6a4a2a')), radii=[1, .8, .4], parent=R)


def H_wolf(L, R):
    rosto(L, R, z=71)
    pele = mat('fur', L['c1'])
    capuz((-.6, 0, 74.5), 13.2, pele, abertura=.5, parent=R)
    for y in (-6, 6):
        cyl((-2, y, 84), (-1, y * 1.1, 93), 3.2, .3, pele, parent=R)
    sph((10, 0, 81), 6.5, mat('fur', shade(L['c1'], -.2)), scale=(1.4, .8, .6), parent=R)
    sph((18.4, 0, 81), 1.6, mat('gloss', '#1a1410'), parent=R)
    for y in (-2.2, 2.2):
        sph((9, y * 2.4, 84.5), .9, mat('emit', '#ffd24a', strength=8), parent=R)
    for i in range(4):
        cyl((11 + i * 1.8, -3.5 + (i % 2) * 7, 78.4), (11 + i * 1.8, -3.5 + (i % 2) * 7, 76.2), .55, .05, mat('bone', '#f4ecd8'), parent=R)


def H_mask(L, R):
    H_hood(L, R)
    sc = mat('cloth', shade(L['c1'], .12))
    sph((4.2, 0, 69), 9.2, sc, scale=(.85, 1, .62), parent=R)
    tubo([(-8, 3, 69), (-16, 5, 68), (-25, 6, 64)], 1.6, sc, radii=[1, .9, .6], parent=R)
    tubo([(-8, -3, 68), (-15, -5, 64), (-22, -6, 58)], 1.5, sc, radii=[1, .9, .6], parent=R)
    for y in (-3.6, 3.6):
        sph((9.6, y, 74), .7, mat('emit', L['tr'], strength=6), parent=R)


def H_goggles(L, R):
    rosto(L, R)
    cabelo(L, R)
    torus((0, 0, 78.5), 10.9, 1.5, mat('cloth', '#a8402a'), parent=R)
    for y in (-3.8, 3.8):
        cyl((9.4, y, 80), (11.4, y, 80), 3.2, 3.2, mat('gold', L['tr']), parent=R)
        cyl((11.3, y, 80), (11.6, y, 80), 2.3, 2.3, mat('glass', '#9ad0e0'), parent=R)


def H_furcap(L, R):
    rosto(L, R)
    pelo = mat('fur', shade(L['c1'], .15))
    sph((-.6, 0, 77.5), 12, pelo, scale=(1, 1, .72), parent=R)
    torus((0, 0, 74.5), 11.4, 2.4, pelo, parent=R)
    for y in (-10, 10):
        box((-1, y, 69), (6, 3, 12), pelo, bevel=1.2, parent=R)
    cauda = [(-11, 0, 74), (-15, 0, 66), (-16, 0, 56)]
    tubo(cauda, 3.2, mat('fur', '#8a7a6a'), radii=[1, 1, .6], parent=R)
    for z in (70, 64, 59):
        torus((-15, 0, z), 3, .9, mat('fur', '#3a2a1a'), parent=R)


def H_bald(L, R):
    rosto(L, R)
    sph((-.5, 0, 74), 11, mat('skin', L.get('sk', SKIN)), parent=R)
    if L.get('beard'):
        tubo([(8, 0, 66), (9, 0, 57), (8, 0, 49)], 5.5, mat('fur', L['beard']), radii=[1, .7, .2], parent=R)
    tubo([(-2, -6, 82), (2, -3, 84.5), (4, 3, 83.5), (0, 7, 81)], .45, mat('emit', L['tr'], strength=3), parent=R)


def H_skullhood(L, R):
    capuz((-.4, 0, 73.6), 13.4, mat('cloth', L['c1']), abertura=.48, parent=R, ponta=(-16, 11))
    osso = mat('bone', '#e8e0d0')
    sph((3, 0, 73), 9.4, osso, scale=(1, .95, 1.05), parent=R)
    for y in (-3.6, 3.6):
        sph((10.2, y, 73.6), 2.2, mat('gloss', '#1a1018'), parent=R)
        sph((10.9, y, 73.6), .8, mat('emit', L['tr'], strength=16), parent=R)
    box((10.2, 0, 66.5), (2, 7, 3), osso, bevel=.6, parent=R)
    luz_ponto((14, 0, 73), 10, L['tr'], parent=R)


def H_judge(L, R):
    rosto(L, R, olhos=False)
    cabelo(L, R, cor='#d8d0c0', longo=True)
    torus((0, 0, 73.5), 10.8, 1.8, mat('cloth', '#ece4d4'), parent=R)
    ch = mat('cloth', L['c2'])
    cyl((0, 0, 80), (0, 0, 100), 9.4, 10.2, ch, parent=R)
    cyl((0, 0, 84), (0, 0, 86.6), 9.8, 9.8, mat('gold', L['tr']), parent=R)


def H_beak(L, R):
    capuz((-.4, 0, 73.6), 13, mat('cloth', L['c1']), abertura=.44, parent=R)
    osso = mat('bone', '#e8dcc4')
    sph((4, 0, 73), 8.8, osso, parent=R)
    cyl((10, 0, 72), (24, 0, 66), 4.6, .3, osso, parent=R)
    for y in (-3.4, 3.4):
        sph((10.6, y, 75.5), 1.8, mat('gloss', '#1a1018'), parent=R)
        sph((11.4, y, 75.5), .8, mat('emit', L['tr'], strength=10), parent=R)
    pena = mat('cloth', L['c2'])
    for i in range(3):
        cyl((-4 + i * 3, 0, 84), (-10 + i * 3, 0, 96 - i * 2), 2.2, .2, pena, parent=R)


def H_cowl(L, R):
    rosto(L, R, cor=shade(L.get('sk', SKIN), -.2))
    capuz((-.6, 0, 74.4), 13.2, mat('cloth', L['c1']), abertura=.52, parent=R, ponta=(-10, 14))
    elo = mat('metal', '#8a8a90')
    for i in range(9):
        a = i / 9 * math.tau
        torus((math.cos(a) * 9, math.sin(a) * 9.5, 62), 1.6, .5, elo, rot=(math.pi / 2, 0, a), parent=R)


def H_coif(L, R):
    rosto(L, R)
    malha = mat('metal', shade(L.get('mt', METAL), -.1), rough=.6)
    capuz((-.6, 0, 73.8), 13, malha, abertura=.5, parent=R)
    cyl((-2, 0, 66), (-2, 0, 59), 12, 14, malha, parent=R)
    torus((0, 0, 79.5), 11.4, .8, tm(L), parent=R)


def H_ribbon(L, R):
    rosto(L, R)
    cabelo(L, R)
    fita = tm(L)
    torus((0, 0, 78), 10.9, 1.4, fita, parent=R)
    tubo([(-10, -2, 78), (-17, -4, 76), (-26, -6, 70)], 1.4, fita, radii=[1, .9, .5], parent=R)
    tubo([(-10, 2, 77), (-16, 5, 72), (-23, 7, 64)], 1.4, fita, radii=[1, .9, .5], parent=R)


def H_visor(L, R):
    mt = mat('metal', L.get('mt', METAL))
    sph((-2.5, 0, 75), 13, mt, scale=(1.18, .98, .9), parent=R)
    box((11.4, 0, 72.5), (1.2, 15, 3.2), mat('gloss', '#120806'), bevel=.3, parent=R)
    box((12, 0, 72.5), (.4, 13, 1.4), mat('emit', L['fx'], strength=14), bevel=.1, parent=R)
    luz_ponto((16, 0, 72.5), 14, L['fx'], parent=R)
    box((0, 0, 86.6), (22, 2.4, 2.6), tm(L, metalico=True), bevel=.8, parent=R)


def H_tophat(L, R):
    rosto(L, R)
    cabelo(L, R, cor='#4a3a2a')
    ch = mat('cloth', L['c2'])
    cyl((1, 0, 80), (1, 0, 81.2), 15, 14.6, ch, parent=R)
    cyl((0, 0, 81), (0, 0, 100), 8.4, 9.2, ch, parent=R)
    cyl((0, 0, 82.5), (0, 0, 85.6), 8.8, 8.8, mat('gold', L['tr']), parent=R)
    torus((8.6, 0, 92), 3.2, 1, mat('gold', L['tr']), rot=(0, math.pi / 2, 0), parent=R)
    if L.get('monocle'):
        torus((10.3, -3.6, 73.4), 2.4, .35, mat('gold', L['tr']), rot=(0, math.pi / 2, 0), parent=R)


def H_halfmask(L, R):
    H_hood(L, R)
    sph((7, 0, 75.5), 6.4, mat('metal', '#dfe8f4', rough=.05), scale=(.6, 1.15, .7), parent=R)
    for y in (-3.6, 3.6):
        sph((10.6, y, 74), .8, mat('gloss', '#1a2030'), parent=R)


def H_capfeather(L, R):
    rosto(L, R)
    cabelo(L, R)
    ch = mat('cloth', L['c2'])
    sph((0, 0, 79), 11, ch, scale=(1.05, 1, .55), parent=R)
    cyl((5, 0, 78.6), (9, 0, 78.6), 8, 7, ch, parent=R)
    poly([(-4, 2, 82), (-16, 4, 90), (-27, 5, 89), (-15, 4, 86)], mat('cloth', '#b08a5a'), esp=.6, parent=R)


def H_brim(L, R):
    rosto(L, R)
    cabelo(L, R, cor='#2a2018')
    ch = mat('leather', shade(L['c1'], -.15))
    cyl((1, 0, 80), (1, 0, 81), 19.5, 19.5, ch, parent=R)
    cyl((0, 0, 80.5), (0, 0, 89), 9, 8, ch, parent=R)
    cyl((0, 0, 81.5), (0, 0, 83.6), 9.1, 9, tm(L), parent=R)
    sph((5, 0, 68.5), 9, mat('cloth', '#8a2a22'), scale=(.75, 1.02, .55), parent=R)


def H_topknot(L, R):
    rosto(L, R)
    sph((-.5, 0, 74), 11, mat('skin', L.get('sk', SKIN)), parent=R)
    sph((-2, 0, 86), 4, mat('fur', '#2a2018'), parent=R)
    torus((0, 0, 77.5), 10.9, 1.2, tm(L), parent=R)
    tubo([(-10, 0, 77.5), (-16, 1, 74), (-20, 2, 69)], 1.1, tm(L), radii=[1, .8, .4], parent=R)


def H_goldmask(L, R):
    capuz((-.4, 0, 73.6), 13.2, mat('cloth', L['c1']), abertura=.46, parent=R, ponta=(-15, 10))
    sph((3.4, 0, 72.6), 9.2, mat('gold', '#d8b450'), parent=R)
    for y in (-3.6, 3.6):
        box((11.6, y, 74), (.8, 3, 1.2), mat('gloss', '#1a1008'), bevel=.2, parent=R)
    sph((10, 0, 80), 2, mat('emit', L['tr'], strength=8), parent=R)


CABECAS = {n[2:]: f for n, f in globals().items() if n.startswith('H_')}


# ---------------- armas (a mão é a origem do grupo; +Z aponta ao longo da arma) ----------------
def lamina(g, comp, larg, cor='#d6dde2', z0=5, espes=1.0):
    poly([(0, -larg, z0), (0, larg, z0), (0, larg * .7, z0 + comp), (0, 0, z0 + comp + 4), (0, -larg * .7, z0 + comp)], mat('metal', cor), esp=espes, parent=g)


def empunhadura(g, guarda, cabo, cor):
    box((0, 0, 4), (2.2, guarda * 2, 2.4), mat('gold', cor) if _goldish(cor) else mat('metal', cor), bevel=.5, parent=g)
    cyl((0, 0, 3), (0, 0, 3 - cabo), 1.4, 1.4, mat('leather', '#3b2a1a'), parent=g)
    sph((0, 0, 2 - cabo), 1.9, mat('gold', cor) if _goldish(cor) else mat('metal', cor), parent=g)


def haste(g, z0, z1, r, cor):
    cyl((0, 0, z0), (0, 0, z1), r, r * .9, mat('wood', cor), parent=g)


def W_stick(g, L):
    haste(g, -38, 42, 1.3, '#6b5236')


def W_sword(g, L):
    lamina(g, 36, 2.4); empunhadura(g, 6.5, 8, L['tr'])


def W_shortsword(g, L):
    lamina(g, 24, 2.6, '#dfe5ea'); empunhadura(g, 5.5, 6, L['tr'])


def W_greatsword(g, L):
    lamina(g, 54, 3.8, '#cfd6dc', z0=7, espes=1.3); empunhadura(g, 10, 13, L['tr'])


def W_rapier(g, L):
    lamina(g, 44, 1.1, '#e4eaee')
    torus((0, 0, 4.5), 4, .5, mat('gold', L['tr']), rot=(0, math.pi / 2, 0), parent=g)
    empunhadura(g, 3.5, 7, L['tr'])


def W_axe(g, L):
    haste(g, -6, 28, 1.3, '#4a3420')
    poly([(0, 1, 30), (0, 14, 33), (0, 13, 17), (0, 1, 20)], mat('metal', L.get('mt', METAL)), esp=1.4, parent=g)


def W_maul(g, L):
    haste(g, -10, 38, 1.5, '#4a3420')
    box((0, 0, 44), (13, 18, 13), mat('metal', shade(L.get('mt', METAL), -.15)), bevel=1.6, parent=g)
    box((0, 0, 44), (13.6, 4, 13.6), mat('gold', L['tr']) if _goldish(L['tr']) else mat('metal', L['tr']), bevel=.6, parent=g)


def espinhos(g, centro, r, cor):
    sph(centro, r, mat('metal', cor), parent=g)
    for i in range(10):
        a, b = i / 10 * math.tau, (i % 2) * .6 - .3
        d = (math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b))
        cyl(tuple(c + dd * r * .8 for c, dd in zip(centro, d)), tuple(c + dd * (r + 4) for c, dd in zip(centro, d)), 1.3, .05, mat('metal', shade(cor, .25)), parent=g)


def W_morningstar(g, L):
    haste(g, -6, 22, 1.4, '#3a2a1a'); espinhos(g, (0, 0, 28), 6, L.get('mt', METAL))


def W_scythe(g, L):
    haste(g, -30, 54, 1.4, '#2a2420')
    poly([(0, 0, 52), (0, 24, 58), (0, 33, 38), (0, 20, 49), (0, 0, 46)], mat('metal', '#c8d0c0'), esp=.9, parent=g)
    tubo([(0, 2, 51.5), (0, 23, 57), (0, 32, 39)], .35, mat('emit', L['fx'], strength=6), parent=g)


def orbe(g, centro, r, cor, forca=10):
    sph(centro, r, mat('emit', cor, strength=forca), parent=g)
    sph(centro, r * 1.7, mat('glass', shade(cor, .3)), parent=g)
    luz_ponto(centro, 22, cor, parent=g)


def W_orbstaff(g, L):
    haste(g, -38, 50, 1.3, '#6b4a2e')
    for a in range(4):
        cyl((0, 0, 48), (math.cos(a * 1.57) * 4, math.sin(a * 1.57) * 4, 56), .6, .3, mat('wood', '#6b4a2e'), parent=g)
    orbe(g, (0, 0, 56), 3.6, L['fx'])


def W_flamewand(g, L):
    haste(g, -4, 20, 1.2, '#3a2418')
    sph((0, 0, 26), 3.6, mat('emit', '#ff7a2a', strength=14), scale=(1, 1, 1.8), parent=g)
    sph((0, 0, 25), 1.8, mat('emit', '#ffe08a', strength=20), scale=(1, 1, 1.6), parent=g)
    luz_ponto((0, 0, 26), 25, '#ff9a4a', parent=g)


def W_icestaff(g, L):
    haste(g, -38, 46, 1.3, '#b8c8d4')
    gelo = mat('glass', '#d2f0ff')
    for dx, dz, h in ((0, 46, 16), (-4, 46, 9), (4, 47, 10)):
        cyl((dx, 0, dz), (dx * 1.2, 0, dz + h), 2.6, .1, gelo, parent=g)
    luz_ponto((0, 0, 54), 16, '#a8e4ff', parent=g)


def W_stormstaff(g, L):
    haste(g, -38, 44, 1.3, '#2a2a3a')
    for s in (-1, 1):
        cyl((0, 0, 44), (s * 6, 0, 55), .9, .5, mat('wood', '#2a2a3a'), parent=g)
    tubo([(-6, 0, 55), (-3, 0, 57.5), (0, 0, 53.5), (3, 0, 57), (6, 0, 55)], .35, mat('emit', '#fff6a0', strength=20), parent=g)
    luz_ponto((0, 0, 56), 22, '#f0f070', parent=g)


def W_tome(g, L):
    t = grupo((5, 0, 12), rot=(0, -.3, 0), parent=g)
    box((0, 0, 0), (12, 18, 1.6), mat('leather', L['c2']), bevel=.4, parent=t)
    box((0, -4.5, 1.2), (11, 8, 1.2), mat('paper', '#ece2c8'), rot=(.12, 0, 0), bevel=.2, parent=t)
    box((0, 4.5, 1.2), (11, 8, 1.2), mat('paper', '#ece2c8'), rot=(-.12, 0, 0), bevel=.2, parent=t)
    sph((0, 0, 8), 1.6, mat('emit', L['tr'], strength=12), parent=t)
    luz_ponto((0, 0, 8), 14, L['tr'], parent=t)


def W_gauntlet(g, L):
    pedra = mat('stone', '#7a6a4a')
    box((2, 0, 0), (13, 12, 13), pedra, bevel=3, parent=g)
    tubo([(8.6, -4, -2), (8.8, 0, 2), (8.6, 3, -1)], .5, mat('emit', L['fx'], strength=8), parent=g)


def W_quill(g, L):
    cyl((0, 0, -8), (0, 0, 40), .7, .4, mat('bone', '#efe6d0'), parent=g)
    poly([(0, 0, 10), (0, 8, 24), (0, 1, 44), (0, -7, 26)], mat('cloth', L['tr']), esp=.5, parent=g)
    cyl((0, 0, -8), (0, 0, -13), .8, .05, mat('metal', '#2a2a2a'), parent=g)
    sph((0, 0, -13), .8, mat('emit', L['fx'], strength=10), parent=g)


def W_palm(g, L):
    sph((2, 0, 4), 3.4, mat('emit', L['fx'], strength=12), parent=g)
    for i in range(5):
        a = i / 5 * math.tau
        sph((2 + math.cos(a) * 7, math.sin(a) * 7, 4 + math.sin(a * 2) * 3), 1, mat('emit', '#ffcf7a', strength=14), parent=g)
    luz_ponto((2, 0, 4), 24, L['fx'], parent=g)


def W_prism(g, L):
    t = grupo((3, 0, 16), rot=(.4, .3, .2), parent=g)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=6 * U, radius2=0, depth=10 * U, location=V((0, 0, 0)))
    o = bpy.context.object
    o.data.materials.append(mat('glass', '#e8d8ff'))
    o.parent = t
    sph((0, 0, 0), 2, mat('emit', '#ff9ae8', strength=8), parent=t)
    luz_ponto((0, 0, 0), 16, '#e8d8ff', parent=t)


def arco(g, R_, span, cor_madeira, recurvo=False, mat_override=None):
    """Arco vertical à frente da mão (a empunhadura fica na mão)."""
    pts = []
    for i in range(9):
        a = -span + i / 8 * 2 * span
        pts.append((R_ * math.cos(a) - R_ + 2, 0, R_ * math.sin(a)))
    madeira = mat_override or mat('wood', cor_madeira)
    tubo(pts, 1.3, madeira, radii=[.6, .8, 1, 1.1, 1.2, 1.1, 1, .8, .6], parent=g)
    topo, base = pts[-1], pts[0]
    if recurvo:
        tubo([topo, (topo[0] + 2, 0, topo[2] + 3), (topo[0] + 5, 0, topo[2] + 4)], 1, madeira, parent=g)
        tubo([base, (base[0] + 2, 0, base[2] - 3), (base[0] + 5, 0, base[2] - 4)], 1, madeira, parent=g)
    cyl(topo, base, .25, .25, mat('cloth', '#ebe1cd'), verts=6, parent=g)
    cyl((topo[0], 0, 0), (8, 0, 0), .4, .4, mat('wood', '#d8ccb0'), verts=8, parent=g)   # flecha encaixada
    cyl((8, 0, 0), (11, 0, 0), 1, .05, mat('metal', '#c8ccd0'), verts=8, parent=g)


def W_bow(g, L):
    arco(g, 22, 1.1, '#7a5a32')


def W_longbow(g, L):
    arco(g, 30, 1.15, '#4a3420')


def W_shortbow(g, L):
    arco(g, 16, 1.05, '#8a6a3a')


def W_recurve(g, L):
    arco(g, 20, 1.0, '#6a4a2a', recurvo=True)


def W_spiritbow(g, L):
    arco(g, 24, 1.1, None, recurvo=True, mat_override=mat('emit', L['fx'], strength=6))
    luz_ponto((-6, 0, 0), 18, L['fx'], parent=g)


def W_crossbow(g, L):
    box((2, 0, 0), (24, 4, 4.4), mat('wood', '#6a4a2a'), bevel=.8, parent=g)
    tubo([(13, -14, 0), (16, 0, 0), (13, 14, 0)], 1.2, mat('metal', L.get('mt', METAL)), parent=g)
    cyl((13, -14, 0), (4, 0, 1), .25, .25, mat('cloth', '#e6dcc8'), verts=6, parent=g)
    cyl((13, 14, 0), (4, 0, 1), .25, .25, mat('cloth', '#e6dcc8'), verts=6, parent=g)
    cyl((3, 0, 2.6), (19, 0, 2.6), .7, .7, mat('wood', '#3a3028'), verts=8, parent=g)


def W_cannon(g, L):
    cyl((-6, 0, 0), (20, 0, 0), 3.4, 3.8, mat('metal', '#3a3634'), parent=g)
    for x in (-2, 8, 17):
        cyl((x, 0, 0), (x + 2, 0, 0), 4, 4, mat('gold', L['tr']), parent=g)
    box((-9, 0, -4), (7, 3, 8), mat('wood', '#6a4a2a'), rot=(0, .6, 0), bevel=.8, parent=g)


def W_spear(g, L):
    haste(g, -26, 48, 1.2, '#6a4a2a')
    poly([(0, 0, 60), (0, 3.6, 51), (0, 0, 45), (0, -3.6, 51)], mat('metal', L.get('mt', METAL)), esp=1.2, parent=g)
    tubo([(0, 0, 45), (-2, 0, 41), (-5, 0, 36)], .8, mat('cloth', L['tr']), parent=g)


def W_dagger(g, L):
    lamina(g, 13, 1.8, '#dfe4ea', z0=3); empunhadura(g, 3.4, 5, L['tr'])


def W_poisondagger(g, L):
    poly([(0, -1.8, 4), (0, -4, 12), (0, 1, 21), (0, 1, 12), (0, 1.8, 4)], mat('metal', '#c8d4c0'), esp=.8, parent=g)
    sph((0, -.5, 12), .9, mat('emit', L['fx'], strength=8), scale=(1, 1, 1.5), parent=g)
    empunhadura(g, 3.4, 5, '#5a3a5a')


def W_sunmace(g, L):
    haste(g, -6, 30, 1.5, '#5a4426')
    sph((0, 0, 35), 6.4, mat('gold', '#d9b85a'), parent=g)
    for i in range(8):
        a = i / 8 * math.tau
        sph((math.cos(a) * 7.6, math.sin(a) * 7.6, 35), 1.8, mat('gold', '#f3dc8e'), parent=g)
    luz_ponto((0, 0, 35), 8, '#ffe8a0', parent=g)


def W_sunhammer(g, L):
    haste(g, -8, 34, 1.5, '#5a4426')
    box((0, 0, 41), (12, 20, 12), mat('gold', L.get('mt', '#e8c870')), bevel=1.8, parent=g)
    for s in (-1, 1):
        sph((0, s * 10.4, 41), 3.4, mat('emit', L['fx'], strength=9), scale=(1, .3, 1), parent=g)
    luz_ponto((0, 0, 41), 20, L['fx'], parent=g)


def W_leafstaff(g, L):
    tubo([(0, 0, -36), (2, 0, -8), (-1, 0, 20), (1, 0, 46)], 1.5, mat('wood', '#5a4026'), parent=g)
    for i, (x, y, z) in enumerate(((-3, 2, 44), (4, -2, 42), (-2, -3, 38), (3, 3, 36), (0, 0, 48))):
        sph((x, y, z), 2, mat('cloth', '#7aa04a'), scale=(.5, 1, 1.9), rot=(i, i * .7, 0), parent=g)
    sph((1, 0, 48), 2.2, mat('cloth', L['tr']), parent=g)


def W_execblade(g, L):
    box((0, 0, 25), (1.6, 8, 40), mat('metal', '#9aa2a8'), bevel=.4, parent=g)
    for z in (14, 23, 32):
        sph((.9, 0, z), 1, mat('gold', L['tr']), parent=g)
    empunhadura(g, 6, 9, L['tr'])


def W_bellstaff(g, L):
    haste(g, -30, 44, 1.3, '#6a5034')
    tubo([(0, 0, 44), (0, 0, 49), (5, 0, 50)], 1.1, mat('wood', '#6a5034'), parent=g)
    cyl((6, 0, 47), (6, 0, 41), 1.4, 4.4, mat('gold', '#e0c060'), parent=g)
    sph((6, 0, 40.6), 1.2, mat('gold', '#a08030'), parent=g)


def W_keystaff(g, L):
    haste(g, -30, 40, 1.3, '#8a7a50')
    torus((0, 0, 46), 6, 1.2, mat('gold', L['tr']), rot=(math.pi / 2, 0, 0), parent=g)
    sph((0, 0, 46), 2.4, mat('emit', L['fx'], strength=10), parent=g)
    for z in (30, 25):
        box((0, 2.5, z), (2, 5, 2.2), mat('gold', L['tr']), bevel=.3, parent=g)
    luz_ponto((0, 0, 46), 14, L['fx'], parent=g)


def W_pilgrimstaff(g, L):
    haste(g, -38, 54, 1.3, '#7a5a3a')
    sph((3, 0, 37), 3, mat('wood', '#c8803a'), parent=g)
    sph((3, 0, 32), 4, mat('wood', '#c8803a'), parent=g)
    tubo([(0, 0, 50), (-4, 0, 47), (-8, 0, 42)], .9, mat('cloth', L['tr']), parent=g)


def W_eyestaff(g, L):
    haste(g, -32, 42, 1.3, '#3a3028')
    torus((0, 0, 48), 7, 1, mat('gold', L['tr']), rot=(math.pi / 2, 0, 0), parent=g)
    sph((0, 0, 48), 4, mat('bone', '#f4ecd8'), scale=(1, 1, .7), parent=g)
    sph((3.4, 0, 48), 1.8, mat('emit', L['fx'], strength=12), parent=g)
    luz_ponto((5, 0, 48), 10, L['fx'], parent=g)


def W_flail(g, L):
    haste(g, -6, 16, 1.4, '#3a2a1a')
    elo = mat('metal', '#8a8a90')
    for i in range(5):
        torus((i * 2.4, 0, 17 - i * 2.6), 1.2, .4, elo, rot=(0, i * .8, 0), parent=g)
    espinhos(g, (12, 0, 3), 5, L.get('mt', METAL))


def W_chain(g, L):
    elo = mat('metal', shade(L.get('mt', METAL), -.1))
    for i in range(10):
        a = i * .32
        torus((math.sin(a) * i * 2.4, 0, -i * 2.6), 1.5, .45, elo, rot=(0, 0, (i % 2) * math.pi / 2), parent=g)
    poly([(9, 0, -26), (13, 0, -29), (11, 0, -34), (8, 0, -31)], mat('metal', L.get('mt', METAL)), esp=1.2, parent=g)


def W_scimitar(g, L):
    poly([(0, -1.8, 4), (0, -3, 16), (0, 4, 32), (0, 3, 16), (0, 2, 4)], mat('metal', '#dfe6ea'), esp=.8, parent=g)
    empunhadura(g, 4, 6, L['tr'])


def W_flamberge(g, L):
    pts = [(0, -2.8, 6)]
    for i in range(1, 9):
        pts.append((0, -2.8 + (-1.2 if i % 2 else 1.2), 6 + i * 6))
    pts.append((0, 0, 60))
    for i in range(8, 0, -1):
        pts.append((0, 2.8 + (1.2 if i % 2 else -1.2), 6 + i * 6))
    pts.append((0, 2.8, 6))
    poly(pts, mat('metal', '#4a3a3a'), esp=1.2, parent=g)
    tubo([(0, 0, 8), (0, 0, 56)], .45, mat('emit', L['fx'], strength=10), parent=g)
    luz_ponto((0, 0, 34), 26, L['fx'], parent=g)
    empunhadura(g, 9, 11, L['tr'])


def W_clockstaff(g, L):
    haste(g, -36, 42, 1.3, '#5a3a22')
    cyl((-1, 0, 50), (1, 0, 50), 8.4, 8.4, mat('gold', L['tr']), parent=g)
    cyl((1, 0, 50), (1.3, 0, 50), 6.8, 6.8, mat('paper', '#f4ecd8'), parent=g)
    cyl((1.4, 0, 50), (1.4, 0, 55), .45, .45, mat('metal', '#2a2018'), verts=8, parent=g)
    cyl((1.4, 0, 50), (1.4, 3.2, 50), .45, .45, mat('metal', '#2a2018'), verts=8, parent=g)
    luz_ponto((4, 0, 50), 8, L['fx'], parent=g)


def W_mirror(g, L):
    cyl((0, 0, -2), (0, 0, 8), 1, 1, mat('wood', '#8a7a6a'), parent=g)
    cyl((-.6, 0, 16), (.6, 0, 16), 7.4, 7.4, mat('gold', L['tr']) if _goldish(L['tr']) else mat('metal', '#dfe6f0'), parent=g).scale = (1, 1, 1.25)
    cyl((.7, 0, 16), (.9, 0, 16), 6, 6, mat('metal', '#e8f0ff', rough=.02), parent=g).scale = (1, 1, 1.25)
    luz_ponto((4, 0, 16), 10, L['fx'], parent=g)


def W_moonstaff(g, L):
    haste(g, -36, 44, 1.2, '#c0c8d8')
    torus((0, 0, 53), 8, 1.6, mat('emit', '#eef2ff', strength=8), rot=(math.pi / 2, 0, 0), scale=(1, 1, 1), parent=g)
    sph((3, 0, 55), 6.6, mat('cloth', '#151c38'), scale=(.3, 1, 1), parent=g)
    luz_ponto((0, 0, 53), 18, L['fx'], parent=g)


def W_bolas(g, L):
    corda = mat('cloth', '#8a7a5a')
    for i in range(3):
        a = i / 3 * math.tau
        p = (math.cos(a) * 9, math.sin(a) * 9, 10)
        cyl((0, 0, 1), p, .3, .3, corda, verts=6, parent=g)
        sph(p, 2.4, mat('stone', '#5a4a3a'), parent=g)


def W_fists(g, L):
    box((1, 0, 0), (8, 7, 7), mat('cloth', '#ece4d0'), bevel=2.2, parent=g)
    sph((2, 0, 0), 6, mat('emit', L['fx'], strength=2.5, alpha=.35), parent=g)
    luz_ponto((4, 0, 0), 12, L['fx'], parent=g)


def W_tridentstaff(g, L):
    haste(g, -26, 44, 1.2, '#3a6a7a')
    prata = mat('metal', '#d8e8ec')
    cyl((0, -6, 44), (0, 6, 44), .9, .9, prata, parent=g)
    for y, h in ((-6, 55), (0, 60), (6, 55)):
        cyl((0, y, 44), (0, y, h), .8, .8, prata, parent=g)
        cyl((0, y, h), (0, y, h + 4), 1.6, .05, prata, parent=g)
    luz_ponto((0, 0, 52), 10, L['fx'], parent=g)


def W_censer(g, L):
    tubo([(0, 0, 0), (2, 0, -8), (3, 0, -16)], .3, mat('metal', '#8a7a5a'), parent=g)
    sph((3, 0, -19), 4.6, mat('gold', L['tr']), scale=(1, 1, .8), parent=g)
    sph((3, 0, -19), 2, mat('emit', '#ffb050', strength=10), parent=g)
    for i in range(3):
        sph((3 + i * .8, 0, -13 + i * 4), 1.6 + i * .7, mat('emit', '#d8c8d8', strength=.4, alpha=.25), parent=g)
    luz_ponto((3, 0, -19), 10, '#ffb050', parent=g)


ARMAS = {n[2:]: f for n, f in globals().items() if n.startswith('W_')}
# pose da arma na mão: (abertura, inclinação) em radianos.
# Abertura positiva gira em X e leva a ponta para fora do corpo (lado -Y); inclinação positiva gira em Y e leva a ponta para a frente.
# Cajados ficam no padrão (abertos e um pouco para trás); objetos de mão (livro, espelho, mangual) quase não giram.
POSE = {'sword': (.42, .05), 'shortsword': (.45, .2), 'greatsword': (.3, -.35), 'rapier': (.2, .95), 'axe': (.4, .1), 'maul': (.3, -.35),
        'morningstar': (.42, .1), 'scythe': (.22, -.18), 'execblade': (.3, -.25), 'flamberge': (.3, -.3), 'scimitar': (.45, .35), 'dagger': (.35, .95),
        'poisondagger': (.35, .95), 'spear': (.18, -.12), 'tridentstaff': (.2, -.1), 'flamewand': (.45, .5), 'quill': (.4, .35),
        'sunmace': (.42, .05), 'sunhammer': (.3, -.2),
        'tome': (.08, 0), 'mirror': (.12, .1), 'prism': (.1, 0), 'palm': (.05, 0), 'gauntlet': (.05, 0), 'fists': (.05, 0),
        'bolas': (.1, 0), 'chain': (0, .05), 'flail': (0, .05), 'censer': (0, .05)}


def arma(L, mao, R):
    tipo = L['wpn']
    if tipo in AIM:
        g = grupo(mao, rot=(math.pi / 2, 0, 0), parent=R) if tipo not in ('crossbow', 'cannon') else grupo(mao, rot=(0, 0, 0), parent=R)
    else:
        ax, ay = POSE.get(tipo, (.3, -.1))
        g = grupo(mao, rot=(ax, ay, 0), parent=R)
    ARMAS.get(tipo, W_stick)(g, L)


def mao_apoio(L, mao, R):
    off, kind = L.get('off'), L.get('offKind')
    if kind == 'scimitar':
        g = grupo(mao, rot=(.1, -2.6, 0), parent=R); W_scimitar(g, L)
    elif kind == 'glove':
        box((mao[0] + 1, mao[1], mao[2] + 1), (8, 8, 11), mat('leather', '#8a6a3a'), bevel=2.4, parent=R)
    elif off == 'axe':
        g = grupo(mao, rot=(-.1, -.3, math.pi), parent=R); W_axe(g, L)
    elif off == 'dagger':
        g = grupo(mao, rot=(.1, -2.5, 0), parent=R); W_dagger(g, L)
    elif off == 'bomb':
        sph((mao[0] + 1, mao[1], mao[2] + 3), 4.6, mat('metal', '#2a2624', rough=.5), parent=R)
        tubo([(mao[0] + 1, mao[1], mao[2] + 7.4), (mao[0] + 3, mao[1], mao[2] + 10), (mao[0] + 5, mao[1], mao[2] + 10.5)], .4, mat('cloth', '#8a7a5a'), parent=R)
        sph((mao[0] + 5.4, mao[1], mao[2] + 10.8), 1.2, mat('emit', '#ffd24a', strength=24), parent=R)
        luz_ponto((mao[0] + 5.4, mao[1], mao[2] + 11), 12, '#ffb040', parent=R)
    elif off == 'tower':
        sc = L.get('shield', L['c1'])
        g = grupo((10, 9, 42), rot=(0, 0, .35), parent=R)
        box((0, 0, 0), (2.4, 18, 46), mat('metal', sc), bevel=1.2, parent=g)
        box((1.4, 0, 0), (.6, 2.6, 40), mat('gold', L['tr']), bevel=.2, parent=g)
        box((1.4, 0, 6), (.6, 14, 2.6), mat('gold', L['tr']), bevel=.2, parent=g)
    elif off == 'round':
        g = grupo((8, 11, 45), rot=(0, math.pi / 2, .5), parent=R)
        cyl((0, 0, -1), (0, 0, 1.4), 12, 11, mat('metal', L.get('mt', METAL)), parent=g)
        torus((0, 0, 1.2), 11, .9, mat('gold', L['tr']), parent=g)
        sph((0, 0, 1.8), 4, mat('bone', '#f0ead8'), scale=(1.2, .8, .4), parent=g)
        sph((0, 0, 2.6), 1.8, mat('emit', L['fx'], strength=12), parent=g)
        luz_ponto((0, 0, 5), 10, L['fx'], parent=g)


# ---------------- costas ----------------
def costas(L, R):
    k = L.get('back')
    if k == 'cape':
        casca(61, 6, 12.5, 21, math.radians(112), math.radians(248), mat('cloth', L.get('cape', L['c2'])), xs=1.0, dobras=1.6, parent=R)
    elif k == 'halfcape':
        casca(61, 32, 12.5, 16, math.radians(120), math.radians(220), mat('cloth', L['c2']), dobras=1, parent=R)
    elif k == 'banner':
        cyl((-10, 0, 20), (-10, 0, 112), 1.2, 1.1, mat('wood', '#5a4026'), parent=R)
        sph((-10, 0, 113), 2.2, mat('gold', L['tr']), parent=R)
        pts = []
        for i in range(7):
            pts.append((-10 - i * 3.8, 0, 108 + math.sin(i * .9) * 1.6))
        for i in range(6, -1, -1):
            pts.append((-10 - i * 3.8, 0, 82 + math.sin(i * .9) * 1.6 - (5 if i == 6 else 0)))
        poly(pts, mat('cloth', L['c1']), esp=.6, parent=R)
        sph((-21, .8, 95), 3.6, mat('gold', L['tr']), scale=(1, .2, 1), parent=R)
    elif k in ('quiver', 'bigquiver'):
        n = 5 if k == 'bigquiver' else 3
        g = grupo((-10, -3, 48), rot=(.5, -.35, 0), parent=R)
        cyl((0, 0, -12), (0, 0, 12), 3.8, 3.4, mat('leather', '#5a3a22'), parent=g)
        torus((0, 0, 9), 3.6, .6, tm(L), parent=g)
        for i in range(n):
            y = -2.4 + i * 4.8 / max(1, n - 1)
            cyl((0, y, 12), (0, y, 20), .4, .4, mat('wood', '#d8ccb0'), verts=6, parent=g)
            poly([(0, y, 18), (0, y - 1.6, 22), (0, y + 1.6, 22)], mat('cloth', '#e8e0d0' if i % 2 else L['tr']), esp=.3, parent=g)
    elif k == 'trap':
        box((-12, 0, 48), (8, 12, 20), mat('leather', '#6a4a2a'), bevel=2, parent=R)
        torus((-16, 0, 32), 5, .7, mat('metal', '#9a9aa0'), rot=(0, math.pi / 2, 0), parent=R)
        for i in range(8):
            a = i / 8 * math.tau
            cyl((-16.6, math.cos(a) * 5, 32 + math.sin(a) * 5), (-16.6, math.cos(a) * 3, 32 + math.sin(a) * 3), .5, .05, mat('metal', '#c8c8cc'), verts=6, parent=R)
    elif k == 'scroll':
        g = grupo((-10, 0, 46), rot=(.6, 0, 0), parent=R)
        cyl((0, 0, -11), (0, 0, 11), 3, 3, mat('leather', L['c2']), parent=g)
        for z in (-10, 10):
            cyl((0, 0, z - 1.2), (0, 0, z + 1.2), 3.4, 3.4, tm(L), parent=g)
        cyl((0, 0, 11), (0, 0, 16), 2.2, 2.2, mat('paper', '#ece2c8'), parent=g)
    elif k == 'pack':
        box((-13, 0, 47), (9, 13, 22), mat('leather', '#7a5a3a'), bevel=2.4, parent=R)
        cyl((-13, -7, 59), (-13, 7, 59), 3.4, 3.4, mat('cloth', '#a08060'), parent=R)
        sph((-17.6, -3, 42), 2.8, mat('bone', '#e8dcc0'), scale=(.3, 1, 1), parent=R)
    elif k == 'basket':
        cyl((-13, 0, 38), (-13, 0, 55), 6, 7, mat('wood', '#a07a4a'), parent=R)
        for i in range(5):
            a = i / 5 * math.tau
            sph((-13 + math.cos(a) * 3, math.sin(a) * 3, 58), 2.2, mat('cloth', '#7aa04a'), scale=(.5, .7, 1.8), parent=R)
    elif k == 'bolts':
        box((-12, 0, 47), (6, 9, 18), mat('leather', '#4a3a2a'), bevel=1.2, parent=R)
        for y in (-2.5, 0, 2.5):
            cyl((-12, y, 56), (-12, y, 62), .5, .5, mat('wood', '#3a3028'), verts=6, parent=R)
            sph((-12, y, 62), .9, tm(L), parent=R)
    elif k == 'barrel':
        cyl((-14, 0, 42), (-14, 0, 60), 6.6, 6.6, mat('wood', '#7a5032'), parent=R)
        for z in (45, 51, 57):
            torus((-14, 0, z), 6.8, .5, mat('metal', '#3a3634'), parent=R)
        sph((-7.6, 0, 51), 1.8, mat('cloth', '#c8402a'), scale=(.3, 1, 1), parent=R)
    elif k == 'reliquary':
        box((-14, 0, 52), (9, 15, 22), mat('wood', '#4a2a1a'), bevel=1.2, parent=R)
        for z in (41.8, 62.2):
            box((-14, 0, z), (9.4, 15.4, 1.6), mat('gold', L['tr']), bevel=.3, parent=R)
        box((-9.3, 0, 52), (.6, 2, 22), mat('gold', L['tr']), bevel=.2, parent=R)
        sph((-9, 0, 54), 2.4, mat('emit', L['fx'], strength=14), parent=R)
        luz_ponto((-6, 0, 54), 14, L['fx'], parent=R)


# ---------------- efeitos (aura) e companheiros ----------------
def aura(L, R):
    a, fx = L.get('aura'), L['fx']
    em = lambda c, f=10: mat('emit', c, strength=f)
    if a == 'rage':
        luz_ponto((-8, 0, 50), 60, '#ff4a2a', raio=.3, parent=R)
        for i in range(8):
            ang = i / 8 * math.tau
            sph((math.cos(ang) * 18, math.sin(ang) * 18, 20 + (i % 4) * 14), .9, em('#ff7a3a', 18), parent=R)
    elif a == 'mist':
        for i in range(6):
            ang = i / 6 * math.tau
            sph((math.cos(ang) * 14, math.sin(ang) * 14, 2), 9, mat('emit', '#b4e696', strength=.25, alpha=.12), scale=(1, 1, .3), parent=R)
    elif a in ('embers', 'wisps', 'spirits', 'incense', 'stars', 'ash', 'sparks'):
        cor = {'embers': '#ff9a4a', 'wisps': '#c070f0', 'spirits': fx, 'incense': '#ffdc8c', 'stars': '#eef2ff', 'ash': '#c8c3b9', 'sparks': '#fff6a0'}[a]
        n = {'embers': 7, 'wisps': 4, 'spirits': 4, 'incense': 9, 'stars': 10, 'ash': 10, 'sparks': 6}[a]
        for i in range(n):
            ang = i / n * math.tau + .4
            r = 18 + (i % 3) * 3
            z = 24 + (i * 37 % 60)
            raio = {'wisps': 1.8, 'spirits': 1.8}.get(a, .8)
            sph((math.cos(ang) * r, math.sin(ang) * r, z), raio, em(cor, 2 if a == 'ash' else 14), parent=R)
        if a in ('wisps', 'spirits', 'embers'):
            luz_ponto((0, -18, 50), 18, cor, raio=.2, parent=R)
    elif a == 'frost':
        for i in range(8):
            ang = i / 8 * math.tau
            sph((math.cos(ang) * 17, math.sin(ang) * 17, 20 + i * 9), .9, em('#e1f5ff', 6), parent=R)
        luz_ponto((10, -10, 70), 12, '#a8e4ff', parent=R)
    elif a == 'rocks':
        for i in range(3):
            ang = i / 3 * math.tau + .5
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=3.4 * U, location=V((math.cos(ang) * 21, math.sin(ang) * 21, 40 + i * 6)))
            o = bpy.context.object
            o.data.materials.append(mat('stone', '#8a7a5a'))
            o.parent = R
            o.rotation_euler = (i, i * 2, i * .5)
    elif a == 'runes':
        for i in range(3):
            ang = i / 3 * math.tau + .3
            torus((math.cos(ang) * 19, math.sin(ang) * 19, 52 + i * 3), 2.4, .35, em('#70e0d0', 12), rot=(math.pi / 2, 0, ang), parent=R)
        luz_ponto((0, -16, 54), 14, '#70e0d0', parent=R)
    elif a == 'prisms':
        for i, c in enumerate(('#ff8ad8', '#8ae8ff', '#ffe88a', '#a8ff9a')):
            ang = i / 4 * math.tau
            sph((math.cos(ang) * 20, math.sin(ang) * 20, 46 + (i % 2) * 6), 2, em(c, 10), scale=(.6, .6, 1.6), parent=R)
    elif a == 'shadow':
        for i in range(5):
            ang = i / 5 * math.tau
            sph((math.cos(ang) * 8, math.sin(ang) * 8, 3 + i * 4), 6 - i * .8, mat('emit', '#28143c', strength=.6, alpha=.35), parent=R)
    elif a == 'bubbles':
        for i in range(5):
            sph((6 + (i % 2) * 3, -8 + i * 3, 36 + i * 6), 1 + i * .3, mat('glass', '#a0e65a'), parent=R)
    elif a == 'smoke':
        for i in range(3):
            sph((-2 + i * 2, 15, 56 + i * 6), 2 + i * 1.4, mat('emit', '#a09690', strength=.3, alpha=.3), parent=R)
    elif a == 'halo':
        torus((-2, 0, 76), 15, .8, em('#ffe080', 9), rot=(0, math.pi / 2, 0), parent=R)
        for i in range(12):
            ang = i / 12 * math.tau
            cyl((-2.5, math.cos(ang) * 16.5, 76 + math.sin(ang) * 16.5), (-2.5, math.cos(ang) * (19 + i % 2 * 2), 76 + math.sin(ang) * (19 + i % 2 * 2)), .5, .2, em('#ffe080', 9), verts=6, parent=R)
        luz_ponto((-6, 0, 76), 30, '#ffe080', parent=R)
    elif a == 'leaves':
        for i in range(5):
            ang = i / 5 * math.tau
            sph((math.cos(ang) * 18, math.sin(ang) * 18, 30 + i * 12), 1.4, mat('cloth', '#8cbe5a'), scale=(.4, 1, 2), rot=(i, i, 0), parent=R)
    elif a == 'notes':
        for i in range(3):
            x, y, z = 12, -10 + i * 6, 64 + i * 10
            sph((x, y, z), 1.6, em('#a0c8ff', 8), scale=(1, 1, .7), parent=R)
            cyl((x, y + 1.4, z), (x, y + 1.4, z + 7), .3, .3, em('#a0c8ff', 8), verts=6, parent=R)
    elif a == 'glyph':
        torus((0, 0, .5), 22, .7, em(fx, 8), parent=R)
        torus((0, 0, .5), 27, .4, em(fx, 6), parent=R)
        luz_ponto((0, 0, 4), 14, fx, parent=R)
    elif a == 'raven':
        corvo = mat('cloth', '#1e1c24')
        sph((-4, 10, 102), 3.4, corvo, scale=(1.4, .8, .8), parent=R)
        poly([(-4, 10, 102), (-10, 22, 108), (-2, 12, 103)], corvo, esp=.5, parent=R)
        poly([(-4, 10, 102), (-10, -2, 108), (-2, 8, 103)], corvo, esp=.5, parent=R)
        sph((.4, 10, 103), .7, mat('emit', L['tr'], strength=10), parent=R)
    elif a == 'chains':
        elo = mat('metal', '#8a8a90')
        for i in range(5):
            torus((3, 15, 36 - i * 2.6), 1.4, .45, elo, rot=(0, 0, (i % 2) * math.pi / 2), parent=R)
    elif a == 'wind':
        for z in (6, 14):
            torus((0, 0, z), 20, .5, mat('emit', fx, strength=2, alpha=.35), scale=(1, 1, .3), parent=R)
    elif a == 'gears':
        for i in range(3):
            ang = i / 3 * math.tau + .4
            g = grupo((math.cos(ang) * 20, math.sin(ang) * 20, 48 + i * 5), rot=(math.pi / 2, 0, ang), parent=R)
            cyl((0, 0, -.6), (0, 0, .6), 3, 3, mat('gold', L['tr']), parent=g)
            for k in range(8):
                b = k / 8 * math.tau
                box((math.cos(b) * 3.4, math.sin(b) * 3.4, 0), (1.4, 1.4, 1.2), mat('gold', L['tr']), rot=(0, 0, b), bevel=.1, parent=g)
    elif a == 'mirrors':
        for i in range(3):
            ang = i / 3 * math.tau + .2
            sph((math.cos(ang) * 21, math.sin(ang) * 21, 46 + i * 4), 3, mat('metal', '#dce8ff', rough=.02), scale=(.2, .7, 1.4), rot=(0, 0, ang), parent=R)
    elif a == 'calm':
        for r in (20, 26):
            torus((0, 0, .5), r, .35, mat('emit', fx, strength=4), parent=R)
    elif a == 'droplets':
        for i in range(6):
            ang = i / 6 * math.tau
            sph((math.cos(ang) * 16, math.sin(ang) * 16, 20 + i * 10), 1, mat('glass', '#a0e6f5'), scale=(1, 1, 1.5), parent=R)


def companheiro(L, R):
    pet = L.get('pet')
    if pet == 'wolf':
        lobo = mat('fur', '#8d8a86')
        g = grupo((4, 26, 0), rot=(0, 0, -.2), parent=R)
        sph((0, 0, 20), 9, lobo, scale=(1.5, .75, .8), parent=g)
        sph((12, 0, 26), 6.4, lobo, parent=g)
        sph((18, 0, 24), 3.6, lobo, scale=(1.4, .8, .7), parent=g)
        sph((22.4, 0, 24.4), 1.2, mat('gloss', '#1a1410'), parent=g)
        for y in (-2.6, 2.6):
            cyl((10, y, 31), (9, y, 37), 2, .2, lobo, parent=g)
            sph((15.6, y * 1.1, 28), .8, mat('emit', '#ffd24a', strength=8), parent=g)
        for x in (-8, 8):
            for y in (-4, 4):
                caps((x, y, 14), (x + 1, y, 1), 2.1, lobo, parent=g)
        tubo([(-13, 0, 22), (-20, 0, 24), (-24, 0, 18)], 2.6, lobo, radii=[1, .8, .3], parent=g)
    elif pet == 'swarm':
        for i in range(10):
            ang = i / 10 * math.tau
            sph((math.cos(ang) * 22, math.sin(ang) * 22, 62 + (i % 3) * 8), .9, mat('emit', '#ffcf7a', strength=24), parent=R)
        luz_ponto((0, -20, 70), 20, '#ffb04a', raio=.3, parent=R)
    elif pet == 'hawk':
        ave = mat('cloth', '#7a5a3a')
        g = grupo((4, 15, 52), parent=R)
        sph((0, 0, 4), 3.4, ave, scale=(1, .8, 1.5), parent=g)
        sph((1.6, 0, 9.4), 2.4, mat('cloth', '#5a3a22'), parent=g)
        cyl((3.6, 0, 9.4), (6.4, 0, 8.4), .8, .05, mat('bone', '#e0a030'), parent=g)
        sph((3, 1.2, 10), .5, mat('emit', '#ffd24a', strength=8), parent=g)
        poly([(0, 1, 6), (-6, 8, 2), (-10, 9, -2), (-2, 2, 2)], ave, esp=.6, parent=g)
        poly([(0, -1, 6), (-6, -8, 2), (-10, -9, -2), (-2, -2, 2)], ave, esp=.6, parent=g)


def construir(L, B, mapa=False):
    """Monta o herói completo e devolve a raiz (girar a raiz em Z muda a vista).
    mapa=True é a versão do herói no mapa do jogo: sem aura e sem companheiro (o jogo desenha os dois em código) e com a
    lanterna no quadril direito, um pouco atrás, onde o desenho do jogo a mostra (no lado esquerdo ela some atrás do corpo nessa vista)."""
    R = raiz('heroi')
    costas(L, R)
    pernas(L, B, R)
    tronco(L, B, R)
    md, me = bracos(L, B, R)
    with parte(R, 'cabeca', (0, 0, 64), amp=.04, fase=.25, atk=.12):
        CABECAS.get(L.get('head', 'hood'), H_hood)(L, R)
    if not L.get('semLanterna'):   # cavaleiros inimigos usam o mesmo kit, sem a lanterna do Portador
        lanterna(R, (-7, -16.5, 27) if mapa else (-2, 14.5, 27))
    with parte(R, 'braco', OMBRO[-1], **braco_anim(L, -1)):   # a arma acompanha o braço direito
        arma(L, md, R)
    with parte(R, 'braco', OMBRO[1], **braco_anim(L, 1)):     # escudo ou arma da outra mão acompanha o esquerdo
        mao_apoio(L, me, R)
    if not mapa:
        aura(L, R)
        companheiro(L, R)
    return R
