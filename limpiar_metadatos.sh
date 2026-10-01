#!/usr/bin/env bash
set -euo pipefail

# ReconForense - backend para limpieza de metadatos
# Requiere: exiftool
#
# Uso:
#   ./limpiar_metadatos.sh analyze archivo.mp4
#   ./limpiar_metadatos.sh clean archivo.mp4 salida_limpia.mp4
#
# El modo clean NO modifica el original: genera una copia limpia.

usage() {
    echo "Uso:"
    echo "  $0 analyze <archivo>"
    echo "  $0 clean   <archivo> <salida>"
}

require_exiftool() {
    command -v exiftool >/dev/null 2>&1 || {
        echo "[ERROR] ExifTool no está instalado." >&2
        echo "Instale con: sudo apt install libimage-exiftool-perl" >&2
        exit 127
    }
}

[[ $# -ge 2 ]] || { usage; exit 2; }
ACTION="$1"
INPUT="$2"

[[ -f "$INPUT" ]] || {
    echo "[ERROR] No existe el archivo: $INPUT" >&2
    exit 3
}

require_exiftool

case "$ACTION" in
    analyze)
        # JSON limpio para que Tkinter pueda cargarlo.
        exiftool -j -G1 -a -s "$INPUT"
        ;;
    clean)
        [[ $# -eq 3 ]] || { usage; exit 2; }
        OUTPUT="$3"

        [[ "$INPUT" != "$OUTPUT" ]] || {
            echo "[ERROR] Entrada y salida no pueden ser el mismo archivo." >&2
            exit 4
        }

        mkdir -p "$(dirname "$OUTPUT")"

        # Copia el archivo y elimina etiquetas de metadatos soportadas por ExifTool.
        # El original permanece intacto.
        exiftool -all= -o "$OUTPUT" "$INPUT" >/dev/null

        # Verificación básica de existencia y tamaño.
        [[ -s "$OUTPUT" ]] || {
            echo "[ERROR] No se generó correctamente la salida." >&2
            exit 5
        }

        echo "[OK] Archivo limpio generado: $OUTPUT"
        ;;
    *)
        usage
        exit 2
        ;;
esac
