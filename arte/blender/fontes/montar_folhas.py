"""Monta as folhas finais a partir dos renders brutos do Blender (arte/blender/renders_2d) e exporta os sprites.

Uso (na raiz do projeto): python -I arte/blender/fontes/montar_folhas.py [classes|inimigos|tudo]
Só processa o que já foi renderizado; pode ser rodado de novo a qualquer momento.
"""
import json
import math
import os
import random
import sys
import unicodedata
import re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.abspath(os.path.join(AQUI, '..', '..'))
RAW = os.path.join(DESIGN, 'blender', 'renders_2d')
D = json.load(open(os.path.join(AQUI, 'dados_jogo.json'), encoding='utf-8'))
FONTES = 'C:/Windows/Fonts/'


def fonte(nome, tam):
    try:
        return ImageFont.truetype(FONTES + nome, tam)
    except OSError:
        return ImageFont.load_default()


TIT = lambda t: fonte('palab.ttf', t)
TXT = lambda t: fonte('georgia.ttf', t)
TXB = lambda t: fonte('georgiab.ttf', t)
INK, DIM, FAINT, EMBER = (236, 227, 207), (182, 174, 158), (128, 122, 112), (240, 162, 63)


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def slug(nome):
    s = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')


def fundo(w, h, cor=(240, 162, 63), centro=(.5, .55), forca=.55, semente=1):
    """Fundo escuro com brilho na cor do efeito, névoa e brasas: dá clima sem competir com a figura."""
    base = Image.new('RGB', (w, h), (13, 14, 17))
    px = base.load()
    cx, cy = centro[0] * w, centro[1] * h
    rmax = math.hypot(w, h) * .55
    for y in range(h):
        for x in range(0, w):
            d = math.hypot(x - cx, (y - cy) * 1.15) / rmax
            g = max(0.0, 1 - d) ** 2.2 * forca
            v = 1 - min(1, (math.hypot(x - w / 2, y - h / 2) / (math.hypot(w, h) / 2))) ** 3 * .35
            px[x, y] = (int((13 + cor[0] * g * .55) * v), int((14 + cor[1] * g * .55) * v), int((17 + cor[2] * g * .55) * v))
    img = base.convert('RGBA')
    nevoa = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dn = ImageDraw.Draw(nevoa)
    rnd = random.Random(semente)
    for i in range(7):
        y0 = h * (.55 + .06 * i) + rnd.uniform(-20, 20)
        dn.ellipse((rnd.uniform(-w * .3, w * .2), y0 - 30, rnd.uniform(w * .7, w * 1.3), y0 + 40), fill=(170, 175, 190, 10))
    img.alpha_composite(nevoa.filter(ImageFilter.GaussianBlur(28)))
    brasas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    db = ImageDraw.Draw(brasas)
    for i in range(70):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h * .9), rnd.uniform(.8, 2.4)
        a = int(rnd.uniform(60, 200))
        db.ellipse((x - r, y - r, x + r, y + r), fill=(*cor, a))
    img.alpha_composite(brasas.filter(ImageFilter.GaussianBlur(.8)))
    return img


def sem_plano(img):
    """Tira a sombra do plano do Blender (pixels pretos e semitransparentes); a figura fica intacta."""
    r, g, b, a = img.split()
    mx = Image.merge('RGB', (r, g, b)).convert('L')
    mascara = Image.eval(mx, lambda v: 255 if v > 6 else 0)
    forte = Image.eval(a, lambda v: 255 if v >= 225 else 0)
    from PIL import ImageChops
    manter = ImageChops.lighter(mascara, forte)
    img = img.copy()
    img.putalpha(ImageChops.multiply(a, manter))
    return img


def sombra_suave(img, raio=18, opac=150):
    """Sombra de contato: uma elipse escura e borrada sob os pés da figura."""
    s = Image.new('RGBA', img.size, (0, 0, 0, 0))
    bb = img.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox()
    if not bb:
        return s
    x0, y0, x1, y1 = bb
    cx, larg = (x0 + x1) / 2, (x1 - x0) * .42
    d = ImageDraw.Draw(s)
    d.ellipse((cx - larg, y1 - larg * .16, cx + larg, y1 + larg * .16), fill=(0, 0, 0, opac))
    return s.filter(ImageFilter.GaussianBlur(raio))


def abrir(caminho):
    return sem_plano(Image.open(caminho).convert('RGBA'))


def recorte(img, pad=4):
    bb = img.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bb:
        return img
    x0, y0, x1, y1 = bb
    return img.crop((max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad)))


def texto_quebrado(d, xy, txt, f, larg, cor, esp=6):
    x, y = xy
    linha = ''
    for pal in txt.split():
        t = (linha + ' ' + pal).strip()
        if d.textlength(t, font=f) > larg and linha:
            d.text((x, y), linha, font=f, fill=cor)
            y += f.size + esp
            linha = pal
        else:
            linha = t
    if linha:
        d.text((x, y), linha, font=f, fill=cor)
        y += f.size + esp
    return y


