#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Textos de ajuda do FS ATAQUE: o que cada módulo faz, como usar e suas ressalvas.
#
# Três níveis de detalhe:
#   RESUMO[mod]   -> uma linha, mostrada na listagem de módulos
#   FLAGS[mod]    -> flags/posicionais especificos daquele módulo
#   DETALHES[mod] -> ressalvas, limites conhecidos e_curto exemplo
#
# Os flags globais (--dry-run, --port, --users, --pass, --host) e os avisos
# de VPN/destrutivo são derivados de CATEGORIAS em core/menu.py e não se repetem aqui.

# Flags aceitas por quase todos os módulos — montadas em ajuda_de().
GLOBAL_FLAGS = (
    ("--dry-run", "Mostra o que faria, sem executar nada."),
    ("--port <n>", "Porta do alvo (bruteforce, phishing)."),
    ("--users <arq>", "Wordlist de usuarios."),
    ("--pass <arq>", "Wordlist de senhas."),
    ("--host <ip>", "Interface do servidor de phishing (padrao 127.0.0.1)."),
)

RESUMO = {
    # ---------------------------------------------------------- recon
    "port_scan": "Scan TCP connect. Usa nmap -sT; sem nmap cai para sockets puros (ate 1024 portas).",
    "service_detect": "Detecta servico e versao (nmap -sV) nas portas 1-1024.",
    "web_vuln": "Scanner de vulnerabilidades web (nikto).",
    "nuclei": "Varredura por templates de vulnerabilidade (nuclei).",
    "dir_brute": "Brute force de diretorios. feroxbuster/gobuster; fallback Python via urllib.",
    "subdomain": "Enumera subdominios. subfinder/assetfinder; fallback DNS brute com wordlist propria.",
    "whois_dns": "Resolucao DNS do alvo + consulta WHOIS.",
    "osint_user": "Procura um username em redes sociais. sherlock; fallback HTTP em 5 sites.",
    "osint_email": "Coleta de e-mails de um dominio (theHarvester, fonte google).",
    "ip_geo": "Geolocalizacao de IP via ip-api.com (sem chave, sem cadastro).",
    "cms_detect": "Detecta CMS por fingerprint. whatweb; fallback Python (WordPress/Joomla/x-powered-by).",
    "ssl_scan": "Le o certificado TLS da porta 443. sslscan; fallback Python (cipher, versao, validade).",
    # ---------------------------------------------------------- network
    "http_flood": "Flood HTTP GET/POST com N threads durante T segundos.",
    "slowloris": "Mantem conexoes TCP abertas com cabecalhos parciais, ocupando slots do servidor.",
    "udp_flood": "Envia consultas DNS craftadas por UDP. Sem amplificacao e sem terceiro envolvido.",
    "tcp_connect": "Abre conexoes TCP em laco (SYN via connect, sem raw socket e sem root).",
    "icmp_flood": "ping em laco, um processo por pacote. Limitado ao binario ping do sistema.",
    "slow_post": "Slow POST / R-U-Dead-Yet: Content-Length alto com corpo enviado devagar.",
    "http2_rapid": "SIMULACAO didatica. Nenhum pacote e enviado; so conta streams ficticios.",
    # ---------------------------------------------------------- bruteforce
    "ssh": "Forca bruta SSH. paramiko, ou hydra se a lib faltar.",
    "ftp": "Forca bruta FTP (ftplib).",
    "http_basic": "Forca bruta HTTP Basic Auth na URL. Sucesso = HTTP 200.",
    "http_form": "Forca bruta de login por formulario HTTP. Sucesso = redirect ou corpo diferente do baseline.",
    "telnet": "Forca bruta Telnet (socket puro, sem telnetlib).",
    "smtp": "Forca bruta SMTP AUTH LOGIN, com STARTTLS quando o servidor suporta.",
    "smb": "Forca bruta SMB via hydra.",
    "rdp": "Forca bruta RDP via hydra (sem GUI).",
    "mysql": "Forca bruta MySQL via pymysql; hydra como fallback.",
    "postgres": "Forca bruta PostgreSQL via psycopg2; hydra como fallback.",
    "rtsp": "Cameras IP via RTSP DESCRIBE, com Basic e Digest.",
    "admin_panel": "HTTP Basic em cada caminho de wordlist_dirs.",
    # ---------------------------------------------------------- phishing
    "clone_page": "Baixa uma pagina de login, reescreve os <form> e serve em 127.0.0.1 capturando POSTs.",
    "templates": "Lista e serve os templates do AdvPhishing (sites/<tema>), convertidos de PHP para estatico.",
    "tunnel": "Expoe o servidor local na internet via ngrok ou cloudflared.",
    "qr": "Gera QR Code da URL (terminal + PNG).",
    "camera_sim": "Captura a camera LOCAL com consentimento explicito em dupla confirmacao.",
    # ---------------------------------------------------------- wireless
    "wifi_scan": "Lista SSID/BSSID/canal das redes proximas via Termux:API.",
    "signal_map": "Mapa de intensidade de sinal (RSSI) das redes visiveis.",
    "open_aps": "Sinaliza redes sem WPA (WEP ou sem cifra) — pontos de acesso abertos.",
    "wps_check": "Detecta se o AP expoe WPS, que e vulneravel a forca bruta de PIN.",
    # ---------------------------------------------------------- bluetooth
    "ble_scan": "Scan BLE passivo (somente leitura). hcitool/bluetoothctl no Linux.",
    # ---------------------------------------------------------- utils
    "revshell": "Gera 7 payloads de reverse shell (bash/python/nc/php) para LHOST:LPORT.",
    "msfvenom": "Wrapper do msfvenom. Pergunta payload, LHOST, LPORT, formato e arquivo de saida.",
    "encoder": "Codifica e decodifica base64, hex e URL.",
    "hash_crack": "Quebra MD5/SHA1/SHA256 com wordlist. Detecta o algoritmo pelo tamanho do hash.",
    "wordlist_gen": "Gera wordlist (base + sufixos + numeros 0-99) em wordlists/gerada_<base>.txt.",
    "exif": "Le metadados de imagem. exiftool, ou fallback JPEG puro (APP1/APP2, GPS/Make/Model).",
    "qr_tools": "Gera ou le QR Code. Leitura via zbarimg.",
    # ---------------------------------------------------------- system
    "update": "git pull --ff-only no repositorio do projeto.",
    "logs": "Mostra os ultimos 20 eventos de logs/fsataque.jsonl.",
    "config": "Imprime o config.json atual.",
}

