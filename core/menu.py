#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FS ATAQUE — menu interativo e subcomandos CLI (Termux / Linux)

import os
import sys

# Garante UTF-8 no console (Windows) sem quebrar o banner
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import utils, logger
from modules import recon, network, bruteforce, phishing, wireless, bluetooth, utilsmod

AVISO = """\
================================================================
   AVISO LEGAL / USO ETICO — FS ATAQUE
================================================================
Esta ferramenta destina-se EXCLUSIVAMENTE a:
  * laboratorios proprios;
  * dispositivos e redes de sua propriedade;
  * testes autorizados por escrito.

E PROIBIDO usar este software contra alvos sem autorizacao.
O uso indevido e crime (Lei 12.737/2012 - Lei Carolina
Dieckmann, art. 154-A do Codigo Penal). Voce assume toda a
responsabilidade pelo uso desta ferramenta.
================================================================"""

BOMBARDEIO_MSG = (
    "Categoria REMOVIDA por decisao de escopo:\n"
    "  SMS/Call/Email Bomb, OTP Flood e WhatsApp Spam atingem\n"
    "  terceiros fora de qualquer laboratorio controlado.\n"
    "  Alternativa disponivel: 'phishing clone_page' contra um\n"
    "  servidor SMTP local para testar fluxo de e-mail em lab."
)