def amostras(d, x, y, look):
    nomes = [('c1', 'principal'), ('c2', 'sombra'), ('tr', 'detalhe'), ('mt', 'metal'), ('fx', 'efeito')]
    for chave, rot in nomes:
        cor = look.get(chave)
        if not cor:
            continue
        d.rounded_rectangle((x, y, x + 34, y + 34), 6, fill=hexrgb(cor), outline=(255, 255, 255, 60))
        d.text((x + 44, y + 2), rot, font=TXT(17), fill=DIM)
        d.text((x + 44, y + 20), cor, font=TXT(13), fill=FAINT)
        y += 46
    return y


# ---------- descrições das peças, para as folhas ----------
CORPO = {'cloak': 'manto com capa curta', 'tunic': 'túnica curta', 'plate': 'armadura de placas', 'robe': 'túnica longa de tecido', 'coat': 'casaco longo',
         'fur': 'peles e peito nu', 'gladiator': 'arnês de arena', 'leather': 'couro leve', 'rags': 'trapos rasgados', 'apron': 'avental de couro', 'monk': 'faixas de monge'}
CABECA = {'hood': 'capuz', 'deephood': 'capuz fundo com olhos acesos', 'helm': 'elmo aberto', 'greathelm': 'elmo fechado', 'crest': 'elmo com crista',
          'horned': 'elmo com chifres', 'spiked': 'elmo de espinhos', 'gladhelm': 'elmo de arena com penacho', 'wild': 'cabelo selvagem e pintura de guerra',
          'plumehat': 'chapéu de pluma', 'widehat': 'chapéu de aba larga', 'kettle': 'chapéu de ferro', 'tricorn': 'chapéu de três pontas',
          'pointhat': 'chapéu pontudo e barba', 'cap': 'barrete de estudioso', 'crown': 'diadema', 'feather': 'faixa com pena', 'wolf': 'pele de lobo',
          'mask': 'capuz com lenço no rosto', 'goggles': 'óculos de latão', 'furcap': 'gorro de pele com cauda', 'bald': 'cabeça raspada e barba',
          'skullhood': 'máscara de caveira', 'judge': 'chapéu alto e venda', 'beak': 'máscara de bico', 'cowl': 'capuz de penitente', 'coif': 'capuz de cota de malha',
          'ribbon': 'faixa com fitas', 'visor': 'elmo de viseira acesa', 'tophat': 'cartola com engrenagem', 'halfmask': 'meia-máscara espelhada',
          'capfeather': 'boné com pena longa', 'brim': 'chapéu de aba e lenço', 'topknot': 'coque e faixa', 'goldmask': 'máscara dourada'}
ARMA = {'stick': 'bastão', 'sword': 'espada', 'shortsword': 'espada curta', 'greatsword': 'montante', 'rapier': 'florete', 'axe': 'machado', 'maul': 'marreta',
        'morningstar': 'maça de espinhos', 'scythe': 'foice', 'orbstaff': 'cajado com orbe', 'flamewand': 'varinha de chama', 'icestaff': 'cajado de gelo',
        'stormstaff': 'cajado de raios', 'tome': 'livro flutuante', 'gauntlet': 'manopla de pedra', 'quill': 'pena gigante', 'palm': 'mão em brasa',
        'prism': 'prisma flutuante', 'bow': 'arco', 'longbow': 'arco longo', 'shortbow': 'arco curto', 'recurve': 'arco recurvo', 'crossbow': 'besta pesada',
        'cannon': 'canhão de mão', 'spear': 'lança', 'dagger': 'adagas', 'poisondagger': 'adaga envenenada', 'sunmace': 'maça solar', 'sunhammer': 'martelo solar',
        'leafstaff': 'cajado de folhas', 'execblade': 'lâmina de execução', 'bellstaff': 'cajado com sino', 'keystaff': 'cajado-chave', 'pilgrimstaff': 'cajado de peregrino',
        'eyestaff': 'cajado com olho', 'flail': 'mangual', 'chain': 'corrente com gancho', 'scimitar': 'cimitarras', 'flamberge': 'espada flamejante',
        'clockstaff': 'cajado-relógio', 'mirror': 'espelho de mão', 'moonstaff': 'cajado lunar', 'spiritbow': 'arco espectral', 'bolas': 'boleadeira',
        'fists': 'punhos enfaixados', 'tridentstaff': 'tridente', 'censer': 'incensário'}
COSTAS = {'cape': 'capa', 'halfcape': 'meia-capa', 'banner': 'estandarte', 'quiver': 'aljava', 'bigquiver': 'aljava grande', 'trap': 'mochila com armadilha',
          'scroll': 'porta-pergaminho', 'pack': 'mochila', 'basket': 'cesto de ervas', 'bolts': 'estojo de virotes', 'barrel': 'barril de pólvora', 'reliquary': 'relicário'}
