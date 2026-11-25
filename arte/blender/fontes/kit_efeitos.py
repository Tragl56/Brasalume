# Kit de efeitos do Brasalume: a base para renderizar os poderes das habilidades em tiras animadas (PNG com transparência).
# Cada efeito é uma cena pequena animada por código: o gerador monta a cena e devolve quadro(t), que acerta tudo no
# instante t (0 a 1); renderizar() grava n quadros e um quadros.json com o ponto de apoio e a escala.
# Efeitos de luz (luz=True, tinta=True) saem em cinza (o brilho) com transparência de verdade: o jogo os pinta na cor da
# habilidade e soma a luz na tela. Os outros (objetos, fogo, fumaça, água) saem nas cores de verdade.
# Medidas em unidades do jogo (1 unidade = 2 cm; o herói tem cerca de 85). Câmera 'iso' a 30 graus, como os sprites do
# jogo (o chão fica com a proporção de 2 para 1 dos losangos); 'lado' de frente, para projéteis, golpes e raios que o
# jogo gira na direção do alvo (eles apontam para +X).
import bpy, bmesh, math, random, json, os
from mathutils import Vector, Matrix, Euler, Quaternion, noise as _ruido
from bpy_extras.object_utils import world_to_camera_view
import kit_base as K

U = K.U
TAU = math.tau
CAM = None   # câmera da cena atual (os geradores precisam dela para virar peças planas de frente)


def V3(x, y, z):
    return Vector((x * U, y * U, z * U))


