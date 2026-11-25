# Remodelagem dark fantasy dos monstros do Brasalume (2026-11-25): anatomia de verdade no lugar de membros-salsicha.
# Rascunho da amostra (quadrúpedes e cabeça do lobo); aplicar() troca as funções do kit_monstros.
import math
from mathutils import Vector
from kit_base import mat, shade, mix, sph, cyl, caps, box, torus, tubo, poly, luz_ponto, U, parte
import kit_monstros as KM
from kit_monstros import pelo, olhos, tufo, tubo_malha, _sem_acento, pele, CAB_FERA


def _membro(R, pts, raios, m, parent=None):
    """Membro em segmentos cônicos com juntas arredondadas (ossos e músculos que afinam)."""
    objs = []
    for (a, b), (ra, rb) in zip(zip(pts, pts[1:]), zip(raios, raios[1:])):
        objs.append(cyl(a, b, ra, rb, m, parent=R))
    for p, r in zip(pts, raios):
        sph(p, r, m, parent=R, seg=16, ring=10)
    return objs


def quadrupede(R, corpo, escuro, comp=1.0, alt=1.0, pesc=1.0, perna=3.6, pelagem=None):
    """Quadrúpede predador: peito fundo, cintura recolhida, garupa e patas com jarrete. Devolve a posição da cabeça."""
    zc = 36 * alt
    c = comp
    peito = sph((13 * c, 0, zc + 1), 15, corpo, scale=(1.15, .84, 1.12), parent=R)          # peito fundo (desce até ~z 20)
    cernelha = sph((7 * c, 0, zc + 11), 9.5, corpo, scale=(1.5, .82, .6), parent=R)       # cernelha (o alto das costas)
    cintura = sph((-3 * c, 0, zc + 4), 10, corpo, scale=(1.5, .78, .82), parent=R)        # cintura recolhida
    garupa = sph((-15 * c, 0, zc + 4), 11.5, corpo, scale=(1.1, .86, .95), parent=R)     # garupa
    cab = (33 * c, 0, zc + 12 * pesc)   # cabeça à frente e baixa: postura de caça
    pescoco = cyl((15 * c, 0, zc + 6), (cab[0] - 4, 0, cab[2] - 2), 10.5, 7, corpo, parent=R)
    if pelagem:
        P = pelagem
        Lp, nev = P['comp'], P.get('nevoa', False)
        pelo(peito, P['cor'], comp=Lp * (1.25 if P.get('juba') else 1.1), n=850, pente=(-1, 0, -.6), nevoa=nev)
        pelo(cernelha, P['cor'], comp=Lp * (1.5 if P.get('juba') else 1), n=380, pente=(-1, 0, .35), nevoa=nev, solto=1.3)
        pelo(cintura, P['cor'], comp=Lp * .7, n=500, pente=(-1, 0, -.3), nevoa=nev)
        pelo(garupa, P['cor'], comp=Lp, n=600, pente=(-1, 0, -.45), nevoa=nev)
        pelo(pescoco, P['cor'], comp=Lp * (1.5 if P.get('juba') else 1.15), n=520, pente=(-1, 0, -.4), nevoa=nev, solto=1.3)
    unha = mat('bone', '#2a221c')
    for frente in (True, False):
        x = 14 * c if frente else -15 * c
        for y in (-7.5, 7.5):
            fase = .5 if frente != (y > 0) else 0   # patas em diagonal andam juntas
            with parte(R, 'perna', (x, y, zc - 3), fase=fase, amp=.38):
                if frente:
                    sph((x - 1, y * 1.02, zc + 1), 6.5, corpo, scale=(.85, .5, 1.45), parent=R)   # escápula
                    pts = [(x, y, zc - 3), (x - 3, y, zc * .56), (x - 1, y, 8), (x + 1.5, y, 3)]
                    raios = [perna + 1.8, perna + .6, perna * .72, perna * .55]
                else:
                    sph((x + 1, y * 1.02, zc - 5), 8.5, corpo, scale=(1.15, .62, 1.3), parent=R)   # coxa musculosa
                    pts = [(x + 1, y, zc - 4), (x + 5, y, zc * .5), (x - 4, y, zc * .3), (x - 1.5, y, 3)]   # joelho para a frente, jarrete para trás
                    raios = [perna + 2.2, perna + .4, perna * .62, perna * .52]
                segs = _membro(R, pts, raios, escuro if not frente else corpo)
                pa = pts[-1]
                sph((pa[0] + 2, y, 2.1), perna * 1.05, escuro, scale=(1.55, 1, .55), parent=R)   # pata
                for j in range(4):   # dedos e garras
                    yy = y + (j - 1.5) * perna * .5
                    sph((pa[0] + 4.2, yy, 1.8), perna * .38, escuro, parent=R)
                    cyl((pa[0] + 4.6, yy, 2), (pa[0] + 6.8, yy * 1.01, .3), .55, .08, unha, parent=R)
                if pelagem:
                    pelo(segs[0], pelagem['cor'], comp=pelagem['comp'] * .45, n=180, pente=(0, 0, -1), nevoa=pelagem.get('nevoa', False))
    return cab