def _sistema_update(alvo, ctx):
    """Atualiza o projeto via git pull (com aviso)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("system_update", "git pull --ff-only em {}".format(ROOT))
        return
    print(utils.c("  Atualizando repositorio (git pull)...", utils.CIANO))
    import subprocess
    try:
        status = subprocess.run(["git", "-C", ROOT, "pull", "--ff-only"]).returncode
    except Exception as erro:
        print(utils.c("  git indisponivel: {}".format(erro), utils.VERMELHO))
        status = 1
    res = "git pull ok" if status == 0 else "git pull falhou"
    utils.log("system_update", "-", res)


def _sistema_logs(alvo, ctx):
    """Mostra os últimos eventos de log."""
    for linha in logger.ultimos(20):
        print("  " + linha)


def _sistema_config(alvo, ctx):
    """Imprime o config.json atual."""
    import json
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        print(json.dumps(json.load(f), indent=2, ensure_ascii=False))


# Registro central: categoria -> módulos (fn recebe alvo e ctx)
CATEGORIAS = {
    "recon": {
        "nome": "Scanning / Recon",
        "mods": {
            "port_scan": dict(nome="Port Scan TCP Connect", fn=recon.port_scan, alvo=True, destrutivo=False, vpn=True),
            "service_detect": dict(nome="Service/Version Detection", fn=recon.service_detect, alvo=True, destrutivo=False, vpn=True),
            "web_vuln": dict(nome="Web Vuln Scan (nikto)", fn=recon.web_vuln, alvo=True, destrutivo=False, vpn=True),
            "nuclei": dict(nome="Vulnerability Templates (nuclei)", fn=recon.nuclei, alvo=True, destrutivo=False, vpn=True),
            "dir_brute": dict(nome="Directory Brute Force", fn=recon.dir_brute, alvo=True, destrutivo=False, vpn=True),
            "subdomain": dict(nome="Subdomain Enum", fn=recon.subdomain, alvo=True, destrutivo=False, vpn=True),
            "whois_dns": dict(nome="WHOIS / DNS Lookup", fn=recon.whois_dns, alvo=True, destrutivo=False, vpn=False),
            "osint_user": dict(nome="OSINT username (sherlock)", fn=recon.osint_user, alvo=True, destrutivo=False, vpn=True),
            "osint_email": dict(nome="OSINT email (theHarvester)", fn=recon.osint_email, alvo=True, destrutivo=False, vpn=True),
            "ip_geo": dict(nome="IP Geolocation", fn=recon.ip_geo, alvo=True, destrutivo=False, vpn=True),
            "cms_detect": dict(nome="CMS Detect", fn=recon.cms_detect, alvo=True, destrutivo=False, vpn=True),
            "ssl_scan": dict(nome="SSL/TLS Scan", fn=recon.ssl_scan, alvo=True, destrutivo=False, vpn=True),
        },
    },
    "network": {
        "nome": "Rede (camada aplicacional)",
        "mods": {
            "http_flood": dict(nome="HTTP Flood (GET/POST)", fn=network.http_flood, alvo=True, destrutivo=True, vpn=True),
            "slowloris": dict(nome="Slowloris", fn=network.slowloris, alvo=True, destrutivo=True, vpn=True),
            "udp_flood": dict(nome="UDP Flood aplicacional", fn=network.udp_flood, alvo=True, destrutivo=True, vpn=True),
            "tcp_connect": dict(nome="TCP SYN via connect()", fn=network.tcp_connect, alvo=True, destrutivo=True, vpn=True),
            "icmp_flood": dict(nome="ICMP Flood (ping loop)", fn=network.icmp_flood, alvo=True, destrutivo=True, vpn=True),
            "slow_post": dict(nome="Slow POST (R-U-Dead-Yet)", fn=network.slow_post, alvo=True, destrutivo=True, vpn=True),
            "http2_rapid": dict(nome="HTTP/2 Rapid Reset (simulacao)", fn=network.http2_rapid, alvo=True, destrutivo=True, vpn=True),
        },
    },
    "bruteforce": {
        "nome": "Forca Bruta / Credenciais",
        "mods": {
            "ssh": dict(nome="SSH Brute Force", fn=bruteforce.ssh, alvo=True, destrutivo=True, vpn=True),
            "ftp": dict(nome="FTP Brute Force", fn=bruteforce.ftp, alvo=True, destrutivo=True, vpn=True),
            "http_basic": dict(nome="HTTP Basic Auth Brute Force", fn=bruteforce.http_basic, alvo=True, destrutivo=True, vpn=True),
            "http_form": dict(nome="HTTP Form Login Brute Force", fn=bruteforce.http_form, alvo=True, destrutivo=True, vpn=True),
            "telnet": dict(nome="Telnet Brute Force", fn=bruteforce.telnet, alvo=True, destrutivo=True, vpn=True),
            "smtp": dict(nome="SMTP Brute Force", fn=bruteforce.smtp, alvo=True, destrutivo=True, vpn=True),
            "smb": dict(nome="SMB Brute Force (hydra)", fn=bruteforce.smb, alvo=True, destrutivo=True, vpn=True),
            "rdp": dict(nome="RDP Brute Force (hydra)", fn=bruteforce.rdp, alvo=True, destrutivo=True, vpn=True),
            "mysql": dict(nome="MySQL Brute Force", fn=bruteforce.mysql, alvo=True, destrutivo=True, vpn=True),
            "postgres": dict(nome="PostgreSQL Brute Force", fn=bruteforce.postgres, alvo=True, destrutivo=True, vpn=True),
            "rtsp": dict(nome="RTSP Brute Force (cameras IP)", fn=bruteforce.rtsp, alvo=True, destrutivo=True, vpn=True),
            "admin_panel": dict(nome="Painel Admin Brute Force (generico)", fn=bruteforce.admin_panel, alvo=True, destrutivo=True, vpn=True),
        },
    },
    "phishing": {
        "nome": "Phishing / Engenharia Social (lab)",
        "mods": {
            "clone_page": dict(nome="Clone de pagina de login (local)", fn=phishing.clone_page, alvo=True, destrutivo=False, vpn=True),
            "templates": dict(nome="Templates AdvPhishing (Termux)", fn=phishing.templates, alvo=False, destrutivo=False, vpn=True),
            "tunnel": dict(nome="Tunel publico (ngrok/cloudflared)", fn=phishing.tunnel, alvo=False, destrutivo=False, vpn=True),
            "qr": dict(nome="QR Code Phishing (gerador)", fn=phishing.qr, alvo=False, destrutivo=False, vpn=False),
            "camera_sim": dict(nome="Captura de camera (simulacao/consentimento)", fn=phishing.camera_sim, alvo=False, destrutivo=True, vpn=False),
        },
    },
    "wireless": {
        "nome": "Wireless (somente leitura, sem root)",
        "mods": {
            "wifi_scan": dict(nome="Wi-Fi Scanner (SSID/BSSID/canal)", fn=wireless.wifi_scan, alvo=False, destrutivo=False, vpn=False),
            "signal_map": dict(nome="Wi-Fi Signal Mapper", fn=wireless.signal_map, alvo=False, destrutivo=False, vpn=False),
            "open_aps": dict(nome="Deteccao de APs abertos", fn=wireless.open_aps, alvo=False, destrutivo=False, vpn=False),
            "wps_check": dict(nome="Deteccao de WPS habilitado", fn=wireless.wps_check, alvo=False, destrutivo=False, vpn=False),
        },
    },
    "bluetooth": {
        "nome": "Bluetooth / BLE (somente leitura)",
        "mods": {
            "ble_scan": dict(nome="BLE Scanner (dispositivos proximos)", fn=bluetooth.ble_scan, alvo=False, destrutivo=False, vpn=False),
        },
    },
    "utils": {
        "nome": "Utilidades / Payload",
        "mods": {
            "revshell": dict(nome="Gerador de Reverse Shell", fn=utilsmod.revshell, alvo=False, destrutivo=False, vpn=False),
            "msfvenom": dict(nome="Gerador de Payload (msfvenom)", fn=utilsmod.msfvenom, alvo=False, destrutivo=False, vpn=False),
            "encoder": dict(nome="Encoder/Decoder (base64/hex/url)", fn=utilsmod.encoder, alvo=False, destrutivo=False, vpn=False),
            "hash_crack": dict(nome="Hash Cracker (wordlist)", fn=utilsmod.hash_crack, alvo=False, destrutivo=False, vpn=True),
            "wordlist_gen": dict(nome="Gerador de Wordlist", fn=utilsmod.wordlist_gen, alvo=False, destrutivo=False, vpn=False),
            "exif": dict(nome="ExifTool wrapper (metadados)", fn=utilsmod.exif, alvo=False, destrutivo=False, vpn=False),
            "qr_tools": dict(nome="QR Code Reader/Generator", fn=utilsmod.qr_tools, alvo=False, destrutivo=False, vpn=False),
        },
    },
    "system": {
        "nome": "Sistema",
        "mods": {
            "update": dict(nome="Atualizar (git pull)", fn=_sistema_update, alvo=False, destrutivo=False, vpn=False),
            "logs": dict(nome="Ver logs de execucao", fn=_sistema_logs, alvo=False, destrutivo=False, vpn=False),
            "config": dict(nome="Ver config.json", fn=_sistema_config, alvo=False, destrutivo=False, vpn=False),
        },
    },
}

# Ordem do menu principal
ORDEM = ["recon", "network", "bruteforce", "phishing", "wireless", "bluetooth", "utils", "system"]

ALIASES = {
    "rede": "network", "net": "network", "flood": "network",
    "bf": "bruteforce", "forca": "bruteforce", "brute": "bruteforce",
    "wifi": "wireless", "wireless": "wireless",
    "ble": "bluetooth", "bluetooth": "bluetooth",
    "utils": "utils", "utilidades": "utils", "util": "utils",
    "sistema": "system", "sys": "system",
    "recon": "recon", "scanning": "recon", "scan": "recon",
    "phishing": "phishing",
}


def banner():
    """Exibe o banner ASCII (verde) e o subtítulo."""
    try:
        with open(os.path.join(ROOT, "banner", "ascii.txt"), encoding="utf-8") as f:
            arte = f.read().rstrip()
    except FileNotFoundError:
        arte = "FS ATAQUE"
    print(utils.c(arte, utils.VERDE))
    print(utils.c("Framework de Pentest — Termux / Linux", utils.CIANO))


def aceite_legal():
    """Aviso legal na primeira execução (marca em logs/.aceite)."""
    marca = os.path.join(ROOT, "logs", ".aceite")
    if os.path.exists(marca):
        return True
    print(utils.c(AVISO, utils.AMARELO))
    try:
        resp = input("\n  Digite EU ACEITO para continuar: ").strip().upper()
    except EOFError:
        print(utils.c("  Sem entrada disponivel. Saindo.", utils.VERMELHO))
        return False
    if resp != "EU ACEITO":
        print(utils.c("  Aceite obrigatorio. Saindo.", utils.VERMELHO))
        return False
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    with open(marca, "w", encoding="utf-8") as f:
        f.write("aceito\n")
    print(utils.c("  Obrigado. Bem-vindo ao FS ATAQUE.", utils.VERDE))
    return True


def executar(cat, chave, alvo=None, extras=None, dry=False):
    """Executa um módulo com alerta VPN, confirmação destrutiva e try/except."""
    cfg = utils.carregar_config()
    if cfg.get("dry_run"):
        dry = True
    mod = CATEGORIAS[cat]["mods"][chave]
    if mod.get("vpn") and cfg.get("vpn_alert", True):
        utils.alerta_vpn()
    if mod.get("alvo") and not alvo:
        alvo = utils.perguntar("Alvo")
        if not alvo:
            print(utils.c("  Sem alvo, cancelado.", utils.VERMELHO))
            return
    if mod.get("destrutivo") and not dry:
        if not utils.confirmar_destrutivo(chave):
            utils.log(chave, alvo or "-", "cancelado pelo usuario")
            return
    modo = " [DRY-RUN]" if dry else ""
    print(utils.c("\n  Executando {}{}...".format(chave, modo), utils.CIANO))
    ctx = {"dry": dry, "extras": extras or [], "config": cfg}
    try:
        mod["fn"](alvo, ctx)
    except KeyboardInterrupt:
        print(utils.c("\n  Interrompido pelo usuario.", utils.AMARELO))
        utils.log(chave, alvo or "-", "interrompido")
    except Exception as erro:
        print(utils.c("  Erro no modulo: {}".format(erro), utils.VERMELHO))
        utils.log(chave, alvo or "-", "erro: {}".format(erro))


def listar_mods(cat, dry=False):
    """Lista os módulos de uma categoria com tags [VPN] e [DESTRutivo]."""
    print(utils.c("\n  === {} ===".format(CATEGORIAS[cat]["nome"]), utils.VERDE))
    mods = CATEGORIAS[cat]["mods"]
    for i, chave in enumerate(mods, 1):
        m = mods[chave]
        tags = ""
        if m.get("vpn"):
            tags += utils.c(" [VPN]", utils.AMARELO)
        if m.get("destrutivo"):
            tags += utils.c(" [DESTRUTIVO]", utils.VERMELHO)
        print("   [{:2d}] {}{}{}".format(i, m["nome"], utils.c(" ({})".format(chave), utils.CIANO), tags))
    print("    [ 0] Voltar")


def menu_categoria(cat, dry):
    """Submenu de uma categoria."""
    while True:
        utils.limpar()
        banner()
        listar_mods(cat, dry)
        esc = input(utils.c("\n  Escolha: ", utils.VERDE)).strip()
        if esc in ("0", ""):
            return
        chaves = list(CATEGORIAS[cat]["mods"].keys())
        if esc.isdigit() and 1 <= int(esc) <= len(chaves):
            executar(cat, chaves[int(esc) - 1], dry=dry)
        else:
            print(utils.c("  Opcao invalida.", utils.VERMELHO))
        input(utils.c("\n  Enter para continuar...", utils.CIANO))


def interativo(dry):
    """Menu principal interativo (por numero)."""
    while True:
        utils.limpar()
        banner()
        print(utils.c("\n  [!] Uso exclusivo em ambientes autorizados.", utils.AMARELO))
        if dry:
            print(utils.c("  [MODO DRY-RUN ATIVO — nada sera executado]", utils.CIANO))
        print(utils.c("\n  Categorias:", utils.VERDE))
        for i, chave in enumerate(ORDEM, 1):
            print("   [{}] {}".format(i, CATEGORIAS[chave]["nome"]))
        print("   [B] " + utils.c("Bombardeio (removido)", utils.VERMELHO))
        print("   [D] Alternar dry-run (agora: {})".format("ON" if dry else "OFF"))
        print("   [0] Sair")
        esc = input(utils.c("\n  Escolha: ", utils.VERDE)).strip().lower()
        if esc in ("0", "q", "sair", ""):
            print(utils.c("  Ate logo!", utils.VERDE))
            return
        if esc == "b":
            print(utils.c("\n  " + BOMBARDEIO_MSG, utils.AMARELO))
            input(utils.c("\n  Enter para voltar...", utils.CIANO))
            continue
        if esc == "d":
            dry = not dry
            continue
        if esc.isdigit() and 1 <= int(esc) <= len(ORDEM):
            menu_categoria(ORDEM[int(esc) - 1], dry)
        else:
            print(utils.c("  Opcao invalida.", utils.VERMELHO))
            input(utils.c("\n  Enter para continuar...", utils.CIANO))


def print_ajuda():
    """Ajuda dos subcomandos."""
    print("""Uso:
  fsataque                          menu interativo
  fsataque help                     esta ajuda
  fsataque <categoria> <modulo> <alvo> [posicionais...] [flags] [--dry-run]