# Flags e posicionais especificos de cada modulo.
FLAGS = {
    "port_scan": (("posicional 1", "Faixa de portas, ex.: 1-1024 ou 80,443,8000-8010 (padrao 1-1024)."),),
    "dir_brute": (("posicional 1", "Arquivo de wordlist (padrao config wordlist_dirs)."),),
    "http_flood": (("posicional 1", "Threads (padrao config threads)."),
                   ("posicional 2", "Duracao em segundos (padrao config duracao_flood)."),
                   ("posicional 3", "Metodo: GET ou POST (padrao GET).")),
    "slowloris": (("posicional 1", "Porta (padrao 80)."),
                  ("posicional 2", "Numero de conexoes (padrao config threads)."),
                  ("posicional 3", "Duracao em segundos.")),
    "udp_flood": (("posicional 1", "Porta UDP (padrao 53)."),
                  ("posicional 2", "Duracao em segundos.")),
    "tcp_connect": (("posicional 1", "Porta (padrao 80)."),
                    ("posicional 2", "Duracao em segundos.")),
    "icmp_flood": (("posicional 1", "Duracao em segundos."),),
    "slow_post": (("posicional 1", "Porta (padrao 80)."),
                  ("posicional 2", "Duracao em segundos.")),
    "http_form": (("posicional 1", "NOME do campo de usuario, nao o valor."),
                  ("posicional 2", "NOME do campo de senha, nao o valor."),
                  ("--user-field", "Igual ao posicional 1."),
                  ("--pass-field", "Igual ao posicional 2.")),
    "admin_panel": (("--users / --pass", "Wordlists aplicadas a cada caminho de wordlist_dirs."),),
    "revshell": (("alvo", "LHOST do lab (padrao 127.0.0.1)."),
                 ("posicional 1", "LPORT (padrao 4444).")),
    "hash_crack": (("posicional 1", "Hash a quebrar; vazio para pedir um arquivo."),
                   ("posicional 2", "Wordlist (padrao config wordlist_passwords).")),
    "wordlist_gen": (("posicional 1", "Palavra base, ex.: senha."),),
    "qr_tools": (("alvo", "Texto/URL a gerar. Sem alvo, pergunta."),
                 ("acao g/l", "No prompt: g=gerar (padrao), l=ler de uma imagem.")),
    "ble_scan": (("posicional 1", "Duracao do scan em segundos (padrao 10)."),),
    "wifi_scan": (("posicional 1", "Quantas vezes repetir o scan (para Signed Signal Mapper)."),),
}

