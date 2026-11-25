# Prévia do polimento: quadro 0 (e o golpe, se pedido) de alguns monstros com a câmera do sprite do jogo, numa pasta de teste.
# Uso: blender --background --factory-startup --python piloto_monstros.py -- <pasta_saida> slug1,slug2,... [golpe]
import sys, os, math, time
FONTES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'arte', 'blender', 'fontes')
sys.path.insert(0, FONTES)
args = sys.argv[sys.argv.index('--') + 1:]
saida, lista = args[0], args[1].split(',')
golpe = len(args) > 2 and args[2] == 'golpe'
sys.argv = [sys.argv[0]]   # gerar.py roda main() ao ser importado; sem argumentos ele não faz nada
import bpy
import kit_base as K
import gerar as G
import kit_monstros as KM
todos = {e[0]: e for e in G.inimigos()}
for s in lista:
    s0, nome, kind, cor, papel = todos[s]
    t0 = time.time()
    K.limpar()
    K.ACAB = os.environ.get('BRASALUME_SEM_ACAB') is None
    K.mundo((.012, .014, .018), 1.0)
    R, topo = KM.construir(nome, kind, cor, papel, marcador=False)
    R.rotation_euler = (0, 0, math.radians(210))
    alvo = topo * K.U * .55 + (.06 if papel else 0)
    aro = '#e8c45a' if papel in ('boss', 'dboss') else '#c792ee' if papel == 'field' else '#9fb8d8'
    K.estudio(alvo_z=alvo, aro=aro)
    escala = max(topo + 34 + (14 if papel else 0), G.LARGURA.get(kind, 100)) * K.U * G.MARGEM
    K.camera(elev_graus=30, alvo_z=alvo, escala=escala)
    lado = round(320 * G.MARGEM)
    K.config_render(lado, lado, amostras=16, transparente=True)
    KM.pose(R, kind, 0)
    K.render(os.path.join(saida, s + '.png'))
    if golpe:
        KM.pose(R, kind, 0, ataque=True)
        K.render(os.path.join(saida, s + '_golpe.png'))
    print('PILOTO_OK', s, kind, round(time.time() - t0, 1), flush=True)
