# Roteiro de render do Brasalume no Blender (modo fundo, sem janela).
# Uso: blender.exe --background --factory-startup --python gerar.py -- classes guerreiro,none
#      blender.exe --background --factory-startup --python gerar.py -- classes all
#      blender.exe --background --factory-startup --python gerar.py -- quadros_herois all   (herói animado no mapa)
#      blender.exe --background --factory-startup --python gerar.py -- chao all             (texturas de chão)
#      blender.exe --background --factory-startup --python gerar.py -- efeitos all          (poderes das habilidades)
#      blender.exe --background --factory-startup --python gerar.py -- ui all               (peças do HUD)
# Saída crua: arte/blender/renders_2d/personagens/<id>/<vista>.png (as folhas finais são montadas depois, com montar_folhas.py)
import sys, os, json, math, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import bpy
import kit_base as K
import kit_heroi as KH

DESIGN = os.path.abspath(os.path.join(AQUI, '..', '..'))
RAW = os.environ.get('BRASALUME_RAW') or os.path.join(DESIGN, 'blender', 'renders_2d')   # BRASALUME_RAW: renders de teste em outra pasta
DADOS = json.load(open(os.path.join(AQUI, 'dados_jogo.json'), encoding='utf-8'))

# vistas: (nome, rotação do herói em graus, elevação da câmera, largura, altura, amostras, sombra no chão)
VISTAS_HEROI = [
    ('frente', -90, 6, 480, 640, 32, True),
    ('tres_quartos', -45, 6, 480, 640, 32, True),
    ('perfil', 0, 6, 480, 640, 32, True),
    ('costas', 90, 6, 480, 640, 32, True),
    ('conceito', -38, 9, 780, 1040, 56, True),
    ('sprite', -30, 30, 320, 400, 40, False),
]


def chao_sombra():
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    p = bpy.context.object
    p.is_shadow_catcher = True
    return p


def render_heroi(cid, vistas=None):
    L = dict(DADOS['LOOK'].get(cid) or DADOS['LOOK']['none'])
    B = DADOS['BODY'].get(L.get('body', 'cloak'), DADOS['BODY']['cloak'])
    t0 = time.time()
    for nome, rot, elev, w, h, amostras, sombra in VISTAS_HEROI:
        if vistas and nome not in vistas:
            continue
        K.limpar()
        K.mundo((.012, .014, .018), 1.0)
        R = KH.construir(L, B)
        R.rotation_euler = (0, 0, math.radians(rot))
        if sombra:
            chao_sombra()
        alvo = 1.08 if nome != 'sprite' else 1.0
        K.estudio(alvo_z=alvo, aro=L['fx'])
        escala = 2.55 if nome != 'conceito' else 2.5
        K.camera(elev_graus=elev, alvo_z=alvo, escala=escala if nome != 'sprite' else 2.45)
        K.config_render(w, h, amostras=amostras, transparente=True)
        K.render(os.path.join(RAW, 'personagens', cid, nome + '.png'))
    print('HEROI_OK', cid, round(time.time() - t0, 1), flush=True)


def slug(nome):
    import unicodedata, re
    s = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')


def inimigos():
    """Todos os inimigos do jogo, sem repetir nome: (slug, nome, família, cor, papel)."""
    D, out, visto = DADOS, [], {}
    ordem = {None: 0, 'mini': 1, 'field': 2, 'boss': 3, 'dboss': 3}
    def add(e, papel):
        s = slug(e[0])
        if s in visto and ordem[visto[s][4]] >= ordem[papel]:
            return
        visto[s] = (s, e[0], e[1], e[2], papel)
    for z in D['ZONES']:
        for m in z['mobs']:
            add(m, None)
        add(z['boss'], 'boss')
    for fb in D['FIELD_BOSSES'].values():
        add(fb, 'field')
    for g in D['DUNGEONS']:
        for m in g['mobs']:
            add(m, None)
        add(g['mini'], 'mini')
        add(g['boss'], 'dboss')
    return list(visto.values())


