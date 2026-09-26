#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Módulos de scanning / recon (funcionam sem root no Termux e no Linux).

import os
import re
import socket
import ssl
import subprocess
import json
import urllib.request
import urllib.parse

from core import utils


def _run(cmd, timeout=180):
    """Executa comando externo e retorna a saída (None se não existir)."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return "[erro] {}".format(e)


def _expandir_portas(txt):
    """Converte '80,443,8000-8010' em lista de inteiros."""
    portas = []
    for pedaco in str(txt).split(","):
        pedaco = pedaco.strip()
        if "-" in pedaco:
            a, b = pedaco.split("-", 1)
            portas.extend(range(int(a), int(b) + 1))
        elif pedaco.isdigit():
            portas.append(int(pedaco))
    return portas


def port_scan(alvo, ctx):
    """Scan TCP Connect (nmap -sT ou fallback com sockets puros)."""
    cfg = ctx["config"]
    faixa = ctx["extras"][0] if ctx["extras"] else "1-1024"
    if utils.is_dry(ctx):
        utils.mostrar_dry("port_scan", "TCP connect scan em {} portas {}".format(alvo, faixa))
        return
    if utils.ferramenta_existe("nmap"):
        saida = _run(["nmap", "-sT", "-p", faixa, alvo])
        print(saida)
        utils.log("port_scan", alvo, "nmap -sT concluido")
        return
    # Fallback sem nmap: scan com sockets (limite de 1024 portas por vez)
    print(utils.c("  nmap nao encontrado — usando scan com sockets.", utils.AMARELO))
    abertas = []
    for porta in _expandir_portas(faixa)[:1024]:
        s = socket.socket()
        s.settimeout(min(cfg.get("timeout", 10), 1.0))
        try:
            if s.connect_ex((alvo, porta)) == 0:
                abertas.append(porta)
                print(utils.c("  [ABERTA] {}".format(porta), utils.VERDE))
        except Exception:
            pass
        finally:
            s.close()
    print("  Portas abertas: {}".format(abertas))
    utils.log("port_scan", alvo, "abertas: {}".format(abertas))


def service_detect(alvo, ctx):
    """Detecção de serviço/versão (nmap -sV)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("service_detect", "nmap -sV em {}".format(alvo))
        return
    if not utils.exigir_ferramenta("nmap"):
        return
    saida = _run(["nmap", "-sV", "-p", "1-1024", alvo])
    print(saida)
    utils.log("service_detect", alvo, "nmap -sV concluido")


def web_vuln(alvo, ctx):
    """Scanner de vulnerabilidades web (nikto)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("web_vuln", "nikto -h {}".format(alvo))
        return
    if not utils.exigir_ferramenta("nikto"):
        return
    saida = _run(["nikto", "-h", alvo], timeout=600)
    print(saida)
    utils.log("web_vuln", alvo, "nikto concluido")


def nuclei(alvo, ctx):
    """Vulnerability templates (nuclei)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("nuclei", "nuclei -u {}".format(alvo))
        return
    if not utils.exigir_ferramenta("nuclei"):
        return
    saida = _run(["nuclei", "-u", alvo], timeout=600)
    print(saida)
    utils.log("nuclei", alvo, "nuclei concluido")


def dir_brute(alvo, ctx):
    """Brute force de diretórios (gobuster/feroxbuster ou fallback Python)."""
    cfg = ctx["config"]
    wordlist = ctx["extras"][0] if ctx["extras"] else cfg.get("wordlist_dirs", "wordlists/dirs.txt")
    caminho_wl = utils.caminho(wordlist)
    if utils.is_dry(ctx):
        utils.mostrar_dry("dir_brute", "wordlist {} em {}".format(caminho_wl, alvo))
        return
    if utils.ferramenta_existe("feroxbuster"):
        saida = _run(["feroxbuster", "-u", alvo, "-w", caminho_wl], timeout=900)
    elif utils.ferramenta_existe("gobuster"):
        saida = _run(["gobuster", "dir", "-u", alvo, "-w", caminho_wl, "-q"], timeout=900)
    else:
        # Fallback: tenta cada caminho com urllib e mostra os códigos interessantes
        print(utils.c("  gobuster/feroxbuster nao encontrados — fallback Python.", utils.AMARELO))
        dirs = utils.ler_lista(wordlist)
        for d in dirs:
            url = alvo.rstrip("/") + "/" + d
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=cfg.get("timeout", 10)) as r:
                    print(utils.c("  [{}] {}".format(r.status, url), utils.VERDE))
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    print(utils.c("  [{}] {}".format(e.code, url), utils.AMARELO))
            except Exception:
                pass
        utils.log("dir_brute", alvo, "fallback python concluido")
        return
    print(saida)
    utils.log("dir_brute", alvo, "concluido")