LIN = {'guerreiro': 'Guerreiro', 'arcanista': 'Arcanista', 'batedor': 'Batedor', 'devoto': 'Devoto', None: 'sem vocação'}


def info_classe(cid):
    if cid == 'none':
        return 'Portador', 'Antes da vocação', [], 'O herói no começo do jogo: manto simples, capuz e o bastão de peregrino.'
    C = D['CLASSES'][cid]
    tiers = C.get('tiers') or []
    nome = C.get('nome') or (tiers[0]['nome'] if tiers else cid)
    lin = 'Vocação-base · ' + LIN[C['arch']] if C.get('base') else 'Linhagem do ' + LIN[C['arch']]
    desc = C.get('desc') or ''
    return nome, lin, [t['nome'] for t in tiers], desc


def destinos_classe(cid):
    if cid == 'none':
        base = os.path.join(DESIGN, 'personagens', 'portador')
        return base, os.path.join(base, 'turnaround'), 'portador'
    base = os.path.join(DESIGN, 'personagens', 'classes', cid)
    return base, os.path.join(base, 'turnaround'), cid


def folha_turnaround(cid):
    pasta = os.path.join(RAW, 'personagens', cid)
    vistas = [('frente', 'FRENTE'), ('tres_quartos', 'TRÊS QUARTOS'), ('perfil', 'PERFIL'), ('costas', 'COSTAS')]
    if not all(os.path.isfile(os.path.join(pasta, v + '.png')) for v, _ in vistas):
        return False
    look = D['LOOK'].get(cid, D['LOOK']['none'])
    nome, lin, estagios, _ = info_classe(cid)
    W, H = 2040, 900
    img = fundo(W, H, hexrgb(look['fx']), centro=(.5, .6), forca=.35, semente=hash(cid) & 255)
    d = ImageDraw.Draw(img)
    d.text((48, 30), nome, font=TIT(52), fill=INK)
    d.text((50, 94), lin + '   ·   ID ' + cid, font=TXT(22), fill=DIM)
    if estagios:
        d.text((50, 124), 'Estágios: ' + ' → '.join(estagios), font=TXT(18), fill=FAINT)
    base, tdir, nome_arq = destinos_classe(cid)
    os.makedirs(tdir, exist_ok=True)
    for i, (v, rot) in enumerate(vistas):
        im = abrir(os.path.join(pasta, v + '.png'))
        x, y = 40 + i * 490, 150
        img.alpha_composite(sombra_suave(im, 10, 150), (x, y))
        img.alpha_composite(im, (x, y))
        tw = d.textlength(rot, font=TXB(20))
        d.text((x + 240 - tw / 2, y + 640), rot, font=TXB(20), fill=EMBER)
        im.save(os.path.join(tdir, '%s_%s.png' % (nome_arq, v)))
    d.line((40, 834, W - 40, 834), fill=(70, 66, 60), width=1)
    d.text((40, 848), 'Brasalume · turnaround renderizado no Blender a partir da descrição visual do jogo (LOOK). Proporções do Canvas: cabeça grande, leitura no mapa.', font=TXT(16), fill=FAINT)
    img.convert('RGB').save(os.path.join(tdir, nome_arq + '_turnaround.png'), optimize=True)
    return True


