# Texturas de chão do Brasalume: um ladrilho sem emenda por cenário, visto de cima e renderizado no Blender com materiais
# procedurais. O plano é deslocado pela altura do material (relevo de verdade), então pedras, tufos de capim, lajes e
# ondulações fazem sombra com o sol e escurecem nas frestas. Para não ter emenda, as coordenadas viram um toro em 4D
# (vetor + W) e o ruído é 4D: a borda da direita continua na da esquerda e a de cima na de baixo. O plano passa um pouco
# do quadro para que as sombras que vêm de fora do ladrilho também apareçam. As cores de base são as do chão de cada
# cenário no jogo (GROUND). O integrar.py projeta o ladrilho no ângulo isométrico e acerta o brilho pela cor do chão do
# jogo; sem a imagem, o chão continua pintado em código.
import os
import math
import bpy
from kit_base import hex_lin, shade, mix

LADRILHOS = 4     # o ladrilho cobre 4 x 4 casas do mapa do jogo (1 casa = 1 metro aqui)
MARGEM = .5       # o plano passa do quadro por esta margem (metros), para as sombras que vêm de fora do ladrilho
RELEVO = .045     # deslocamento do relevo, em metros, quando a altura do material vale 1
NEVE = (.3, .36)   # faixa do valor 'neve' em que a neve cobre a rocha (medida com a sonda)
SONDAS = {}       # valores guardados com sonda(); BRASALUME_SONDA=nome troca o material por esse valor em cinza


def sonda(nome, sock):
    """Guarda um valor do material para medir: com BRASALUME_SONDA=nome a imagem sai com esse valor em cinza."""
    SONDAS[nome] = sock
    return sock


def E(por_casa):
    """Escala do ruído 4D para ter 'por_casa' detalhes em cada casa do mapa (no toro, a largura do ladrilho vale 2π)."""
    return por_casa * LADRILHOS / math.tau


class Nos:
    """Atalhos para montar a árvore de nós do material (números e cores '#rrggbb' entram como valores fixos)."""

    def __init__(self, m):
        self.nt = m.node_tree
        self.N = self.nt.nodes
        self.L = self.nt.links
        self.casa = 1.0   # tamanho de uma casa do mapa nas coordenadas do objeto

    def no(self, tipo, **props):
        n = self.N.new(tipo)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def liga(self, a, b):
        self.L.new(a, b)

    def _entrada(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, str):
            sock.default_value = hex_lin(v)
        else:
            self.liga(v, sock)

    def math(self, op, a, b=None, c=None, valor=None):
        n = self.no('ShaderNodeMath', operation=op)
        self._entrada(n.inputs[0], a)
        if b is not None:
            self._entrada(n.inputs[1], b)
        if valor is not None:
            n.inputs[1].default_value = valor
        if c is not None:
            self._entrada(n.inputs[2], c)
        return n.outputs[0]

    def soma(self, *pares):
        """Soma ponderada: soma((a, .5), (b, .3)) = a * .5 + b * .3 (a pode ser um número)."""
        total = None
        for sock, peso in pares:
            total = self.math('MULTIPLY', sock, peso) if total is None else self.math('MULTIPLY_ADD', sock, peso, total)
        return total

    def lerp(self, f, a, b):
        """Valor que vai de a (f = 0) a b (f = 1)."""
        return self.math('MULTIPLY_ADD', self.math('SUBTRACT', b, a), f, a)

    def faixa(self, valor, de0, de1, para0, para1):
        n = self.no('ShaderNodeMapRange')
        n.clamp = True
        self._entrada(n.inputs['Value'], valor)
        n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = de0, de1
        n.inputs['To Min'].default_value, n.inputs['To Max'].default_value = para0, para1
        return n.outputs['Result']

    def canal(self, cor, i):
        """Um canal (0 = R, 1 = G, 2 = B) de uma cor: as cores das células do Voronoi são sorteios independentes."""
        n = self.no('ShaderNodeSeparateColor')
        self.liga(cor, n.inputs[0])
        return n.outputs[i]

    def mistura(self, fator, a, b, modo='MIX'):
        n = self.no('ShaderNodeMix', data_type='RGBA', blend_type=modo)
        self._entrada(n.inputs[0], fator)
        self._entrada(n.inputs[6], a)
        self._entrada(n.inputs[7], b)
        return n.outputs[2]


def toro(T):
    """(u, v) do plano (0..1 dentro do quadro, e repete fora dele) viram (cos u, sin u, cos v) e W = sin v: tudo que é
    calculado a partir disso repete sem emenda. Devolve (vetor, W, u, v); u e v lineares servem para padrões que repetem
    um número inteiro de vezes."""
    tc = T.no('ShaderNodeTexCoord')
    sep = T.no('ShaderNodeSeparateXYZ')
    T.liga(tc.outputs['Object'], sep.inputs[0])
    u = T.math('MULTIPLY_ADD', sep.outputs['X'], 1 / (LADRILHOS * T.casa), .5)
    v = T.math('MULTIPLY_ADD', sep.outputs['Y'], 1 / (LADRILHOS * T.casa), .5)
    au, av = T.math('MULTIPLY', u, math.tau), T.math('MULTIPLY', v, math.tau)
    comb = T.no('ShaderNodeCombineXYZ')
    T.liga(T.math('COSINE', au), comb.inputs[0])
    T.liga(T.math('SINE', au), comb.inputs[1])
    T.liga(T.math('COSINE', av), comb.inputs[2])
    return comb.outputs[0], T.math('SINE', av), u, v