Categorias: recon, network, bruteforce, phishing, wireless, bluetooth, utils, system

Flags (funcionam em qualquer modulo):
  --port <n>        porta do alvo (bruteforce, phishing)
  --users <arq>     wordlist de usuarios      --pass <arq>  wordlist de senhas
  --host <ip>       interface do servidor de phishing (padrao 127.0.0.1)
  --dry-run         mostra o que faria, sem executar

Exemplos:
  fsataque recon port_scan 192.168.0.10 1-1024
  fsataque network http_flood http://lab.local --dry-run
  fsataque bruteforce ssh 192.168.0.10 --port 2222
  fsataque bruteforce ssh 192.168.0.10 --users wordlists/users.txt --pass wordlists/passwords.txt
  fsataque bruteforce http_form http://lab/login username password
  fsataque phishing clone_page http://192.168.0.5/login --host 0.0.0.0
  fsataque system logs""")

    print("\nModulos por categoria:")
    for cat in ORDEM:
        mods = ", ".join(CATEGORIAS[cat]["mods"].keys())
        print("  {:12s} {}".format(cat, mods))


def main():
    args = sys.argv[1:]
    dry = False
    if "--dry-run" in args:
        dry = True
        args.remove("--dry-run")
    if not args:
        if not aceite_legal():
            return
        interativo(dry)
        return
    if args[0] in ("-h", "--help", "help"):
        print_ajuda()
        return
    if not aceite_legal():
        return
    cat = ALIASES.get(args[0], args[0])
    if cat not in CATEGORIAS:
        print(utils.c("Categoria desconhecida: {}".format(args[0]), utils.VERMELHO))
        print_ajuda()
        return
    if len(args) == 1:
        listar_mods(cat, dry)
        return
    chave = args[1]
    if chave not in CATEGORIAS[cat]["mods"]:
        print(utils.c("Modulo desconhecido: {}".format(chave), utils.VERMELHO))
        listar_mods(cat, dry)
        return
    alvo = args[2] if len(args) > 2 else None
    extras = args[3:]
    executar(cat, chave, alvo=alvo, extras=extras, dry=dry)


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print(utils.c("\n  Entrada encerrada. Ate logo!", utils.AMARELO))
