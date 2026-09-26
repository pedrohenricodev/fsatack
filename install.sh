#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# FS ATAQUE — instalador para Termux (sem root) e Linux
# Uso: git clone <repo> && cd fsatack && bash install.sh
# ============================================================
set -e

VERDE="\e[32m"; AMARELO="\e[33m"; VERMELHO="\e[31m"; RESET="\e[0m"

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
cd "$DIR"

# ------------------------------------------------------------
# 1. Detecta Termux ou Linux
# ------------------------------------------------------------
if [ -n "$PREFIX" ] && [ -d "/data/data/com.termux" ]; then
    PLATAFORMA="termux"
    GERENCIADOR="pkg"
    echo -e "${VERDE}[+] Plataforma detectada: Termux${RESET}"
else
    PLATAFORMA="linux"
    echo -e "${VERDE}[+] Plataforma detectada: Linux${RESET}"
    if command -v apt-get >/dev/null 2>&1; then
        GERENCIADOR="sudo apt-get"
    elif command -v pacman >/dev/null 2>&1; then
        GERENCIADOR="sudo pacman -S --noconfirm"
    else
        GERENCIADOR=""
        echo -e "${AMARELO}[!] Gerenciador de pacotes nao identificado.${RESET}"
    fi
fi

# ------------------------------------------------------------
# 2. Instala dependências do sistema
# ------------------------------------------------------------
PAQUETES="python git curl nmap openssl"
if [ -n "$GERENCIADOR" ]; then
    echo -e "${VERDE}[+] Instalando dependencias: $PAQUETES${RESET}"
    if [ "$PLATAFORMA" = "termux" ]; then
        pkg update -y || true
        pkg install -y $PAQUETES || true
    else
        $GERENCIADOR update -y || true
        $GERENCIADOR install -y $PAQUETES || true
    fi
fi

# hydra é opcional (nem toda distro/locação o possui)
echo -e "${AMARELO}[+] Tentando instalar hydra (opcional)...${RESET}"
if [ "$PLATAFORMA" = "termux" ]; then
    pkg install -y hydra || echo -e "${AMARELO}[!] hydra indisponivel — modulos SMB/RDP usam alternativas.${RESET}"
else
    $GERENCIADOR install -y hydra || echo -e "${AMARELO}[!] hydra indisponivel.${RESET}"
fi

# ------------------------------------------------------------
# 3. Dependências Python
# ------------------------------------------------------------
echo -e "${VERDE}[+] Instalando requirements.txt...${RESET}"
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install -r requirements.txt || python3 -m pip install --user -r requirements.txt

# ------------------------------------------------------------
# 4. Telas de phishing (AdvPhishing, adaptado para Termux)
# ------------------------------------------------------------
if [ ! -d "modules/phishing/AdvPhishing" ]; then
    echo -e "${AMARELO}[+] Clonando telas do AdvPhishing (Ignitetch)...${RESET}"
    git clone --depth 1 https://github.com/Ignitetch/AdvPhishing.git modules/phishing/AdvPhishing \
        || echo -e "${AMARELO}[!] Falha ao clonar — o modulo 'templates' tenta de novo depois.${RESET}"
fi

# ------------------------------------------------------------
# 5. Permissões + comando global
# ------------------------------------------------------------
chmod +x fsataque.sh install.sh 2>/dev/null || true

if [ "$PLATAFORMA" = "termux" ]; then
    ALVO_BIN="$PREFIX/bin"
else
    if [ -w "/usr/local/bin" ]; then
        ALVO_BIN="/usr/local/bin"
    else
        ALVO_BIN="$HOME/.local/bin"
        mkdir -p "$ALVO_BIN"
    fi
fi

cat > "$ALVO_BIN/fsataque" << EOF
#!/usr/bin/env bash
exec bash "$DIR/fsataque.sh" "\$@"
EOF
chmod +x "$ALVO_BIN/fsataque"
echo -e "${VERDE}[+] Comando global criado: fsataque -> $ALVO_BIN/fsataque${RESET}"

# ------------------------------------------------------------
# 6. Avisos de limitação (sem root)
# ------------------------------------------------------------
echo ""
echo -e "${AMARELO}================ AVISOS ================${RESET}"
echo -e "${AMARELO}* SEM ROOT no Termux:${RESET}"
echo "  - Wi-Fi: apenas LEITURA (sem deauth/evil twin/ARP spoof)."
echo "  - BLE: scan limitado; flooding/fuzzing nao incluidos."
echo "  - Sem ICMP raw: ping usa o comando comum (limitado)."
echo "* Para Wi-Fi/BLE completos: Android com root + suporte de hardware."
echo "* Use APENAS em alvos autorizados. Logs em ./logs/"
echo -e "${AMARELO}=======================================${RESET}"
echo -e "${VERDE}[+] Instalacao concluida. Rode: fsataque${RESET}"
