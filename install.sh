#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# FS ATAQUE — instalador INTERATIVO (Termux / Linux)
# O usuario apenas SELECIONA opcoes numeradas — nenhum
# comando extra precisa ser digitado.
# Uso: git clone <repo> && cd fsatack && bash install.sh
# ============================================================

VERDE="\e[32m"; AMARELO="\e[33m"; VERMELHO="\e[31m"; CIANO="\e[36m"; RESET="\033[0m"

echo -e "${VERDE}"
cat << 'BANNER'
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
BANNER
echo -e "${RESET}Framework de Pentest — Termux / Linux"
echo ""

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
mkdir -p logs
PIP_LOG="$DIR/logs/install_pip.log"
: > "$PIP_LOG"

RESUMO_OK=0
RESUMO_FALHAS=""
FALHAS_PY=""
TOOLCHAIN_OK=0      # 1 = usuario autorizou compilar fonte (opcao 1 do submenu)
COMANDO_CRIADO=""

ok()      { RESUMO_OK=$((RESUMO_OK + 1)); echo -e "  ${VERDE}[OK]${RESET} $1"; }
falha()   { RESUMO_FALHAS="$RESUMO_FALHAS  - $1"$'\n'; echo -e "  ${VERMELHO}[FALHOU]${RESET} $1"; }
aviso()   { echo -e "  ${AMARELO}[!]${RESET} $1"; }

# ------------------------------------------------------------
# 1. Funcoes base (definidas ANTES de qualquer uso)
# ------------------------------------------------------------
sys_instalar() {   # instala pacotes do sistema tolerando falhas
    [ -z "$GERENCIADOR" ] && return 1
    case "$GERENCIADOR" in
        pkg)      pkg install -y "$@" ;;
        apt-get)  $SUDO apt-get install -y "$@" ;;
        pacman)   $SUDO pacman -S --noconfirm "$@" ;;
        apk)      $SUDO apk add "$@" ;;
        dnf)      $SUDO dnf install -y "$@" ;;
        *)        return 1 ;;
    esac
}

sys_atualizar() {
    [ -z "$GERENCIADOR" ] && return 1
    case "$GERENCIADOR" in
        pkg)      pkg update -y ;;
        apt-get)  $SUDO apt-get update ;;
        pacman)   $SUDO pacman -Syu --noconfirm ;;
        apk)      $SUDO apk update ;;
        dnf)      $SUDO dnf makecache || true ;;
        *)        return 1 ;;
    esac
}

# nome de importacao difere do nome do pacote (pynacl -> nacl)
nome_import() {
    case "$1" in
        pynacl) echo "nacl" ;;
        *)      echo "$1" ;;
    esac
}

py_ok() { "$PY" -c "import $(nome_import "$1")" >/dev/null 2>&1; }

pip_tentar() {   # tenta instalacao; saida vai para o log (nunca polui a tela)
    "$PY" -m pip install "$@" >> "$PIP_LOG" 2>&1
}

# Pacotes que exigem RUST/C para compilar: NUNCA sao buildados da fonte
# (e exatamente daqui que vem o erro 'metadata-generation-failed / maturin').
fonte_exige_toolchain() {
    case "$1" in
        cryptography|bcrypt|pynacl|nacl|cffi|paramiko|maturin|setuptools-rust) return 0 ;;
        *) return 1 ;;
    esac
}

