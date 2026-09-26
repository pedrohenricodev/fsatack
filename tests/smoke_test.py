#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test do FS ATAQUE — exercita TODOS os modulos em dry-run.

Criterio: so sai com codigo 0 quando 100% dos testes passam.
Uso: python tests/smoke_test.py
"""

import os
import py_compile
import shutil
import subprocess
import sys

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

    # 6. sintaxe dos scripts bash + menu do instalador (se bash existir)
    bash = achar_bash()
    if bash:
        for script in ("install.sh", "fsataque.sh"):
            rc, saida = rodar([bash, "-n", os.path.join(ROOT, script)])
            checar("bash:-n:{}".format(script), rc, saida)
        # instalador: escolhe [4] Sair — nenhum install real
        rc, saida = rodar([bash, os.path.join(ROOT, "install.sh")], entrada="4\n", timeout=120)
        if rc == 0 and "INSTALADOR" in saida:
            registrar("instalador:menu_sair", True)
        else:
            registrar("instalador:menu_sair", False, "rc={} ".format(rc) + saida[-300:].replace("\n", " "))
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