def torcer(T, vw, por_casa, forca, detalhe=2.0):
    """Coordenadas torcidas por um ruído (continuam sem emenda): células e manchas ficam com contorno orgânico."""
    n = T.no('ShaderNodeTexNoise', noise_dimensions='4D')
    T.liga(vw[0], n.inputs['Vector'])
    T.liga(vw[1], n.inputs['W'])
    n.inputs['Scale'].default_value = E(por_casa)
    n.inputs['Detail'].default_value = detalhe
    d = T.no('ShaderNodeVectorMath', operation='MULTIPLY_ADD')
    T.liga(n.outputs['Color'], d.inputs[0])
    d.inputs[1].default_value = (forca, forca, forca)
    T.liga(vw[0], d.inputs[2])
    return d.outputs[0], T.math('MULTIPLY_ADD', n.outputs['Fac'], forca, vw[1]), vw[2], vw[3]


def ruido(T, vw, por_casa, detalhe=4.0, aspereza=.55, distorcao=0.0):
    n = T.no('ShaderNodeTexNoise', noise_dimensions='4D')
    T.liga(vw[0], n.inputs['Vector'])
    T.liga(vw[1], n.inputs['W'])
    n.inputs['Scale'].default_value = E(por_casa)
    n.inputs['Detail'].default_value = detalhe
    n.inputs['Roughness'].default_value = aspereza
    n.inputs['Distortion'].default_value = distorcao
    return n.outputs['Fac']


def vor(T, vw, por_casa, modo='F1', aleatorio=1.0):
    n = T.no('ShaderNodeTexVoronoi', voronoi_dimensions='4D', feature=modo)
    T.liga(vw[0], n.inputs['Vector'])
    T.liga(vw[1], n.inputs['W'])
    n.inputs['Scale'].default_value = E(por_casa)
    n.inputs['Randomness'].default_value = aleatorio
    return n


def bordas(T, vw, por_casa, aleatorio=1.0):
    """Distância até a borda da célula: perto de 0 nas rachaduras."""
    return vor(T, vw, por_casa, 'DISTANCE_TO_EDGE', aleatorio).outputs['Distance']


def pedras(T, vw, por_casa, densidade, raio=.4, aleatorio=1.0):
    """Pedras (ou tufos, folhas, flores) soltas: cada célula do Voronoi tem uma no meio, ou não (densidade = parte das
    células que têm). O tamanho varia sozinho, porque as sementes ficam em 4D e cada uma está a uma distância do plano.
    Devolve (máscara, cúpula 0..1, tom 0..1 de cada uma, sombra de contato em volta)."""
    n = vor(T, vw, por_casa, 'F1', aleatorio)
    d = n.outputs['Distance']
    tem = T.math('LESS_THAN', T.canal(n.outputs['Color'], 0), densidade)
    cupula = T.math('MULTIPLY', T.math('POWER', T.faixa(d, 0, raio, 1, 0), .55), tem)
    mascara = T.math('MULTIPLY', T.faixa(d, raio * .78, raio, 1, 0), tem)
    contato = T.math('MULTIPLY', T.faixa(d, raio, raio * 1.5, 1, 0), tem)
    return mascara, cupula, T.canal(n.outputs['Color'], 1), contato


