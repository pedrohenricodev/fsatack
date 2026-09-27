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

### 🚨 Problemas comuns na instalação

| Sintoma | Causa / correção |
|---|---|
| `metadata-generation-failed` / `maturin` / `Failed to build 'cryptography'` | O pip tentou **compilar** `cryptography` (precisa de Rust). O instalador **não compila mais** isso: ele instala via `pkg install python-cryptography python-bcrypt python-pynacl` e, se falhar, avisa e segue (SSH brute passa a usar `hydra`). Rode `bash install.sh` de novo e escolha `[1]`. |
| `fsataque: command not found` | O comando global não foi criado (instalação interrompida). Rode `bash install.sh` de novo **ou** use `bash fsataque.sh` — o instalador agora cria o comando **antes** de instalar qualquer coisa. |
| `fsataque` só funciona depois de reabrir o terminal | `$PREFIX/bin` entrou no PATH agora; feche e abra o Termux. |

---

## 🎮 Uso

### Menu interativo

```bash
fsataque
```

No menu, `[?]` na categoria mostra a ajuda dela e `[H]` na tela principal abre
a ajuda completa. Antes de executar, o CLI pergunta se você quer ver a ajuda do
módulo e só roda se você digitar o nome dele.

### Ajuda

Cada um dos 51 módulos tem resumo, flags, ressalvas conhecidas e exemplo.

```bash
fsataque help                            # visão geral das categorias
fsataque help bruteforce                 # a categoria inteira, com o resumo de cada módulo
fsataque help bruteforce http_form       # detalhe: flags, ressalvas, exemplo
fsataque help unethical                  # o que ficou fora do escopo, e por quê
fsataque help ble_attack                 # detalhe de um tema fora do escopo
fsataque bruteforce ssh --help           # ajuda só daquele módulo
```

As ressalvas não são decorativas: `help bruteforce http_form` avisa que o
critério de sucesso é o tamanho do corpo e que redirects não são detectados,
porque `allow_redirects=True` faz o status nunca aparecer como 3xx. `help
bruteforce admin_panel` avisa que qualquer HTTP 200 conta como acerto.

### Subcomandos

```bash
fsataque help
fsataque recon port_scan 192.168.0.10 1-1024
fsataque network http_flood http://lab.local --dry-run
fsataque bruteforce ssh 192.168.0.10 --port 2222
fsataque bruteforce ssh 192.168.0.10 --users wordlists/users.txt --pass wordlists/passwords.txt
fsataque bruteforce http_form http://192.168.0.5/login username password
fsataque phishing clone_page http://192.168.0.5/login --host 0.0.0.0
fsataque phishing templates
fsataque phishing camera_sim
fsataque wireless wifi_scan
fsataque system logs
fsataque system update
```

### Flags

| Flag | Efeito |
|---|---|
| `--dry-run` (ou `"dry_run": true`) | mostra o que faria, sem executar nada |
| `--port <n>` / `--port=<n>` | porta do alvo (bruteforce, phishing) — **nunca confunde com wordlist** |
| `--users <arq>` | wordlist de usuários |
| `--pass <arq>` | wordlists de senhas |
| `--host <ip>` | interface do servidor de phishing (padrão `127.0.0.1`) |
| `--user-field` / `--pass-field` | nomes dos campos no brute de formulário |

### Dry-run (testar sem disparo real)

- Flag: `--dry-run` em qualquer comando
- Ou `"dry_run": true` no `config.json`
- No menu interativo: tecla `[D]` alterna o modo

### Logs

Toda execução grava `data`, `módulo`, `alvo` e `resultado` em
`logs/fsataque.jsonl`. **Senhas nunca são gravadas em texto puro** — o
sucesso do brute é registrado como `user:***`. Capturas de phishing ficam em
`logs/phishing_captures.jsonl` (arquivo **sensível**, permissão `600`; é o
artefato do teste de lab, trate como credencial real).

---

## 🧪 Testes

```bash
python tests/smoke_test.py
```

O teste roda **todos os módulos** da CLI em `--dry-run`, verifica a compilação
de todos os arquivos, o `help`, o menu interativo, as dependências Python e a
sintaxe dos scripts bash. Além disso executa **testes REAIS** contra um
servidor local (`127.0.0.1`, nenhum alvo externo):

- flood HTTP de 2s com contagem de requisições no servidor;
- brute force HTTP Basic com wordlist temporária (caminho completo);
- regressão: `--port` não pode sequestrar as wordlists;
- regressão: senha real ausente de `logs/fsataque.jsonl`;
- `port_scan` com sockets (fallback sem nmap);
- templates do AdvPhishing descobertos, convertidos e sem `.php` servível;
- fluxo de 3 etapas do phishing encadeia os redirecionamentos e grava a etapa
  correta em `logs/phishing_captures.jsonl`;
