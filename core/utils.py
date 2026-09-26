#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Utilitários compartilhados do FS ATAQUE: cores, config, confirmações e alertas.

import os
import sys
import json
import shutil
import subprocess

# Raiz do projeto (pasta fsatack)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.json")

# Cores ANSI (cor 32 = verde conforme identidade visual)
VERDE = "\033[32m"
AMARELO = "\033[33m"
VERMELHO = "\033[31m"
CIANO = "\033[36m"
RESET = "\033[0m"

# Padroes UNICOS de configuracao (o config.json apenas sobrescreve)
DEFAULTS = {
    "threads": 20,
    "timeout": 10,
    "duracao_flood": 15,
    "bruteforce_delay": 1,
    "dry_run": False,
    "vpn_alert": True,
    "phishing_port": 8080,
    "phishing_host": "127.0.0.1",
    "wordlist_users": "wordlists/users.txt",
    "wordlist_passwords": "wordlists/passwords.txt",
    "wordlist_dirs": "wordlists/dirs.txt",
    "wordlist_subs": "wordlists/subs.txt",
    "logs_dir": "logs",
}


def c(txt, cor):
    """Envolve um texto com cor ANSI."""
    return "{}{}{}".format(cor, txt, RESET)


def limpar():
    """Limpa a tela no Termux e no Linux (clear/cls)."""
    os.system("cls" if os.name == "nt" else "clear")


def sair(status=0):
    sys.exit(status)


def carregar_config():
    """Lê o config.json sobreposto aos DEFAULTS (faltando/chave quebrada usa padrao)."""
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            dados = json.load(f)
        if isinstance(dados, dict):
            cfg.update(dados)
    except Exception:
        pass
    return cfg


def parse_extras(extras):
    """Separa os extras da CLI em posicionais e flags.

    Aceita `--port 2222`, `--port=2222` e `--users wl.txt`.
    Retorna (posicionais, {flag: valor}).
    """
    pos, flags = [], {}
    lista = list(extras or [])
    i = 0
    while i < len(lista):
        tok = str(lista[i])
        if tok.startswith("--") and "=" in tok:
            chave, valor = tok[2:].split("=", 1)
            flags[chave] = valor
        elif tok.startswith("--"):
            chave = tok[2:]
            if i + 1 < len(lista) and not str(lista[i + 1]).startswith("--"):
                flags[chave] = str(lista[i + 1])
                i += 1
            else:
                flags[chave] = "1"
        else:
            pos.append(tok)
        i += 1
    return pos, flags


def mascarar(segredo, mantidos=0):
    """Mascara um segredo para logs (nunca grava senha em texto puro)."""
    txt = str(segredo)
    if not txt:
        return ""
    if mantidos > 0:
        return txt[:mantidos] + "*" * max(3, len(txt) - mantidos)
    return "***"


def caminho(rel):
    """Converte caminho relativo do projeto em absoluto."""
    if os.path.isabs(rel):
        return rel
    return os.path.join(ROOT, rel)


def eh_termux():
    """Detecta se está rodando dentro do Termux."""
    return bool(os.environ.get("PREFIX")) and os.path.isdir("/data/data/com.termux")


def plataforma():
    return "Termux" if eh_termux() else "Linux"


def ler_lista(rel):
    """Lê uma wordlist (uma entrada por linha, # = comentário)."""
    caminho_abs = caminho(rel)
    try:
        with open(caminho_abs, encoding="utf-8", errors="ignore") as f:
            return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    except FileNotFoundError:
        return []


def ferramenta_existe(nome):
    """Verifica se um binário externo está no PATH."""
    return shutil.which(nome) is not None


def _somente_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _comando_instalacao(nome):
    """Lista-argumento do gerenciador de pacotes (nunca passa por shell)."""
    if eh_termux():
        return ["pkg", "install", "-y", nome]
    sudo = [] if _somente_root() or not shutil.which("sudo") else ["sudo"]
    if shutil.which("apt-get"):
        return sudo + ["apt-get", "install", "-y", nome]
    if shutil.which("pacman"):
        return sudo + ["pacman", "-S", "--noconfirm", nome]
    if shutil.which("apk"):
        return sudo + ["apk", "add", nome]
    return None