def lajes(T, largura, altura_linha, desloca=.5, junta=.035, gasto=None):
    """Lajes alinhadas às casas do mapa (largura e altura da fileira em casas; 4 / largura e 4 / altura inteiros, e par
    quando há deslocamento entre as fileiras). Calculadas aqui, e não com o nó Brick, para que o sorteio de cada laje
    também repita no ladrilho. gasto = (ruído, força) lasca as bordas.
    Devolve (junta 0..1, distância até a borda em casas, e três sorteios 0..1 por laje)."""
    tc = T.no('ShaderNodeTexCoord')
    sep = T.no('ShaderNodeSeparateXYZ')
    T.liga(tc.outputs['Object'], sep.inputs[0])
    x = T.math('MULTIPLY_ADD', sep.outputs['X'], 1 / T.casa, LADRILHOS / 2)
    y = T.math('MULTIPLY_ADD', sep.outputs['Y'], 1 / T.casa, LADRILHOS / 2)
    yl = T.math('DIVIDE', y, altura_linha)
    linha, fy = T.math('FLOOR', yl), T.math('FRACT', yl)
    impar = T.math('MODULO', T.math('ADD', linha, 120), 2)      # somar 120 evita resto negativo fora do quadro
    xl = T.math('MULTIPLY_ADD', impar, desloca, T.math('DIVIDE', x, largura))
    col, fx = T.math('FLOOR', xl), T.math('FRACT', xl)
    bx = T.math('MULTIPLY', T.math('MINIMUM', fx, T.math('SUBTRACT', 1, fx)), largura)
    by = T.math('MULTIPLY', T.math('MINIMUM', fy, T.math('SUBTRACT', 1, fy)), altura_linha)
    borda = T.math('MINIMUM', bx, by)
    if gasto is not None:
        borda = T.math('MULTIPLY_ADD', T.math('SUBTRACT', gasto[0], .5), gasto[1], borda)
    jt = T.faixa(borda, junta * .35, junta, 1, 0)
    nc, nl = round(LADRILHOS / largura), round(LADRILHOS / altura_linha)
    cid = T.math('MODULO', T.math('ADD', col, nc * 40), nc)
    lid = T.math('MODULO', T.math('ADD', linha, nl * 40), nl)

    def sorteio(a, b):
        s = T.math('SINE', T.math('MULTIPLY_ADD', cid, a, T.math('MULTIPLY', lid, b)))
        return T.math('FRACT', T.math('MULTIPLY', s, 43758.5453))
    return jt, borda, sorteio(12.9898, 78.233), sorteio(39.3468, 11.1351), sorteio(73.1563, 52.2357)


def pedras_quinas(T, vw, por_casa, densidade, folga=.06, chanfro=.08, aleatorio=1.0):
    """Pedras de quinas: as células do Voronoi encolhidas pela folga (algumas ficam vazias), com a borda chanfrada.
    Com as coordenadas torcidas, as quinas ficam irregulares. Devolve (máscara, altura 0..1, tom 0..1 de cada uma)."""
    f1 = vor(T, vw, por_casa, 'F1', aleatorio)
    de = bordas(T, vw, por_casa, aleatorio)
    tem = T.math('LESS_THAN', T.canal(f1.outputs['Color'], 0), densidade)
    forma = T.math('MULTIPLY', T.faixa(de, folga, folga + chanfro, 0, 1), tem)
    mascara = T.math('MULTIPLY', T.faixa(de, folga, folga + .015, 0, 1), tem)
    return mascara, forma, T.canal(f1.outputs['Color'], 1)


def rachaduras(T, vw, por_casa, largura, quanto=.5):
    """Rachaduras em trechos soltos: bordas de células de contorno torto que só aparecem onde um ruído deixa
    (quanto = parte da rede que aparece, mais ou menos)."""
    d = bordas(T, torcer(T, vw, por_casa * 2.5, .1), por_casa)
    corte = .62 - quanto * .24
    return T.math('MULTIPLY', T.faixa(d, 0, largura, 1, 0), T.faixa(ruido(T, vw, por_casa * .8, 2, .5), corte, corte + .06, 0, 1))


def tom_pedra(T, tom, escura, clara, grao, forma=None):
    """Cor de pedra: o tom sorteado de cada uma entre escura e clara, com manchas finas e a beirada mais escura."""
    c = T.mistura(tom, escura, clara)
    c = T.mistura(1.0, c, T.faixa(grao, .25, .75, .8, 1.15), 'MULTIPLY')
    if forma is not None:
        c = T.mistura(1.0, c, T.faixa(forma, 0, 1, .72, 1), 'MULTIPLY')
    return c


# ---------------------------------------------------------------------------------------------------------------
# chão de cada cenário: devolve (cor, altura ~0..1, aspereza, emissão ou None)

