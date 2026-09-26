#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Wireless SOMENTE LEITURA (sem root): deauth/evil twin/ARP NAO existem aqui.

import json
import os
import time
import subprocess

from core import utils


def _run(cmd, timeout=60):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return None
    except Exception as e:
        return "[erro] {}".format(e)


def _scan_termux():
    """Scan via Termux:API (termux-wifi-scaninfo)."""
    saida = _run(["termux-wifi-scaninfo"])
    if not saida or saida.startswith("["):
        return None
    try:
        dados = json.loads(saida)
        resultados = []
        for item in dados:
            resultados.append({
                "ssid": item.get("ssid", "(oculto)"),
                "bssid": item.get("bssid", "-"),
                "canal": item.get("frequency", "-"),
                "nivel": item.get("level", "-"),
                "capacidades": item.get("capabilities", ""),
            })
        return resultados
    except Exception:
        return None


def _scan_linux():
    """Scan via nmcli (NetworkManager) ou iw."""
    saida = _run(["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "dev", "wifi"])
    if saida and "ERROR" not in saida and saida.strip():
        resultados = []
        for linha in saida.strip().splitlines():
            partes = linha.split(":")
            if len(partes) < 5:
                continue
            resultados.append({
                "ssid": partes[0] or "(oculto)",
                "bssid": partes[1],
                "canal": partes[2],
                "nivel": partes[3],
                "capacidades": ":".join(partes[4:]),
            })
        return resultados
    # Fallback: iw scan (pode exigir permissao)
    saida_iw = _run(["iw", "dev"], timeout=30)
    iface = None
    if saida_iw:
        for linha in saida_iw.splitlines():
            if "Interface" in linha:
                iface = linha.split()[-1]
                break
    if iface:
        saida = _run(["sudo", "iw", "dev", iface, "scan"], timeout=90)
        if saida:
            resultados = []
            atual = {}
            for linha in saida.splitlines():
                linha = linha.strip()
                if linha.startswith("BSS "):
                    if atual:
                        resultados.append(atual)
                    atual = {"bssid": linha.split()[1].rstrip(":"), "ssid": "", "canal": "-", "nivel": "-", "capacidades": ""}
                elif linha.startswith("SSID:"):
                    atual["ssid"] = linha.split(":", 1)[1].strip() or "(oculto)"
                elif linha.startswith("signal:"):
                    atual["nivel"] = linha.split(":", 1)[1].strip()
                elif linha.startswith("DS Parameter set: canal"):
                    atual["canal"] = linha.split()[-1]
                elif linha.startswith("WPS:"):
                    atual["capacidades"] += " WPS"
            if atual:
                resultados.append(atual)
            return resultados
    return None


def _scan():
    """Escolhe o melhor método de scan disponível."""
    if utils.eh_termux():
        return _scan_termux()
    return _scan_linux()


def _imprimir_tabela(redes):
    print("  {:3s} {:28s} {:18s} {:6s} {:8s}".format("#", "SSID", "BSSID", "CANAL", "SINAL"))
    for i, r in enumerate(redes, 1):
        print("  {:3d} {:28.28s} {:18s} {:6s} {:8s}".format(
            i, str(r.get("ssid", "-")), str(r.get("bssid", "-")),
            str(r.get("canal", "-")), str(r.get("nivel", "-"))))


def wifi_scan(alvo, ctx):
    """Wi-Fi Scanner: SSID, BSSID, canal e sinal (leitura)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("wifi_scan", "scan de redes Wi-Fi proximas")
        return
    redes = _scan()
    if redes is None:
        print(utils.c("  Scan indisponivel.", utils.VERMELHO))
        if utils.eh_termux():
            print("  Instale: pkg install termux-api + app Termux:API (F-Droid).")
        else:
            print("  Instale NetworkManager (nmcli) ou rode com sudo para iw scan.")
        utils.log("wifi_scan", "-", "indisponivel")
        return
    _imprimir_tabela(redes)
    utils.log("wifi_scan", "-", "{} redes".format(len(redes)))


def signal_map(alvo, ctx):
    """Mapa de sinal: amostras repetidas por BSSID (texto simples)."""
    amostras = int(ctx["extras"][0]) if ctx["extras"] and ctx["extras"][0].isdigit() else 5
    if utils.is_dry(ctx):
        utils.mostrar_dry("signal_map", "{} amostras de sinal".format(amostras))
        return
    historico = {}
    for n in range(amostras):
        redes = _scan()
        if not redes:
            print(utils.c("  Sem dados de scan.", utils.VERMELHO))
            return
        for r in redes:
            try:
                valor = float(str(r.get("nivel", "0")).split()[0])
            except Exception:
                continue
            historico.setdefault(r.get("bssid", "-"), {"ssid": r.get("ssid"), "sinais": []})
            historico[r.get("bssid", "-")]["sinais"].append(valor)
        print("  Amostra {}/{} registrada...".format(n + 1, amostras))
        time.sleep(3)
    print("\n  {:28s} {:18s} {:8s} {:8s}".format("SSID", "BSSID", "MEDIA", "N"))
    for bssid, dados in historico.items():
        media = sum(dados["sinais"]) / len(dados["sinais"])
        barra = "#" * max(0, int((media + 100) / 5))  # -100..0 dBm
        print("  {:28.28s} {:18s} {:8.1f} {} {}".format(
            str(dados["ssid"]), bssid, media, barra, len(dados["sinais"])))
    utils.log("signal_map", "-", "{} BSSID mapeados".format(len(historico)))


def open_aps(alvo, ctx):
    """Detecta pontos de acesso abertos (sem senha)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("open_aps", "listar APs abertos")
        return
    redes = _scan()
    if not redes:
        print(utils.c("  Sem dados de scan.", utils.VERMELHO))
        return
    abertos = []
    for r in redes:
        seg = str(r.get("capacidades", "")).upper()
        # Aberto = sem marcadores WPA/WEP no resultado do scan
        if ("WPA" not in seg) and ("WEP" not in seg):
            abertos.append(r)
    if not abertos:
        print("  Nenhum AP aberto detectado.")
    else:
        print(utils.c("  APs ABERTOS encontrados:", utils.VERMELHO))
        _imprimir_tabela(abertos)
    utils.log("open_aps", "-", "{} abertos".format(len(abertos)))


def wps_check(alvo, ctx):
    """Detecta WPS habilitado (via iw scan, quando possível)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("wps_check", "procurar WPS nas redes")
        return
    redes = _scan()
    if not redes:
        print(utils.c("  Sem dados de scan.", utils.VERMELHO))
        return
    com_wps = [r for r in redes if "WPS" in str(r.get("capacidades", "")).upper()]
    if com_wps:
        print(utils.c("  Redes com WPS habilitado:", utils.AMARELO))
        _imprimir_tabela(com_wps)
    else:
        print("  Nenhuma rede com WPS detectada (o campo pode nao ser exposto pelo scan).")
    utils.log("wps_check", "-", "{} com WPS".format(len(com_wps)))