# ------------------------------------------------------------
# 2. Comando global 'fsataque' (criado ANTES das instalacoes)
# ------------------------------------------------------------
criar_comando() {
    chmod +x "$DIR/fsataque.sh" "$DIR/install.sh" 2>/dev/null || true
    if [ "$PLATAFORMA" = "termux" ] && [ -n "${PREFIX:-}" ]; then
        ALVO_BIN="$PREFIX/bin"
    elif [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
        ALVO_BIN="$PREFIX/bin"
    elif [ -w "/usr/local/bin" ]; then
        ALVO_BIN="/usr/local/bin"
    else
        ALVO_BIN="$HOME/.local/bin"
        mkdir -p "$ALVO_BIN"
    fi
    cat > "$ALVO_BIN/fsataque" << EOF
#!/usr/bin/env bash
exec bash "$DIR/fsataque.sh" "\$@"
EOF
    chmod +x "$ALVO_BIN/fsataque"
    COMANDO_CRIADO="$ALVO_BIN/fsataque"
    ok "comando global: fsataque -> $COMANDO_CRIADO"
    case ":$PATH:" in
        *":$ALVO_BIN:"*) : ;;
        *) aviso "$ALVO_BIN fora do PATH — reabra o terminal ou rode: bash \"$DIR/fsataque.sh\"" ;;
    esac
}

# ------------------------------------------------------------
# 3. Detecta Termux ou Linux
# ------------------------------------------------------------
if [ -n "${PREFIX:-}" ] && { [ -d "/data/data/com.termux" ] || command -v pkg >/dev/null 2>&1; }; then
    PLATAFORMA="termux"
    GERENCIADOR="pkg"
    echo -e "${VERDE}[+] Plataforma detectada: Termux${RESET}"
else
    PLATAFORMA="linux"
    if command -v apt-get >/dev/null 2>&1; then GERENCIADOR="apt-get"
    elif command -v pacman >/dev/null 2>&1; then GERENCIADOR="pacman"
    elif command -v apk >/dev/null 2>&1; then GERENCIADOR="apk"
    elif command -v dnf >/dev/null 2>&1; then GERENCIADOR="dnf"
    else GERENCIADOR=""
    fi
    echo -e "${VERDE}[+] Plataforma detectada: Linux (gerenciador: ${GERENCIADOR:-nenhum})${RESET}"
fi

SUDO=""
if [ "$PLATAFORMA" = "linux" ] && [ "$(id -u)" != "0" ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
    echo -e "${AMARELO}[!] Python ainda nao instalado — instalando...${RESET}"
    if [ "$PLATAFORMA" = "termux" ]; then sys_instalar python >> "$PIP_LOG" 2>&1
    else sys_instalar python3 >> "$PIP_LOG" 2>&1; fi
    PY="$(command -v python3 || command -v python || true)"
fi

if [ -z "$PY" ]; then
    echo -e "${VERMELHO}[!] Python nao encontrado — instale manualmente e rode de novo.${RESET}"
    exit 1
fi

pacote_sistema() {   # nome do pacote no gerenciador para modulo python (vazio = nao existe)
    if [ "$PLATAFORMA" = "termux" ]; then
        # nomes verificados no repositorio termux-packages
        case "$1" in
            cryptography) echo "python-cryptography" ;;
            bcrypt)       echo "python-bcrypt" ;;
            pynacl)       echo "python-pynacl" ;;
            pillow)       echo "python-pillow" ;;
            *)            echo "" ;;   # requests/qrcode/paramiko: pip (puro Python / --no-deps)
        esac
    else
        case "$1" in
            requests)     echo "python3-requests" ;;
            qrcode)       echo "python3-qrcode" ;;
            cryptography) echo "python3-cryptography" ;;
            paramiko)     echo "python3-paramiko" ;;
            bcrypt)       echo "python3-bcrypt" ;;
            pynacl)       echo "python3-nacl" ;;
            *)            echo "" ;;
        esac
    fi
}