def folha_conceito(cid):
    pasta = os.path.join(RAW, 'personagens', cid)
    fc, fs = os.path.join(pasta, 'conceito.png'), os.path.join(pasta, 'sprite.png')
    if not os.path.isfile(fc):
        return False
    look = D['LOOK'].get(cid, D['LOOK']['none'])
    nome, lin, estagios, desc = info_classe(cid)
    W, H = 1500, 1120
    img = fundo(W, H, hexrgb(look['fx']), centro=(.3, .55), forca=.6, semente=(hash(cid) >> 3) & 255)
    con = abrir(fc)
    img.alpha_composite(sombra_suave(con, 16, 160), (20, 40))
    img.alpha_composite(con, (20, 40))
    d = ImageDraw.Draw(img)
    x0 = 830
    d.rounded_rectangle((x0 - 20, 40, W - 36, H - 40), 18, fill=(10, 11, 14, 170), outline=(90, 84, 74, 120))
    d.text((x0, 66), nome, font=TIT(50), fill=INK)
    y = 128
    d.text((x0 + 2, y), lin, font=TXT(22), fill=DIM)
    y += 40
    if estagios:
        d.text((x0 + 2, y), 'Estágios do caminho', font=TXB(18), fill=EMBER)
        y += 28
        for i, t in enumerate(estagios):
            d.text((x0 + 14, y), '%d. %s' % (i + 2, t), font=TXT(19), fill=INK)
            y += 27
        y += 10
    if desc:
        y = texto_quebrado(d, (x0 + 2, y), desc, TXT(20), 600, DIM) + 12
    d.text((x0 + 2, y), 'Silhueta', font=TXB(18), fill=EMBER)
    y += 28
    pecas = [CORPO.get(look.get('body', 'cloak'), look.get('body', '')), CABECA.get(look.get('head', 'hood'), look.get('head', '')), ARMA.get(look.get('wpn', ''), look.get('wpn', ''))]
    if look.get('back'):
        pecas.append(COSTAS.get(look['back'], look['back']))
    if look.get('off') in ('tower', 'round'):
        pecas.append('escudo ' + ('torre' if look['off'] == 'tower' else 'redondo'))
    if look.get('pet'):
        pecas.append({'wolf': 'lobo companheiro', 'hawk': 'falcão', 'swarm': 'enxame de fagulhas'}[look['pet']])
    pecas.append('lanterna acesa no cinto')
    y = texto_quebrado(d, (x0 + 14, y), ' · '.join(pecas), TXT(19), 590, INK) + 14
    d.text((x0 + 2, y), 'Paleta', font=TXB(18), fill=EMBER)
    y = amostras(d, x0 + 14, y + 30, look) + 6
    if os.path.isfile(fs):
        spr = recorte(Image.open(fs).convert('RGBA'))
        d.text((x0 + 2, y), 'Leitura no mapa (tamanho do jogo e o dobro)', font=TXB(18), fill=EMBER)
        y += 32
        caixa = (x0 + 10, y, W - 56, min(H - 60, y + 150))
        d.rounded_rectangle(caixa, 10, fill=(32, 40, 30, 255))
        for k, alt in enumerate((46, 92)):
            s = spr.resize((max(1, int(spr.width * alt / spr.height)), alt), Image.LANCZOS)
            img.alpha_composite(s, (caixa[0] + 30 + k * 140, caixa[3] - alt - 18))
        y = caixa[3] + 24
    # as quatro vistas do turnaround, pequenas, no pé do painel
    vs = [os.path.join(pasta, v + '.png') for v in ('frente', 'tres_quartos', 'perfil', 'costas')]
    if all(os.path.isfile(v) for v in vs) and y < H - 220:
        d.text((x0 + 2, y), 'Vistas', font=TXB(18), fill=EMBER)
        alt = min(220, H - 70 - (y + 30))
        for k, v in enumerate(vs):
            t = recorte(abrir(v))
            t = t.resize((max(1, int(t.width * alt / t.height)), alt), Image.LANCZOS)
            img.alpha_composite(t, (x0 + 14 + k * 150, y + 30))
    img.convert('RGB').save(os.path.join(destinos_classe(cid)[0], destinos_classe(cid)[2] + '_conceito.png'), optimize=True)
    return True


def exportar_sprite(origem, destino, altura=256):
    if not os.path.isfile(origem):
        return None
    im = recorte(abrir(origem))
    k = altura / im.height
    im = im.resize((max(1, round(im.width * k)), altura), Image.LANCZOS)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    im.save(destino, optimize=True)
    return {'w': im.width, 'h': im.height, 'ax': round(im.width / 2), 'ay': im.height - 6}


def classes():
    feitos, meta = 0, {}
    for cid in ['none'] + list(D['CLASSES']):
        a = folha_turnaround(cid)
        b = folha_conceito(cid)
        nome_arq = 'portador' if cid == 'none' else cid
        m = exportar_sprite(os.path.join(RAW, 'personagens', cid, 'sprite.png'), os.path.join(DESIGN, 'exports', 'sprites', 'personagens', nome_arq + '.png'))
        if m:
            meta[nome_arq] = m
        feitos += bool(a or b or m)
    if meta:
        p = os.path.join(DESIGN, 'exports', 'sprites', 'personagens', 'sprites.json')
        antigo = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
        antigo.update(meta)
        json.dump(antigo, open(p, 'w', encoding='utf-8'), indent=1)
    print('classes processadas:', feitos)


PAPEL = {None: ('Monstro', (159, 184, 216)), 'boss': ('Chefe de região', (232, 196, 90)), 'field': ('Chefe errante', (199, 146, 238)),
         'mini': ('Subchefe de masmorra', (200, 208, 216)), 'dboss': ('Chefe de masmorra', (232, 196, 90))}


