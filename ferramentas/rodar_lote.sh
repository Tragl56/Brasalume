#!/bin/bash
# Renderiza uma lista de monstros, um processo do Blender por monstro (uma falha não derruba o resto), com uma nova tentativa.
# uso: rodar_lote.sh <lista.txt> <modo: quadros|monstros> <log> <gpu|cpu>
LISTA=$1; MODO=$2; LOG=$3; LADO=$4
cd "$(dirname "$0")/.."   # raiz do projeto
: > "$LOG"
for s in $(tr ',' ' ' < "$LISTA"); do
  for tent in 1 2; do
    if [ "$LADO" = gpu ]; then
      out=$(BRASALUME_GPU=CUDA /e/blender.exe --background --factory-startup --python arte/blender/fontes/gerar.py -- $MODO $s 2>&1 | grep -E "QUADROS_OK|INIMIGO_OK|_ERRO|EXCEPTION|Traceback" | tr '\n' ' ')
    else
      out=$(BRASALUME_THREADS=6 /e/blender.exe --background --factory-startup --python arte/blender/fontes/gerar.py -- $MODO $s 2>&1 | grep -E "QUADROS_OK|INIMIGO_OK|_ERRO|EXCEPTION|Traceback" | tr '\n' ' ')
    fi
    echo "$s [$tent] $out" >> "$LOG"
    case "$out" in *_OK*) break;; esac
  done
done
echo FIM >> "$LOG"