# Ressalvas reais, limites conhecidos e exemplos. So o que importa ao usuario.
DETALHES = {
    "port_scan": (
        "O fallback em Python e sequencial e para em 1024 portas, entao um range grande "
        "e silenciosamente truncado. Prefira nmap quando disponivel.",
        "fsataque recon port_scan 192.168.0.10 1-1024",
    ),
    "dir_brute": (
        "O fallback so reporta 200 e 401/403. Um 404 noisso nao aparece, o que reduz o ruido "
        "mas tambem esconde variantes de 404 como soft-404.",
        "fsataque recon dir_brute http://192.168.0.5/dir wordlists/dirs.txt",
    ),
    "osint_user": (
        "O fallback so checa HTTP 200. Sites que retornam 200 para usuario inexistente "
        "viram falso positivo.",
        "fsataque recon osint_user meuusuario",
    ),
    "ip_geo": (
        "Consulta ip-api.com em texto plano. O IP de quem consulta fica exposto ao servico.",
        "fsataque recon ip_geo 8.8.8.8",
    ),
    "ssl_scan": (
        "Le apenas a porta 443 e nao avalia a validade da cadeia. Para isso, use sslscan.",
        "fsataque recon ssl_scan lab.local",
    ),
    "http_flood": (
        "A contagem de progresso so atualiza a cada 5s. Se o alvo responder rapido, "
        "o numero final e bem maior do que o ultimo progresso mostrado.",
        "fsataque network http_flood http://127.0.0.1:8080 10 5 POST",
    ),
    "udp_flood": (
        "O throttle de 500 pacotes e contado sobre envios bem-sucedidos. Se o destino "
        "recusar tudo, o contador nao avanca e nao ha limite de ritmo.",
        "fsataque network udp_flood 127.0.0.1 53 5",
    ),
    "icmp_flood": (
        "Um processo ping por iteração, entao o teto real e de algumas centenas por "
        "segundo, muito abaixo do que o modulo sugere.",
        None,
    ),
    "http2_rapid": (
        "NAO faz nada de fato. Imprime numeros crescentes para explicar o ataque. "
        "Nao há envio de frames HTTP/2.",
        None,
    ),
    "http_form": (
        "Como os redirects sao seguidos, o status nunca aparece como 3xx: o unico criterio "
        "real de sucesso e o tamanho do corpo diferir do baseline em mais de 15%. Isso "
        "gera falsos positivos em paginas com horario, banner rotativo ou CSRF token. "
        "Trate o resultado como indicio, nunca como confirmacao.",
        "fsataque bruteforce http_form http://192.168.0.5/login username password",
    ),
    "telnet": (
        "O sucesso e inferido por ausencia de mensagem de erro e presenca de prompt. "
        "Sessao que nao responde nada e contada como falha.",
        None,
    ),
    "smtp": (
        "Se o servidor recusar STARTTLS, o login segue em texto plano. Em alvos de "
        "verdade isso vaza a credencial em teste — prefira 465 (SSL implicito).",
        None,
    ),
    "rtsp": (
        "O Digest e recalculado por cima do nonce do servidor a cada tentativa, entao "
        "funciona com cameras que nao expiram o nonce.",
        None,
    ),
    "admin_panel": (
        "ATENCAO: considera sucesso qualquer HTTP 200 em qualquer caminho da wordlist, "
        "inclusive a pagina inicial. Contra um servidor web comum ele acusa 'acesso' "
        "em segundos. Trate com desconfio.",
        None,
    ),
    "clone_page": (
        "So o HTML e salvo — CSS, JS e imagens da pagina original NAO sao baixados, entao "
        "a tela aparece sem estilo. Para telas prontas e completas, use 'templates'.",
        "fsataque phishing clone_page http://127.0.0.1:8000/login --host 0.0.0.0",
    ),
    "templates": (
        "Os templates do AdvPhishing sao convertidos de PHP para estatico: os blocos "
        "<?php ?> sao removidos e os <form> passam a apontar para o endpoint de captura. "
        "Sem PHP, paginas de fluxo multi-etapa (login -> OTP) param na primeira etapa. "
        "O servidor escuta em 127.0.0.1 por padrao.",
        "fsataque phishing templates",
    ),
    "tunnel": (
        "Expor o servidor na internet e o passo que tira a coisa do laboratorio. "
        "So faca com o alvo do lab avisado.",
        None,
    ),
    "camera_sim": (
        "Captura a camera do PROPRIO aparelho. Exige consentimento explicito em dupla "
        "confirmacao, e o arquivo vai para logs/camera_foto.jpg. No Android exige o app "
        "Termux:API (F-Droid) e permissao de camera; no Linux, fswebcam ou ffmpeg.",
        "fsataque phishing camera_sim",
    ),
    "wifi_scan": (
        "No Android 9+ o Wi-Fi scan exige concessao de localizacao, e o sistema devolve "
        "SSID e BSSID mascarados (<unknown>) ate a permissao ser concedida em ajustes.",
        None,
    ),
    "ble_scan": (
        "Somente leitura. No Termux nao ha acesso a discovery de BLE, entao o modulo "
        "avisa e sai. Requer bluez e um adaptador BLE no Linux.",
        "fsataque bluetooth ble_scan 15",
    ),
    "revshell": (
        "Imprime comandos prontos, nao executa nada. Substitua LHOST pelo IP da sua "
        "maquina de lab, nunca pelo da vitima.",
        "fsataque utils revshell 192.168.0.2 4444",
    ),
    "hash_crack": (
        "O algoritmo e deduzido pelo tamanho do hash (32/40/64 hex). Nao ha suporte a "
        "salt, NTLM, bcrypt ou argon2.",
        "fsataque utils hash_crack 5f4dcc3b5aa765d61d8327deb882cf99 wordlists/passwords.txt",
    ),
    "wordlist_gen": (
        "O nome do arquivo usa a palavra base crua, entao uma base com '/' ou espaco "
        "cria um caminho invalido.",
        None,
    ),
    "exif": (
        "O fallback le so os primeiros 64KB e so APP1/APP2. Tags GPS em segmentos "
        "posteriores ficam de fora.",
        None,
    ),
    "update": (
        "git pull --ff-only: falha em vez de criar merge commit se o repo local "
        "estiver divergente.",
        None,
    ),
    "logs": (
        "Senhas nunca vao para o log em texto puro — o brute registra user:***. Ja o "
        "logs/phishing_captures.jsonl guarda credenciais em claro e e um artefato "
        "sensivel.",
        None,
    ),
}