LARGURA = {'beast': 120, 'spider': 110, 'crab': 110, 'serpent': 120, 'mimic': 100, 'worm': 90, 'plant': 100, 'flyer': 100, 'tome': 90,
           'golem': 128, 'knight': 120, 'treant': 128, 'wisp': 132, 'jelly': 110, 'skeleton': 110, 'eye': 100, 'imp': 90, 'blob': 90, 'mushroom': 80, 'maw': 96}


def render_inimigo(s, nome, kind, cor, papel, vistas=None):
    import kit_monstros as KM
    t0 = time.time()
    K.ACAB = True   # acabamento dos monstros (manchas, sombra nas dobras, brilho menos plástico)
    for vista, rot, elev, w, h, amostras, sombra in (('conceito', 215, 10, 720, 720, 32, False), ('sprite', 210, 30, 320, 320, 24, False)):
        if vistas and vista not in vistas:
            continue
        K.limpar()
        K.mundo((.012, .014, .018), 1.0)
        R, topo = KM.construir(nome, kind, cor, papel, marcador=(vista == 'conceito'))
        R.rotation_euler = (0, 0, math.radians(rot))
        if sombra:
            chao_sombra()
        alvo = topo * K.U * .55 + (.06 if papel else 0)
        aro = '#e8c45a' if papel in ('boss', 'dboss') else '#c792ee' if papel == 'field' else '#9fb8d8'
        K.estudio(alvo_z=alvo, aro=aro)
        escala = max(topo + 34 + (14 if papel else 0), LARGURA.get(kind, 100)) * K.U
        K.camera(elev_graus=elev, alvo_z=alvo, escala=escala)
        K.config_render(w, h, amostras=amostras, transparente=True)
        K.render(os.path.join(RAW, 'inimigos', s, vista + '.png'))
    print('INIMIGO_OK', s, kind, papel or '-', round(time.time() - t0, 1), flush=True)


MARGEM = 1.25   # quadros animados: câmera 25% mais aberta (mesma densidade de pixels) para caber asa erguida e bote


def render_quadros(s, nome, kind, cor, papel):
    """Animação do sprite do jogo: QUADROS quadros do ciclo (quadro_0..) e o do golpe (quadro_ataque), mesma câmera do sprite."""
    import kit_monstros as KM
    t0 = time.time()
    K.limpar()
    K.mundo((.012, .014, .018), 1.0)
    K.ACAB = True
    R, topo = KM.construir(nome, kind, cor, papel, marcador=False)
    R.rotation_euler = (0, 0, math.radians(210))
    alvo = topo * K.U * .55 + (.06 if papel else 0)
    aro = '#e8c45a' if papel in ('boss', 'dboss') else '#c792ee' if papel == 'field' else '#9fb8d8'
    K.estudio(alvo_z=alvo, aro=aro)
    escala = max(topo + 34 + (14 if papel else 0), LARGURA.get(kind, 100)) * K.U * MARGEM
    K.camera(elev_graus=30, alvo_z=alvo, escala=escala)
    lado = round(320 * MARGEM)
    K.config_render(lado, lado, amostras=16, transparente=True)
    pasta = os.path.join(RAW, 'inimigos', s)
    for i in range(KM.QUADROS):
        KM.pose(R, kind, i / KM.QUADROS)
        K.render(os.path.join(pasta, 'quadro_%d.png' % i))
    KM.pose(R, kind, 0, ataque=True)
    K.render(os.path.join(pasta, 'quadro_ataque.png'))
    print('QUADROS_OK', s, kind, papel or '-', round(time.time() - t0, 1), flush=True)


