#!/usr/bin/env bash
# ============================================================
# FS ATAQUE — launcher principal (Termux / Linux)
# ============================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Limpa a tela apenas no menu interativo (sem argumentos)
if [ $# -eq 0 ]; then
    clear 2>/dev/null || true
fi

exec python3 "$DIR/core/menu.py" "$@"