# ------------------------------------------------------------
# 4. Instalacao de pacote Python SEM compilar codigo
#    ordem: system pkg -> pip (so wheels) -> pip --user -> no-deps
#    Fonte so quando o usuario escolheu a toolchain (submenu [1]).
# ------------------------------------------------------------
instalar_py() {
    MOD="$1"
    if py_ok "$MOD"; then ok "python:$MOD (ja instalado)"; return 0; fi

    SYSN="$(pacote_sistema "$MOD")"
    if [ -n "$SYSN" ]; then
        sys_instalar "$SYSN" >> "$PIP_LOG" 2>&1 || true
        if ! py_ok "$MOD" && [ "$PLATAFORMA" = "termux" ]; then
            # repositorio desatualizado e a causa mais comum do pkg falhar
            aviso "pkg nao resolveu $SYSN — atualizando repositorio e tentando de novo..."
            sys_atualizar >> "$PIP_LOG" 2>&1 || true
            sys_instalar "$SYSN" >> "$PIP_LOG" 2>&1 || true
        fi
        if py_ok "$MOD"; then ok "python:$MOD (pacote do sistema: $SYSN)"; return 0; fi
        aviso "pacote do sistema '$SYSN' nao resolveu (detalhes em logs/install_pip.log)"
    fi

    if pip_tentar --only-binary :all: "$MOD" && py_ok "$MOD"; then
        ok "python:$MOD (wheel)"; return 0
    fi
    if pip_tentar --user --only-binary :all: "$MOD" && py_ok "$MOD"; then
        ok "python:$MOD (wheel --user)"; return 0
    fi
    if [ "$MOD" = "paramiko" ]; then
        if pip_tentar --no-deps paramiko && py_ok "$MOD"; then
            ok "python:$MOD (no-deps; crypto via pacote do sistema)"; return 0
        fi
    fi

    # NUNCA compilar pacotes Rust/C sem toolchain autorizada:
    # evita exatamente o erro 'metadata-generation-failed (maturin)'.
    if fonte_exige_toolchain "$MOD" && [ "$TOOLCHAIN_OK" != "1" ]; then
        falha "python:$MOD (sem wheel; fonte exige Rust — instalacao pelo gerenciador)"
        if [ "$PLATAFORMA" = "termux" ]; then
            case "$MOD" in
                cryptography) aviso "Termux: 'pkg install python-cryptography'" ;;
                bcrypt)       aviso "Termux: 'pkg install python-bcrypt'" ;;
                pynacl)       aviso "Termux: 'pkg install python-pynacl'" ;;
                *)            aviso "Termux: 'pkg install python-$MOD'" ;;
            esac
        else
            case "$MOD" in
                cryptography) aviso "Debian/Ubuntu: 'sudo apt install python3-cryptography'" ;;
                paramiko)     aviso "Debian/Ubuntu: 'sudo apt install python3-paramiko'" ;;
                pynacl)       aviso "Debian/Ubuntu: 'sudo apt install python3-nacl'" ;;
                bcrypt)       aviso "Debian/Ubuntu: 'sudo apt install python3-bcrypt'" ;;
                *)            aviso "Tente pelo gerenciador de pacotes do seu sistema" ;;
            esac
        fi
        aviso "SSH brute continua disponivel via hydra (fallback automatico)"
        FALHAS_PY="$FALHAS_PY $MOD"
        return 1
    fi

    if pip_tentar "$MOD" && py_ok "$MOD"; then
        ok "python:$MOD (fonte)"; return 0
    fi

    falha "python:$MOD"
    FALHAS_PY="$FALHAS_PY $MOD"
    aviso "detalhes em logs/install_pip.log"
    return 1
}

# ------------------------------------------------------------
# 5. Dependencias do sistema
# ------------------------------------------------------------
instalar_sistema() {
    echo -e "${VERDE}[+] Dependencias do sistema...${RESET}"
    if [ -z "$GERENCIADOR" ]; then
        aviso "gerenciador de pacotes nao detectado — pulando pacotes do sistema"
        return 0
    fi
    sys_atualizar >> "$PIP_LOG" 2>&1 || aviso "atualizacao de index ignorada"
    if sys_instalar python git curl nmap openssl >> "$PIP_LOG" 2>&1; then
        ok "sistema (python git curl nmap openssl)"
    else
        falha "sistema (pacotes base)"
    fi
    if sys_instalar hydra >> "$PIP_LOG" 2>&1; then
        ok "sistema:hydra"
    else
        aviso "hydra indisponivel — SMB/RDP usam alternativas quando existirem"
    fi
    # pip garantido (Debian costuma separar)
    if ! "$PY" -m pip --version >> "$PIP_LOG" 2>&1; then
        sys_instalar python3-pip >> "$PIP_LOG" 2>&1 || sys_instalar pip >> "$PIP_LOG" 2>&1 || true
    fi
}