- `camera_sim` só aceita imagem válida e monta todo comando como argv.

Só sai com código `0` quando **100% passam** (91 verificações no estado atual).

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

Estes não estão na CLI e não voltam. O motivo não é técnico — é que não existe
enquadramento de laboratório que os torne legítimos. `fsataque help unethical`
imprime esta seção com o texto completo, e `fsataque help <tema>` detalha um
deles.

- **Bombardeio** (SMS/Call/Email Bomb, OTP Flood, WhatsApp Spam) — atingem
  telefones e contas de pessoas que não consentiram. Um número de celular real
  não é alvo de teste, com ou sem `EU ACEITO`.
- **BLE spam/flood/fuzz** — desconectam fones, teclados e relógios de quem
  estiver por perto, ou seja, pessoas que nunca pediram para participar. O que
  existe é `ble_scan`, que só observa.
- **Amplificação** (DNS/NTP/SSDP) — abusa de servidores de terceiros para
  multiplicar o tráfego contra um alvo que não autorizou nada.
- **Wi-Fi de injeção** (deauth, evil twin, ARP spoof) — exige root/hardware;
  esta CLI nunca roda com root.

---

## 🎣 Phishing (AdvPhishing adaptado ao Termux)

O `install.sh` clona [Ignitetch/AdvPhishing](https://github.com/Ignitetch/AdvPhishing)
em `modules/phishing/AdvPhishing/`. As telas são servidas por um **servidor Python
puro** — sem PHP, sem Apache e sem `sudo`, funcionando igual no Termux e no Linux.

Os templates vivem em `AdvPhishing/sites/<tema>/` (não em `Webpages/`, que é
apenas um placeholder). São 29 temas utilizáveis — `google-otp`, `paypal`,
`whatsapp-phishing`, `Netflix`, `telegram`, `ajio`, `mobikwik` e outros.

`sites/<tema>/` traz as telas em `.php` e um espelho dos assets. Na conversão:

- cada `.php` de entrada vira `.html` (`index`, `pass.login`, `otp.login`);
- os `<form>` passam a postar para o **próprio nome da página**, que é como o
  servidor sabe em que etapa do fluxo o POST caiu;
- CSS, JS e imagens vão junto com o nome original (inclusive o sufixo
  `.download` do mirror — renomear quebraria todas as referências);
- nenhum `.php` nem `.sh` é servido.

Fluxos de várias etapas funcionam de ponta a ponta: após cada captura o servidor
redireciona para a próxima tela e, na última, mostra uma confirmação. As
capturas são gravadas em `logs/phishing_captures.jsonl` com o campo `etapa`.

O único tema ignorado é `ipfinder`: o `ip.php` dele é 100% PHP (grava IP e
user-agent) e não tem HTML estático para servir.

O servidor escuta em **`127.0.0.1`** por padrão (só a sua máquina). Para uma
vítima de lab em outra máquina: `--host 0.0.0.0` (ou use o módulo `tunnel`,
que expõe via ngrok/cloudflared sem abrir a interface).

### `camera_sim` — o que ele exige

Tira uma foto da câmera do **próprio aparelho** e exige consentimento explícito
em dupla confirmação. O sucesso só é declarado depois de validar o arquivo
gerado (assinatura JPEG/PNG + tamanho mínimo) — a versão anterior confiava no
exit code, e o Termux:API devolve `0` mesmo recusando a permissão, então ela
anunciava "salvo" sem foto nenhuma.

Backends tentados, em ordem de preferência:

| Plataforma | Backend | Requisito |
|---|---|---|
| Android/Termux | `termux-camera-photo` | app Termux:API (F-Droid) **e** permissão de câmera concedida ao app |
| Linux | `fswebcam` | `apt install fswebcam`, `/dev/video0` |
| Linux/BSD | `ffmpeg -f v4l2` | `apt install ffmpeg` |
| Windows | `ffmpeg -f dshow` | `ffmpeg` no PATH; os nomes das webcams são listados para escolha |
| macOS | `imagesnap` | `brew install imagesnap` |

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
├── core/                 # menu, ajuda, utils, logger
│   ├── ajuda.py          # texto de ajuda: resumo, flags, ressalvas, exemplos
│   ├── menu.py           # registro de módulos, roteamento, subcomandos
│   ├── utils.py          # config, cores, prompts, dependências
│   └── logger.py         # JSONL de execuções
├── modules/              # recon, network, bruteforce, phishing...
├── tests/smoke_test.py   # teste de todos os módulos (dry-run) + regressões
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