def render_quadros_heroi(cid):
    """Herói no mapa do jogo: 6 quadros do passo (quadro_0..5) e o do golpe (quadro_ataque), na vista do sprite
    (3/4 olhando para a direita, câmera a 30°). Sem aura e sem companheiro, que o jogo desenha em código.
    quadros.json guarda onde cai o pé (origem) na imagem e quantas unidades do jogo cabem num pixel na vertical."""
    import kit_monstros as KM
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    L = dict(DADOS['LOOK'].get(cid) or DADOS['LOOK']['none'])
    B = DADOS['BODY'].get(L.get('body', 'cloak'), DADOS['BODY']['cloak'])
    t0 = time.time()
    K.limpar()
    K.mundo((.012, .014, .018), 1.0)
    R = KH.construir(L, B, mapa=True)
    R.rotation_euler = (0, 0, math.radians(-30))
    K.estudio(alvo_z=1.0, aro=L['fx'])
    cam = K.camera(elev_graus=30, alvo_z=1.0, escala=2.45 * MARGEM)
    K.config_render(round(320 * MARGEM), round(400 * MARGEM), amostras=16, transparente=True)
    cena = bpy.context.scene
    bpy.context.view_layer.update()   # sem isto a câmera recém-criada ainda não tem a matriz de posição
    W, H = cena.render.resolution_x, cena.render.resolution_y
    p0 = world_to_camera_view(cena, cam, Vector((0, 0, 0)))
    p1 = world_to_camera_view(cena, cam, Vector((0, 0, 100 * K.U)))
    pasta = os.path.join(RAW, 'personagens', cid)
    os.makedirs(pasta, exist_ok=True)
    json.dump({'ox': p0.x * W, 'oy': (1 - p0.y) * H, 'u': 100 / ((p1.y - p0.y) * H), 'w': W, 'h': H}, open(os.path.join(pasta, 'quadros.json'), 'w'))
    for i in range(KM.QUADROS):
        KM.pose(R, 'knight', i / KM.QUADROS)
        K.render(os.path.join(pasta, 'quadro_%d.png' % i))
    KM.pose(R, 'knight', 0, ataque=True)
    K.render(os.path.join(pasta, 'quadro_ataque.png'))
    print('HEROI_QUADROS_OK', cid, round(time.time() - t0, 1), flush=True)


# ---------------- mapas ----------------
LARG_PECA = {'cart': 100, 'pond': 100, 'wreck': 76, 'bones': 64, 'boulder': 74, 'gate': 80, 'portal': 70, 'round': 84, 'pine': 80, 'snowpine': 80,
             'tower': 64, 'birch': 70, 'dead': 70, 'bookshelf': 56, 'vent': 50}
PECAS_ANIMADAS = {'torch', 'pond'}   # no jogo essas se mexem ou ficam no chão: continuam com o desenho do código
# (shard e vent viraram imagem: o jogo faz o cristal flutuar e a fenda pulsar em código, por cima da peça renderizada)


def render_regiao(i, z):
    import kit_mapas as KMP
    t0 = time.time()
    K.limpar()
    K.ACAB = True   # o mesmo acabamento dos monstros em toda a cena (peças, herói e monstros)
    KMP.cena_regiao(z, i, DADOS)
    KMP.camera_iso(1040, alvo_z=40)
    K.config_render(1600, 1040, amostras=32, transparente=True)
    K.render(os.path.join(RAW, 'mapas', 'regioes', z['id'], 'cena.png'))
    print('REGIAO_OK', z['id'], round(time.time() - t0, 1), flush=True)


def render_masmorra(i, g):
    import kit_mapas as KMP
    t0 = time.time()
    K.limpar()
    K.ACAB = True
    KMP.cena_masmorra(g, i, DADOS)
    KMP.camera_iso(900, alvo_z=50)
    K.config_render(1600, 1040, amostras=32, transparente=True)
    K.render(os.path.join(RAW, 'mapas', 'masmorras', g['id'], 'cena.png'))
    print('MASMORRA_OK', g['id'], round(time.time() - t0, 1), flush=True)


