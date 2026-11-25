# Kit da interface do Brasalume: peças de HUD renderizadas no Blender, vistas de cima (molduras de ferro com bronze,
# medalhão do retrato, tubo das barras, encaixes das habilidades, placa da barra de ações, placas de botão, faixa de
# título, divisor, ícones de recursos e a textura de couro dos painéis). Saem em PNG com transparência para o CSS do
# jogo (border-image e fundos). Medidas em pixels da imagem: 1 unidade do kit_base = 1 pixel (a câmera mede assim).
# A luz é de sóis (direção fixa): o lado de cima de uma moldura sai igual em qualquer ponto, e o meio de cada peça
# pode ser repetido ou esticado pelo CSS sem emenda.
import bpy, bmesh, math, os, json, random
from mathutils import Vector
import kit_base as K
import kit_efeitos as KE

U = K.U
TAU = math.tau


def V2(x, y, z=0.0):
    return Vector((x * U, y * U, z * U))


# ---------------- cena ----------------
def cena(W, H, fundo=False):
    K.limpar()
    K.ACAB = False
    K.mundo((.26, .23, .2), 1.0)   # o metal plano reflete o alto do céu: um meio-tom quente
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = max(W, H) * U
    o = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(o)
    o.location = (0, 0, 40)
    K.mirar(o, (0, 0, 0))
    bpy.context.scene.camera = o
    for nome, rot, forca, cor in (('chave', (math.radians(42), 0, math.radians(-135)), 3.0, (1.0, .9, .78)),
                                  ('preench', (math.radians(55), 0, math.radians(45)), .55, (.62, .7, .95))):
        L = bpy.data.lights.new(nome, 'SUN')
        L.energy = forca
        L.color = cor
        L.angle = math.radians(12)
        so = bpy.data.objects.new(nome, L)
        bpy.context.collection.objects.link(so)
        so.rotation_euler = rot
    K.config_render(W, H, amostras=96, transparente=not fundo)
    sc = bpy.context.scene
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'   # cores fiéis (o AgX desbotava o bronze e as gemas)
    sc.view_settings.look = 'None'
    return sc


def renderizar(nome, fn, W, H, saida, fundo=False):
    import time
    t0 = time.time()
    cena(W, H, fundo)
    info = fn(W, H) or {}
    bpy.context.view_layer.update()
    K.render(os.path.join(saida, nome + '.png'))
    json.dump(dict(info, w=W, h=H), open(os.path.join(saida, nome + '.json'), 'w', encoding='utf-8'))
    print('UI_OK', nome, round(time.time() - t0, 1), flush=True)


# ---------------- materiais ----------------
FERRO = '#2e2d33'
BRONZE = '#9c6a2e'
OURO = '#c99a46'


def ferro():
    return K.mat('metal', FERRO, rough=.46)


def bronze():
    return K.mat('gold', BRONZE, rough=.34)


def ouro():
    return K.mat('gold', OURO, rough=.26)


def gema(cor='#ff5a14', forca=1.6):
    return KE.mat_nat('glass', cor, emis=cor, forca=forca, rough=.05)


# ---------------- formas ----------------
def pts_ret(w, h, r=0.0, seg=6, cx=0.0, cy=0.0):
    """Contorno de retângulo (cantos arredondados se r > 0), no sentido anti-horário."""
    if r <= 0:
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    out = []
    for (qx, qy, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            out.append((cx + qx + r * math.cos(a), cy + qy + r * math.sin(a)))
    return out


def pts_circ(r, n=72, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(TAU * i / n), cy + r * math.sin(TAU * i / n)) for i in range(n)]


def _obj(bm, nome, mat, bevel=0.0, seg=3, liso=True):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(mat)
    if bevel:
        bv = o.modifiers.new('chanfro', 'BEVEL')
        bv.width = bevel * U
        bv.segments = seg
        bv.limit_method = 'ANGLE'
    for p in me.polygons:
        p.use_smooth = liso
    if liso:
        try:
            o.modifiers.new('normais', 'WEIGHTED_NORMAL')
        except Exception:
            pass
    return o