def lista_inimigos():
    sys.path.insert(0, AQUI)
    out, visto, onde = [], {}, {}
    ordem = {None: 0, 'mini': 1, 'field': 2, 'boss': 3, 'dboss': 3}
    def add(e, papel, lugar):
        s = slug(e[0])
        onde.setdefault(s, [])
        if lugar not in onde[s]:
            onde[s].append(lugar)
        if s in visto and ordem[visto[s][4]] >= ordem[papel]:
            return
        visto[s] = (s, e[0], e[1], e[2], papel)
    for z in D['ZONES']:
        for m in z['mobs']:
            add(m, None, z['nome'])
        add(z['boss'], 'boss', z['nome'])
    zn = {z['id']: z['nome'] for z in D['ZONES']}
    for zid, fb in D['FIELD_BOSSES'].items():
        add(fb, 'field', zn.get(zid, zid))
    for g in D['DUNGEONS']:
        for m in g['mobs']:
            add(m, None, g['nome'])
        add(g['mini'], 'mini', g['nome'])
        add(g['boss'], 'dboss', g['nome'])
    return [(v, onde[k]) for k, v in visto.items()]


def inimigos():
    feitos, meta = 0, {}
    for (s, nome, kind, cor, papel), lugares in lista_inimigos():
        pasta = os.path.join(RAW, 'inimigos', s)
        fc = os.path.join(pasta, 'conceito.png')
        if os.path.isfile(fc):
            rot, tom = PAPEL[papel]
            W, H = 980, 900
            img = fundo(W, H, tom, centro=(.5, .5), forca=.45 if papel else .3, semente=hash(s) & 255)
            con = abrir(fc)
            img.alpha_composite(sombra_suave(con, 14, 160), (130, 110))
            img.alpha_composite(con, (130, 110))
            d = ImageDraw.Draw(img)
            d.text((40, 28), nome, font=TIT(46), fill=INK)
            d.text((42, 84), rot + '   ·   família ' + kind, font=TXT(21), fill=tom)
            texto_quebrado(d, (42, 840), 'Aparece em: ' + ', '.join(lugares), TXT(18), W - 80, DIM)
            alvo = os.path.join(DESIGN, 'inimigos', 'chefes' if papel else os.path.join('monstros', kind), s + '.png')
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            img.convert('RGB').save(alvo, optimize=True)
            feitos += 1
        m = exportar_sprite(os.path.join(pasta, 'sprite.png'), os.path.join(DESIGN, 'exports', 'sprites', 'inimigos', s + '.png'), altura=224 if papel else 192)
        if m:
            meta[s] = dict(m, kind=kind, papel=papel or 'comum')
    if meta:
        p = os.path.join(DESIGN, 'exports', 'sprites', 'inimigos', 'sprites.json')
        antigo = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
        antigo.update(meta)
        json.dump(antigo, open(p, 'w', encoding='utf-8'), indent=1)
    print('inimigos processados:', feitos)


# ---------------- mapas ----------------
DECOR_PT = {'trees': 'bosque de pinheiros e copas', 'reeds': 'juncos, lagoas e lama', 'rocks': 'pedreira e matacões', 'pale': 'bétulas e galhos secos',
            'ruins': 'colunas e cacos de vitral', 'dunes': 'dunas, obeliscos e ossadas', 'peaks': 'pinheiros nevados e rocha', 'void': 'estilhaços do vazio',
            'tar': 'destroços e poças de piche', 'crystals': 'cristais de obsidiana', 'city': 'torres afundadas', 'lava': 'respiros de lava',
            'dawn': 'pilares da aurora'}
PECA_PT = {'pine': 'pinheiro', 'snowpine': 'pinheiro nevado', 'round': 'árvore de copa', 'bush': 'arbusto', 'rock': 'pedra', 'boulder': 'matacão',
           'birch': 'bétula', 'dead': 'árvore seca', 'reeds': 'juncos', 'column': 'coluna', 'glass': 'cacos de vitral', 'obelisk': 'obelisco',
           'bones': 'ossada', 'wreck': 'destroço', 'crystal': 'cristal', 'tower': 'torre', 'pillar': 'pilar da aurora', 'shroomprop': 'cogumelos',
           'bonepile': 'pilha de ossos', 'honey': 'favo', 'icicle': 'estalagmite de gelo', 'crate': 'caixote', 'coins': 'moedas', 'cart': 'vagonete',
           'bookshelf': 'estante', 'portal': 'portal', 'menhir': 'menir'}


def ceu(w, h, topo, baixo, brilho=None):
    """Degradê nas cores de céu do jogo, com vinheta e um brilho opcional atrás da cena."""
    a = Image.new('RGB', (w, h), hexrgb(topo))
    b = Image.new('RGB', (w, h), hexrgb(baixo))
    img = Image.composite(b, a, Image.linear_gradient('L').resize((w, h)))
    if brilho:
        luz = Image.new('RGB', (w, h), brilho)
        m = Image.radial_gradient('L').resize((w, h)).point(lambda v: int(max(0, 255 - v * 1.25) * .35))
        img = Image.composite(luz, img, m)
    vin = Image.radial_gradient('L').resize((w, h)).point(lambda v: int(min(255, max(0, v - 120) * 1.6)))
    img = Image.composite(Image.new('RGB', (w, h), (4, 4, 6)), img, vin)
    return img.convert('RGBA')