def _capim(T, vw, cores, decor, largo, medio, grao):
    """Mato baixo: tufos e fios com o fundo escuro e as pontas claras, manchas secas, terra com pedrinhas e folhas."""
    c0, c1 = cores
    seco = {'trees': '#6f6a3c', 'reeds': '#5c6a3c', 'dawn': '#8c86a6', 'pale': '#8e958a'}.get(decor, '#6f6a3c')
    fundo = shade(mix(c0, '#0e1719', .4), -.25)
    relva = ruido(T, torcer(T, vw, 2, .12), 6, 8, .68, distorcao=.5)
    fio = ruido(T, vw, 24, 3, .6, distorcao=2.0)
    alt = T.soma((relva, .7), (fio, .35))
    meio = T.mistura(T.faixa(largo, .35, .65, 0, 1), c0, c1)
    meio = T.mistura(T.faixa(medio, .5, .65, 0, .45), meio, mix(c1, seco, .45))
    cor = T.mistura(T.faixa(alt, .38, .6, 0, 1), fundo, meio)
    cor = T.mistura(T.faixa(alt, .58, .72, 0, .6), cor, mix(shade(c1, .15), seco, .35))
    # terra aparecendo, com pedrinhas de quina
    terra = T.faixa(sonda('terra', T.soma((ruido(T, vw, 2.2, 3, .5), 1), (grao, .14))), .64, .68, 0, 1)
    cor_terra = shade(mix(c0, '#4a4430', .65), -.05)
    pm, pf, pt = pedras_quinas(T, torcer(T, vw, 25, .06), 10, .45, folga=.14, chanfro=.08)
    solo = T.mistura(T.faixa(grao, .3, .7, 0, 1), shade(cor_terra, -.18), shade(cor_terra, .1))
    solo = T.mistura(pm, solo, tom_pedra(T, pt, mix(cor_terra, '#5e5a52', .55), mix(cor_terra, '#8a857a', .55), grao, pf))
    cor = T.mistura(terra, cor, solo)
    alt = T.lerp(terra, alt, T.soma((pf, .3), (grao, .12), (relva, .15)))
    # folhas caídas, juntas pelo vento
    fm, _, ft, _ = pedras(T, torcer(T, vw, 3, .06), 8, .3, raio=.24)
    fm = T.math('MULTIPLY', fm, T.faixa(ruido(T, vw, 1.1, 2, .5), .5, .62, 0, 1))
    cor_folha = {'trees': '#7a5a2e', 'reeds': '#66703a', 'dawn': '#b08aa4', 'pale': '#9a998a'}.get(decor, '#7a5a2e')
    cor = T.mistura(fm, cor, T.mistura(ft, shade(cor_folha, -.22), shade(cor_folha, .1)))
    alt = T.math('MULTIPLY_ADD', fm, .05, alt)
    rug = .92
    if decor == 'trees':     # Clareira das Cinzas: cinza velha entre o capim
        cinza = T.faixa(T.soma((ruido(T, vw, 2, 3, .55), 1), (grao, .1)), .62, .72, 0, .55)
        cor = T.mistura(cinza, cor, T.mistura(T.faixa(grao, .3, .7, 0, 1), '#3e3c39', '#5a5752'))
    if decor == 'reeds':     # brejo: lama molhada e poças de água parada
        np_ = sonda('poca', T.soma((ruido(T, vw, 2, 3, .5), 1), (grao, .04)))
        lama = T.faixa(np_, .6, .625, 0, 1)
        poca = T.faixa(np_, .625, .64, 0, 1)
        cor = T.mistura(T.math('MULTIPLY', lama, .7), cor, shade(mix(c0, '#2a2418', .5), -.3))
        cor = T.mistura(poca, cor, shade(mix(c0, '#0c1416', .4), -.12))
        rug = T.math('MINIMUM', T.faixa(lama, 0, 1, .92, .16), T.faixa(poca, 0, 1, 1, .05))
        alt = T.lerp(poca, T.lerp(lama, alt, T.math('MULTIPLY', alt, .45)), .14)
    if decor == 'dawn':      # flores miúdas em moitas
        flm, _, flt, _ = pedras(T, torcer(T, vw, 4, .05), 12, .5, raio=.2)
        flm = T.math('MULTIPLY', flm, T.faixa(ruido(T, vw, 1.3, 2, .5), .55, .64, 0, 1))
        cor = T.mistura(flm, cor, T.mistura(flt, '#e6d2e6', '#f4e6c8'))
        alt = T.math('MULTIPLY_ADD', flm, .08, alt)
    return cor, alt, rug, None


def _pedreira(T, vw, cores, largo, medio, grao):
    """Pedreira: terra batida com poeira, cascalho de quina, pedras soltas e rocha aflorando com rachaduras."""
    c0, c1 = cores
    solo = T.mistura(T.faixa(largo, .3, .7, 0, 1), shade(c0, -.04), shade(c1, .04))
    solo = T.mistura(T.faixa(medio, .45, .7, 0, .55), solo, mix(c1, '#8f887c', .35))
    solo = T.mistura(1.0, solo, T.faixa(grao, .25, .75, .84, 1.12), 'MULTIPLY')
    gm, gf, gt = pedras_quinas(T, torcer(T, vw, 30, .05), 13, .6, folga=.08, chanfro=.1)
    cor = T.mistura(gm, solo, tom_pedra(T, gt, shade(mix(c0, '#66625c', .5), -.12), shade(mix(c1, '#a19b90', .45), .06), grao, gf))
    alt = T.soma((medio, .14), (grao, .1), (gf, .22))
    pm, pf, pt = pedras_quinas(T, torcer(T, vw, 7, .12), 3, .32, folga=.14, chanfro=.14)
    cor = T.mistura(pm, cor, tom_pedra(T, pt, shade(mix(c0, '#5c5852', .4), -.06), shade(mix(c1, '#8e887e', .45), .1), ruido(T, vw, 9, 4, .6), pf))
    alt = T.soma((alt, 1), (pf, .6), (T.math('MULTIPLY', pt, pf), .25))
    laje = T.faixa(sonda('laje', T.soma((ruido(T, vw, 1.8, 3, .5), 1), (grao, .08))), .625, .655, 0, 1)
    racha = rachaduras(T, vw, 1.8, .02, .55)
    rocha = T.mistura(T.faixa(medio, .3, .7, 0, 1), shade(c1, .02), shade(mix(c1, '#9a948a', .3), .1))
    rocha = T.mistura(1.0, rocha, T.faixa(grao, .25, .75, .9, 1.08), 'MULTIPLY')
    rocha = T.mistura(racha, rocha, shade(c0, -.6))
    cor = T.mistura(laje, cor, rocha)
    alt = T.lerp(laje, alt, T.soma((racha, -.35), (grao, .05), (medio, .2), (.45, 1)))
    return cor, alt, .86, None