def render_peca(pasta, tipo, cores, semente=3):
    """Uma peça de cenário sozinha, no ângulo do jogo (30°), fundo transparente. Grava também onde fica o pé da peça na imagem."""
    import random
    import kit_mapas as KMP
    K.limpar()
    K.ACAB = True   # peça de cenário com o acabamento dos monstros
    KMP.mundo_cena('#2a2e34', 1.2)
    KMP.sol('#fff2e0', 2.6, (math.radians(55), 0, math.radians(-77)))
    R = K.raiz('peca')
    g, alt = KMP.peca(tipo, cores, random.Random(semente), parent=R)
    larg = LARG_PECA.get(tipo, 60)
    escala = max(alt * 1.18, larg * 1.25, 40)
    alvo = alt * .45
    KMP.camera_iso(escala, alvo_z=alvo)
    W = 420
    K.config_render(W, W, amostras=32, transparente=True)
    destino = os.path.join(RAW, 'mapas', 'pecas', pasta, tipo + '.png')
    K.render(destino)
    oy = W / 2 + alvo * math.cos(math.radians(30)) * (W / escala)
    json.dump({'ox': W / 2, 'oy': oy}, open(destino[:-4] + '.json', 'w'))
    print('PECA_OK', pasta, tipo, flush=True)