instalar_extras() {
    echo -e "${VERDE}[+] Ferramentas extras (disponiveis na plataforma)...${RESET}"
    if [ "$PLATAFORMA" = "termux" ]; then
        EXTRAS="cloudflared exiftool zbar whois termux-api"
    else
        EXTRAS="cloudflared exiftool zbar-utils whois"
    fi
    for f in $EXTRAS; do
        if sys_instalar "$f" >> "$PIP_LOG" 2>&1; then ok "extra:$f"; else aviso "extra:$f indisponivel (opcional)"; fi
    done
}

# ------------------------------------------------------------
# 6. Pacotes Python
# ------------------------------------------------------------
instalar_python_core() {   # nucleo: sempre instala (puro Python)
    echo -e "${VERDE}[+] Pacotes Python nucleo...${RESET}"
    for m in requests qrcode; do instalar_py "$m"; done
}

instalar_python_full() {   # nucleo + crypto/paramiko (SSH brute)
    instalar_python_core
    echo -e "${VERDE}[+] Pacotes Python de crypto/SSH (sem compilacao)...${RESET}"
    # ordem importa: cryptography via pkg ANTES de paramiko (evita pip puxar crypto)
    for m in cryptography bcrypt pynacl paramiko; do instalar_py "$m"; done
}

repetir_falhas() {
    for m in $FALHAS_PY; do instalar_py "$m"; done
}

submenu_falhas() {
    # so aparece se algum pacote Python falhou — usuario escolhe a correcao
    while [ -n "$FALHAS_PY" ]; do
        echo ""
        echo -e "${AMARELO}================ PACOTES COM PROBLEMA ================${RESET}"
        echo -e "${AMARELO}Falharam:$FALHAS_PY${RESET}"
        echo "  [1] Instalar ferramentas de compilacao e tentar de novo"
        echo "  [2] Continuar mesmo assim (modulos afectados mostram aviso)"
        echo "  [3] Sair do submenu (o comando 'fsataque' ja esta criado)"
        printf "%b" "${VERDE}  Escolha: ${RESET}"
        if ! read -r sub; then sub="2"; fi
        sub="${sub%$'\r'}"
        case "$sub" in
            1)
                TOOLCHAIN_OK=1
                aviso "instalando toolchain (pode demorar)..."
                if [ "$PLATAFORMA" = "termux" ]; then
                    sys_instalar rust clang binutils-is-llvm binutils >> "$PIP_LOG" 2>&1 || true
                    # Termux exige o alvo explicito do Cargo para achar o toolchain
                    if command -v rustc >/dev/null 2>&1; then
                        export CARGO_BUILD_TARGET="$(rustc -Vv 2>/dev/null | awk '/host:/{print $2}')"
                        aviso "CARGO_BUILD_TARGET=$CARGO_BUILD_TARGET"
                    fi
                else
                    sys_instalar build-essential python3-dev >> "$PIP_LOG" 2>&1 || true
                fi
                FALHAS_PY=""
                repetir_falhas
                ;;
            2) FALHAS_PY=""; aviso "seguindo com o que falta (fallbacks ativos)" ;;
            3) FALHAS_PY=""; aviso "submenu encerrado — rodando 'fsataque' mesmo assim" ;;
            *) echo -e "${VERMELHO}  Opcao invalida.${RESET}" ;;
        esac
    done
}

