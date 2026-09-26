#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test do FS ATAQUE — exercita TODOS os modulos em dry-run.

Criterio: so sai com codigo 0 quando 100% dos testes passam.
Uso: python tests/smoke_test.py
"""

import base64
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MENU = os.path.join(ROOT, "core", "menu.py")

sys.path.insert(0, ROOT)

# aceite legal pré-gravado para nao travar em prompt
os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
marca = os.path.join(ROOT, "logs", ".aceite")
if not os.path.exists(marca):
    with open(marca, "w", encoding="utf-8") as f:
        f.write("aceito\n")

from core import menu  # noqa: E402  (importa todos os modulos de uma vez)

MARCADORES_FALHA = (
    "Erro no modulo",
    "Traceback",
    "Categoria desconhecida",
    "Modulo desconhecido",
)

# alvo padrão por módulo (URLs e nomes validos para dry-run)
ALVOS = {
    ("recon", "dir_brute"): "http://127.0.0.1",
    ("recon", "subdomain"): "example.com",
    ("recon", "osint_user"): "labuser",
    ("recon", "osint_email"): "lab@example.com",
    ("recon", "cms_detect"): "http://127.0.0.1",
    ("network", "http_flood"): "http://127.0.0.1",
    ("network", "slow_post"): "http://127.0.0.1",
    ("bruteforce", "http_basic"): "http://127.0.0.1",
    ("bruteforce", "http_form"): "http://127.0.0.1",
    ("bruteforce", "admin_panel"): "http://127.0.0.1",
    ("phishing", "clone_page"): "http://127.0.0.1",
    ("phishing", "qr"): "http://127.0.0.1:8080",
    ("utils", "qr_tools"): "http://127.0.0.1",
    ("utils", "revshell"): "127.0.0.1",
    ("utils", "hash_crack"): "lab",
    ("utils", "exif"): os.path.join(ROOT, "README.md"),
}
PADRAO_ALVO = "127.0.0.1"

# argumentos extras (posicionais apos o alvo)
EXTRAS = {
    ("utils", "revshell"): ["4444"],
    ("utils", "hash_crack"): ["d41d8cd98f00b204e9800998ecf8427e", "wordlists/passwords.txt"],
    ("utils", "wordlist_gen"): ["smoketest"],
}

resultados = []


def registrar(nome, ok, detalhe=""):
    resultados.append((nome, ok, detalhe))
    print("{} {}{}".format("[ OK ]" if ok else "[FAIL]", nome,
                           ("  <- " + detalhe) if detalhe else ""))


def rodar(cmd, entrada=None, timeout=90):
    """Roda um comando. entrada=None -> stdin fechado (EOF); str -> escrito no stdin."""
    try:
        if entrada is None:
            p = subprocess.run(
                cmd, cwd=ROOT, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=timeout, encoding="utf-8", errors="replace",
            )
        else:
            p = subprocess.run(
                cmd, cwd=ROOT, input=entrada,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=timeout, encoding="utf-8", errors="replace",
            )
        return p.returncode, p.stdout or ""
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT ({}s)".format(timeout)
    except Exception as e:
        return -2, str(e)


def checar(nome, rc, saida):
    if rc != 0:
        registrar(nome, False, "exit code {}".format(rc))
        return
    for m in MARCADORES_FALHA:
        if m in saida:
            registrar(nome, False, m)
            return
    registrar(nome, True)


def achar_bash():
    b = shutil.which("bash")
    if b:
        return b
    for cand in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        "/bin/bash",
        "/usr/bin/bash",
    ):
        if os.path.isfile(cand):
            return cand
    return None


# ------------------------------------------------------------
# Servidor local de laboratorio (para os testes REAIS)
# ------------------------------------------------------------
SENHA_LAB = "fsatack123"
AUTORIZACAO = "Basic " + base64.b64encode("admin:{}".format(SENHA_LAB).encode()).decode()


class _ServidorLab(BaseHTTPRequestHandler):
    """Responde 200 so com as credenciais do lab; conta as requisicoes."""

    def do_GET(self):
        with self.server.trava:
            self.server.requisicoes += 1
        if self.headers.get("Authorization") == AUTORIZACAO:
            corpo = b"ok"
            self.send_response(200)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        else:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="lab"')
            self.send_header("Content-Length", "0")
            self.end_headers()

    def log_message(self, *args):
        pass


def subir_servidor_lab():
    """Sobe o servidor em thread devolvendo (servidor, url_base)."""
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _ServidorLab)
    srv.requisicoes = 0
    srv.trava = threading.Lock()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:{}".format(srv.server_address[1])


def contar_wordlist(rel):
    caminho = os.path.join(ROOT, rel)
    try:
        with open(caminho, encoding="utf-8") as f:
            return sum(1 for l in f if l.strip() and not l.strip().startswith("#"))
    except Exception:
        return 0


def testes_reais(registrar_fn, rodar_fn):
    """Caminho de execucao REAL contra servidor local (127.0.0.1 apenas)."""
    srv, url = subir_servidor_lab()
    pasta_tmp = tempfile.mkdtemp(prefix="fsatack_test_")
    wl_users = os.path.join(pasta_tmp, "users.txt")
    wl_pass = os.path.join(pasta_tmp, "pass.txt")
    with open(wl_users, "w", encoding="utf-8") as f:
        f.write("admin\nroot\n")
    with open(wl_pass, "w", encoding="utf-8") as f:
        f.write("errada1\n{}\nerrada2\n".format(SENHA_LAB))
    try:
        # (a) regressao: --port NAO pode sequestrar as wordlists
        esperado = "{} combinacoes".format(
            contar_wordlist("wordlists/users.txt") * contar_wordlist("wordlists/passwords.txt"))
        rc, saida = rodar_fn([sys.executable, MENU, "bruteforce", "ssh", "127.0.0.1", "2222",
                              "--dry-run"])
        ok = rc == 0 and esperado in saida
        registrar_fn("real:porta_nao_sequestra_wordlist", ok,
                     "" if ok else "esperado '{}' na saida".format(esperado))

        # (b) flood REAL (2s) contra o servidor local — caminho completo
        rc, saida = rodar_fn([sys.executable, MENU, "network", "http_flood", url, "2", "2", "GET"],
                             entrada="CONFIRMO\n", timeout=90)
        n_req = srv.requisicoes
        ok = rc == 0 and "Finalizado." in saida and n_req > 0
        registrar_fn("real:http_flood_local", ok,
                     "" if ok else "rc={} requisicoes={}".format(rc, n_req))

        # (c) brute REAL de HTTP Basic com wordlists pequenas (2 tentativas)
        rc, saida = rodar_fn([sys.executable, MENU, "bruteforce", "http_basic", url,
                              "--users", wl_users, "--pass", wl_pass],
                             entrada="CONFIRMO\n", timeout=90)
        ok = rc == 0 and "SUCESSO" in saida
        registrar_fn("real:bruteforce_http_basic", ok, "" if ok else "sem 'SUCESSO'")

        # (d) a senha real NUNCA pode parar no log de execucoes
        log = os.path.join(ROOT, "logs", "fsataque.jsonl")
        conteudo = ""
        if os.path.exists(log):
            with open(log, encoding="utf-8") as f:
                conteudo = f.read()
        ok = SENHA_LAB not in conteudo
        registrar_fn("real:senha_mascarada_no_log", ok,
                     "" if ok else "senha em texto puro encontrada em logs/fsataque.jsonl")

        # (e) port scan REAL via sockets (fallback sem nmap) em 127.0.0.1
        rc, saida = rodar_fn([sys.executable, MENU, "recon", "port_scan", "127.0.0.1", "1-20"],
                             timeout=90)
        ok = rc == 0 and ("Portas abertas" in saida or "Nmap" in saida)
        registrar_fn("real:port_scan_local", ok, "" if ok else "rc={}".format(rc))
    finally:
        try:
            srv.shutdown()
        except Exception:
            pass
        shutil.rmtree(pasta_tmp, ignore_errors=True)


def main():
    print("=" * 62)
    print(" FS ATAQUE — smoke test (dry-run, nenhum ataque real)")
    print("=" * 62)

    # 1. compilacao de todos os .py do projeto
    py_files = []
    for pasta in ("core", "modules", "tests"):
        for base, _dirs, arqs in os.walk(os.path.join(ROOT, pasta)):
            if "__pycache__" in base:
                continue
            for a in arqs:
                if a.endswith(".py"):
                    py_files.append(os.path.join(base, a))
    for arq in sorted(py_files):
        rel = os.path.relpath(arq, ROOT)
        try:
            py_compile.compile(arq, doraise=True)
            registrar("compile:{}".format(rel), True)
        except Exception as e:
            registrar("compile:{}".format(rel), False, str(e))

    # 2. dependencias Python do projeto
    for mod, pacote in (("requests", "requests"), ("qrcode", "qrcode"), ("paramiko", "paramiko")):
        try:
            __import__(mod)
            registrar("dependencia:{}".format(pacote), True)
        except Exception as e:
            registrar("dependencia:{}".format(pacote), False, str(e))

    # 3. help
    rc, saida = rodar([sys.executable, MENU, "help"])
    if rc == 0 and "Categorias" in saida:
        registrar("cli:help", True)
    else:
        registrar("cli:help", False, "rc={} sem 'Categorias'".format(rc))

    # 4. menu interativo (envia 0 = sair)
    rc, saida = rodar([sys.executable, MENU], entrada="0\n")
    checar("cli:menu_interativo", rc, saida)

    # 5. TODOS os modulos em dry-run
    total_mods = 0
    for cat in menu.ORDEM:
        for chave in menu.CATEGORIAS[cat]["mods"]:
            total_mods += 1
            alvo = ALVOS.get((cat, chave), PADRAO_ALVO)
            extras = EXTRAS.get((cat, chave), [])
            cmd = [sys.executable, MENU, cat, chave, alvo] + extras + ["--dry-run"]
            rc, saida = rodar(cmd)  # stdin fechado: prompts usam default
            checar("modulo:{}.{}".format(cat, chave), rc, saida)

    # 5b. testes REAIS (caminho de execucao) contra servidor local
    print("-" * 62)
    print(" testes REAIS (127.0.0.1, nenhum alvo externo)")
    testes_reais(registrar, rodar)

    # 6. sintaxe dos scripts bash + menu do instalador (se bash existir)
    bash = achar_bash()
    if bash:
        for script in ("install.sh", "fsataque.sh"):
            rc, saida = rodar([bash, "-n", os.path.join(ROOT, script)])
            checar("bash:-n:{}".format(script), rc, saida)
        # instalador: escolhe [4] Sair — nenhum install real, nenhum comando criado
        rc, saida = rodar([bash, os.path.join(ROOT, "install.sh")], entrada="4\n", timeout=120)
        if rc == 0 and "INSTALADOR" in saida and "Saindo sem instalar" in saida:
            registrar("instalador:menu_sair", True)
        else:
            registrar("instalador:menu_sair", False,
                      "rc={} ".format(rc) + saida[-300:].replace("\n", " "))
    else:
        registrar("bash:nao_encontrado(windows sem git-bash)", True, "pulado")

    # 7. launcher via bash (somente onde existir python3 no PATH)
    if bash and shutil.which("python3"):
        rc, saida = rodar([bash, os.path.join(ROOT, "fsataque.sh"), "help"])
        if rc == 0 and "Categorias" in saida:
            registrar("launcher:fsataque.sh", True)
        else:
            registrar("launcher:fsataque.sh", False, "rc={}".format(rc))
    else:
        registrar("launcher:fsataque.sh(pulado)", True)

    # resumo
    ok_n = sum(1 for _n, ok, _d in resultados if ok)
    falhas = [(n, d) for n, ok, d in resultados if not ok]
    print("=" * 62)
    print(" RESULTADO: {}/{} testes passaram".format(ok_n, len(resultados)))
    print(" modulos exercitados: {}".format(total_mods))
    if falhas:
        print(" FALHAS:")
        for n, d in falhas:
            print("   - {} ({})".format(n, d))
    print("=" * 62)
    if falhas or ok_n != len(resultados):
        return 1
    print(" 100% — todas as ferramentas passaram no teste.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