def render_chao(decor, cores):
    """Textura de chão sem emenda (vista de cima, 4 x 4 casas do mapa) para o jogo cobrir o chão do cenário."""
    import kit_chao as KC
    K.limpar()
    KC.cena_chao(decor, cores)
    K.config_render(512, 512, amostras=64, transparente=False)
    sc = bpy.context.scene
    sc.view_settings.view_transform = 'Standard'   # cores fiéis à paleta do jogo
    sc.view_settings.look = 'None'
    K.render(os.path.join(RAW, 'chao', decor + '.png'))
    print('CHAO_OK', decor, flush=True)


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if not args:
        print('nada a fazer'); return
    modo, lista = args[0], (args[1] if len(args) > 1 else 'all')
    vistas = set(args[2].split(',')) if len(args) > 2 else None
    if modo == 'regioes':
        for i, z in enumerate(DADOS['ZONES']):
            if lista == 'all' or z['id'] in lista.split(','):
                try:
                    render_regiao(i, z)
                except Exception as ex:
                    import traceback; traceback.print_exc()
                    print('REGIAO_ERRO', z['id'], ex, flush=True)
    if modo == 'masmorras':
        for i, g in enumerate(DADOS['DUNGEONS']):
            if lista == 'all' or g['id'] in lista.split(','):
                try:
                    render_masmorra(i, g)
                except Exception as ex:
                    import traceback; traceback.print_exc()
                    print('MASMORRA_ERRO', g['id'], ex, flush=True)
    if modo == 'pecas':
        import kit_mapas as KMP
        feitos = []
        for z in DADOS['ZONES']:
            if lista != 'all' and z['id'] not in lista.split(','):
                continue
            c = KMP._cores(z['decor'], DADOS)
            for tipo in dict.fromkeys(DADOS['PROP_SET'].get(z['decor'], [])):
                if tipo in PECAS_ANIMADAS:
                    continue
                try:
                    render_peca(z['id'], tipo, c)
                except Exception as ex:
                    import traceback; traceback.print_exc()
                    print('PECA_ERRO', z['id'], tipo, ex, flush=True)
        for g in DADOS['DUNGEONS']:
            if lista != 'all' and g['id'] not in lista.split(','):
                continue
            tipo = KMP.DG_DECO.get(g['theme'])
            if not tipo or (tipo in PECAS_ANIMADAS and not os.environ.get('BRASALUME_ANIMADAS')):   # animadas só como referência
                continue
            c = {'folha': '#3f7048', 'pedra': K.shade(g['floor'][0], .2), 'chao': g['floor'], 'decor': g['theme']}
            try:
                render_peca(g['id'], tipo, c)
            except Exception as ex:
                import traceback; traceback.print_exc()
                print('PECA_ERRO', g['id'], tipo, ex, flush=True)
        if lista == 'all':   # peças comuns a todas as regiões: portal e menir da toca
            c = KMP._cores('rocks', DADOS)
            for tipo in ('portal', 'menhir'):
                render_peca('comum', tipo, c)
    if modo == 'chao':   # texturas de chão: uma por cenário (GROUND do jogo) e a de lajotas das masmorras
        for decor, cores in DADOS['GROUND'].items():
            if lista == 'all' or decor in lista.split(','):
                try:
                    render_chao(decor, cores)
                except Exception as ex:
                    import traceback; traceback.print_exc()
                    print('CHAO_ERRO', decor, ex, flush=True)
        if lista == 'all' or 'masmorra' in lista.split(','):
            render_chao('masmorra', ['#7a7a7a', '#8a8a8a'])
    if modo == 'monstros':
        todos = inimigos()
        escolha = todos if lista == 'all' else [e for e in todos if e[0] in lista.split(',') or e[2] in lista.split(',')]
        print('INIMIGOS', len(escolha), flush=True)
        for e in escolha:
            try:
                render_inimigo(*e, vistas=vistas)
            except Exception as ex:
                import traceback; traceback.print_exc()
                print('INIMIGO_ERRO', e[0], ex, flush=True)
    if modo == 'quadros':   # animação dos monstros no jogo
        todos = inimigos()
        escolha = todos if lista == 'all' else [e for e in todos if e[0] in lista.split(',') or e[2] in lista.split(',')]
        print('INIMIGOS', len(escolha), flush=True)
        for e in escolha:
            try:
                render_quadros(*e)
            except Exception as ex:
                import traceback; traceback.print_exc()
                print('QUADROS_ERRO', e[0], ex, flush=True)
    if modo == 'quadros_herois':   # animação do herói no mapa, uma tira por vocação
        ids = ['none'] + list(DADOS['CLASSES']) if lista == 'all' else lista.split(',')
        print('HEROIS', len(ids), flush=True)
        for cid in ids:
            try:
                render_quadros_heroi(cid)
            except Exception as e:
                import traceback; traceback.print_exc()
                print('HEROI_QUADROS_ERRO', cid, e, flush=True)
    if modo == 'efeitos':   # biblioteca de poderes das habilidades: tiras animadas que o jogo combina por habilidade
        import kit_efeitos as KE
        import kit_poderes as KP
        nomes = list(KP.EFEITOS) if lista == 'all' else lista.split(',')
        print('EFEITOS', len(nomes), flush=True)
        for nome in nomes:
            try:
                KE.renderizar(nome, KP.EFEITOS[nome], os.path.join(RAW, 'efeitos'))
            except Exception as ex:
                import traceback; traceback.print_exc()
                print('EFEITO_ERRO', nome, ex, flush=True)
    if modo == 'ui':   # peças do HUD: molduras, medalhão, tubo das barras, encaixes, botões, ícones e o couro dos painéis
        import kit_ui as KU
        nomes = list(KU.PECAS) if lista == 'all' else lista.split(',')
        for nome in nomes:
            fn, W, H, op = KU.PECAS[nome]
            try:
                KU.renderizar(nome, fn, W, H, os.path.join(RAW, 'ui'), fundo=op.get('fundo', False))
            except Exception as ex:
                import traceback; traceback.print_exc()
                print('UI_ERRO', nome, ex, flush=True)
    if modo == 'classes':
        ids = ['none'] + list(DADOS['CLASSES']) if lista == 'all' else lista.split(',')
        for cid in ids:
            try:
                render_heroi(cid, vistas)
            except Exception as e:
                import traceback; traceback.print_exc()
                print('HEROI_ERRO', cid, e, flush=True)


main()
