#!/usr/bin/env bash
set -e

# Activa el entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python -m src.main "$@"
