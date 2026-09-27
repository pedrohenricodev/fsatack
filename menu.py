#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FS ATAQUE — menu interativo e subcomandos CLI (Termux / Linux)

# Adicione bluetooth_spam e bomb na lista de imports
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 1. Define a raiz do projeto como o diretório onde este arquivo está
ROOT = os.path.dirname(os.path.abspath(__file__))

# 2. Adiciona a raiz ao sys.path para o Python encontrar 'core' e 'modules'
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 3. Agora sim, os imports
from core import utils, logger, ajuda
from modules import recon, network, bruteforce, phishing, wireless, bluetooth, utilsmod, bluetooth_spam, bomb

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 3. IMPORTS DO CORE (Sempre depois do sys.path)
from core import utils, logger, ajuda

# 4. IMPORTS DOS MÓDULOS (Agora o Python saberá onde procurar)
from modules import (
    recon, network, bruteforce, phishing, 
    wireless, bluetooth, utilsmod, bluetooth_spam, bomb
)

# ... restante do seu código (AVISO, CATEGORIAS, etc)

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
        "nome": "Bluetooth / BLE (Scanner e Spam)",
        "mods": {
            "ble_scan": dict(nome="BLE Scanner (dispositivos proximos)", fn=bluetooth.ble_scan, alvo=False, destrutivo=False, vpn=False),
            "ble_spam": dict(nome="BLE Spam (Flood de anúncios)", fn=bluetooth_spam.ble_spam, alvo=True, destrutivo=True, vpn=False),
        },
    },
        "bomb": {
        "nome": "Bombing (SMS/Call)",
        "mods": {
            "sms_bomb": dict(nome="SMS Bomb (OTP Flood)", fn=bomb.sms_bomb, alvo=True, destrutivo=True, vpn=True),
            "call_bomb": dict(nome="Call Bomb (VoIP)", fn=bomb.call_bomb, alvo=True, destrutivo=True, vpn=True),
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
# Adicione "bomb" na lista para aparecer no menu principal
ORDEM = ["recon", "network", "bruteforce", "phishing", "wireless", "bluetooth", "bomb", "utils", "system"]

ALIASES = {
    "rede": "network", "net": "network", "flood": "network",
    "bf": "bruteforce", "forca": "bruteforce", "brute": "bruteforce",
    "wifi": "wireless", "wireless": "wireless",
    "ble": "bluetooth", "bluetooth": "bluetooth",
    "utils": "utils", "utilidades": "utils", "util": "utils",
    "sistema": "system", "sys": "system",
    "recon": "recon", "scanning": "recon", "scan": "recon",
    "phishing": "phishing",
    
    # Novos Aliases para os ataques que você adicionou
    "bomb": "bomb", 
    "sms": "bomb", 
    "call": "bomb",
    "spam": "bluetooth", # Atalho para o menu de bluetooth/ble
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


def _tags(mod):
    """Tags de aviso ([VPN]/[DESTRUTIVO]) de um modulo do registro."""
    tags = ""
    if mod.get("vpn"):
        tags += utils.c(" [VPN]", utils.AMARELO)
    if mod.get("destrutivo"):
        tags += utils.c(" [DESTRUTIVO]", utils.VERMELHO)
    return tags


def listar_mods(cat, dry=False):
    """Lista os módulos de uma categoria com resumo, tags e atalho de ajuda."""
    print(utils.c("\n  === {} ===".format(CATEGORIAS[cat]["nome"]), utils.VERDE))
    mods = CATEGORIAS[cat]["mods"]
    for i, chave in enumerate(mods, 1):
        m = mods[chave]
        print("   [{:2d}] {}{}{}".format(
            i, m["nome"], utils.c(" ({})".format(chave), utils.CIANO), _tags(m)))
        print("        " + utils.c(ajuda.resumo(chave), utils.AMARELO))
    print("    [ 0] Voltar")
    print("    [?] Ajuda detalhada desta categoria")


def _linha_ajuda(rotulo, texto, cor=None):
    """Uma linha 'rotulo: texto' alinhada, para os blocos de ajuda."""
    print("  {} {}".format(
        utils.c("{:<18}".format(rotulo), cor or utils.CIANO),
        utils.c(str(texto), utils.AMARELO)))


def ajuda_categoria(cat):
    """Ajuda de uma categoria inteira: o que ela faz e o que cada módulo faz."""
    if cat not in CATEGORIAS:
        print(utils.c("  Categoria desconhecida: {}".format(cat), utils.VERMELHO))
        return
    info = CATEGORIAS[cat]
    print(utils.c("\n  {} — {} modulos".format(info["nome"], len(info["mods"])), utils.VERDE))
    destrutivos = [k for k, m in info["mods"].items() if m.get("destrutivo")]
    leitura = [k for k, m in info["mods"].items() if not m.get("destrutivo")]
    if destrutivos:
        print(utils.c("  Destrutivos (exigem CONFIRMO): " + ", ".join(destrutivos), utils.VERMELHO))
    if leitura:
        print(utils.c("  Nao destrutivos: " + ", ".join(leitura), utils.VERDE))
    print()
    for chave, m in info["mods"].items():
        print("  {} {}{}".format(
            utils.c(m["nome"], utils.VERDE),
            utils.c("({})".format(chave), utils.CIANO), _tags(m)))
        print("      " + ajuda.resumo(chave))
    relacionados = ajuda.ESCOPO_POR_CATEGORIA.get(cat)
    if relacionados:
        print(utils.c("\n  Relacionado (fora do escopo): "
                      + ", ".join(relacionados), utils.VERMELHO))
        for tema in relacionados:
            print("    " + utils.c(ajuda.FORA_DE_ESCOPO.get(tema, ""), utils.AMARELO))
        print(utils.c("    Detalhe: fsataque help {}".format(relacionados[0]), utils.CIANO))
    print(utils.c("\n  Detalhe de um modulo: fsataque help {} <modulo>".format(cat), utils.CIANO))
    print(utils.c("  Testar sem executar: acrescente --dry-run", utils.CIANO))


def ajuda_modulo(cat, chave):
    """Ajuda completa de um modulo: resumo, flags, ressalvas e exemplo."""
    if cat not in CATEGORIAS or chave not in CATEGORIAS[cat]["mods"]:
        print(utils.c("  Modulo desconhecido: {} {}".format(cat, chave), utils.VERMELHO))
        return
    m = CATEGORIAS[cat]["mods"][chave]
    aviso, exemplo = ajuda.detalhe(chave)

    print(utils.c("\n  {}  {}".format(m["nome"], _tags(m)), utils.VERDE))
    print(utils.c("  {}{}".format(cat, utils.c(" > " + chave, utils.CIANO)), utils.VERDE))
    print()
    print(utils.c("  O que faz", utils.VERDE))
    print("    " + ajuda.resumo(chave))
    if m.get("alvo"):
        print("    Precisa de alvo (IP, host ou URL).")
    if m.get("destrutivo"):
        # camera_sim e destrutivo no sentido de "invade a privacidade", nao de
        # "derruba servico": a frase generica seria enganosa.
        if chave == "camera_sim":
            print(utils.c("    DESTRUTIVO: exige 'CONFIRMO' e consentimento da pessoa "
                          "filmada. Sem alvo: afeta o seu proprio aparelho.", utils.VERMELHO))
        else:
            print(utils.c("    DESTRUTIVO: exige 'CONFIRMO' e pode derrubar o servico do alvo.",
                          utils.VERMELHO))
    if m.get("vpn"):
        print(utils.c("    Alerta de VPN exibido antes de rodar.", utils.AMARELO))

    flags_mod = ajuda.flags(cat, chave)
    if flags_mod:
        print(utils.c("\n  Flags e posicionais", utils.VERDE))
        for nome, doc in flags_mod:
            _linha_ajuda(nome, doc)

    if aviso:
        print(utils.c("\n  Ressalva", utils.VERDE))
        # Quebra o texto em linhas de ~72 colunas para nao quebrar o terminal.
        for pedaco in _quebrar(aviso, 72):
            print(utils.c("    " + pedaco, utils.AMARELO))

    if exemplo:
        print(utils.c("\n  Exemplo", utils.VERDE))
        print("    " + utils.c(exemplo, utils.VERDE))

    print(utils.c("\n  Dry-run (nao executa nada):", utils.CIANO))
    print("    " + utils.c("fsataque {} {} <alvo> --dry-run".format(cat, chave), utils.CIANO))
    print(utils.c("  Aviso legal vigente em: fsataque help unethical", utils.AMARELO))


def _quebrar(texto, largura):
    """Quebra um texto em linhas de no maximo `largura` caracteres."""
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 > largura and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = "{} {}".format(atual, p) if atual else p
    if atual:
        linhas.append(atual)
    return linhas


def ajuda_etica(topico="todos"):
    """Explica o que fica fora do escopo e por que.

   `topico` pode ser "todos"/"unethical" (panorama) ou o nome de um tema.
    """
    ok, topicos = ajuda.fora_de_escopo(topico)
    if not ok:
        print(utils.c("  Topico de escopo desconhecido: {}".format(topico), utils.VERMELHO))
        print(utils.c("  Temas: " + ", ".join(sorted(ajuda.FORA_DE_ESCOPO)), utils.AMARELO))
        return
    titulo = "fora do escopo" if len(topicos) > 1 else list(topicos)[0]
    print(utils.c("\n  O que ficou {} desta CLI".format(titulo), utils.VERDE))
    print(utils.c("  O motivo nao e tecnico:", utils.AMARELO))
    for chave, texto in topicos.items():
        print(utils.c("\n  {}".format(chave), utils.VERMELHO))
        for pedaco in _quebrar(texto, 72):
            print("    " + utils.c(pedaco, utils.AMARELO))
    print(utils.c("\n  Uso permitido: seus proprios dispositivos, suas redes, ou alvos", utils.VERDE))
    print(utils.c("  com autorizacao por escrito. Uso indevido e crime", utils.VERDE))
    print(utils.c("  (Lei 12.737/2012, art. 154-A do Codigo Penal).", utils.VERDE))



def menu_categoria(cat, dry):
    """Submenu de uma categoria."""
    while True:
        utils.limpar()
        banner()
        listar_mods(cat, dry)
        esc = input(utils.c("\n  Escolha: ", utils.VERDE)).strip()
        if esc in ("0", ""):
            return
        if esc in ("?", "h", "help"):
            ajuda_categoria(cat)
            input(utils.c("\n  Enter para continuar...", utils.CIANO))
            continue
        chaves = list(CATEGORIAS[cat]["mods"].keys())
        if esc.isdigit() and 1 <= int(esc) <= len(chaves):
            escolha = chaves[int(esc) - 1]
            if _confirmar_ajuda(cat, escolha):
                executar(cat, escolha, dry=dry)
        else:
            print(utils.c("  Opcao invalida.", utils.VERMELHO))
        input(utils.c("\n  Enter para continuar...", utils.CIANO))


def _confirmar_ajuda(cat, chave):
    """Oferece a ajuda do modulo antes de executar. True = pode executar."""
    print(utils.c("\n  {} — {}".format(CATEGORIAS[cat]["mods"][chave]["nome"], chave), utils.VERDE))
    print("  " + ajuda.resumo(chave))
    aviso, _ex = ajuda.detalhe(chave)
    if aviso:
        for pedaco in _quebrar(aviso, 72):
            print(utils.c("  ! " + pedaco, utils.AMARELO))
    if not utils.confirmar("  Ver ajuda completa antes de executar? (s/N)", "n"):
        return True
    ajuda_modulo(cat, chave)
    resp = utils.perguntar("  Executar mesmo assim? (digite o nome do modulo para confirmar)", "")
    return resp.strip() == chave



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
        print("   [H] " + utils.c("Ajuda: o que cada modulo faz", utils.CIANO))
        print("   [D] Alternar dry-run (agora: {})".format("ON" if dry else "OFF"))
        print("   [0] Sair")
        esc = input(utils.c("\n  Escolha: ", utils.VERDE)).strip().lower()
        if esc in ("0", "q", "sair", ""):
            print(utils.c("  Ate logo!", utils.VERDE))
            return
        if esc in ("h", "help", "?"):
            _menu_ajuda()
            continue
        if esc == "d":
            dry = not dry
            continue
        if esc.isdigit() and 1 <= int(esc) <= len(ORDEM):
            menu_categoria(ORDEM[int(esc) - 1], dry)
        else:
            print(utils.c("  Opcao invalida.", utils.VERMELHO))
            input(utils.c("\n  Enter para continuar...", utils.CIANO))


def _menu_ajuda():
    """Submenu de ajuda: escolha de categoria ou modulo."""
    while True:
        utils.limpar()
        banner()
        print(utils.c("\n  Ajuda — o que voce quer ver?", utils.VERDE))
        print(utils.c("\n  Categorias:", utils.VERDE))
        for i, chave in enumerate(ORDEM, 1):
            print("   [{}] {}".format(i, CATEGORIAS[chave]["nome"]))
        print("   [E] " + utils.c("O que ficou fora do escopo (e por que)", utils.AMARELO))
        print("   [0] Voltar")
        esc = input(utils.c("\n  Escolha: ", utils.VERDE)).strip()
        if esc in ("0", "", "q"):
            return
        if esc.lower() in ("e", "escopo", "unethical"):
            ajuda_etica()
            input(utils.c("\n  Enter para continuar...", utils.CIANO))
            continue
        if esc.isdigit() and 1 <= int(esc) <= len(ORDEM):
            _ajuda_modulos_de(ORDEM[int(esc) - 1])
        else:
            print(utils.c("  Opcao invalida.", utils.VERMELHO))
        input(utils.c("\n  Enter para continuar...", utils.CIANO))


def _ajuda_modulos_de(cat):
    """Lista os módulos de uma categoria e mostra a ajuda do escolhido."""
    while True:
        utils.limpar()
        print(utils.c("\n  {} — modulos".format(CATEGORIAS[cat]["nome"]), utils.VERDE))
        chaves = list(CATEGORIAS[cat]["mods"].keys())
        for i, chave in enumerate(chaves, 1):
            m = CATEGORIAS[cat]["mods"][chave]
            print("   [{:2d}] {}{}".format(
                i, m["nome"], utils.c(" ({})".format(chave), utils.CIANO)))
            print("        " + ajuda.resumo(chave))
        print("    [0] Voltar")
        esc = input(utils.c("\n  Modulo: ", utils.VERDE)).strip()
        if esc in ("0", "", "q"):
            return
        if esc.isdigit() and 1 <= int(esc) <= len(chaves):
            ajuda_modulo(cat, chaves[int(esc) - 1])
            input(utils.c("\n  Enter para continuar...", utils.CIANO))
            continue
        print(utils.c("  Opcao invalida.", utils.VERMELHO))
        input(utils.c("\n  Enter para continuar...", utils.CIANO))


def print_ajuda():
    """Ajuda dos subcomandos."""
    print("""Uso:
  fsataque                          menu interativo
  fsataque help                     visão geral das categorias
  fsataque help <categoria>         o que a categoria faz + todos os módulos
  fsataque help <categoria> <modulo>  detalhe: flags, ressalvas e exemplo
  fsataque help unethical           o que ficou fora do escopo, e por quê
  fsataque <categoria> <modulo> <alvo> [posicionais...] [flags] [--dry-run]
  fsataque <categoria> <modulo> --help    ajuda só deste módulo

Categorias: recon, network, bruteforce, phishing, wireless, bluetooth, utils, system

Flags (funcionam em qualquer modulo):
  --port <n>        porta do alvo (bruteforce, phishing)
  --users <arq>     wordlist de usuarios      --pass <arq>  wordlist de senhas
  --host <ip>       interface do servidor de phishing (padrao 127.0.0.1)
  --dry-run         mostra o que faria, sem executar

No menu interativo, digite [?] na categoria para ver a ajuda dela.

Exemplos:
  fsataque help bruteforce
  fsataque help bruteforce http_form
  fsataque recon port_scan 192.168.0.10 1-1024
  fsataque network http_flood http://lab.local --dry-run
  fsataque bruteforce ssh 192.168.0.10 --port 2222
  fsataque bruteforce http_form http://192.168.0.5/login username password
  fsataque phishing clone_page http://192.168.0.5/login --host 0.0.0.0
  fsataque system logs""")

    print("\nCategorias:")
    for cat in ORDEM:
        nome = CATEGORIAS[cat]["nome"]
        n = len(CATEGORIAS[cat]["mods"])
        print("  {:12s} {} ({} modulos)".format(cat, nome, n))

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
        # help unethical [tema] | help <categoria> [modulo]
        # A categoria tem precedencia sobre o topico fora de escopo.
        if len(args) > 1 and not (args[1] in CATEGORIAS or ALIASES.get(args[1]) in CATEGORIAS):
            ok, _t = ajuda.fora_de_escopo(args[1])
            if ok:
                ajuda_etica(args[1] if len(args) > 2 else "todos")
                return
        if len(args) > 2:
            cat = ALIASES.get(args[1], args[1])
            ajuda_modulo(cat, args[2])
            return
        if len(args) > 1:
            ajuda_categoria(ALIASES.get(args[1], args[1]))
            return
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
    if "--help" in args or "-h" in args:
        # fsataque <cat> <modulo> --help
        args.remove("--help" if "--help" in args else "-h")
        ajuda_modulo(cat, chave)
        return
    alvo = args[2] if len(args) > 2 else None
    extras = args[3:]
    executar(cat, chave, alvo=alvo, extras=extras, dry=dry)


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print(utils.c("\n  Entrada encerrada. Ate logo!", utils.AMARELO))