def _anti(pts):
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return list(pts) if a > 0 else list(reversed(pts))


def anel(ext, inte, z0, z1, mat, bevel=2.0, nome='anel'):
    """Faixa entre dois contornos com o mesmo número de pontos (molduras, aros), com espessura z0..z1."""
    ext, inte = _anti(ext), _anti(inte)   # os contornos daqui já começam no mesmo canto: só acerta o sentido
    bm = bmesh.new()
    n = len(ext)
    be = [bm.verts.new(V2(x, y, z0)) for x, y in ext]
    bi = [bm.verts.new(V2(x, y, z0)) for x, y in inte]
    te = [bm.verts.new(V2(x, y, z1)) for x, y in ext]
    ti = [bm.verts.new(V2(x, y, z1)) for x, y in inte]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((te[i], te[j], ti[j], ti[i]))
        bm.faces.new((be[j], be[i], bi[i], bi[j]))
        bm.faces.new((be[i], be[j], te[j], te[i]))
        bm.faces.new((bi[j], bi[i], ti[i], ti[j]))
    return _obj(bm, nome, mat, bevel)


def placa(pts, z0, z1, mat, bevel=2.0, nome='placa'):
    """Placa cheia a partir de um contorno, com espessura e borda chanfrada."""
    pts = _anti(pts)
    bm = bmesh.new()
    b = [bm.verts.new(V2(x, y, z0)) for x, y in pts]
    t = [bm.verts.new(V2(x, y, z1)) for x, y in pts]
    bm.faces.new(t)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], t[j], t[i]))
    return _obj(bm, nome, mat, bevel)


def rebite(x, y, z, r, mat):
    return K.sph((x, y, z), r, mat, scale=(1, 1, .55), seg=16, ring=10)


def pedra_gema(x, y, z, r, cor='#ff6a20', forca=5.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r * U, location=V2(x, y, z))
    o = bpy.context.object
    o.scale = (1, 1, .6)
    o.data.materials.append(gema(cor, forca))
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def losango(x, y, z0, z1, r, mat, bevel=1.5):
    return placa([(x + r, y), (x, y + r), (x - r, y), (x, y - r)], z0, z1, mat, bevel)


# ============================================================================================================
# peças
# ============================================================================================================
def moldura(W, H, borda=44, canto=48, passo=48, fina=False):
    """Moldura de 9 partes: aro de ferro com friso de bronze por dentro e por fora, cantos em losango de bronze com
    rebite e rebites no meio dos lados a cada 'passo' px (o CSS repete o meio: o espaçamento continua igual)."""
    f, b, o = ferro(), bronze(), ouro()
    ext = pts_ret(W - 2, H - 2)
    inte = pts_ret(W - 2 * borda, H - 2 * borda)
    anel(ext, inte, 0, 10, f, bevel=3.0, nome='aro')
    anel(pts_ret(W - 2 * borda + 12, H - 2 * borda + 12), inte, 8, 14, b, bevel=1.6, nome='friso_dentro')
    anel(ext, pts_ret(W - 12, H - 12), 8, 13, b, bevel=1.4, nome='friso_fora')
    meio = (borda + 6) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (W / 2 - canto / 2), sy * (H / 2 - canto / 2)
            losango(cx, cy, 10, 17, canto * .38 if not fina else canto * .3, b)
            rebite(cx, cy, 17, 5.5 if not fina else 4, o)
    # rebites dos lados: o meio de cada lado vai de 'canto' a W - 'canto', com um rebite a cada 'passo' px
    for lado in ('h', 'v'):
        L = (W if lado == 'h' else H) - 2 * canto
        k = max(1, round(L / passo))
        for i in range(k):
            t = -L / 2 + (i + .5) * L / k
            for s in (-1, 1):
                x, y = (t, s * (H / 2 - meio)) if lado == 'h' else (s * (W / 2 - meio), t)
                rebite(x, y, 12, 3.2 if not fina else 2.4, o)
    return {'corte': canto, 'borda': borda}


