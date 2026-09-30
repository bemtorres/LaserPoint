#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/python" ]; then
  echo "Ejecuta ./install.sh primero."
  exit 1
fi
exec .venv/bin/python main.py "$@"