def subdomain(alvo, ctx):
    """Enumeração de subdomínios (subfinder/assetfinder ou DNS brute)."""
    cfg = ctx["config"]
    if utils.is_dry(ctx):
        utils.mostrar_dry("subdomain", "enumerar subdominios de {}".format(alvo))
        return
    if utils.ferramenta_existe("subfinder"):
        saida = _run(["subfinder", "-d", alvo, "-silent"], timeout=300)
    elif utils.ferramenta_existe("assetfinder"):
        saida = _run(["assetfinder", "--subs-only", alvo], timeout=300)
    else:
        # Fallback: brute DNS com wordlist própria
        print(utils.c("  subfinder nao encontrado — DNS brute com wordlist interna.", utils.AMARELO))
        achados = []
        for sub in utils.ler_lista(cfg.get("wordlist_subs", "wordlists/subs.txt")):
            host = "{}.{}".format(sub, alvo)
            try:
                ip = socket.gethostbyname(host)
                achados.append("{} -> {}".format(host, ip))
                print(utils.c("  {}".format(achados[-1]), utils.VERDE))
            except Exception:
                pass
        utils.log("subdomain", alvo, "achados: {}".format(achados))
        return
    print(saida)
    utils.log("subdomain", alvo, "concluido")


def whois_dns(alvo, ctx):
    """WHOIS + resolução DNS."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("whois_dns", "whois/dns de {}".format(alvo))
        return
    try:
        infos = socket.getaddrinfo(alvo, None)
        ips = sorted({i[4][0] for i in infos})
        print("  IPs: {}".format(ips))
    except Exception as e:
        print(utils.c("  Falha DNS: {}".format(e), utils.VERMELHO))
        ips = []
    if utils.ferramenta_existe("whois"):
        saida = _run(["whois", alvo])
        print((saida or "")[:3000])
    else:
        print(utils.c("  whois nao instalado (pkg install whois / apt install whois).", utils.AMARELO))
    utils.log("whois_dns", alvo, "ips: {}".format(ips))


def osint_user(alvo, ctx):
    """OSINT de username (sherlock ou fallback HTTP em sites comuns)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("osint_user", "buscar username '{}' em redes".format(alvo))
        return
    if utils.ferramenta_existe("sherlock"):
        saida = _run(["sherlock", alvo, "--printfound"], timeout=600)
        print(saida)
        utils.log("osint_user", alvo, "sherlock concluido")
        return
    print(utils.c("  sherlock nao encontrado — fallback com verificacao HTTP basica.", utils.AMARELO))
    sites = [
        ("GitHub", "https://github.com/{}"),
        ("Reddit", "https://www.reddit.com/user/{}"),
        ("Instagram", "https://www.instagram.com/{}/"),
        ("X", "https://x.com/{}"),
        ("TikTok", "https://www.tiktok.com/@{}"),
    ]
    achados = []
    for nome, modelo in sites:
        url = modelo.format(alvo)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    achados.append(url)
                    print(utils.c("  [ENCONTRADO] {}".format(url), utils.VERDE))
        except Exception:
            pass
    utils.log("osint_user", alvo, "encontrados: {}".format(achados))