def medalhao(W, H):
    """Aro redondo do retrato: ferro com bronze, oito rebites e a gema de brasa no alto."""
    f, b, o = ferro(), bronze(), ouro()
    R0, R1 = 124, 98
    anel(pts_circ(R0), pts_circ(R1), 0, 12, f, bevel=3.0)
    anel(pts_circ(R1 + 9), pts_circ(R1), 10, 16, b, bevel=1.6)
    anel(pts_circ(R0 - 1), pts_circ(R0 - 8), 9, 14, b, bevel=1.4)
    for i in range(8):
        a = TAU * i / 8 + TAU / 16
        rebite(math.cos(a) * (R0 + R1) / 2, math.sin(a) * (R0 + R1) / 2, 12, 4.2, o)
    placa([(-20, 104), (0, 128), (20, 104), (0, 92)], 10, 18, b, bevel=2)
    pedra_gema(0, 110, 20, 9)
    return {'r_dentro': R1}


def tubo(W, H):
    """Tubo de vidro das barras (3 partes na horizontal): aro de ferro, canal transparente e tampas de bronze."""
    f, b, o = ferro(), bronze(), ouro()
    cap = H
    ext = pts_ret(W - 4, H - 6, r=(H - 6) / 2, seg=10)
    inte = pts_ret(W - 2 * cap + 20, H - 30, r=(H - 30) / 2, seg=10)
    anel(ext, inte, 0, 10, f, bevel=2.5)
    anel(pts_ret(W - 2 * cap + 30, H - 22, r=(H - 22) / 2, seg=10), inte, 8, 13, b, bevel=1.2)
    for s in (-1, 1):
        cx = s * (W / 2 - cap / 2 + 2)
        anel(pts_circ(H / 2 - 7, 48, cx, 0), pts_circ(H / 2 - 17, 48, cx, 0), 9, 16, b, bevel=1.6)
        pedra_gema(cx, 0, 13, H / 2 - 19, '#ff7a2a' if s < 0 else '#8fd0ff', 3.0)
    return {'corte_l': cap, 'corte_v': 15}