def suave(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def env(t, sobe=.12, desce=.4):
    """Envelope de um efeito: acende rápido no começo e apaga no fim."""
    return suave(0, sobe, t) * (1 - suave(1 - desce, 1, t))


def chega(t, a, b):
    """0 antes de a e 1 depois de b, rápido no começo (desacelera ao chegar)."""
    x = max(0.0, min(1.0, (t - a) / max(1e-6, b - a)))
    return 1 - (1 - x) ** 3


def cai(t, a, b):
    """0 antes de a e 1 depois de b, acelerando (queda)."""
    x = max(0.0, min(1.0, (t - a) / max(1e-6, b - a)))
    return x * x


# ---------------- materiais por nós ----------------
class Nos:
    """Material montado por nós em poucas linhas. Valores animáveis ficam em self.v[nome] (saída de um nó Value)."""

    def __init__(self, nome):
        m = bpy.data.materials.new(nome)
        m.use_nodes = True
        self.m, self.nt = m, m.node_tree
        for nd in list(self.nt.nodes):
            self.nt.nodes.remove(nd)
        self.out = self.no('ShaderNodeOutputMaterial')
        self.v = {}
        m['nos'] = 1

    def no(self, tipo, **kw):
        n = self.nt.nodes.new(tipo)
        for k, x in kw.items():
            setattr(n, k, x)
        return n

    def liga(self, a, b):
        self.nt.links.new(a, b)

    def e(self, sock, x):
        if x is None:
            return
        if isinstance(x, (int, float)):
            sock.default_value = float(x)
        elif isinstance(x, (tuple, list)):
            sock.default_value = x
        else:
            self.liga(x, sock)

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.no('ShaderNodeMath', operation=op)
        n.use_clamp = clamp
        self.e(n.inputs[0], a)
        if b is not None:
            self.e(n.inputs[1], b)
        if c is not None:
            self.e(n.inputs[2], c)
        return n.outputs[0]

    def soma(self, *xs):
        r = xs[0]
        for x in xs[1:]:
            r = self.math('ADD', r, x)
        return r

    def mul(self, *xs, clamp=False):
        r = xs[0]
        for x in xs[1:]:
            r = self.math('MULTIPLY', r, x, clamp=clamp)
        return r

    def valor(self, nome, x=0.0):
        n = self.no('ShaderNodeValue')
        n.outputs[0].default_value = x
        self.v[nome] = n.outputs[0]
        return n.outputs[0]

    def faixa(self, x, a, b, c=0.0, d=1.0, suave=False):
        n = self.no('ShaderNodeMapRange')
        n.clamp = True
        if suave:
            n.interpolation_type = 'SMOOTHSTEP'
        self.e(n.inputs['Value'], x)
        self.e(n.inputs['From Min'], a)
        self.e(n.inputs['From Max'], b)
        self.e(n.inputs['To Min'], c)
        self.e(n.inputs['To Max'], d)
        return n.outputs['Result']

    def coord(self, tipo='Object'):
        return self.no('ShaderNodeTexCoord').outputs[tipo]

    def xyz(self, vec):
        s = self.no('ShaderNodeSeparateXYZ')
        self.liga(vec, s.inputs[0])
        return s.outputs

    def vet(self, x, y, z):
        c = self.no('ShaderNodeCombineXYZ')
        for i, a in enumerate((x, y, z)):
            self.e(c.inputs[i], a)
        return c.outputs[0]

    def vmath(self, op, a, b=None, escala=None):
        n = self.no('ShaderNodeVectorMath', operation=op)
        self.e(n.inputs[0], a)
        if b is not None:
            self.e(n.inputs[1], b)
        if escala is not None:
            self.e(n.inputs['Scale'], escala)
        return n.outputs['Value'] if op in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else n.outputs['Vector']

    def ruido(self, vec, escala=4.0, w=None, det=2.0, rug=.5, dist=0.0):
        n = self.no('ShaderNodeTexNoise')
        n.noise_dimensions = '4D' if w is not None else '3D'
        self.liga(vec, n.inputs['Vector'])
        self.e(n.inputs['Scale'], escala)
        n.inputs['Detail'].default_value = det
        n.inputs['Roughness'].default_value = rug
        n.inputs['Distortion'].default_value = dist
        if w is not None:
            self.e(n.inputs['W'], w)
        return n.outputs['Fac']

    def obj_cor(self):
        """Cor do objeto (cada peça tem a sua): R = acender (0 a 1), G = multiplica a cobertura, B = brilho extra."""
        oi = self.no('ShaderNodeObjectInfo')
        s = self.no('ShaderNodeSeparateColor')
        self.liga(oi.outputs['Color'], s.inputs[0])
        return s.outputs[0], s.outputs[1], s.outputs[2]

    def facing(self, blend=.5):
        lw = self.no('ShaderNodeLayerWeight')
        lw.inputs['Blend'].default_value = blend
        return lw.outputs['Facing']

    def rampa(self, x, paradas):
        """Rampa de cor: paradas = [(posição, '#hex'), ...]."""
        cr = self.no('ShaderNodeValToRGB')
        el = cr.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position, el[0].color = paradas[0][0], K.hex_lin(paradas[0][1])
        for p, h in paradas[1:]:
            e = el.new(p)
            e.color = K.hex_lin(h)
        self.e(cr.inputs['Fac'], x)
        return cr.outputs['Color']

    def luz(self, intens, alfa):
        """Saída dos efeitos de luz: o brilho em cinza (intens) e a cobertura (alfa), sem luz de cena."""
        cc = self.no('ShaderNodeCombineColor')
        for k in ('Red', 'Green', 'Blue'):
            self.e(cc.inputs[k], intens)
        return self.luz_cor(cc.outputs[0], alfa)

    def luz_cor(self, cor, alfa, forca=1.0):
        em = self.no('ShaderNodeEmission')
        self.e(em.inputs['Color'], cor)
        self.e(em.inputs['Strength'], forca)
        tr = self.no('ShaderNodeBsdfTransparent')
        mx = self.no('ShaderNodeMixShader')
        self.e(mx.inputs[0], alfa)
        self.liga(tr.outputs[0], mx.inputs[1])
        self.liga(em.outputs[0], mx.inputs[2])
        self.liga(mx.outputs[0], self.out.inputs['Surface'])
        return self.m


def mat_luz(nome='luz', base=.78, borda=.38, cobre=1.0, blend=.4, borda_a=.3):
    """Luz para traços, faíscas e partículas: mais clara no miolo de cada peça e mais fraca na borda.
    A cor de cada objeto controla: R = acender, G = cobertura (halo mais fraco), B = brilho extra."""
    N = Nos(nome)
    R, G, B = N.obj_cor()
    f = N.facing(blend)
    I = N.soma(N.faixa(f, 0, 1, base, borda), N.mul(B, .5))
    A = N.mul(R, G, N.faixa(f, 0, 1, cobre, cobre * borda_a), clamp=True)
    return N.luz(I, A)


def mat_espectral(nome='espectral', base=.3, borda=.92, a0=.16, a1=.95, fluxo=2.2, blend=.38):
    """Corpo de luz (armas, mãos, bichos e astros feitos de energia): de frente o fundo aparece através dele, na borda
    ele acende; uma energia corre por dentro (ruído animado em self.v['w']). Cor do objeto: R acender, G cobertura, B brilho."""
    N = Nos(nome)
    R, G, B = N.obj_cor()
    f = N.facing(blend)
    w = N.valor('w', 0.0)
    co = N.coord('Object')
    rn = N.ruido(co, escala=fluxo, w=w, det=3.0, rug=.55)
    fio = N.faixa(rn, .42, .62, 0, 1)
    I = N.soma(N.faixa(f, 0, 1, base, borda), N.mul(fio, .28), N.mul(B, .5))
    A = N.mul(R, G, N.soma(N.faixa(f, 0, 1, a0, a1), N.mul(fio, .18)), clamp=True)
    return N.luz(I, A)


def mat_nat(kind, cor, emis=None, forca=0.0, rough=None, metal=None):
    """Material de verdade (iluminado) com a cobertura no vermelho da cor do objeto (para sumir aos poucos) e brilho próprio opcional."""
    m = K.mat(kind, cor, rough=rough).copy()
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    sp = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(oi.outputs['Color'], sp.inputs[0])
    nt.links.new(sp.outputs[0], b.inputs['Alpha'])
    if emis:
        b.inputs['Emission Color'].default_value = K.hex_lin(emis)
        b.inputs['Emission Strength'].default_value = forca
    if metal is not None:
        b.inputs['Metallic'].default_value = metal
    return m


def acender(o, r=1.0, g=None, b=None):
    """Acerta a cor do objeto (e dos filhos) que os materiais leem: r = acender, g = cobertura, b = brilho extra."""
    c = list(o.color)
    c[0] = r
    if g is not None:
        c[1] = g
    if b is not None:
        c[2] = b
    o.color = c
    for f in o.children:
        acender(f, r, g, b)


def trocar_material(o, m):
    """Troca o material de tudo sob o objeto (para os corpos de luz feitos com as peças dos monstros)."""
    if o.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT'):
        o.data.materials.clear()
        o.data.materials.append(m)
        for ps in list(getattr(o, 'particle_systems', [])):
            pass
        for md in list(o.modifiers):
            if md.type == 'PARTICLE_SYSTEM':
                o.modifiers.remove(md)
    for f in o.children:
        trocar_material(f, m)


# ---------------- malhas pequenas ----------------
def malha(nome, fn, liso=True):
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    fn(bm)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = liso
    return me


def objeto(me, nome='peca', mat=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(nome, me)
    bpy.context.collection.objects.link(o)
    if mat is not None:
        me.materials.clear()
        me.materials.append(mat)
    o.location = V3(*loc)
    return o


def m_esfera(r, seg=14, anel=9, esc=(1, 1, 1)):
    def fn(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=anel, radius=r * U)
        for v in bm.verts:
            v.co.x *= esc[0]
            v.co.y *= esc[1]
            v.co.z *= esc[2]
    return malha('esfera', fn)


def m_plana(pts, nome='plana', curva=0.0):
    """Peça plana no plano XY (de frente para +Z); curva entorta ao longo de X."""
    def fn(bm):
        vs = [bm.verts.new(V3(x, y, curva * x * x)) for x, y in pts]
        bm.faces.new(vs)
    return malha(nome, fn)


def m_cilindro(r, h, seg=16, r2=None):
    def fn(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r * U, radius2=(r if r2 is None else r2) * U, depth=h * U)
    return malha('cilindro', fn)


def m_rocha(r, semente=0, aspereza=.35, sub=2):
    def fn(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r * U)
        off = Vector((semente * 1.731 + .3, semente * 2.417 + .7, semente * 3.119 + .1))
        for v in bm.verts:
            d = _ruido.fractal(v.co.normalized() * 1.8 + off, .7, 2.0, 3)
            v.co *= 1 + aspereza * max(-1.0, min(1.0, d))
    return malha('rocha', fn, liso=False)


def estrela_pts(R, pontas=4, miolo=.28, giro=0.0):
    return [((R if i % 2 == 0 else R * miolo) * math.cos(giro + i * math.pi / pontas + math.pi / 2),
             (R if i % 2 == 0 else R * miolo) * math.sin(giro + i * math.pi / pontas + math.pi / 2)) for i in range(pontas * 2)]


def de_frente(o, giro=0.0):
    """Vira uma peça plana (feita no plano XY) de frente para a câmera, girada no próprio plano."""
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = CAM.rotation_euler.to_quaternion() @ Quaternion((0, 0, 1), giro)


def apontar(o, d, giro=0.0):
    """Gira a peça para que o seu +X aponte na direção d (alongadas: faíscas, flechas, gotas)."""
    d = Vector(d)
    if d.length < 1e-9:
        return
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('X', 'Z') @ Quaternion((1, 0, 0), giro)


def fita(pts, larg, nome='fita', plano='XZ'):
    """Faixa ao longo de uma linha (pts em unidades do jogo, (x, z) no plano XZ, virado para a câmera de 'lado');
    larg = largura em cada ponto. UV: u ao longo (0 a 1), v de um lado ao outro."""
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    n = len(pts)
    pares = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / L, tx / L
        w = larg[i] / 2
        x, z = pts[i]
        if plano == 'XZ':
            pares.append((bm.verts.new(V3(x - nx * w, 0, z - nz * w)), bm.verts.new(V3(x + nx * w, 0, z + nz * w))))
        else:   # XY: deitada no chão
            pares.append((bm.verts.new(V3(x - nx * w, z - nz * w, 0)), bm.verts.new(V3(x + nx * w, z + nz * w, 0))))
    for i in range(n - 1):
        f = bm.faces.new((pares[i][0], pares[i + 1][0], pares[i + 1][1], pares[i][1]))
        s0, s1 = i / (n - 1), (i + 1) / (n - 1)
        for lp, q in zip(f.loops, ((s0, 0), (s1, 0), (s1, 1), (s0, 1))):
            lp[uv].uv = q
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    bpy.context.collection.objects.link(o)
    return o


def curva(tracos, raio, nome='traco', mat=None, plano='XY', z=0.0, res=2):
    """Traços (listas de pontos (a, b) em unidades do jogo) como tubos finos: no chão (XY) ou de frente (XZ)."""
    cu = bpy.data.curves.new(nome, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = raio * U
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    for tr in tracos:
        sp = cu.splines.new('POLY')
        sp.points.add(len(tr) - 1)
        for p, (a, b) in zip(sp.points, tr):
            p.co = (a * U, b * U, z * U, 1) if plano == 'XY' else (a * U, z * U, b * U, 1)
    o = bpy.data.objects.new(nome, cu)
    bpy.context.collection.objects.link(o)
    if mat is not None:
        cu.materials.append(mat)
    return o


def circulo(r, n=64, a0=0.0, a1=TAU, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


# ---------------- cena, câmera, luz e render ----------------
def cena_nova(ambiente=0.0):
    K.limpar()
    K.mundo((.03, .034, .045), ambiente)


def camera(modo, larg, alt, alvo):
    global CAM
    elev = math.radians(30 if modo == 'iso' else 0)
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = (larg if larg >= alt else alt) * U
    cam.clip_start, cam.clip_end = .05, 500
    o = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(o)
    d = 80.0
    o.location = (0, -d * math.cos(elev), alvo * U + d * math.sin(elev))
    K.mirar(o, (0, 0, alvo * U))
    bpy.context.scene.camera = o
    CAM = o
    return o


def luzes(tam=100.0, aro='#ffd9a0', forte=1.0):
    """Luz de estúdio na escala do efeito (a do herói é para 2 m de altura)."""
    s = max(.4, tam * U / 2.0)
    alvo = (0, 0, tam * U * .25)
    K.luz_area('chave', (2.4 * s, -2.8 * s, 3.8 * s), 320 * s * s * forte, (1.0, .93, .84), .9 * s, alvo)
    K.luz_area('preench', (-3.4 * s, -2.4 * s, 1.2 * s), 60 * s * s * forte, (.55, .62, .85), 2.4 * s, alvo)
    r, g, b, _ = K.hex_lin(aro)
    K.luz_area('aro', (-1.8 * s, 3.0 * s, 3.4 * s), 900 * s * s * forte, (r, g, b), 1.0 * s, alvo)
    K.luz_area('topo', (0, 0, 5 * s), 80 * s * s * forte, (.75, .8, .95), 1.5 * s, (0, 0, 0))


def renderizar(nome, E, saida):
    """Monta e renderiza um efeito do catálogo. E: dicionário do efeito (gen, modo, larg, alt, alvo, u, n, luz, tinta...)."""
    import time
    t0 = time.time()
    luz = E.get('luz', True)
    cena_nova(0.0 if luz else E.get('ambiente', .8))
    modo, larg, alt, alvo = E.get('modo', 'iso'), E['larg'], E['alt'], E.get('alvo', 0.0)
    cam = camera(modo, larg, alt, alvo)
    quadro = E['gen'](E)
    if not luz:
        luzes(E.get('tam_luz', max(larg, alt) * .6), E.get('aro', '#ffd9a0'), E.get('forte', 1.0))
    u = E.get('u', 1.0)
    W, H = max(8, round(larg / u)), max(8, round(alt / u))
    K.config_render(W, H, amostras=E.get('amostras', 20 if luz else 32), transparente=True)
    sc = bpy.context.scene
    sc.cycles.use_denoising = E.get('ruido', not luz)
    try:
        sc.cycles.transparent_max_bounces = 64
        sc.cycles.max_bounces = 6
        sc.cycles.volume_step_rate = E.get('passo_vol', 3.0)
        sc.cycles.volume_max_steps = 512
    except Exception:
        pass
    sc.render.filter_size = 1.2
    if luz and E.get('tinta', True):
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
    elif E.get('vista'):
        sc.view_settings.view_transform = E['vista']
        sc.view_settings.look = 'None'
    bpy.context.view_layer.update()
    W2, H2 = sc.render.resolution_x, sc.render.resolution_y
    p0 = world_to_camera_view(sc, cam, Vector((0, 0, 0)))
    pasta = os.path.join(saida, nome)
    os.makedirs(pasta, exist_ok=True)
    for f in os.listdir(pasta):
        if f.startswith('quadro_') and f.endswith('.png'):
            os.remove(os.path.join(pasta, f))
    n, laco = E.get('n', 12), E.get('laco', False)
    for i in range(n):
        t = i / n if laco else (i / (n - 1) if n > 1 else E.get('t_fixo', 0.0))
        quadro(t)
        bpy.context.view_layer.update()
        K.render(os.path.join(pasta, 'quadro_%d.png' % i))
    info = {'w': W2, 'h': H2, 'n': n, 'ox': round(p0.x * W2, 2), 'oy': round((1 - p0.y) * H2, 2), 'u': round(larg / W2, 4),
            'luz': 1 if luz else 0, 'tinta': 1 if (luz and E.get('tinta', True)) else 0, 'laco': 1 if laco else 0,
            'dur': E.get('dur', .5), 'modo': modo, 'brilho': E.get('brilho', 0), 'chao': 1 if E.get('chao') else 0}
    json.dump(info, open(os.path.join(pasta, 'quadros.json'), 'w', encoding='utf-8'))
    print('EFEITO_OK', nome, n, round(time.time() - t0, 1), flush=True)


# ============================================================================================================
# geradores genéricos (cada um monta a cena a partir do dicionário do efeito e devolve quadro(t))
# ============================================================================================================

# ---------- golpes: faixas de luz que varrem o ar ----------
def _forma_rastro(forma, R, W):
    """Linhas de um golpe (cada uma: pontos, larguras, atraso)."""
    out = []
    if forma == 'arco':
        a0, a1, m = math.radians(150), math.radians(-48), 40
        pts = [(R * 1.12 * math.cos(lerp(a0, a1, i / m)), R * math.sin(lerp(a0, a1, i / m))) for i in range(m + 1)]
        out.append((pts, [W * max(0.0, math.sin(math.pi * i / m)) ** .7 for i in range(m + 1)], 0.0))
    elif forma == 'estocada':
        m = 30
        pts = [(lerp(-R, R, i / m), 0.0) for i in range(m + 1)]
        out.append((pts, [W * (i / m) ** .45 * (1 - (i / m) ** 7) for i in range(m + 1)], 0.0))
    elif forma == 'x':
        m = 26
        for k, (s, atraso) in enumerate(((1, 0.0), (-1, .16))):
            pts = [(lerp(-R, R, i / m), s * lerp(R * .78, -R * .78, i / m) + math.sin(math.pi * i / m) * R * .12) for i in range(m + 1)]
            out.append((pts, [W * max(0.0, math.sin(math.pi * i / m)) ** .6 for i in range(m + 1)], atraso))
    elif forma == 'garra':
        m = 22
        for k in range(3):
            off = (k - 1) * R * .42
            pts = [(lerp(-R * .8, R * .8, i / m) + off * .5, lerp(R * .9, -R * .9, i / m) + off - math.sin(math.pi * i / m) * R * .15) for i in range(m + 1)]
            out.append((pts, [W * .7 * max(0.0, math.sin(math.pi * i / m)) ** .6 for i in range(m + 1)], k * .07))
    return out


def g_rastro(E):
    R, W = E.get('raio', 40.0), E.get('largura', 14.0)
    N = Nos('rastro')
    uv = N.xyz(N.coord('UV'))
    u, v = uv[0], uv[1]
    Rr, G, B = N.obj_cor()   # R = cabeça do golpe (0 a 1,2), G = cobertura, B = cauda
    h = Rr
    L = B
    along = N.math('POWER', N.mul(N.faixa(u, N.math('SUBTRACT', h, L), h, 0, 1, suave=True), N.faixa(u, h, N.soma(h, .03), 1, 0)), .55)
    meio = N.math('ABSOLUTE', N.math('SUBTRACT', N.mul(v, 2), 1))
    perfil = N.faixa(meio, 0, 1, 1, 0, suave=True)
    nucleo = N.faixa(N.math('ABSOLUTE', N.math('SUBTRACT', v, E.get('fio', .72))), 0, .16, 1, 0, suave=True)
    rn = N.ruido(N.vet(N.mul(u, 14), N.mul(v, 1.4), 0), escala=1.0, det=2.0)
    risco = N.faixa(rn, .3, .7, .55, 1.15)
    A = N.mul(along, N.soma(N.mul(perfil, .55), N.mul(nucleo, .7)), risco, G, clamp=True)
    I = N.soma(.32, N.mul(nucleo, along, .7), N.mul(perfil, along, .18))
    m = N.luz(I, A)
    linhas = []
    for pts, larg, atraso in _forma_rastro(E.get('forma', 'arco'), R, W):
        o = fita(pts, larg, 'golpe')
        o.data.materials.append(m)
        ha = fita(pts, [x * 2.2 for x in larg], 'halo')
        ha.data.materials.append(m)
        ha.location.y += .002
        linhas.append((o, ha, atraso))

    def quadro(t):
        # a cabeça varre o arco rápido deixando o rastro inteiro aceso; depois o rastro recolhe para a ponta e apaga
        for o, ha, atraso in linhas:
            tt = max(0.0, min(1.0, (t - atraso) / max(.3, 1 - atraso)))
            cab = chega(tt, 0, .3) * 1.12
            cauda = 1.1 * (1 - suave(.3, 1.0, tt)) + .04
            fade = 1 - suave(.5, 1.0, tt)
            o.color = (cab, fade, cauda, 1)
            ha.color = (cab, fade * .3, cauda * 1.1, 1)
    return quadro


# ---------- partículas: faíscas, motas, notas, folhas, moedas, cacos... ----------
def _malha_part(tipo, tam):
    if tipo in ('faisca', 'risco'):
        return m_esfera(tam, 8, 6, esc=(3.2 if tipo == 'faisca' else 5.0, 1, 1))
    if tipo in ('mota', 'brasa', 'conta', 'neve'):
        return m_esfera(tam, 10, 7)
    if tipo == 'gota':
        def fn(bm):
            bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=tam * U)
            for v in bm.verts:
                if v.co.x > 0:
                    v.co.x *= 1 + 1.6 * (v.co.x / (tam * U)) ** 2
        return malha('gota', fn)
    if tipo == 'estrela':
        return m_plana(estrela_pts(tam, 4, .26), 'estrela')
    if tipo == 'floco':
        return m_plana(estrela_pts(tam, 6, .45), 'floco')
    if tipo == 'nota':
        def fn(bm):
            cab = [bm.verts.new(V3(math.cos(a) * tam * .62 - tam * .2, math.sin(a) * tam * .44 - tam * .9, 0))
                   for a in [i / 14 * TAU + .45 for i in range(14)]]
            bm.faces.new(cab)
            haste = [V3(tam * .32, -tam * .8, 0), V3(tam * .48, -tam * .8, 0), V3(tam * .48, tam * 1.1, 0), V3(tam * .32, tam * 1.1, 0)]
            bm.faces.new([bm.verts.new(p) for p in haste])
            band = [V3(tam * .48, tam * 1.1, 0), V3(tam * 1.15, tam * .45, 0), V3(tam * 1.0, tam * .2, 0), V3(tam * .48, tam * .62, 0)]
            bm.faces.new([bm.verts.new(p) for p in band])
        return malha('nota', fn, liso=False)
    if tipo == 'folha':
        pts = [(tam * math.cos(a) * 1.4, tam * .55 * math.sin(a) * (1 - .35 * math.cos(a))) for a in [i / 16 * TAU for i in range(16)]]
        return m_plana(pts, 'folha', curva=.05)
    if tipo == 'pena':
        pts = [(tam * 1.6 * math.cos(a), tam * .32 * math.sin(a) * (1 + .4 * math.cos(a))) for a in [i / 14 * TAU for i in range(14)]]
        return m_plana(pts, 'pena')
    if tipo == 'moeda':
        return m_cilindro(tam, tam * .22, 18)
    if tipo == 'caco':
        def fn(bm):
            r = random.Random(7)
            pts = [(r.uniform(-1, -.4) * tam, r.uniform(-.5, .5) * tam), (r.uniform(.6, 1.4) * tam, r.uniform(-.3, .3) * tam), (r.uniform(-.2, .2) * tam, r.uniform(.6, 1.1) * tam)]
            a = [bm.verts.new(V3(x, y, -tam * .12)) for x, y in pts]
            b = [bm.verts.new(V3(x, y, tam * .12)) for x, y in pts]
            bm.faces.new(a)
            bm.faces.new(list(reversed(b)))
            for i in range(3):
                j = (i + 1) % 3
                bm.faces.new((a[i], a[j], b[j], b[i]))
        return malha('caco', fn, liso=False)
    if tipo == 'pedra':
        return m_rocha(tam, 3)
    if tipo == 'engrenagem':
        def fn(bm):
            bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=tam * U, radius2=tam * U, depth=tam * .3 * U)
            for i in range(8):
                a = i / 8 * TAU
                m = Matrix.Translation(V3(math.cos(a) * tam * 1.12, math.sin(a) * tam * 1.12, 0)) @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Diagonal((tam * .34 * U, tam * .3 * U, tam * .3 * U, 1))
                bmesh.ops.create_cube(bm, size=1.0, matrix=m)
        return malha('engrenagem', fn, liso=False)
    return m_esfera(tam)


def _mat_part(E):
    if E.get('luz', True):
        if E.get('tipo') in ('estrela', 'nota', 'floco', 'caco'):
            return mat_luz('part', base=E.get('base', .95), borda=.9, cobre=1.0)
        return mat_luz('part', base=E.get('base', .95), borda=E.get('borda', .45), cobre=1.0)
    return mat_nat(E.get('kind', 'stone'), E.get('cor', '#888888'), emis=E.get('emis'), forca=E.get('forca', 0.0), rough=E.get('rough'), metal=E.get('metal'))


def g_particulas(E):
    rnd = random.Random(E.get('semente', 11))
    tipo, tam, n = E.get('tipo', 'faisca'), E.get('tam', 2.0), E.get('quant', 24)
    mov = E.get('mov', 'explode')
    me = _malha_part(tipo, tam)
    mat = _mat_part(E)
    me.materials.append(mat)
    R, H, Z0 = E.get('raio', 40.0), E.get('altura', 60.0), E.get('z0', 30.0)
    plana = tipo in ('estrela', 'nota', 'floco', 'pena', 'folha')
    ps = []
    for i in range(n):
        o = bpy.data.objects.new('p%d' % i, me)
        bpy.context.collection.objects.link(o)
        a = rnd.uniform(0, TAU)
        if E.get('modo') == 'lado' and mov == 'explode':
            d = Vector((math.cos(a), 0, math.sin(a)))
        elif mov == 'leque':
            ab = rnd.uniform(-E.get('abre', .5), E.get('abre', .5))
            d = Vector((math.cos(ab), rnd.uniform(-.2, .2), math.sin(ab)))
        else:
            el = rnd.uniform(E.get('el0', -.1), E.get('el1', 1.0))
            d = Vector((math.cos(a) * math.cos(el * 1.2), math.sin(a) * math.cos(el * 1.2), math.sin(el * 1.2)))
        ps.append(dict(o=o, d=d.normalized(), v=rnd.uniform(.55, 1.0), a=a, r=rnd.uniform(.25, 1.0), atraso=rnd.uniform(0, E.get('espalha', .3)),
                       giro=rnd.uniform(0, TAU), vg=rnd.uniform(-1, 1), esc=rnd.uniform(.6, 1.25), fase=i / n, h=rnd.uniform(0, 1)))
    g = E.get('gravidade', 0.0)
    voltas = E.get('voltas', 1)
    laco = E.get('laco', False)

    def quadro(t):
        for p in ps:
            o = p['o']
            tt = (t + p['fase']) % 1.0 if laco else max(0.0, min(1.0, (t - p['atraso']) / (1 - p['atraso'] + 1e-6)))
            vivo = 1.0 if laco else (1.0 if t >= p['atraso'] else 0.0)
            if mov in ('explode', 'leque'):
                k = chega(tt, 0, 1.0)
                pos = Vector((0, 0, Z0)) + p['d'] * R * p['v'] * k - Vector((0, 0, g * tt * tt))
                fade = (1 - suave(.45, 1, tt)) * vivo
                esc = p['esc'] * (1 - .45 * tt)
                vel = p['d'] * R * p['v'] * (1 - tt) * 3 - Vector((0, 0, 2 * g * tt))
            elif mov == 'sobe':
                pos = Vector((math.cos(p['a']) * R * p['r'], math.sin(p['a']) * R * p['r'] * .8, H * .1 + H * tt * p['v'])) + Vector((math.sin(tt * 5 + p['giro']) * 4, 0, 0))
                fade = suave(0, .15, tt) * (1 - suave(.6, 1, tt)) * vivo
                esc = p['esc'] * (1 - .3 * tt)
                vel = Vector((0, 0, 1))
            elif mov == 'cai':
                vento = E.get('vento', 0.0)
                z = H * (1 - cai(tt, 0, 1)) * (.8 + .4 * p['h'])
                pos = Vector((math.cos(p['a']) * R * p['r'] + vento * (1 - tt), math.sin(p['a']) * R * p['r'] * .8, z))
                fade = suave(0, .1, tt) * (1 - suave(.85, 1, tt)) * vivo
                esc = p['esc']
                vel = Vector((-vento, 0, -H))
            elif mov == 'orbita':
                ang = p['a'] + TAU * voltas * t + p['fase'] * TAU
                rr = R * (.8 + .2 * math.sin(p['giro'] + t * TAU))
                pos = Vector((math.cos(ang) * rr, math.sin(ang) * rr, Z0 + math.sin(ang * 2 + p['giro']) * E.get('ondula', 3.0)))
                fade = (.55 + .45 * math.sin(t * TAU * 2 + p['giro'])) * vivo if E.get('pisca') else vivo
                esc = p['esc']
                vel = Vector((-math.sin(ang), math.cos(ang), 0))
            elif mov == 'gira_sobe':
                ang = p['a'] + TAU * voltas * tt
                rr = R * (1 - .5 * tt) * (.6 + .4 * p['r'])
                pos = Vector((math.cos(ang) * rr, math.sin(ang) * rr * .85, H * tt * (.6 + .4 * p['v'])))
                fade = suave(0, .12, tt) * (1 - suave(.7, 1, tt)) * vivo
                esc = p['esc']
                vel = Vector((-math.sin(ang), math.cos(ang), .4))
            else:   # 'espiral': converge para o meio girando
                ang = p['a'] + TAU * voltas * tt
                rr = R * (1 - chega(tt, 0, 1)) * (.5 + .5 * p['r'])
                pos = Vector((math.cos(ang) * rr, math.sin(ang) * rr, Z0 + H * .5 * tt * p['v']))
                fade = suave(0, .15, tt) * (1 - suave(.75, 1, tt)) * vivo
                esc = p['esc'] * (1 - .75 * tt)
                vel = Vector((-math.sin(ang), math.cos(ang), 0))
            o.location = V3(*pos)
            o.scale = (max(.001, esc),) * 3
            if plana:
                de_frente(o, p['giro'] + p['vg'] * t * TAU * E.get('rola', .5))
            elif tipo in ('faisca', 'risco', 'gota'):
                apontar(o, vel)
            else:
                o.rotation_euler = (p['giro'] + t * p['vg'] * 6, p['giro'] * .5 + t * 4 * p['vg'], p['giro'])
            o.color = (fade, 1.0, E.get('extra', 0.0) * fade, 1)
    return quadro


# ---------- onda de choque no chão ----------
def g_onda(E):
    R = E.get('raio', 70.0)
    me = malha('chao', lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=R * U * 1.05))
    N = Nos('onda')
    co = N.coord('Object')
    x, y, z = N.xyz(co)
    rho = N.math('DIVIDE', N.vmath('LENGTH', N.vet(x, y, 0)), R * U)
    r0 = N.valor('r0', .2)
    w = N.valor('w', .08)
    fade = N.valor('fade', 1.0)
    wt = N.valor('wt', 0.0)
    anel = N.faixa(N.math('ABSOLUTE', N.math('SUBTRACT', rho, r0)), 0, w, 1, 0, suave=True)
    dentro = N.mul(N.faixa(rho, 0, r0, .0, .32, suave=True), N.faixa(rho, r0, N.soma(r0, .01), 1, 0))
    rn = N.ruido(N.vet(N.math('DIVIDE', x, R * U * .18), N.math('DIVIDE', y, R * U * .18), 0), escala=1.0, w=wt, det=3)
    falha = N.faixa(rn, .3, .62, .25, 1.15)
    A = N.mul(N.soma(N.mul(anel, .95), N.mul(dentro, .5)), falha, fade, clamp=True)
    I = N.soma(.38, N.mul(anel, .62))
    m = N.luz(I, A)
    o = objeto(me, 'onda', m, (0, 0, .3))

    def quadro(t):
        k = chega(t, 0, .8)
        N.v['r0'].default_value = .08 + .92 * k
        N.v['w'].default_value = lerp(.22, .05, t) * E.get('grossura', 1.0)
        N.v['fade'].default_value = env(t, .05, .55)
        N.v['wt'].default_value = t * 1.5
    return quadro


# ---------- volumes: explosões, fumaça, poeira, veneno, chamas ----------
def g_volume(E):
    """Nuvem de volume (ruído em 4D dentro de uma esfera que cresce). E: raio, altura do centro, cores e curvas no tempo.
    fogo=True dá brilho próprio pela temperatura; cor_fumaca dá a cor da fumaça; laco=True ferve sem crescer."""
    R = E.get('raio', 60.0)
    cx = E.get('cx', 0.0)
    larg = E.get('dom', (2.4 * R, 2.4 * R, 2.6 * R))
    me = malha('dominio', lambda bm: bmesh.ops.create_cube(bm, size=1.0))
    o = objeto(me, 'volume')
    o.scale = (larg[0] * U, larg[1] * U, larg[2] * U)
    o.location = V3(cx, 0, larg[2] * .5 + E.get('base', -10.0))
    N = Nos('volume')
    co = N.coord('Object')   # -0,5 a 0,5 no domínio
    x, y, z = N.xyz(co)
    # posição em unidades do jogo, com a origem do efeito no 0 (o domínio pode estar deslocado em X: cauda de fogo)
    px = N.soma(N.mul(x, larg[0]), cx)
    py = N.mul(y, larg[1])
    pz = N.soma(N.mul(z, larg[2]), larg[2] * .5 + E.get('base', -10.0))
    cz = N.valor('cz', E.get('z', 40.0))
    rt = N.valor('rt', R)
    ach = E.get('achata', 1.0)
    d = N.math('DIVIDE', N.vmath('LENGTH', N.vet(px, py, N.math('DIVIDE', N.math('SUBTRACT', pz, cz), ach))), rt)
    if E.get('cauda'):   # bola de fogo e meteoro: a nuvem se estica para trás (-X)
        cauda = E['cauda']
        xef = N.soma(N.math('MAXIMUM', px, 0), N.math('DIVIDE', N.math('MINIMUM', px, 0), cauda))   # para trás a nuvem se estica
        d = N.math('DIVIDE', N.vmath('LENGTH', N.vet(xef, py, N.math('DIVIDE', N.math('SUBTRACT', pz, cz), ach))), rt)
    w = N.valor('w', 0.0)
    sobe = N.valor('sobe', 0.0)
    gx, gy = N.valor('gx', 0.0), N.valor('gy', 0.0)
    escala = E.get('grao', 2.2) / R
    pr = N.vet(N.soma(N.mul(px, escala), gx), N.soma(N.mul(py, escala), gy), N.math('SUBTRACT', N.mul(pz, escala), sobe))
    rn = N.ruido(pr, escala=1.0, w=w, det=E.get('det', 3.5), rug=E.get('rug', .58), dist=E.get('torce', .25))
    forma = N.faixa(d, E.get('miolo', .35), 1.0, 1, 0, suave=True)
    dmul = N.valor('dmul', 1.0)
    # densidade por metro: a nuvem do tamanho R fica com a mesma opacidade em qualquer escala
    dens = N.mul(N.math('MAXIMUM', N.soma(N.mul(forma, 1.35), N.mul(N.math('SUBTRACT', rn, .5), E.get('fofo', 2.0)), -.42), 0), dmul,
                 E.get('densidade', 6.0) * .6 / (R * U))
    dens = N.mul(dens, N.faixa(d, 1.0, 1.25, 1, 0))
    vol = N.no('ShaderNodeVolumePrincipled')
    N.e(vol.inputs['Density'], dens)
    vol.inputs['Color'].default_value = K.hex_lin(E.get('cor_fumaca', '#55504a'))
    vol.inputs['Anisotropy'].default_value = E.get('aniso', .25)
    if E.get('absorve'):
        vol.inputs['Absorption Color'].default_value = K.hex_lin(E['absorve'])
    if E.get('fogo'):
        calor = N.valor('calor', 1.0)
        q = N.mul(N.soma(N.mul(forma, .8), N.mul(rn, .55)), calor, clamp=False)
        cor = N.rampa(N.math('MINIMUM', q, 1.0), E.get('rampa_fogo', [(0, '#000000'), (.32, '#5a0e02'), (.5, '#c2340a'), (.68, '#ff8a1c'), (.84, '#ffd25a'), (1.0, '#fff6d8')]))
        N.e(vol.inputs['Emission Color'], cor)
        N.e(vol.inputs['Emission Strength'], N.mul(N.faixa(q, .3, 1.0, 0, 1), N.valor('brilho', E.get('brilho_fogo', 18.0))))
    elif E.get('emis'):
        vol.inputs['Emission Color'].default_value = K.hex_lin(E['emis'])
        N.e(vol.inputs['Emission Strength'], N.mul(forma, N.valor('brilho', E.get('forca', 2.0))))
    N.liga(vol.outputs['Volume'], N.out.inputs['Volume'])
    me.materials.append(N.m)
    curva_r = E.get('curva_r', lambda t: R * (.35 + .65 * chega(t, 0, .7)))
    curva_z = E.get('curva_z', lambda t: E.get('z', 40.0) + E.get('sobe', 20.0) * t)
    curva_d = E.get('curva_d', lambda t: env(t, .06, .5))
    curva_c = E.get('curva_c', lambda t: 1.15 - 1.0 * chega(t, 0, .8))
    laco = E.get('laco', False)

    def quadro(t):
        if laco:
            a = t * TAU
            N.v['gx'].default_value = math.cos(a) * E.get('ferve', .6)
            N.v['gy'].default_value = math.sin(a) * E.get('ferve', .6)
            N.v['sobe'].default_value = 0.0
            N.v['w'].default_value = E.get('w0', 0.0)
        else:
            N.v['w'].default_value = t * E.get('mexe', 1.2)
            N.v['sobe'].default_value = t * E.get('rola', 1.2)
        N.v['rt'].default_value = curva_r(t)
        N.v['cz'].default_value = curva_z(t)
        N.v['dmul'].default_value = curva_d(t)
        if 'calor' in N.v:
            N.v['calor'].default_value = curva_c(t)
    return quadro


# ---------- raios ----------
def _zigue(a, b, rnd, rugo=.28, nivel=6):
    pts = [Vector(a), Vector(b)]
    amp = (Vector(b) - Vector(a)).length * rugo
    d = (Vector(b) - Vector(a)).normalized()
    lado = d.cross(Vector((0, 1, 0)))
    if lado.length < .1:
        lado = d.cross(Vector((1, 0, 0)))
    lado.normalize()
    for _ in range(nivel):
        novo = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            m = (p + q) / 2 + lado * rnd.uniform(-amp, amp) + Vector((0, rnd.uniform(-amp, amp) * .3, 0))
            novo += [m, q]
        pts = novo
        amp *= .52
    return pts


def g_raio(E):
    rnd = random.Random(E.get('semente', 5))
    m = mat_luz('raio', base=1.0, borda=.75, cobre=1.0, blend=.3)
    lado = E.get('modo') == 'lado'
    L = E.get('comp', 120.0)
    objs = []

    def novo_raio():
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
        objs.clear()
        if lado:
            a, b = (-L / 2, 0, 0), (L / 2, 0, 0)
        else:
            a, b = (rnd.uniform(-12, 12), 0, E.get('alto', 260.0)), (0, 0, 0)
        tronco = _zigue(a, b, rnd, E.get('rugo', .22))
        tracos = [[(p.x, p.z) for p in tronco]]
        for _ in range(E.get('galhos', 4)):
            i = rnd.randrange(len(tronco) // 5, len(tronco) * 4 // 5)
            p = tronco[i]
            dirv = (Vector(b) - Vector(a)).normalized()
            gd = (dirv + Vector((rnd.uniform(-.9, .9), 0, rnd.uniform(-.5, .5)))).normalized()
            q = p + gd * (Vector(b) - Vector(a)).length * rnd.uniform(.12, .3)
            tracos.append([(v.x, v.z) for v in _zigue(p, q, rnd, .3, 4)])
        for k, (r, g) in enumerate(((E.get('grosso', 1.6), 1.0), (E.get('grosso', 1.6) * 4.5, .22))):
            for j, tr in enumerate(tracos):
                o = curva([tr], r * (1 if j == 0 else .55), 'raio', m, plano='XZ', res=1)
                o.color = (1, g, 1 if k == 0 else 0, 1)
                objs.append(o)
    if not lado:   # clarão no chão onde o raio cai
        cl = objeto(m_esfera(14, 16, 10, esc=(1.6, 1.6, .5)), 'clarao', mat_luz('clarao', base=.9, borda=.2, cobre=.9, blend=.6))
    else:
        cl = None
    pisca = E.get('pisca', [1.0, .65, 1.0, .5, .85, .4, .22, .08])
    troca = E.get('troca', {0, 2, 4})
    n = E.get('n', 8)

    def quadro(t):
        i = min(n - 1, round(t * (n - 1))) if not E.get('laco') else min(n - 1, round(t * n))
        if E.get('laco') or i in troca or not objs:
            novo_raio()
        f = pisca[i % len(pisca)]
        for o in objs:
            c = list(o.color)
            c[0] = f
            o.color = c
        if cl:
            cl.color = (f * .9, 1, 0, 1)
    return quadro


# ---------- traços desenhados: círculos mágicos, runas, mira ----------
def runa_tracos(rnd, cx, cy, tam, ang=0.0):
    """Uma runa inventada: 2 a 4 traços numa grade de 3 x 4, girada e posta em (cx, cy)."""
    pontos = [(i, j) for i in range(3) for j in range(4)]
    tr = []
    for _ in range(rnd.randint(2, 4)):
        p = rnd.choice(pontos)
        linha = [p]
        for _ in range(rnd.randint(1, 3)):
            q = (max(0, min(2, linha[-1][0] + rnd.choice((-1, 0, 1)))), max(0, min(3, linha[-1][1] + rnd.choice((-1, 1)))))
            linha.append(q)
        tr.append(linha)
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for linha in tr:
        pts = []
        for i, j in linha:
            x, y = (i - 1) * tam * .45, (j - 1.5) * tam * .4
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        out.append(pts)
    return out


def sigilo_tracos(rnd, R, pontas=6, runas=8, raios=48):
    tr = [circulo(R), circulo(R * .9), circulo(R * .6), circulo(R * .54)]
    k = 2 if pontas == 6 else 3 if pontas in (5, 7) else 1
    pts = [(R * .9 * math.cos(i * TAU / pontas + math.pi / 2), R * .9 * math.sin(i * TAU / pontas + math.pi / 2)) for i in range(pontas)]
    vistos = set()
    for i in range(pontas):
        j = (i + k) % pontas
        if (j, i) in vistos:
            continue
        vistos.add((i, j))
        tr.append([pts[i], pts[j]])
    for i in range(raios):
        a = i / raios * TAU
        r1 = R * (.95 if i % 4 else .9)
        tr.append([(R * math.cos(a), R * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a))])
    semente = rnd.randrange(1000)
    for i in range(runas):   # a mesma runa em todas as posições: o círculo fica simétrico e gira em laço sem emenda
        a = i / runas * TAU + math.pi / runas
        rr = R * .75
        tr += runa_tracos(random.Random(semente), rr * math.cos(a), rr * math.sin(a), R * .14, a - math.pi / 2)
    return tr


def g_traco(E):
    rnd = random.Random(E.get('semente', 3))
    R = E.get('raio', 50.0)
    plano = E.get('plano', 'XY')
    forma = E.get('forma', 'sigilo')
    if forma == 'sigilo':
        tracos = sigilo_tracos(rnd, R, E.get('pontas', 6), E.get('runas', 8))
    elif forma == 'runa':
        tracos = runa_tracos(rnd, 0, 0, R, 0) + [circulo(R * .95, 48)]
    elif forma == 'mira':
        tracos = [circulo(R, 64, .25, math.pi / 2 - .25), circulo(R, 64, math.pi / 2 + .25, math.pi - .25), circulo(R, 64, math.pi + .25, 1.5 * math.pi - .25),
                  circulo(R, 64, 1.5 * math.pi + .25, TAU - .25), circulo(R * .5, 48), circulo(R * .12, 16)]
        for a in (0, math.pi / 2, math.pi, 1.5 * math.pi):
            tracos.append([(R * .62 * math.cos(a), R * .62 * math.sin(a)), (R * 1.18 * math.cos(a), R * 1.18 * math.sin(a))])
    else:
        tracos = E['tracos'](rnd, R)
    m = mat_luz('traco', base=.72, borda=.55, cobre=1.0, blend=.35)
    z = E.get('z', .5) if plano == 'XY' else 0.0
    nucleo = curva(tracos, E.get('fino', .85), 'traco', m, plano, z)
    halo = curva(tracos, E.get('fino', .85) * 2.6, 'halo', m, plano, z - (.2 if plano == 'XY' else -.2))
    raiz = bpy.data.objects.new('sigilo', None)
    bpy.context.collection.objects.link(raiz)
    for o in (nucleo, halo):
        o.parent = raiz
        o.data.bevel_factor_mapping_end = 'SPLINE'
    if plano != 'XY':
        raiz.location = V3(0, 0, E.get('z', 0.0))
    giro = E.get('giro', .25)
    sim = E.get('simetria', 1)
    laco = E.get('laco', False)

    def quadro(t):
        if laco:
            desenho, fade, rot = 1.0, E.get('pulso', 0) and (.75 + .25 * math.sin(t * TAU)) or 1.0, t * TAU / sim
        else:
            desenho = chega(t, 0, E.get('desenha', .4))
            fade = 1 - suave(1 - E.get('apaga', .35), 1, t)
            rot = giro * t
        for o in (nucleo, halo):
            o.data.bevel_factor_end = max(.001, desenho)
        if plano == 'XY':
            raiz.rotation_euler = (0, 0, rot)
        else:
            raiz.rotation_euler = (0, rot * .0, 0)
        esc = E.get('cresce', 0.0)
        s = 1 + esc * (t if not laco else 0)
        raiz.scale = (s, s, s)
        nucleo.color = (fade, 1.0, .4 * fade, 1)
        halo.color = (fade, .2, 0, 1)
    return quadro


# ---------- objetos parados (projéteis) e objetos que pairam ----------
def g_objeto(E):
    raiz = E['monta'](E)
    anim = E.get('anim', 'parado')

    def quadro(t):
        if anim == 'paira':
            raiz.location = V3(0, 0, E.get('z', 0.0) + math.sin(t * TAU) * E.get('bob', 3.0))
            raiz.rotation_euler = (0, 0, E.get('giro0', 0.0) + t * TAU * E.get('voltas', 0))
        elif anim == 'gira':
            raiz.rotation_euler = (0, t * TAU, 0)
        if E.get('extra'):
            E['extra'](raiz, t)
    return quadro


# ---------- coisas que irrompem do chão (cristais, espinhos, pilares, raízes) ----------
def g_irrompe(E):
    """E['monta'](E) devolve [(objeto, atraso, altura)]: cada peça sobe do chão com um tranco, fica e afunda no fim."""
    pecas = E['monta'](E)
    for o, atraso, alt in pecas:
        o['z0'] = o.location.z
        o['s0'] = tuple(o.scale)

    def quadro(t):
        for o, atraso, alt in pecas:
            k = chega(t, atraso, atraso + E.get('sobe', .22))
            k = k * (1 + .12 * math.sin(math.pi * min(1, k * 1.0))) if k < 1 else 1.0
            some = suave(1 - E.get('afunda', .3), 1.0, t)
            s0 = o['s0']
            fz = max(.001, k * (1 - some * E.get('encolhe', .6)))
            o.scale = (s0[0] * (.6 + .4 * fz), s0[1] * (.6 + .4 * fz), s0[2] * fz)
            o.location.z = o['z0'] - alt * U * some * E.get('desce', .5)
            acender(o, 1 - some * E.get('some', 1.0))
        if E.get('extra'):
            E['extra'](t)
    return quadro