def cabeca_lobo(R, cab, corpo, escuro, cor_pelo, foc, nevoa, olho, lince=False):
    """Crânio em cunha, testa marcada, focinho que afina, mandíbula separada (abre no ataque) e presas."""
    x, _, z = cab
    osso = mat('bone', '#efe4c8')
    gengiva = mat('skin', '#3a1418')
    cranio = sph((x, 0, z), 10.4, corpo, scale=(1.2, .92, .84), parent=R)
    pelo(cranio, cor_pelo, comp=1.3, n=420, pente=(-1, 0, .25), nevoa=nevoa)
    for y in (-1, 1):   # arcada sobre os olhos e maçãs
        sph((x + 5.5, y * 3.6, z + 3.2), 2.6, corpo, scale=(1.4, .9, .55), rot=(0, -.25, 0), parent=R)
        bochecha = sph((x + 1, y * 6.2, z - 3), 4.6, corpo, scale=(1.1, .8, .9), parent=R)
        pelo(bochecha, cor_pelo, comp=2.4 if not lince else 3, n=120, pente=(-1, y * .8, -.6), nevoa=nevoa, solto=1.4)
    # focinho: largo na base, fino e um pouco caído na ponta
    cyl((x + 5, 0, z - .5), (x + 6 + foc, 0, z - 3.4), 6.2, 3.0, corpo, parent=R)
    sph((x + 6 + foc, 0, z - 3.2), 2.7, corpo, scale=(1, 1, .8), parent=R)
    sph((x + 7.6 + foc, 0, z - 2.4), 1.7, mat('gloss', '#100c0a'), scale=(1, 1.2, .8), parent=R)   # trufa
    for y in (-1, 1):   # beiço escuro e presas de cima
        tubo([(x + 3, y * 4.6, z - 4.6), (x + 4 + foc * .6, y * 3.2, z - 5.6), (x + 6 + foc, y * 1.6, z - 5)], .55, gengiva, parent=R)
        cyl((x + 4 + foc * .75, y * 2.4, z - 5.2), (x + 4.4 + foc * .75, y * 2.2, z - 8.6), .8, .05, osso, parent=R)
        for k in range(3):
            cyl((x + 3 + k * 2, y * (3.6 - k * .4), z - 5.2), (x + 3 + k * 2, y * (3.6 - k * .4), z - 6.4), .45, .05, osso, parent=R)
    with parte(R, 'boca', (x + 1, 0, z - 4.5), amp=.08, atk=.5):   # mandíbula
        cyl((x + 1, 0, z - 5.2), (x + 4 + foc, 0, z - 7), 3.6, 1.6, escuro, parent=R)
        tubo([(x + 2, 0, z - 4.8), (x + 3 + foc, 0, z - 5.8)], 1.2, gengiva, parent=R)   # língua
        for y in (-1, 1):
            cyl((x + 3 + foc * .7, y * 1.8, z - 5.8), (x + 3.2 + foc * .7, y * 1.7, z - 3.4), .7, .05, osso, parent=R)
    for y in (-1, 1):   # orelhas em ponta, inclinadas para trás
        cyl((x - 1, y * 4.8, z + 5), (x - 4, y * 6.8, z + 15), 3.6, .2, escuro, parent=R)
        cyl((x - .4, y * 4.6, z + 5.4), (x - 3.2, y * 6.4, z + 13), 2.2, .15, mat('skin', '#5a3a3a'), parent=R)
        if lince:
            cyl((x - 4, y * 6.8, z + 15), (x - 4.6, y * 7.4, z + 20), .5, .05, mat('fur', '#1a1410'), parent=R)
    olhos(R, (x + 6.4, 0, z + 1.4), 1.3, cor=olho, sep=7.2)