def encaixe(W, H):
    """Encaixe quadrado de uma habilidade: aro de ferro com chanfro de bronze e quatro cravos."""
    f, b, o = ferro(), bronze(), ouro()
    anel(pts_ret(W - 4, H - 4, r=12), pts_ret(W - 30, H - 30, r=6), 0, 12, f, bevel=3.0)
    anel(pts_ret(W - 24, H - 24, r=8), pts_ret(W - 30, H - 30, r=6), 10, 15, b, bevel=1.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            rebite(sx * (W / 2 - 13), sy * (H / 2 - 13), 13, 4.5, o)
    return {}


def barra_acoes(W, H):
    """Placa comprida da barra de habilidades (3 partes): ferro com frisos de bronze e as pontas com uma lanterna
    de brasa entre duas asas de bronze (o meio repete sem emenda)."""
    f, b, o = ferro(), bronze(), ouro()
    cap = 170
    placa(pts_ret(W - 2 * cap + 60, H - 44, r=10), 0, 9, f, bevel=2.5, nome='placa')
    for s in (-1, 1):
        placa([(-W / 2 + cap - 40, s * (H / 2 - 30)), (W / 2 - cap + 40, s * (H / 2 - 30)), (W / 2 - cap + 40, s * (H / 2 - 22)),
               (-W / 2 + cap - 40, s * (H / 2 - 22))], 8, 13, b, bevel=1.2, nome='friso')
    for s in (-1, 1):
        cx = s * (W / 2 - cap / 2 - 6)
        asa = [(cx - s * 70, 30), (cx - s * 20, 46), (cx + s * 30, 34), (cx + s * 78, 6), (cx + s * 30, -30), (cx - s * 20, -44), (cx - s * 70, -28)]
        if s < 0:
            asa = list(reversed(asa))
        placa(asa, 0, 10, f, bevel=3.0, nome='ponta')
        anel(pts_circ(32, 48, cx, 0), pts_circ(22, 48, cx, 0), 9, 17, b, bevel=1.6)
        pedra_gema(cx, 0, 14, 20, '#ff6a20', 6.0)
        for k in (-1, 1):
            rebite(cx + s * 52, k * 18, 11, 3.6, o)
            rebite(cx - s * 48, k * 26, 11, 3.6, o)
    return {'corte': cap}


def botao(W, H, quente=False):
    """Placa de botão (3 partes): ferro chanfrado com aro de bronze; a quente tem o aro em cobre aceso."""
    f = ferro()
    b = KE.mat_nat('gold', '#b8662c', emis='#ff6a20', forca=.45, rough=.3) if quente else bronze()
    placa(pts_ret(W - 6, H - 8, r=12), 0, 8, f, bevel=2.5)
    anel(pts_ret(W - 6, H - 8, r=12), pts_ret(W - 16, H - 18, r=8), 7, 11, b, bevel=1.2)
    for s in (-1, 1):
        rebite(s * (W / 2 - 16), 0, 10, 3.2, ouro())
    return {'corte': 28}


def faixa(W, H):
    """Placa de título de bronze com as pontas em rabo de andorinha (3 partes) e friso por dentro."""
    b, o = bronze(), ouro()
    ent = 26
    pts = [(-W / 2 + 4, H / 2 - 6), (W / 2 - 4, H / 2 - 6), (W / 2 - 4 - ent, 0), (W / 2 - 4, -H / 2 + 6), (-W / 2 + 4, -H / 2 + 6), (-W / 2 + 4 + ent, 0)]
    placa(pts, 0, 9, KE.mat_nat('gold', '#8a6232', rough=.38), bevel=2.5)
    dentro = pts_ret(W - 88, H - 32)
    anel(dentro, pts_ret(W - 100, H - 40), 8, 11, o, bevel=1.0)
    for s in (-1, 1):
        rebite(s * (W / 2 - 34), 0, 10, 4.0, o)
    return {'corte': 64}


def divisor(W, H):
    b, o = bronze(), ouro()
    for s in (-1, 1):
        placa([(s * 22, -1.6), (s * (W / 2 - 8), -.6), (s * (W / 2 - 8), .6), (s * 22, 1.6)] if s > 0 else
              [(s * (W / 2 - 8), -.6), (s * 22, -1.6), (s * 22, 1.6), (s * (W / 2 - 8), .6)], 0, 3, b, bevel=.6)
        losango(s * 34, 0, 0, 4, 4.5, o, bevel=.8)
    losango(0, 0, 0, 7, 13, b, bevel=1.6)
    pedra_gema(0, 0, 7, 6, '#ff6a20', 5.0)
    return {}


def icone_ouro(W, H):
    o = K.mat('gold', '#e8b850', rough=.3)
    rnd = random.Random(3)
    for i, (x, y, z) in enumerate(((-9, -6, 0), (8, -8, 0), (0, 4, 0), (-4, -2, 7), (6, 0, 6), (0, -6, 12))):
        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=12 * U, depth=3.2 * U, location=V2(x, y, z + 2))
        c = bpy.context.object
        c.rotation_euler = (rnd.uniform(-.35, .35), rnd.uniform(-.35, .35), 0)
        c.data.materials.append(o)
        bv = c.modifiers.new('chanfro', 'BEVEL')
        bv.width = .8 * U
        bv.segments = 2
    return {}


