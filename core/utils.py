#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Utilitários compartilhados do FS ATAQUE: cores, config, confirmações e alertas.

import os
import sys
import json
import shutil

# Raiz do projeto (pasta fsatack)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.json")

# Cores ANSI (cor 32 = verde conforme identidade visual)
VERDE = "\033[32m"
AMARELO = "\033[33m"
VERMELHO = "\033[31m"
CIANO = "\033[36m"
RESET = "\033[0m"


def c(txt, cor):
    """Envolve um texto com cor ANSI."""
    return "{}{}{}".format(cor, txt, RESET)


def limpar():
    """Limpa a tela no Termux e no Linux (clear/cls)."""
    os.system("cls" if os.name == "nt" else "clear")


def sair(status=0):
    sys.exit(status)


def carregar_config():
    """Lê o config.json (retorna padrões caso esteja quebrado)."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "threads": 20,
            "timeout": 10,
            "duracao_flood": 15,
            "bruteforce_delay": 1,
            "dry_run": False,
            "vpn_alert": True,
            "phishing_port": 8080,
            "wordlist_users": "wordlists/users.txt",
            "wordlist_passwords": "wordlists/passwords.txt",
            "wordlist_dirs": "wordlists/dirs.txt",
            "wordlist_subs": "wordlists/subs.txt",
            "logs_dir": "logs",
        }


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


def instalar_ferramenta(nome):
    """Oferece instalação automática via pkg (Termux) ou apt (Linux)."""
    if eh_termux():
        cmd = "pkg install -y {}".format(nome)
    else:
        cmd = "sudo apt-get install -y {}".format(nome)
    try:
        resp = input(c("  Deseja instalar '{}' agora? (S/n): ".format(nome), AMARELO)).strip().lower()
    except EOFError:
        return False
    if resp not in ("s", "sim", "y", "yes", ""):
        return False
    print(c("  Executando: {}".format(cmd), CIANO))
    return os.system(cmd) == 0


def exigir_ferramenta(nome):
    """Garante que uma ferramenta existe; oferece instalação se faltar."""
    if ferramenta_existe(nome):
        return True
    print(c("  Ferramenta '{}' não encontrada no sistema.".format(nome), VERMELHO))
    return instalar_ferramenta(nome)


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
