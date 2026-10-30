#!/bin/bash
ollama serve >/dev/null 2>&1 &
exec gunicorn app:server -b 0.0.0.0:${PORT:-7860} --timeout 180 --workers 1 --threads 4