def _ruinas(T, vw, cores, largo, medio, grao):
    """Piso antigo: lajes grandes de alturas diferentes, lascadas, algumas rachadas, musgo nas juntas e capim onde faltam."""
    c0, c1 = cores
    jt, borda, s1, s2, s3 = lajes(T, 4 / 3, 2 / 3, .5, junta=.05, gasto=(ruido(T, vw, 5, 3, .6), .06))
    tom = T.mistura(s1, shade(mix(c0, '#5c6563', .5), .02), shade(mix(c1, '#7c827d', .5), .12))
    tom = T.mistura(1.0, tom, T.faixa(ruido(T, vw, 7, 4, .6), .3, .7, .8, 1.15), 'MULTIPLY')
    tom = T.mistura(T.faixa(medio, .5, .7, 0, .5), tom, shade(c0, -.3))
    racha = T.math('MULTIPLY', rachaduras(T, vw, 2.2, .014, .45), T.math('GREATER_THAN', s3, .5))
    tom = T.mistura(racha, tom, shade(c0, -.6))
    musgo_c = mix('#3f6a48', c1, .25)
    musgo = T.faixa(T.soma((ruido(T, vw, 1.3, 4, .6), 1), (T.faixa(borda, 0, .14, .3, 0), 1), (grao, .08)), .62, .74, 0, 1)
    musgo = T.math('MAXIMUM', musgo, jt)
    cor = T.mistura(T.math('MULTIPLY', musgo, .9), tom, T.mistura(T.faixa(grao, .3, .7, 0, 1), shade(musgo_c, -.3), shade(musgo_c, .08)))
    alt = T.soma((T.math('SUBTRACT', 1, jt), .55), (s2, .18), (racha, -.25), (grao, .05), (musgo, .06))
    perdida = T.faixa(sonda('perdida', T.soma((ruido(T, vw, 1.8, 3, .5), 1), (grao, .1))), .64, .67, 0, 1)
    relva = ruido(T, torcer(T, vw, 2, .12), 6, 8, .68, distorcao=.5)
    mato = T.mistura(T.faixa(relva, .38, .62, 0, 1), shade(mix(c0, '#1a2a24', .5), -.2), mix(musgo_c, '#5e6a3c', .3))
    mato = T.mistura(T.faixa(grao, .55, .75, 0, .5), mato, shade(mix(c0, '#3e3424', .6), -.1))
    cor = T.mistura(perdida, cor, mato)
    alt = T.lerp(perdida, alt, T.soma((relva, .4), (grao, .08)))
    return cor, alt, .88, None


def _cidade(T, vw, cores, largo, medio, grao):
    """Cidade afundada: lajes nas casas do mapa, limo nas juntas e água parada nas lajes que afundaram."""
    c0, c1 = cores
    jt, borda, s1, s2, s3 = lajes(T, 1, .5, .5, junta=.04, gasto=(ruido(T, vw, 6, 3, .6), .045))
    tom = T.mistura(s1, shade(mix(c0, '#46524f', .4), .02), shade(mix(c1, '#62706c', .4), .1))
    tom = T.mistura(1.0, tom, T.faixa(ruido(T, vw, 8, 4, .6), .3, .7, .82, 1.12), 'MULTIPLY')
    racha = T.math('MULTIPLY', rachaduras(T, vw, 2.6, .012, .45), T.math('GREATER_THAN', s3, .55))
    tom = T.mistura(racha, tom, shade(c0, -.6))
    limo_c = mix('#2f5a50', c1, .3)
    limo = T.faixa(T.soma((ruido(T, vw, 1, 4, .6), 1), (T.faixa(borda, 0, .1, .25, 0), 1)), .6, .72, 0, 1)
    limo = T.math('MAXIMUM', limo, jt)
    cor = T.mistura(T.math('MULTIPLY', limo, .85), tom, T.mistura(T.faixa(grao, .3, .7, 0, 1), shade(limo_c, -.35), shade(limo_c, .02)))
    afundada = T.math('LESS_THAN', s2, .1)
    agua = T.math('MULTIPLY', afundada, T.faixa(borda, .02, .06, 0, 1))
    cor = T.mistura(T.math('MULTIPLY', agua, .85), cor, shade(mix(c0, '#0e1c1e', .4), -.1))
    rug = T.math('MINIMUM', T.faixa(limo, 0, 1, .62, .22), T.faixa(agua, 0, 1, 1, .05))
    alt = T.soma((T.math('SUBTRACT', 1, jt), .5), (s2, .15), (racha, -.2), (grao, .04), (afundada, -.3))
    return cor, alt, rug, None