def osint_email(alvo, ctx):
    """OSINT de email (theHarvester ou dica de instalação)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("osint_email", "theHarvester -d {}".format(alvo))
        return
    if not utils.exigir_ferramenta("theHarvester") and not utils.exigir_ferramenta("theharvester"):
        print(utils.c("  Instale com: pkg install theharvester / apt install theharvester", utils.AMARELO))
        return
    binario = "theHarvester" if utils.ferramenta_existe("theHarvester") else "theharvester"
    dominio = alvo.split("@")[-1]
    saida = _run([binario, "-d", dominio, "-b", "google", "-l", "200"], timeout=600)
    print(saida)
    utils.log("osint_email", alvo, "theHarvester concluido")


def ip_geo(alvo, ctx):
    """Geolocalização de IP (ip-api.com, sem chave/cadastro)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("ip_geo", "consulta geolocalizacao de {}".format(alvo))
        return
    url = "http://ip-api.com/json/{}?lang=pt".format(urllib.parse.quote(alvo))
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            dados = json.loads(r.read().decode())
        if dados.get("status") == "fail":
            print(utils.c("  Falha: {}".format(dados.get("message")), utils.VERMELHO))
            return
        for chave in ("country", "regionName", "city", "isp", "org", "as", "query"):
            print("  {:10s}: {}".format(chave, dados.get(chave)))
        utils.log("ip_geo", alvo, "{} {}".format(dados.get("country"), dados.get("city")))
    except Exception as e:
        print(utils.c("  Erro na consulta: {}".format(e), utils.VERMELHO))


def cms_detect(alvo, ctx):
    """Detecção de CMS (whatweb ou fingerprint Python)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("cms_detect", "fingerprint de {}".format(alvo))
        return
    if utils.ferramenta_existe("whatweb"):
        saida = _run(["whatweb", "--color", "auto", alvo], timeout=300)
        print(saida)
        utils.log("cms_detect", alvo, "whatweb concluido")
        return
    print(utils.c("  whatweb nao encontrado — fingerprint Python.", utils.AMARELO))
    indicios = []
    try:
        req = urllib.request.Request(alvo, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            corpo = r.read(80000).decode("utf-8", "ignore")
            cab = {k.lower(): v for k, v in r.headers.items()}
        checks = [
            ("WordPress", "/wp-content/"),
            ("Joomla", "/media/jui/"),
            ("Drupal", "Drupal.settings"),
            ("Magento", "/skin/frontend/"),
            ("Wix", "wix.com"),
        ]
        for nome, marca in checks:
            if marca in corpo:
                indicios.append(nome)
        if "x-powered-by" in cab:
            indicios.append(cab["x-powered-by"])
        if "server" in cab:
            indicios.append("server: " + cab["server"])
    except Exception as e:
        print(utils.c("  Erro: {}".format(e), utils.VERMELHO))
        return
    print("  Indicios: {}".format(indicios or "nenhum"))
    utils.log("cms_detect", alvo, str(indicios))


def ssl_scan(alvo, ctx):
    """Scan SSL/TLS (sslscan/testssl ou coleta via Python)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("ssl_scan", "certificado TLS de {}".format(alvo))
        return
    if utils.ferramenta_existe("sslscan"):
        saida = _run(["sslscan", "{}:443".format(alvo)], timeout=300)
        print(saida)
        utils.log("ssl_scan", alvo, "sslscan concluido")
        return
    # Fallback: conecta com TLS e imprime dados do certificado
    print(utils.c("  sslscan nao encontrado — leitura do certificado via Python.", utils.AMARELO))
    try:
        ctx_ssl = ssl.create_default_context()
        with socket.create_connection((alvo, 443), timeout=15) as sock:
            with ctx_ssl.wrap_socket(sock, server_hostname=alvo) as tls:
                cert = tls.getpeercert()
                print("  Cipher: {}".format(tls.cipher()))
                print("  Versao: {}".format(tls.version()))
                for tipo, valor in cert.get("subject", ()):
                    print("  Subject {}: {}".format(tipo, valor))
                for tipo, valor in cert.get("issuer", ()):
                    print("  Issuer  {}: {}".format(tipo, valor))
                print("  Valido ate: {}".format(cert.get("notAfter")))
        utils.log("ssl_scan", alvo, "certificado lido")
    except Exception as e:
        print(utils.c("  Falha TLS: {}".format(e), utils.VERMELHO))
