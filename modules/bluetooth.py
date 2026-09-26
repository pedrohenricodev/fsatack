#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Bluetooth / BLE SOMENTE LEITURA (scanner). Sem spam/flood (excluídos do escopo).

import os
import subprocess
import tempfile

from core import utils


def _run(cmd, timeout=30):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return None
    except Exception as e:
        return "[erro] {}".format(e)


def ble_scan(alvo, ctx):
    """Descobre dispositivos BLE próximos (hcitool/bluetoothctl no Linux)."""
    duracao = int(ctx["extras"][0]) if ctx["extras"] and ctx["extras"][0].isdigit() else 10
    if utils.is_dry(ctx):
        utils.mostrar_dry("ble_scan", "scan BLE por {}s".format(duracao))
        return
    if utils.eh_termux():
        print(utils.c("  Termux nao expoe scan BLE sem root/permissoes especiais.", utils.AMARELO))
        print("  Disponivel apenas via Termux:API basica (pareamento), nao descoberta.")
        utils.log("ble_scan", "-", "indisponivel no Termux")
        return
    if utils.ferramenta_existe("hcitool"):
        # hcitool lescan roda infinitamente — usamos Popen e matamos no tempo
        with tempfile.TemporaryFile(mode="w+") as f:
            proc = subprocess.Popen(["hcitool", "lescanning"], stdout=f, stderr=subprocess.DEVNULL)
            try:
                import time
                time.sleep(duracao)
            finally:
                proc.kill()
            f.seek(0)
            linhas = f.read()
        vistos = set()
        for linha in linhas.splitlines():
            if ":" in linha and not linha.startswith("Failed"):
                partes = linha.split(None, 1)
                addr = partes[0]
                nome = partes[1] if len(partes) > 1 else ""
                if addr not in vistos:
                    vistos.add(addr)
                    print("  {}  {}".format(addr, nome))
        print("  {} dispositivos encontrados.".format(len(vistos)))
        utils.log("ble_scan", "-", "{} dispositivos".format(len(vistos)))
        return
    if utils.ferramenta_existe("bluetoothctl"):
        saida = _run(["timeout", str(duracao), "bluetoothctl", "--", "scan", "on"], timeout=duracao + 10)
        print((saida or "")[:4000])
        utils.log("ble_scan", "-", "bluetoothctl scan")
        return
    print(utils.c("  Nenhuma ferramenta BLE (hcitool/bluetoothctl).", utils.VERMELHO))
    print("  Instale: pkg install root-repo && pkg install bluez / apt install bluez")
    utils.log("ble_scan", "-", "sem ferramentas")