def _masmorra(T, vw, cores, largo, medio, grao):
    """Lajotas em cinza médio (o jogo tinge com a cor de cada masmorra): uma por casa, gastas, algumas rachadas, sujas."""
    jt, borda, s1, s2, s3 = lajes(T, 1, 1, 0, junta=.04, gasto=(ruido(T, vw, 6, 3, .6), .05))
    tom = T.mistura(s1, '#7a7a7a', '#9c9c9c')
    tom = T.mistura(1.0, tom, T.faixa(ruido(T, vw, 7, 4, .6), .3, .7, .84, 1.12), 'MULTIPLY')
    tom = T.mistura(T.faixa(medio, .5, .7, 0, .5), tom, '#5e5e5e')
    racha = T.math('MULTIPLY', rachaduras(T, vw, 2, .012, .5), T.math('GREATER_THAN', s3, .45))
    tom = T.mistura(racha, tom, '#3a3a3a')
    tom = T.mistura(T.faixa(borda, 0, .1, .7, 0), tom, '#4a4a4a')
    cor = T.mistura(jt, tom, '#2a2a2a')
    alt = T.soma((T.math('SUBTRACT', 1, jt), .55), (s2, .12), (racha, -.25), (grao, .05))
    return cor, alt, .8, None


def _dunas(T, vw, cores, largo, medio, grao):
    """Areia: ondulações do vento (sobem devagar e caem de repente), grãos grossos nos vales e pedrinhas soltas."""
    c0, c1 = cores
    fase = T.soma((vw[2], 8), (vw[3], 3), (ruido(T, vw, .6, 3, .5), 1.6), (ruido(T, vw, 2, 3, .5), .25))   # em voltas
    f = T.math('FRACT', fase)
    onda = T.math('MINIMUM', T.math('DIVIDE', f, .78), T.math('DIVIDE', T.math('SUBTRACT', 1, f), .22))
    amp = T.faixa(ruido(T, vw, 1.2, 3, .5), .3, .7, .3, 1)
    alt = T.soma((T.math('MULTIPLY', onda, amp), .5), (largo, .4), (grao, .06))
    cor = T.mistura(T.faixa(largo, .3, .7, 0, 1), c0, c1)
    cor = T.mistura(T.faixa(onda, .6, 1, 0, .35), cor, shade(c1, .12))
    graos = pedras(T, vw, 28, .35, raio=.35)[0]
    cor = T.mistura(T.math('MULTIPLY', graos, T.faixa(onda, 0, .4, .5, 0)), cor, shade(c0, -.3))
    cor = T.mistura(1.0, cor, T.faixa(grao, .25, .75, .9, 1.08), 'MULTIPLY')
    pm, pf, pt = pedras_quinas(T, torcer(T, vw, 15, .06), 5, .05, folga=.18, chanfro=.12)
    cor = T.mistura(pm, cor, tom_pedra(T, pt, '#6a5a48', '#9a8a74', grao, pf))
    alt = T.math('MULTIPLY_ADD', pf, .5, alt)
    return cor, alt, .95, None


def _picos(T, vw, cores, largo, medio, grao):
    """Montanha: pedras frias de quina com rachaduras, neve juntando entre elas e gelo liso em pocinhas."""
    c0, c1 = cores
    pm, pf, pt = pedras_quinas(T, torcer(T, vw, 10, .1), 4.5, .2, folga=.07, chanfro=.16)
    racha = rachaduras(T, vw, 2.6, .014, .45)
    rocha = tom_pedra(T, pt, shade(mix(c0, '#4a525c', .5), -.05), shade(mix(c1, '#66707a', .4), .06), ruido(T, vw, 9, 4, .6), pf)
    rocha = T.mistura(T.math('SUBTRACT', 1, pm), rocha, T.mistura(T.faixa(grao, .3, .7, 0, 1), shade(c0, -.2), shade(c0, -.05)))
    rocha = T.mistura(racha, rocha, shade(c0, -.45))
    alt_r = T.soma((pf, .6), (T.math('MULTIPLY', pt, pf), .2), (medio, .2), (racha, -.2), (grao, .06))
    nv = sonda('neve', T.soma((ruido(T, vw, 3, 3, .55), .6), (alt_r, -.6), (grao, .15), (medio, .2)))
    neve = T.faixa(nv, NEVE[0], NEVE[1], 0, 1)
    neve_cor = T.mistura(T.faixa(medio, .3, .7, 0, 1), '#b9c4cf', '#d8dfe6')
    neve_cor = T.mistura(1.0, neve_cor, T.faixa(grao, .3, .7, .95, 1.03), 'MULTIPLY')
    cor = T.mistura(neve, rocha, neve_cor)
    alt = T.math('MAXIMUM', alt_r, T.math('MULTIPLY', T.soma((medio, .2), (grao, .05), (.32, 1)), neve))
    gelo = T.faixa(sonda('gelo', T.soma((ruido(T, vw, 2.2, 3, .5), 1), (grao, .04))), .615, .64, 0, 1)
    cor = T.mistura(T.math('MULTIPLY', gelo, .85), cor, T.mistura(T.faixa(medio, .3, .7, 0, 1), '#7f9fb6', '#a9c3d4'))
    alt = T.lerp(gelo, alt, .3)
    return cor, alt, T.faixa(gelo, 0, 1, .7, .06), None