# Modulos deliberadamente fora do escopo, para a ajuda responder "por que nao existe?".
FORA_DE_ESCOPO = {
    "bombardeio": (
        "SMS/Call/Email Bomb, OTP Flood e WhatsApp Spam nao estao nesta CLI. "
        "Eles miram telefones e contas de pessoas que nao consentiram, e nao existe "
        "alvo de laboratorio que os torne legitimos."
    ),
    "ble_attack": (
        "BLE spam/flood/fuzz nao estao nesta CLI. Eles desconectam fones, teclados e "
        "relogios de quem estiver por perto — pessoas que nunca pediram "
        "para participar. O modulo disponivel e 'ble_scan', que so observa."
    ),
    "amplificacao": (
        "Amplificacao DNS/NTP/SSDP nao estao nesta CLI. Ela abusa de servidores de "
        "terceiros para multiplicar o trafego contra um alvo que nao autorizou nada."
    ),
    "wifi_injection": (
        "Deauth, evil twin e ARP spoof nao estao nesta CLI. Exigem root e hardware de "
        "injetao, e esta CLI tem regra de nunca rodar com root."
    ),
}

# Aliases aceitos na linha de comando. "unethical" e "todos" mostram o panorama.
ALIASES_ESCOPO = {
    "unethical": "todos",
    "escopo": "todos",
    "scope": "todos",
    "todos": "todos",
    "bomb": "bombardeio",
    "sms": "bombardeio",
    "spam": "bombardeio",
    "ble": "ble_attack",
    "amplificacao": "amplificacao",
    "dns": "amplificacao",
    "ntp": "amplificacao",
    "ssdp": "amplificacao",
    "wifi": "wifi_injection",
    "deauth": "wifi_injection",
    "evil_twin": "wifi_injection",
}


# Temas fora do escopo que o usuario provavelmente procurar na categoria.
ESCOPO_POR_CATEGORIA = {
    "bluetooth": ("ble_attack",),
    "wireless": ("wifi_injection",),
    "network": ("amplificacao",),
    "phishing": ("bombardeio",),
}


