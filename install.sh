#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# FS ATAQUE — instalador INTERATIVO (Termux / Linux)
# O usuario apenas SELECIONA opcoes numeradas — nenhum
# comando extra precisa ser digitado.
# Uso: git clone <repo> && cd fsatack && bash install.sh
# ============================================================

VERDE="\e[32m"; AMARELO="\e[33m"; VERMELHO="\e[31m"; CIANO="\e[36m"; RESET="\e[0m"

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

ok()      { RESUMO_OK=$((RESUMO_OK + 1)); echo -e "  ${VERDE}[OK]${RESET} $1"; }
falha()   { RESUMO_FALHAS="$RESUMO_FALHAS  - $1"$'\n'; echo -e "  ${VERMELHO}[FALHOU]${RESET} $1"; }
aviso()   { echo -e "  ${AMARELO}[!]${RESET} $1"; }

# ------------------------------------------------------------
# 1. Detecta Termux ou Linux
# ------------------------------------------------------------
if [ -n "${PREFIX:-}" ] && [ -d "/data/data/com.termux" ]; then
    PLATAFORMA="termux"
    GERENCIADOR="pkg"
    echo -e "${VERDE}[+] Plataforma detectada: Termux${RESET}"
else
    PLATAFORMA="linux"
    if command -v apt-get >/dev/null 2>&1; then GERENCIADOR="apt-get"
    elif command -v pacman >/dev/null 2>&1; then GERENCIADOR="pacman"
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
    if [ "$PLATAFORMA" = "termux" ]; then pkg install -y python >/dev/null 2>&1; else $SUDO "$GERENCIADOR" install -y python3 >/dev/null 2>&1; fi
    PY="$(command -v python3 || command -v python || true)"
fi

sys_instalar() {   # instala pacotes do sistema tolerando falhas
    [ -z "$GERENCIADOR" ] && return 1
    case "$GERENCIADOR" in
        pkg)     pkg install -y "$@" ;;
        apt-get) $SUDO apt-get install -y "$@" ;;
        pacman)  $SUDO pacman -S --noconfirm "$@" ;;
        *)       return 1 ;;
    esac
}

sys_atualizar() {
    [ -z "$GERENCIADOR" ] && return 1
    case "$GERENCIADOR" in
        pkg)     pkg update -y ;;
        apt-get) $SUDO apt-get update ;;
        pacman)  $SUDO pacman -Sy --noconfirm ;;
        *)       return 1 ;;
    esac
}

py_ok() { "$PY" -c "import $1" >/dev/null 2>&1; }

pip_tentar() {   # tenta instalacao; saida vai para o log (nunca polui a tela)
    "$PY" -m pip install "$@" >> "$PIP_LOG" 2>&1
}

pacote_sistema() {   # nome do pacote no gerenciador para modulo python (vazio = nao existe)
    if [ "$PLATAFORMA" = "termux" ]; then
        case "$1" in
            cryptography) echo "python-cryptography" ;;
            bcrypt)      echo "python-bcrypt" ;;
            *)           echo "" ;;
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
# 2. Instalacao de pacote Python SEM compilar codigo
#    ordem: system pkg -> pip (so wheels) -> pip --user -> no-deps -> fonte
# ------------------------------------------------------------
instalar_py() {
    MOD="$1"
    if py_ok "$MOD"; then ok "python:$MOD (ja instalado)"; return 0; fi

    SYSN="$(pacote_sistema "$MOD")"
    if [ -n "$SYSN" ]; then
        sys_instalar "$SYSN" >> "$PIP_LOG" 2>&1 || true
        if py_ok "$MOD"; then ok "python:$MOD (pacote do sistema: $SYSN)"; return 0; fi
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
    if pip_tentar "$MOD" && py_ok "$MOD"; then
        ok "python:$MOD (fonte)"; return 0
    fi

    falha "python:$MOD"
    FALHAS_PY="$FALHAS_PY $MOD"
    aviso "detalhes em logs/install_pip.log"
    return 1
}

# ------------------------------------------------------------
# 3. Dependencias do sistema
# ------------------------------------------------------------
instalar_sistema() {
    echo -e "${VERDE}[+] Dependencias do sistema...${RESET}"
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
# 4. Pacotes Python
# ------------------------------------------------------------
instalar_python_core() {   # nucleo: sempre instala (puro Python)
    echo -e "${VERDE}[+] Pacotes Python nucleo...${RESET}"
    for m in requests qrcode; do instalar_py "$m"; done
}

instalar_python_full() {   # nucleo + crypto/paramiko (SSH brute)
    instalar_python_core
    echo -e "${VERDE}[+] Pacotes Python de crypto/SSH (sem compilacao)...${RESET}"
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
        echo "  [3] Sair"
        printf "%b" "${VERDE}  Escolha: ${RESET}"
        if ! read -r sub; then sub="2"; fi
        case "$sub" in
            1)
                aviso "instalando toolchain (pode demorar)..."
                if [ "$PLATAFORMA" = "termux" ]; then
                    sys_instalar rust clang binutils >> "$PIP_LOG" 2>&1 || true
                else
                    sys_instalar build-essential python3-dev >> "$PIP_LOG" 2>&1 || true
                fi
                FALHAS_PY=""
                repetir_falhas
                ;;
            2) FALHAS_PY=""; aviso "seguindo com o que falta (fallbacks ativos)" ;;
            3) exit 1 ;;
            *) echo -e "${VERMELHO}  Opcao invalida.${RESET}" ;;
        esac
    done
}

# ------------------------------------------------------------
# 5. Telas de phishing (AdvPhishing) + comando global + avisos
# ------------------------------------------------------------
pos_instalacao() {
    if [ ! -d "modules/phishing/AdvPhishing" ]; then
        echo -e "${AMARELO}[+] Clonando telas do AdvPhishing (Ignitetch)...${RESET}"
        git clone --depth 1 https://github.com/Ignitetch/AdvPhishing.git modules/phishing/AdvPhishing \
            >> "$PIP_LOG" 2>&1 \
            || aviso "falha ao clonar — o modulo 'templates' tenta de novo depois"
    fi

    chmod +x fsataque.sh install.sh 2>/dev/null || true

    if [ "$PLATAFORMA" = "termux" ]; then
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
    ok "comando global: fsataque -> $ALVO_BIN/fsataque"

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
    echo "  Use APENAS em alvos autorizados. Logs em ./logs/${RESET}"
    echo -e "${VERDE}[+] Instalacao concluida. Rode: fsataque${RESET}"
}

# ------------------------------------------------------------
# 6. MENU PRINCIPAL (o usuario so digita o numero)
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
    case "$ESCOLHA" in
        1)
            instalar_sistema
            instalar_python_full
            printf "%b" "${CIANO}  Instalar ferramentas extras opcionais? [1] Sim (recomendado) / 2 Nao: ${RESET}"
            if ! read -r ex; then ex="1"; fi
            if [ "$ex" = "1" ] || [ -z "$ex" ]; then instalar_extras; fi
            submenu_falhas
            pos_instalacao
            break
            ;;
        2)
            instalar_sistema
            instalar_python_core
            submenu_falhas
            pos_instalacao
            break
            ;;
        3)
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