def instalar_ferramenta(nome):
    """Oferece instalação automática via pkg (Termux), apt, pacman ou apk."""
    cmd = _comando_instalacao(nome)
    if not cmd:
        print(c("  Nenhum gerenciador de pacotes detectado.", VERMELHO))
        return False
    try:
        resp = input(c("  Deseja instalar '{}' agora? (S/n): ".format(nome), AMARELO)).strip().lower()
    except EOFError:
        return False
    if resp not in ("s", "sim", "y", "yes", ""):
        return False
    print(c("  Executando: {}".format(" ".join(cmd)), CIANO))
    try:
        return subprocess.run(cmd).returncode == 0
    except Exception as erro:
        print(c("  Falha ao executar: {}".format(erro), VERMELHO))
        return False


def exigir_ferramenta(nome):
    """Garante que uma ferramenta existe; oferece instalação se faltar."""
    if ferramenta_existe(nome):
        return True
    print(c("  Ferramenta '{}' não encontrada no sistema.".format(nome), VERMELHO))
    return instalar_ferramenta(nome)


def instalar_dependencia(modulo, pacote=None):
    """Oferece instalação automática de pacote Python — o usuário apenas
    seleciona [1] Instalar agora / [2] Continuar sem (nenhum comando manual).
    Retorna True se o módulo passar a importar após a instalação."""
    pacote = pacote or modulo
    print(c("  Pacote Python '{}' não instalado (necessário para '{}').".format(pacote, modulo), VERMELHO))
    try:
        resp = input(c("  [1] Instalar agora  [2] Continuar sem: ", AMARELO)).strip()
    except EOFError:
        return False
    if resp != "1":
        print(c("  Seguindo sem '{}' — recursos dependentes ficam indisponíveis.".format(pacote), AMARELO))
        return False
    print(c("  Instalando {}...".format(pacote), CIANO))
    exe = sys.executable
    # 1ª tentativa: apenas wheels (nunca compila código-fonte)
    status = subprocess.run([exe, "-m", "pip", "install", "--only-binary", ":all:", pacote]).returncode
    if status != 0:
        status = subprocess.run([exe, "-m", "pip", "install", "--user", pacote]).returncode
    if status == 0:
        try:
            __import__(modulo)
            print(c("  '{}' instalado com sucesso.".format(pacote), VERDE))
            return True
        except Exception as erro:
            print(c("  Instalado, mas o import falhou: {}".format(erro), AMARELO))
            return False
    print(c("  Falha ao instalar '{}' (sem wheel para esta plataforma).".format(pacote), VERMELHO))
    print(c("  Detalhes: rode 'pip install {}' ou use o instalador do projeto.".format(pacote), AMARELO))
    return False


def alerta_vpn():
    """Alerta padrão exibido ao lado dos comandos ofensivos."""
    print(c(" ⚠ Recomendado uso de VPN antes de executar este comando.", AMARELO))


def confirmar_destrutivo(modulo):
    """Confirmação dupla: digitar CONFIRMO para módulos destrutivos."""
    print(c("  ATENÇÃO: '{}' é um módulo destrutivo/interruptivo.".format(modulo), VERMELHO))
    print(c("  Use somente em alvos laboratoriais sob SEU controle.", AMARELO))
    try:
        resp = input("  Digite CONFIRMO para prosseguir: ").strip()
    except EOFError:
        print(c("  Sem entrada disponivel — cancelado.", VERMELHO))
        return False
    if resp != "CONFIRMO":
        print(c("  Cancelado pelo usuário.", VERMELHO))
        return False
    return True


def confirmar(txt, padrao="n"):
    """Confirmação simples (S/n)."""
    try:
        resp = input("{} ({}) ".format(txt, padrao)).strip().lower()
    except EOFError:
        return padrao in ("s", "sim")
    if not resp:
        return padrao in ("s", "sim")
    return resp in ("s", "sim", "y", "yes")


def perguntar(txt, padrao=""):
    """Pede input com valor padrão."""
    sufixo = " [{}]".format(padrao) if padrao else ""
    try:
        resp = input(" {}{}: ".format(txt, sufixo)).strip()
    except EOFError:
        return padrao
    return resp if resp else padrao


def is_dry(ctx):
    """Verifica se o contexto está em modo dry-run."""
    return bool(ctx.get("dry"))


def mostrar_dry(modulo, resumo):
    """Exibe o que seria feito no dry-run, sem executar nada."""
    print(c(" [DRY-RUN] {}: {}".format(modulo, resumo), CIANO))
    print(c("  Nenhuma ação real foi executada.", CIANO))


def log(modulo, alvo, resultado, extra=None):
    """Atalho para registrar evento no logger."""
    from core import logger  # import tardio evita ciclo
    logger.registrar(modulo, alvo, resultado, extra)