# ------------------------------------------------------------
# 7. Telas de phishing (AdvPhishing) + resumo
# ------------------------------------------------------------
pos_instalacao() {
    if [ ! -d "modules/phishing/AdvPhishing" ]; then
        echo -e "${AMARELO}[+] Clonando telas do AdvPhishing (Ignitetch)...${RESET}"
        git clone --depth 1 https://github.com/Ignitetch/AdvPhishing.git modules/phishing/AdvPhishing \
            >> "$PIP_LOG" 2>&1 \
            || aviso "falha ao clonar — o modulo 'templates' tenta de novo depois"
    fi

    [ -n "$COMANDO_CRIADO" ] || criar_comando

    echo ""
    echo -e "${AMARELO}================ RESUMO ================${RESET}"
    echo -e "${VERDE}  Pacotes OK: $RESUMO_OK${RESET}"
    if [ -n "$RESUMO_FALHAS" ]; then
        echo -e "${VERMELHO}  Com falha:${RESET}"
        printf "%b" "$RESUMO_FALHAS"
    fi
    echo -e "${AMARELO}=======================================${RESET}"
    echo -e "${AMARELO}SEM ROOT no Termux: Wi-Fi apenas leitura; BLE limitado;"
    echo "  sem ICMP raw; sem deauth/evil twin/ARP spoof."
    echo -e "  Use APENAS em alvos autorizados. Logs em ./logs/${RESET}"
    if command -v fsataque >/dev/null 2>&1; then
        echo -e "${VERDE}[+] Instalacao concluida. Rode: fsataque${RESET}"
    elif [ -n "$COMANDO_CRIADO" ]; then
        echo -e "${AMARELO}[!] 'fsataque' nao esta no PATH desta sessao.${RESET}"
        echo -e "${AMARELO}    Rode agora:  bash \"$DIR/fsataque.sh\"${RESET}"
        echo -e "${AMARELO}    (reabra o terminal depois para usar 'fsataque')${RESET}"
    else
        echo -e "${VERMELHO}[!] Comando nao criado. Rode: bash \"$DIR/fsataque.sh\"${RESET}"
    fi
}

# ------------------------------------------------------------
# 8. MENU PRINCIPAL (o usuario so digita o numero)
# ------------------------------------------------------------
while true; do
    echo ""
    echo -e "${VERDE}============================================================${RESET}"
    echo -e "${VERDE} FS ATAQUE — INSTALADOR${RESET}   ${CIANO}(digite apenas o numero)${RESET}"
    echo -e "${VERDE}============================================================${RESET}"
    echo "  [1] Instalacao completa (recomendado)"
    echo "       sistema + Python (requests, qrcode, cryptography, paramiko) + extras"
    echo "  [2] Instalacao leve"
    echo "       sistema + Python nucleo — sem brute SSH (evita crypto)"
    echo "  [3] Somente dependencias do sistema"
    echo "  [4] Sair"
    printf "%b" "${VERDE}  Escolha: ${RESET}"
    if ! read -r ESCOLHA; then ESCOLHA="1"; fi   # sem terminal: completa
    ESCOLHA="${ESCOLHA%$'\r'}"                   # pipes do Git Bash mandam CRLF
    case "$ESCOLHA" in
        1)
            criar_comando
            instalar_sistema
            instalar_python_full
            printf "%b" "${CIANO}  Instalar ferramentas extras opcionais? [1] Sim (recomendado) / 2 Nao: ${RESET}"
            if ! read -r ex; then ex="1"; fi
            ex="${ex%$'\r'}"
            if [ "$ex" = "1" ] || [ -z "$ex" ]; then instalar_extras; fi
            submenu_falhas
            pos_instalacao
            break
            ;;
        2)
            criar_comando
            instalar_sistema
            instalar_python_core
            submenu_falhas
            pos_instalacao
            break
            ;;
        3)
            criar_comando
            instalar_sistema
            pos_instalacao
            break
            ;;
        4)
            echo -e "${AMARELO}  Saindo sem instalar.${RESET}"
            exit 0
            ;;
        *)
            echo -e "${VERMELHO}  Opcao invalida — digite 1, 2, 3 ou 4.${RESET}"
            ;;
    esac
done

exit 0