def exportar_peca(origem, destino, altura_max=256, pad=4):
    """Sprite de cenário com ponto de apoio no chão (ax, ay) e altura do modelo em pixels (hpx), no formato que o jogo lê."""
    meta_raw = json.load(open(origem[:-4] + '.json'))
    im = Image.open(origem).convert('RGBA')
    bb = im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bb:
        return None
    x0, y0 = max(0, bb[0] - pad), max(0, bb[1] - pad)
    im = im.crop((x0, y0, min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
    ax, ay = meta_raw['ox'] - x0, meta_raw['oy'] - y0
    # o chão do jogo é escuro: as peças saem 30% mais claras para não sumirem no mapa
    from PIL import ImageEnhance
    alfa = im.split()[3]
    im = Image.merge('RGBA', (*ImageEnhance.Brightness(im.convert('RGB')).enhance(1.3).split(), alfa))
    k = min(1.0, altura_max / im.height)
    if k < 1:
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    ax, ay = ax * k, ay * k
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    im.save(destino, optimize=True)
    return {'w': im.width, 'h': im.height, 'ax': round(ax, 1), 'ay': round(ay, 1), 'hpx': round(max(1, ay - pad * k), 1)}


def folha_mapa(tipo, item, idx):
    pasta_raw = os.path.join(RAW, 'mapas', 'regioes' if tipo == 'regiao' else 'masmorras', item['id'])
    cena = os.path.join(pasta_raw, 'cena.png')
    if not os.path.isfile(cena):
        return False
    W, H = 2000, 1220
    if tipo == 'regiao':
        topo, baixo = item['sky'][0], item['sky'][1]
        brilho = hexrgb(D['FOLIAGE'].get(item['decor'], '#3f7048'))
    else:
        topo, baixo = shade_hex(item['floor'][0], -.45), shade_hex(item['floor'][0], -.8)
        brilho = hexrgb(item['floor'][1])
    img = ceu(W, H, topo, baixo, brilho)
    im = Image.open(cena).convert('RGBA')
    im = im.resize((1500, round(1500 * im.height / im.width)), Image.LANCZOS)
    img.alpha_composite(im, (16, 170))
    d = ImageDraw.Draw(img)
    d.text((40, 30), item['nome'], font=TIT(60), fill=INK)
    x0 = 1540
    d.rounded_rectangle((x0 - 14, 150, W - 24, H - 70), 14, fill=(12, 13, 16, 215), outline=(70, 66, 60, 255))
    y = 172
    if tipo == 'regiao':
        sub = 'Região %d  ·  níveis %d–%d  ·  %s' % (idx + 1, item['lv'][0], item['lv'][1], DECOR_PT.get(item['decor'], item['decor']))
        d.text((42, 104), sub, font=TXT(24), fill=EMBER)
        d.text((x0, y), 'Monstros', font=TXB(22), fill=EMBER); y += 34
        for m in item['mobs']:
            d.text((x0 + 8, y), '· ' + m[0], font=TXT(19), fill=INK); y += 27
        y += 8
        d.text((x0, y), 'Chefe da toca', font=TXB(22), fill=EMBER); y += 32
        d.text((x0 + 8, y), item['boss'][0], font=TXT(19), fill=INK); y += 30
        fb = D['FIELD_BOSSES'].get(item['id'])
        if fb:
            d.text((x0, y), 'Chefe errante', font=TXB(22), fill=EMBER); y += 32
            d.text((x0 + 8, y), fb[0], font=TXT(19), fill=INK); y += 30
        dgs = [g for g in D['DUNGEONS'] if g['after'] == idx]
        if dgs:
            d.text((x0, y), 'Entrada de masmorra', font=TXB(22), fill=EMBER); y += 32
            for g in dgs:
                d.text((x0 + 8, y), g['nome'], font=TXT(19), fill=INK); y += 27
        cores = [('céu', item['sky'][0]), ('céu baixo', item['sky'][1]), ('chão', D['GROUND'][item['decor']][0]), ('chão claro', D['GROUND'][item['decor']][1]),
                 ('folhagem', D['FOLIAGE'][item['decor']])]
        pecas_dir = os.path.join(DESIGN, 'exports', 'sprites', 'mapas', item['id'])
    else:
        sub = 'Masmorra  ·  nível %d  ·  abre depois de %s  ·  tema %s' % (item['lv'], D['ZONES'][item['after']]['nome'], item['theme'])
        d.text((42, 104), sub, font=TXT(24), fill=EMBER)
        d.text((x0, y), 'Monstros', font=TXB(22), fill=EMBER); y += 34
        for m in item['mobs']:
            d.text((x0 + 8, y), '· ' + m[0], font=TXT(19), fill=INK); y += 27
        y += 8
        for rot, e in (('Subchefe', item['mini']), ('Chefe', item['boss'])):
            d.text((x0, y), rot, font=TXB(22), fill=EMBER); y += 32
            d.text((x0 + 8, y), e[0], font=TXT(19), fill=INK); y += 30
        cores = [('piso', item['floor'][0]), ('piso claro', item['floor'][1]), ('parede', shade_hex(item['floor'][0], -.22)), ('topo do muro', shade_hex(item['floor'][0], .06))]
        pecas_dir = os.path.join(DESIGN, 'exports', 'sprites', 'mapas', item['id'])
    y += 10
    d.text((x0, y), 'Paleta (do jogo)', font=TXB(22), fill=EMBER); y += 34
    for k, (rot, c) in enumerate(cores):
        cx, cy = x0 + 8 + (k % 2) * 210, y + (k // 2) * 44
        d.rounded_rectangle((cx, cy, cx + 34, cy + 34), 6, fill=hexrgb(c), outline=(220, 210, 190))
        d.text((cx + 44, cy + 2), rot, font=TXT(16), fill=INK)
        d.text((cx + 44, cy + 19), c, font=TXT(12), fill=FAINT)
    y += ((len(cores) + 1) // 2) * 44 + 10
    if os.path.isdir(pecas_dir):
        arqs = sorted(f for f in os.listdir(pecas_dir) if f.endswith('.png'))
        if arqs:
            d.text((x0, y), 'Peças de cenário (sprites)', font=TXB(22), fill=EMBER); y += 34
            col = 0
            for f in arqs:
                t = Image.open(os.path.join(pecas_dir, f)).convert('RGBA')
                t.thumbnail((120, 120), Image.LANCZOS)
                if y + 150 > H - 80:
                    break
                cx = x0 + 8 + col * 140
                img.alpha_composite(t, (cx + (120 - t.width) // 2, y + 120 - t.height))
                d.text((cx, y + 124), PECA_PT.get(f[:-4], f[:-4]), font=TXT(14), fill=DIM)
                col += 1
                if col == 3:
                    col, y = 0, y + 150
    d.text((40, H - 46), 'Brasalume · cena montada no Blender a partir dos dados do jogo (%s). Peças, cores e chefes vêm do código; desenho original.'
           % ('ZONES, GROUND, FOLIAGE, PROP_SET' if tipo == 'regiao' else 'DUNGEONS, piso e decoração do tema'), font=TXT(16), fill=FAINT)
    alvo = os.path.join(DESIGN, 'mapas', 'regioes' if tipo == 'regiao' else 'masmorras', item['id'], item['id'] + '_conceito.png')
    os.makedirs(os.path.dirname(alvo), exist_ok=True)
    img.convert('RGB').save(alvo, optimize=True)
    return True


def shade_hex(h, f):
    r, g, b = (v / 255 for v in hexrgb(h))
    if f < 0:
        r, g, b = r * (1 + f), g * (1 + f), b * (1 + f)
    else:
        r, g, b = r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f
    return '#%02x%02x%02x' % tuple(max(0, min(255, round(v * 255))) for v in (r, g, b))


def mapas():
    # 1) peças: sprites recortados com ponto de apoio
    base = os.path.join(RAW, 'mapas', 'pecas')
    meta = {}
    if os.path.isdir(base):
        for pasta in sorted(os.listdir(base)):
            for f in sorted(os.listdir(os.path.join(base, pasta))):
                if f.endswith('.png'):
                    m = exportar_peca(os.path.join(base, pasta, f), os.path.join(DESIGN, 'exports', 'sprites', 'mapas', pasta, f))
                    if m:
                        meta[pasta + '/' + f[:-4]] = m
    if meta:
        json.dump(meta, open(os.path.join(DESIGN, 'exports', 'sprites', 'mapas', 'sprites.json'), 'w', encoding='utf-8'), indent=1)
    # 2) folhas de conceito
    n = sum(folha_mapa('regiao', z, i) for i, z in enumerate(D['ZONES']))
    n2 = sum(folha_mapa('masmorra', g, i) for i, g in enumerate(D['DUNGEONS']))
    print('peças:', len(meta), ' regiões:', n, ' masmorras:', n2)


QUADROS = 6   # o mesmo de kit_monstros.QUADROS: quadros do ciclo; depois deles vem o do golpe


def exportar_quadros(s, papel):
    """Tira com os quadros do sprite animado (ciclo + golpe), todos com o mesmo recorte e a mesma escala.
    O ponto de apoio fica nos pés do quadro 0 e a altura de referência (hpx) é a do quadro 0, como no sprite parado."""
    pasta = os.path.join(RAW, 'inimigos', s)
    nomes = ['quadro_%d.png' % i for i in range(QUADROS)] + ['quadro_ataque.png']
    if not all(os.path.isfile(os.path.join(pasta, n)) for n in nomes):
        return None
    ims = [abrir(os.path.join(pasta, n)) for n in nomes]
    caixas = [im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox() for im in ims]
    if not all(caixas):
        return None
    W0, H0 = ims[0].size
    x0, y0 = max(0, min(b[0] for b in caixas) - 4), max(0, min(b[1] for b in caixas) - 4)
    x1, y1 = min(W0, max(b[2] for b in caixas) + 4), min(H0, max(b[3] for b in caixas) + 4)
    b0 = caixas[0]
    k = (224 if papel else 192) / (b0[3] - b0[1] + 8)   # mesma escala do sprite parado
    w, h = max(1, round((x1 - x0) * k)), max(1, round((y1 - y0) * k))
    tira = Image.new('RGBA', (w * len(ims), h), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        tira.paste(im.crop((x0, y0, x1, y1)).resize((w, h), Image.LANCZOS), (i * w, 0))
    ay = (b0[3] + 4 - y0) * k - 6
    destino = os.path.join(DESIGN, 'exports', 'sprites', 'inimigos_anim', s + '.png')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tira.save(destino, optimize=True)
    return {'w': w, 'h': h, 'ax': round(((b0[0] + b0[2]) / 2 - x0) * k, 1), 'ay': round(ay, 1), 'hpx': round(ay - (b0[1] - 4 - y0) * k, 1), 'n': len(ims)}


ESCALA_HEROI = .8   # tira do herói: 80% do render (o herói em pé fica com uns 210 px de altura)


def exportar_quadros_heroi(cid):
    """Tira do herói no mapa: 6 quadros do passo e 1 do golpe, todos com o mesmo recorte e sem mudar a escala de uma vocação
    para outra (chapéu alto fica mais alto). O ponto de apoio é a projeção da origem (o pé) e u diz quantas unidades do jogo
    cabem num pixel, para o herói sair do mesmo tamanho do desenho em código."""
    pasta = os.path.join(RAW, 'personagens', cid)
    nomes = ['quadro_%d.png' % i for i in range(QUADROS)] + ['quadro_ataque.png']
    pj = os.path.join(pasta, 'quadros.json')
    if not os.path.isfile(pj) or not all(os.path.isfile(os.path.join(pasta, n)) for n in nomes):
        return None
    cam = json.load(open(pj, encoding='utf-8'))
    ims = [abrir(os.path.join(pasta, n)) for n in nomes]
    caixas = [im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox() for im in ims]
    if not all(caixas):
        return None
    W0, H0 = ims[0].size
    x0, y0 = max(0, min(b[0] for b in caixas) - 4), max(0, min(b[1] for b in caixas) - 4)
    x1, y1 = min(W0, max(b[2] for b in caixas) + 4), min(H0, max(b[3] for b in caixas) + 4)
    k = ESCALA_HEROI * cam['w'] / W0 if W0 != cam['w'] else ESCALA_HEROI
    w, h = max(1, round((x1 - x0) * k)), max(1, round((y1 - y0) * k))
    tira = Image.new('RGBA', (w * len(ims), h), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        tira.paste(im.crop((x0, y0, x1, y1)).resize((w, h), Image.LANCZOS), (i * w, 0))
    destino = os.path.join(DESIGN, 'exports', 'sprites', 'personagens_anim', cid + '.png')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tira.save(destino, optimize=True)
    b0 = caixas[0]
    ay = (cam['oy'] - y0) * k
    return {'w': w, 'h': h, 'ax': round((cam['ox'] - x0) * k, 1), 'ay': round(ay, 1), 'hpx': round(ay - (b0[1] - y0) * k, 1),
            'n': len(ims), 'u': round(cam['u'] / k, 5)}


def quadros_herois():
    meta = {}
    for cid in ['none'] + list(D['CLASSES']):
        m = exportar_quadros_heroi(cid)
        if m:
            meta[cid] = m
    if meta:
        p = os.path.join(DESIGN, 'exports', 'sprites', 'personagens_anim', 'sprites.json')
        antigo = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
        antigo.update(meta)
        json.dump(antigo, open(p, 'w', encoding='utf-8'), indent=1)
    print('heróis animados:', len(meta))


def quadros():
    meta = {}
    for (s, nome, kind, cor, papel), _ in lista_inimigos():
        m = exportar_quadros(s, papel)
        if m:
            meta[s] = dict(m, kind=kind, papel=papel or 'comum')
    if meta:
        p = os.path.join(DESIGN, 'exports', 'sprites', 'inimigos_anim', 'sprites.json')
        antigo = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
        antigo.update(meta)
        json.dump(antigo, open(p, 'w', encoding='utf-8'), indent=1)
    print('monstros animados:', len(meta))


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'tudo'
    if modo in ('classes', 'tudo'):
        classes()
    if modo in ('inimigos', 'tudo'):
        inimigos()
    if modo in ('quadros', 'tudo'):
        quadros()
    if modo in ('quadros_herois', 'tudo'):
        quadros_herois()
    if modo in ('mapas', 'tudo'):
        mapas()