def fora_de_escopo(nome):
    """Resolve um topico de escopo.

   Retorna (True, {chave: texto}) para um topico conhecido (ou para todos, no
    alias "unethical"), e (False, None) se o nome nao corresponde a nada.
   Aceita tanto o alias quanto a chave canonica.
   """
    nome = str(nome).lower()
    chave = ALIASES_ESCOPO.get(nome, nome)
    if chave == "todos":
        return True, dict(FORA_DE_ESCOPO)
    if chave in FORA_DE_ESCOPO:
        return True, {chave: FORA_DE_ESCOPO[chave]}
    return False, None


# Modulos que aceitam --port mas nao o usam de fato (o controle de porta fica na URL).
SEM_PORTA = {
    "http_basic",     # urllib usa a porta da URL
    "admin_panel",    # idem
    "http_form",      # idem
    "hash_crack",     # opera sobre arquivo, nao rede
    "wordlist_gen",   # opera sobre arquivo, nao rede
    "osint_user",     # URLs fixas dos sites
}

# Modulos que nao usam wordlists.
SEM_WORDLIST = {
    "port_scan", "service_detect", "web_vuln", "nuclei", "dir_brute", "subdomain",
    "whois_dns", "osint_user", "osint_email", "ip_geo", "cms_detect", "ssl_scan",
    "http_flood", "slowloris", "udp_flood", "tcp_connect", "icmp_flood", "slow_post",
    "http2_rapid",
    "clone_page", "templates", "tunnel", "qr", "camera_sim",
    "wifi_scan", "signal_map", "open_aps", "wps_check", "ble_scan",
    "revshell", "msfvenom", "encoder", "exif", "qr_tools",
    "update", "logs", "config",
}

# Modulos que nao fazem rede (nem --port nem --host fazem sentido).
# 'qr' e 'camera_sim' estao aqui mesmo sendo da categoria phishing: os dois
# rodam 100% no aparelho e nunca sobem servidor nenhum.
OFFLINE = {
    "encoder", "exif", "msfvenom", "wordlist_gen", "update", "logs", "config",
    "wifi_scan", "signal_map", "open_aps", "wps_check", "ble_scan",
    "qr", "camera_sim",
}

# Modulos que nao pedem alvo (sao puramente locais).
SEM_ALVO = {
    "update", "logs", "config", "qr", "camera_sim", "encoder", "msfvenom",
    "wordlist_gen", "exif", "qr_tools", "templates", "tunnel",
    "wifi_scan", "signal_map", "open_aps", "wps_check", "ble_scan", "hash_crack",
}


def tem_ajuda(chave):
    """True se o modulo tem resumo cadastrado."""
    return chave in RESUMO


def global_flags_de(cat, chave):
    """Flags globais que fazem sentido para este modulo daquela categoria.

   Nem todo modulo usa todas: `--host` so existe em phishing, `--port` nao
    existe onde a porta ja esta na URL, e modulos offline nao usam nada de rede.
    Sugerir flag sem efeito e pior que nao sugerir.
    """
    if chave in OFFLINE:
        return (("--dry-run", "Mostra o que faria, sem executar nada."),)
    if cat == "phishing":
        base = [("--port <n>", "Porta do servidor local (padrao config phishing_port)."),
                ("--host <ip>", "Interface do servidor (padrao 127.0.0.1 = so esta maquina).")]
        return tuple(base + [("--dry-run", "Mostra o que faria, sem executar nada.")])
    if cat == "bruteforce":
        base = []
        if chave not in SEM_PORTA:
            base.append(("--port <n>", "Porta do servico (padrao da lib)."))
        if chave not in SEM_WORDLIST:
            base.append(("--users <arq>", "Wordlist de usuarios."))
            base.append(("--pass <arq>", "Wordlist de senhas."))
        return tuple(base + [("--dry-run", "Mostra o que faria, sem executar nada.")])
    return GLOBAL_FLAGS


def precisa_alvo(chave):
    """True se o modulo faz sentido com alvo de rede."""
    return chave not in SEM_ALVO


def resumo(chave, padrao="(sem descricao cadastrada)"):
    """One-liner do modulo, com fallback seguro."""
    return RESUMO.get(chave, padrao)


def flags(cat, chave):
    """Flags especificas + globais relevantes, sem duplicar."""
    especificas = FLAGS.get(chave, ())
    nomes = {nome for nome, _doc in especificas}
    return tuple(especificas) + tuple(
        (nome, doc) for nome, doc in global_flags_de(cat, chave) if nome not in nomes
    )


def detalhe(chave):
    """(ressalva, exemplo) ou (None, None) se o modulo nao tem ressalva."""
    return DETALHES.get(chave, (None, None))
