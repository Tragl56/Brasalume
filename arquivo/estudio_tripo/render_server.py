"""Estúdio de sprites do Brasalume: serve a pasta idle (o jogo, o estúdio em /assets/render.html e os
modelos da Tripo) e grava os PNGs que a página do estúdio envia.

Uso: python -I render_server.py [porta]   (padrão 8790; só escuta em 127.0.0.1)
Grava em E:\\RPGjogo\\idle\\sprites\\ apenas nomes simples (a-z, 0-9, _) com extensão .png ou .json.
"""
import http.server
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SPRITES = HERE.parent / 'sprites'
MAX_BODY = 8 * 1024 * 1024


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE.parent), **kw)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_POST(self):
        m = re.fullmatch(r'/save/([a-z0-9_]+)\.(png|json)', self.path)
        n = int(self.headers.get('Content-Length') or 0)
        if not m or n <= 0 or n > MAX_BODY:
            self.send_error(400, 'nome ou tamanho inválido')
            return
        data = self.rfile.read(n)
        if m.group(2) == 'png' and not data.startswith(b'\x89PNG\r\n\x1a\n'):
            self.send_error(400, 'não é PNG')
            return
        if m.group(2) == 'json':
            try:
                json.loads(data.decode('utf-8'))
            except ValueError:
                self.send_error(400, 'JSON inválido')
                return
        SPRITES.mkdir(exist_ok=True)
        (SPRITES / f'{m.group(1)}.{m.group(2)}').write_bytes(data)
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write('[estudio] ' + (fmt % args) + '\n')


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
    print(f'Estúdio de sprites em http://127.0.0.1:{port}/assets/render.html', flush=True)
    http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