def F_beast(R, nome, cor, t):
    n = _sem_acento(nome)
    if any(k in n for k in ('escorpiao', 'escavador', 'javali', 'cervo')):
        return _F_beast_antigo(R, nome, cor, t)
    nevoa = t == 'sombra'
    if t in ('gelo', 'vidro', 'sombra'):
        cor_pelo = mix(cor, '#e8f6ff', .3) if not nevoa else cor
        corpo = mat('fur', cor_pelo)
    else:
        cor_pelo = cor
        corpo = pele(cor, t, 'fur')
    escuro = mat('fur', shade(cor_pelo, -.3))
    lince = 'lince' in n
    alfa = 'alfa' in n or 'ancestral' in n
    cab = quadrupede(R, corpo, escuro, comp=1.0, alt=1.0 if not alfa else 1.06, pesc=1.0, perna=3.0 if not alfa else 3.5,
                     pelagem=dict(cor=cor_pelo, comp=1.8 if lince else 2.3 if not alfa else 2.8, nevoa=nevoa, juba=not lince))
    pc = (cab[0] - 8, 0, cab[2] - 4)
    olho = '#a8e4ff' if t in ('gelo', 'sombra') else '#ffd98a'
    with parte(R, 'cabeca', pc, **CAB_FERA):
        cabeca_lobo(R, cab, corpo, escuro, cor_pelo, 12 if not lince else 6, nevoa, olho, lince)
    pelo_m = mat('fur', shade(cor_pelo, -.12))
    if not lince:
        with parte(R, 'cauda', (-26, 0, 40), amp=.3):
            for seg in tubo_malha([(-26, 0, 40), (-35, 0, 39), (-43, 0, 31), (-47, 0, 22)], 3.4, pelo_m, radii=[.8, 1, .8, .25], parent=R):
                pelo(seg, cor_pelo, comp=4 if not alfa else 4.8, n=200, pente=(-1, 0, -.5), nevoa=nevoa, solto=1.4)
    else:
        with parte(R, 'cauda', (-26, 0, 40), amp=.4):
            for seg in tubo_malha([(-26, 0, 40), (-31, 0, 43)], 2.4, pelo_m, radii=[1, .6], parent=R):
                pelo(seg, cor_pelo, comp=2, n=160, pente=(-1, 0, .4))
            sph((-31.6, 0, 43.4), 2.6, mat('fur', '#1a1410'), parent=R)
        for i in range(10):
            a = i * 1.7
            sph((-14 + i * 3.6, math.cos(a) * 11.4, 40 + math.sin(a) * 5), 2.2, mat('fur', shade(cor_pelo, -.5)), scale=(1, 1, .6), parent=R)
    if alfa:   # cicatriz no focinho e cristas de pelo eriçado nas costas
        with parte(R, 'cabeca', pc, **CAB_FERA):
            box((cab[0] + 5, -5.6, cab[2] + 2), (6, .6, 1), mat('skin', '#c87a7a'), rot=(0, .4, 0), bevel=.2, parent=R)
        for i in range(7):
            tufo((12 - i * 5, 0, 50 - abs(i - 2) * 1.2), (-4, 0, 6), pelo_m, r=1.8, parent=R)
    if t == 'gelo':
        g = mat('glass', '#d8f2ff')
        for i in range(3):
            cyl((6 - i * 9, 0, 49), (5 - i * 9, (i % 2 - .5) * 3, 56), 1.8, .1, g, parent=R)
    if t == 'sombra':
        luz_ponto((10, 0, 40), 30, '#c8dcff', raio=.4, parent=R)
    return 70 if not alfa else 76


_F_beast_antigo = KM.F_beast


def aplicar():
    KM.quadrupede = quadrupede
    KM.FAMILIAS['beast'] = F_beast