def _rachado(T, vw, cores, decor, largo, medio, grao):
    """Placas de crosta escura; as rachaduras acendem (lava: brasa; vazio: luz violeta), com trechos apagados."""
    c0, c1 = cores
    vt = torcer(T, vw, 1, .15)
    tom_placa = T.canal(vor(T, vt, 1.1, 'F1', .9).outputs['Color'], 0)
    rd = bordas(T, vt, 1.1, .9)
    crosta = T.mistura(T.faixa(largo, .3, .7, 0, 1), shade(c0, -.05), shade(c1, .05))
    crosta = T.mistura(T.math('MULTIPLY', tom_placa, .5), crosta, shade(c0, -.3))
    crosta = T.mistura(1.0, crosta, T.faixa(ruido(T, vw, 9, 4, .6), .3, .7, .78, 1.15), 'MULTIPLY')
    po = '#4a4642' if decor == 'lava' else '#3c3646'
    crosta = T.mistura(T.faixa(T.soma((ruido(T, vw, 1.6, 3, .55), 1), (grao, .1)), .58, .7, 0, .6), crosta, po)
    linha = T.faixa(rd, 0, .012, 1, 0)
    halo = T.faixa(rd, 0, .05, 1, 0)
    acesa = T.faixa(ruido(T, vw, 1.6, 2, .5), .4, .62, 0, 1)
    fina = rachaduras(T, vw, 3.6, .006, .4)
    cor = T.mistura(T.math('MAXIMUM', linha, T.math('MULTIPLY', fina, .7)), crosta, shade(c0, -.65))
    quente = ('#ffb35a', '#ff4a12') if decor == 'lava' else ('#d2b0ff', '#7a48d0')
    brilho = T.math('MULTIPLY', T.soma((linha, 1), (halo, .1), (fina, .3)), acesa)
    alt = T.soma((T.faixa(rd, 0, .07, 0, 1), .5), (tom_placa, .15), (grao, .06), (fina, -.1))
    return cor, alt, .9, (brilho, T.mistura(linha, quente[1], quente[0]), 1.5 if decor == 'lava' else 1.0)


def _piche(T, vw, cores, largo, medio, grao):
    """Piche: crosta escura e enrugada, meio brilhante, com rachaduras, e poças pretas e lisas com bolhas que pegam o sol."""
    c0, c1 = cores
    crosta = T.mistura(T.faixa(largo, .3, .7, 0, 1), shade(c0, -.1), c1)
    crosta = T.mistura(1.0, crosta, T.faixa(grao, .25, .75, .82, 1.14), 'MULTIPLY')
    racha = rachaduras(T, vw, 2.8, .016, .5)
    crosta = T.mistura(racha, crosta, '#08090a')
    caroco = ruido(T, vw, 3, 5, .65, distorcao=1.2)
    crosta = T.mistura(T.faixa(caroco, .35, .65, .3, 0), crosta, shade(c0, -.35))
    np_ = sonda('poca', T.soma((ruido(T, vw, 1.6, 3, .5), 1), (grao, .04)))
    poca = T.faixa(np_, .615, .635, 0, 1)
    beira = T.math('MULTIPLY', T.faixa(np_, .595, .615, 0, 1), T.faixa(np_, .615, .635, 1, 0))
    _, bc, _, _ = pedras(T, vw, 6, .25, raio=.32)
    cor = T.mistura(poca, crosta, T.mistura(T.faixa(medio, .3, .7, 0, 1), '#050607', '#0b0d10'))
    cor = T.mistura(T.math('MULTIPLY', beira, .6), cor, '#101214')
    alt_c = T.soma((caroco, .4), (racha, -.25), (grao, .08), (.15, 1))
    alt = T.lerp(poca, alt_c, T.soma((T.math('MULTIPLY', bc, poca), .25), (.05, 1)))
    return cor, alt, T.faixa(poca, 0, 1, .5, .03), None


def _cristais(T, vw, cores, largo, medio, grao):
    """Vidro vulcânico: chão escuro com fraturas finas e cristais facetados cravados, alguns com pontos acesos."""
    c0, c1 = cores
    chao = T.mistura(T.faixa(largo, .3, .7, 0, 1), shade(c0, -.1), c1)
    chao = T.mistura(1.0, chao, T.faixa(grao, .25, .75, .84, 1.12), 'MULTIPLY')
    fratura = rachaduras(T, vw, 2.6, .01, .45)
    chao = T.mistura(T.math('MULTIPLY', fratura, .7), chao, mix(c1, '#b89ae8', .35))
    pm, pf, _ = pedras_quinas(T, torcer(T, vw, 6, .1), 3, .22, folga=.12, chanfro=.06)
    faceta = T.canal(vor(T, vw, 10, 'F1').outputs['Color'], 2)
    cor = T.mistura(pm, chao, T.mistura(faceta, mix(c1, '#6e52a8', .45), mix(c1, '#b8a0ee', .45)))
    gm = pedras(T, vw, 9, .08, raio=.14)[0]
    brilho = T.math('MAXIMUM', gm, T.math('MULTIPLY', pm, T.faixa(faceta, .82, .95, 0, .5)))
    brilho = T.math('MULTIPLY', brilho, T.faixa(ruido(T, vw, 1.2, 2, .5), .5, .62, .2, 1))
    alt = T.soma((pf, .7), (T.math('MULTIPLY', faceta, pf), .2), (grao, .06), (fratura, -.1))
    return cor, alt, T.faixa(pm, 0, 1, .55, .12), (brilho, '#d6c2ff', 2.4)


