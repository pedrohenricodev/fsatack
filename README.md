# FS ATAQUE

```
●●●●●  ●●●●●
●  ●
●  ●
●●●●●  ●●●●●
●      ●
●      ●
●  ●●●●●

 ●●●   ●●●●●   ●●●    ●●●●  ●   ●
●   ●    ●    ●   ●  ●  ●  ●
●   ●    ●    ●   ●  ●  ● ●
●●●●●    ●    ●●●●●  ●  ●●
●   ●    ●    ●   ●  ●  ● ●
●   ●    ●    ●   ●  ●  ●  ●
●   ●    ●    ●   ●   ●●●●  ●   ●
```

**Framework de Pentest — Termux / Linux**

CLI de segurança da informação para **ambiente controlado**: laboratório próprio,
dispositivos próprios, redes próprias e testes autorizados por escrito.

---

## ⚠️ AVISO LEGAL / USO ÉTICO

- Uso **exclusivo** em alvos de sua propriedade ou com autorização formal.
- O uso indevido é crime (Lei 12.737/2012 — Lei Carolina Dieckmann, art. 154-A do Código Penal).
- Na primeira execução o CLI exige digitar `EU ACEITO`.
- Módulos destrutivos (flood, força bruta) exigem digitar `CONFIRMO`.
- Recomendamos **VPN** — o CLI exibe `⚠ Recomendado uso de VPN` ao lado dos comandos ofensivos.

---

## 📦 Instalação

O instalador é **interativo**: você só digita o **número da opção**.
Nenhum comando extra é pedido — se um pacote falhar, o próprio script
oferece as opções de correção (nunca compila código-fonte à toa).

### Termux (Android, sem root)

```bash
pkg install git
git clone https://github.com/pedrohenricodev/fsatack.git
cd fsatack
bash install.sh
fsataque
```

### Linux (Debian/Ubuntu/Arch)

```bash
git clone https://github.com/pedrohenricodev/fsatack.git
cd fsatack
bash install.sh
fsataque
```

### Opções do instalador

| Opção | O que faz |
|---|---|
| `[1]` **Completa** (recomendado) | sistema + Python (`requests`, `qrcode`, `cryptography`, `paramiko`) + ferramentas extras opcionais |
| `[2]` **Leve** | sistema + Python núcleo (`requests`, `qrcode`) — sem brute SSH |
| `[3]` **Só sistema** | apenas pacotes do sistema (python, git, nmap, openssl…) |
| `[4]` **Sair** | nada é instalado |

Se algum pacote Python falhar (ex.: `cryptography` sem wheel pré-compilado),
aparece um sub-menu: `[1]` instalar toolchain e tentar de novo, `[2]`
continuar com os fallbacks automáticos, `[3]` sair. No Termux o instalador
usa `pkg install python-cryptography python-bcrypt` **antes** do pip —
sem tentar compilar Rust. Os detalhes de cada tentativa ficam em
`logs/install_pip.log`.

Dependências: `python3 (3.8+)`, `pip`, `git`, `curl`, `nmap`, `openssl`,
`hydra` (opcional). Python: `requests` e `qrcode` (núcleo, sempre
instaláveis) e `paramiko`/`cryptography` (SSH brute, opcionais).

---

## 🎮 Uso

### Menu interativo

```bash
fsataque
```

### Subcomandos

```bash
fsataque help
fsataque recon port_scan 192.168.0.10
fsataque network http_flood http://lab.local --dry-run
fsataque bruteforce ssh 192.168.0.10
fsataque phishing clone_page http://192.168.0.5/login
fsataque wireless wifi_scan
fsataque system logs
fsataque system update
```

### Dry-run (testar sem disparo real)

- Flag: `--dry-run` em qualquer comando
- Ou `"dry_run": true` no `config.json`

### Logs

Toda execução grava `data`, `módulo`, `alvo` e `resultado` em
`logs/fsataque.jsonl`. Capturas de phishing ficam em
`logs/phishing_captures.jsonl`.

---

## 🧪 Testes

```bash
python tests/smoke_test.py
```

O teste roda **todos os módulos** da CLI em `--dry-run` (nenhum ataque real),
verifica a compilação de todos os arquivos, o `help`, o menu interativo e as
dependências Python. Só sai com código `0` quando **100% passam**.

---

## 🧩 Módulos

| Categoria | Módulos |
|---|---|
| **recon** | port_scan, service_detect, web_vuln, nuclei, dir_brute, subdomain, whois_dns, osint_user, osint_email, ip_geo, cms_detect, ssl_scan |
| **network** | http_flood, slowloris, udp_flood, tcp_connect, icmp_flood, slow_post, http2_rapid (simulação) |
| **bruteforce** | ssh, ftp, http_basic, http_form, telnet, smtp, smb, rdp, mysql, postgres, rtsp, admin_panel |
| **phishing** | clone_page, templates (AdvPhishing), tunnel (ngrok/cloudflared), qr, camera_sim |
| **wireless** | wifi_scan, signal_map, open_aps, wps_check *(somente leitura)* |
| **bluetooth** | ble_scan *(somente leitura)* |
| **utils** | revshell, msfvenom, encoder, hash_crack, wordlist_gen, exif, qr_tools |
| **system** | update (git pull), logs, config |

### Módulos deliberadamente REMOVIDOS

- **Bombardeio** (SMS/Call/Email Bomb, OTP Flood, WhatsApp Spam) — atinge terceiros.
- **Amplificação** (DNS/NTP/SSDP) — abusa de servidores de terceiros.
- **BLE spam/flood/fuzz** — incomoda dispositivos alheios.
- **Wi-Fi de injeção** (deauth, evil twin, ARP spoof) — exige root/hardware;
  esta CLI nunca roda com root.

---

## 🎣 Phishing (AdvPhishing adaptado ao Termux)

O `install.sh` clona [Ignitetch/AdvPhishing](https://github.com/Ignitetch/AdvPhishing)
em `modules/phishing/AdvPhishing/`. As telas são servidas por um **servidor Python
puro** — sem PHP, sem Apache e sem `sudo`, funcionando igual no Termux e no Linux.
Formulários são reescritos para o endpoint de captura e os POSTs são gravados em
`logs/phishing_captures.jsonl`.

---

## 📁 Estrutura

```
fsatack/
├── install.sh            # instalador INTERATIVO Termux/Linux (menu de opções)
├── fsataque.sh           # launcher
├── requirements.txt      # núcleo: requests, qrcode
├── requirements-full.txt # + paramiko (SSH brute)
├── config.json           # threads, timeout, wordlists, dry_run
├── banner/ascii.txt      # banner em pontos
├── core/                 # menu, utils, logger
├── modules/              # recon, network, bruteforce, phishing...
├── tests/smoke_test.py   # teste de todos os módulos (dry-run)
├── wordlists/            # wordlists mínimas próprias
└── logs/                 # JSONL de execuções
```

---

## 🛠 Limitações sem root (Termux)

- Wi-Fi: somente leitura via Termux:API (`pkg install termux-api`).
- ICMP: limitado ao comando `ping` comum.
- Nenhum módulo exige root — é regra do projeto.

---

**MIT License** — use com responsabilidade. Créditos ao
[AdvPhishing](https://github.com/Ignitetch/AdvPhishing) pelas telas de exemplo.