def icone_cinzas(W, H):
    b = bronze()
    anel(pts_circ(22), pts_circ(15), 0, 6, b, bevel=1.4)
    pedra_gema(0, 0, 6, 15, '#ff5a14', 2.6)
    return {}


def icone_insignia(W, H):
    o = K.mat('gold', '#c8a058', rough=.3)
    pts = [(math.cos(math.pi / 2 + i * math.pi / 5) * (26 if i % 2 == 0 else 11), math.sin(math.pi / 2 + i * math.pi / 5) * (26 if i % 2 == 0 else 11)) for i in range(10)]
    placa(pts, 0, 7, o, bevel=2.0)
    pedra_gema(0, 0, 7, 7, '#4fb04a', .9)
    return {}


def couro(W, H):
    """Couro escuro curtido que repete sem emenda (fundo dos painéis): grão em pontos, rugas largas e manchas."""
    me = KE.malha('couro', lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=W * U / 2))
    N = KE.Nos('couro')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    u = N.math('MULTIPLY_ADD', x, 1 / (W * U), .5)
    v = N.math('MULTIPLY_ADD', y, 1 / (W * U), .5)
    au, av = N.mul(u, TAU), N.mul(v, TAU)
    vet = N.vet(N.math('COSINE', au), N.math('SINE', au), N.math('COSINE', av))
    w = N.math('SINE', av)
    grao = N.ruido(N.vmath('SCALE', vet, escala=26.0), escala=1.0, w=N.mul(w, 26.0), det=2.0, rug=.6)
    ruga = N.ruido(N.vmath('SCALE', vet, escala=3.2), escala=1.0, w=N.mul(w, 3.2), det=5.0, rug=.62, dist=.6)
    mancha = N.ruido(N.vmath('SCALE', vet, escala=1.4), escala=1.0, w=N.mul(w, 1.4), det=3.0)
    cor = N.no('ShaderNodeMix', data_type='RGBA')
    N.liga(N.faixa(N.soma(mancha, N.mul(ruga, .5)), .3, 1.0, 0, 1), cor.inputs[0])
    cor.inputs[6].default_value = K.hex_lin('#1a120d')
    cor.inputs[7].default_value = K.hex_lin('#3a281b')
    bsdf = N.no('ShaderNodeBsdfPrincipled')
    N.liga(cor.outputs[2], bsdf.inputs['Base Color'])
    N.e(bsdf.inputs['Roughness'], N.faixa(grao, .3, .7, .45, .75))
    bp = N.no('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .5
    N.liga(N.soma(N.mul(grao, .35), N.mul(ruga, 1.0)), bp.inputs['Height'])
    N.liga(bp.outputs['Normal'], bsdf.inputs['Normal'])
    N.liga(bsdf.outputs[0], N.out.inputs['Surface'])
    me.materials.append(N.m)
    o = bpy.data.objects.new('couro', me)
    bpy.context.collection.objects.link(o)
    return {}


PECAS = {
    'ui_moldura': (moldura, 192, 192, {}),
    'ui_moldura_fina': (lambda W, H: moldura(W, H, borda=28, canto=32, passo=32, fina=True), 128, 128, {}),
    'ui_medalhao': (medalhao, 256, 256, {}),
    'ui_tubo': (tubo, 512, 64, {}),
    'ui_encaixe': (encaixe, 128, 128, {}),
    'ui_barra_acoes': (barra_acoes, 1024, 128, {}),
    'ui_botao': (botao, 256, 72, {}),
    'ui_botao_quente': (lambda W, H: botao(W, H, quente=True), 256, 72, {}),
    'ui_faixa': (faixa, 512, 80, {}),
    'ui_divisor': (divisor, 512, 40, {}),
    'ui_ouro': (icone_ouro, 64, 64, {}),
    'ui_cinzas': (icone_cinzas, 64, 64, {}),
    'ui_insignia': (icone_insignia, 64, 64, {}),
    'ui_couro': (couro, 512, 512, {'fundo': True}),
}