def material_chao(decor, cores, casa=1.0, deslocar=True, brilho=1.0):
    """Material de cada cenário, com relevo de verdade (deslocamento) e o detalhe fino em relevo de sombreamento.
    casa = tamanho de uma casa do mapa nas coordenadas do objeto; deslocar=False deixa só o relevo de sombreamento
    (malha grossa, como o chão das cenas de região); brilho multiplica a cor (as cenas usam o brilho que o
    integrar.py mede, para o chão da cena ficar como o do jogo)."""
    m = bpy.data.materials.new('chao_' + decor)
    m.use_nodes = True
    T = Nos(m)
    b = T.N.get('Principled BSDF')
    T.casa = casa
    vw = toro(T)
    largo = ruido(T, vw, 1.6, 3, .5)
    medio = ruido(T, vw, 2.5, 4, .55)
    grao = ruido(T, vw, 20, 3, .6)
    if decor in ('trees', 'reeds', 'dawn', 'pale'):
        r = _capim(T, vw, cores, decor, largo, medio, grao)
    elif decor in ('void', 'lava'):
        r = _rachado(T, vw, cores, decor, largo, medio, grao)
    else:
        f = {'rocks': _pedreira, 'ruins': _ruinas, 'city': _cidade, 'masmorra': _masmorra, 'dunes': _dunas,
             'peaks': _picos, 'tar': _piche, 'crystals': _cristais}.get(decor)
        r = f(T, vw, cores, largo, medio, grao) if f else _capim(T, vw, cores, decor, largo, medio, grao)
    cor, alt, rug, emissao = r
    pedido = os.environ.get('BRASALUME_SONDA')
    if pedido:   # medição: o valor pedido em cinza, sem relevo nem luz
        valor = SONDAS.get(pedido, alt if pedido == 'altura' else None)
        if valor is not None:
            em = T.no('ShaderNodeEmission')
            T.liga(valor, em.inputs['Color'])
            T.liga(em.outputs[0], T.N.get('Material Output').inputs['Surface'])
            return m
    if brilho != 1.0:
        mul = T.no('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
        mul.inputs[0].default_value = 1.0
        T.liga(cor, mul.inputs[6])
        mul.inputs[7].default_value = (brilho, brilho, brilho, 1.0)
        cor = mul.outputs[2]
    T.liga(cor, b.inputs['Base Color'])
    T._entrada(b.inputs['Roughness'], rug)
    b.inputs['Specular IOR Level'].default_value = .4
    if emissao:
        fator, ecor, forca = emissao
        T._entrada(b.inputs['Emission Color'], ecor)
        T.liga(T.math('MULTIPLY', fator, forca), b.inputs['Emission Strength'])
    desl = T.no('ShaderNodeDisplacement')
    T.liga(alt, desl.inputs['Height'])
    desl.inputs['Midlevel'].default_value = 0.0
    desl.inputs['Scale'].default_value = RELEVO * casa
    T.liga(desl.outputs['Displacement'], T.N.get('Material Output').inputs['Displacement'])
    for alvo in (m, getattr(m, 'cycles', None)):   # deslocamento de verdade + relevo de sombreamento no detalhe fino
        try:
            alvo.displacement_method = 'BOTH' if deslocar else 'BUMP'
            break
        except Exception:
            pass
    return m


def cena_chao(decor, cores, px=512):
    """Malha de LADRILHOS x LADRILHOS metros (mais a margem) vista de cima, com um quadradinho por pixel; a câmera
    enquadra exatamente o ladrilho (a imagem repete sem emenda)."""
    lado = LADRILHOS + 2 * MARGEM
    n = round(px * lado / LADRILHOS)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=lado, location=(0, 0, 0))
    plano = bpy.context.object
    plano.data.materials.append(material_chao(decor, cores))
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = LADRILHOS
    co = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(co)
    co.location = (0, 0, 10)
    bpy.context.scene.camera = co
    sol = bpy.data.lights.new('sol', 'SUN')
    sol.energy = 4.2
    sol.angle = math.radians(8)
    so = bpy.data.objects.new('sol', sol)
    bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(38), 0, math.radians(-135))   # a luz vem do alto da tela do jogo
    w = bpy.data.worlds.new('mundo')
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes.get('Background').inputs['Strength'].default_value = .35
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = px
    sc.render.film_transparent = False
