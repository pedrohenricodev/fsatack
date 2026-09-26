#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Logger do FS ATAQUE: grava data, módulo, alvo e resultado em JSONL.

import os
import json
from datetime import datetime

from core import utils


def registrar(modulo, alvo, resultado, extra=None):
    """Registra uma execução em logs/fsataque.jsonl (nunca derruba a CLI)."""
    try:
        cfg = utils.carregar_config()
        pasta = utils.caminho(cfg.get("logs_dir", "logs"))
        os.makedirs(pasta, exist_ok=True)
        evento = {
            "data": datetime.now().isoformat(timespec="seconds"),
            "modulo": str(modulo),
            "alvo": str(alvo) if alvo is not None else "-",
            "resultado": str(resultado),
        }
        if extra:
            evento["extra"] = extra
        with open(os.path.join(pasta, "fsataque.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except Exception as e:
        print(utils.c("  (log ignorado: {})".format(e), utils.AMARELO))


def ultimos(n=20):
    """Retorna as últimas n linhas de log formatadas."""
    cfg = utils.carregar_config()
    caminho_log = os.path.join(utils.caminho(cfg.get("logs_dir", "logs")), "fsataque.jsonl")
    try:
        with open(caminho_log, encoding="utf-8") as f:
            linhas = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        return ["(nenhum log ainda)"]
    saida = []
    for linha in linhas[-n:]:
        try:
            ev = json.loads(linha)
            saida.append("{} | {} | {} | {}".format(
                ev.get("data"), ev.get("modulo"), ev.get("alvo"), ev.get("resultado")))
        except Exception:
            saida.append(linha)
    return saida
