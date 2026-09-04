#!/usr/bin/env bash
set -e
SRC="/www/wwwroot/91porny"
BACKUP_DIR="/www/wwwroot/91porny_backup_archives"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="${BACKUP_DIR}/91porny_STAGE6_ATTACK_SURFACE_TEST03_${TS}.tar.gz"
mkdir -p "$BACKUP_DIR"
tar -czf "$OUT" --exclude="$SRC/venv" --exclude="$SRC/.git" -C "$(dirname "$SRC")" "$(basename "$SRC")"
sha256sum "$OUT" | tee "${OUT}.sha256"
tar -tzf "$OUT" >/dev/null
echo "FILE=$OUT"
echo "SHA256=$(cut -d' ' -f1 "${OUT}.sha256")"
echo "TAR_TEST=PASS"
