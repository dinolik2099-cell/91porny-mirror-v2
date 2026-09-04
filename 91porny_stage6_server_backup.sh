#!/usr/bin/env bash
set -euo pipefail

# 91porny.com Mirror Project
# Stage 6 server-side code/evidence backup
# Safe backup: does NOT stop/restart V1 or V2 and does NOT make network requests.

PROJECT="/www/wwwroot/91porny"
ARCHIVE_DIR="/www/wwwroot/91porny_backup_archives"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
NAME="91porny_STAGE6_SERVER_BACKUP_${TIMESTAMP}"
WORK="${ARCHIVE_DIR}/${NAME}"
TAR="${ARCHIVE_DIR}/${NAME}.tar.gz"
SHA="${ARCHIVE_DIR}/${NAME}.sha256"

if [[ ! -d "$PROJECT" ]]; then
    echo "ERROR: project directory not found: $PROJECT" >&2
    exit 1
fi

mkdir -p "$ARCHIVE_DIR" "$WORK"

# Preserve the V1 production baseline hash when the file exists.
V1="$PROJECT/mirror/mirror_v1.py"
if [[ -f "$V1" ]]; then
    echo "===== V1 SHA256 ====="
    sha256sum "$V1" | tee "$WORK/V1_SHA256.txt"
fi

# Record current V2 hashes when present.
for f in \
    "$PROJECT/mirror/mirror_v2/config/ad_config.py" \
    "$PROJECT/mirror/mirror_v2/rewrite/ad.py" \
    "$PROJECT/mirror/mirror_v2/rewrite/html.py"; do
    if [[ -f "$f" ]]; then
        sha256sum "$f"
    fi
done | tee "$WORK/V2_SHA256.txt"

# Compile V2 only; no process is started or stopped.
if [[ -d "$PROJECT/mirror" ]]; then
    echo "===== V2 PYTHON COMPILE =====" | tee "$WORK/compile.txt"
    (
        cd "$PROJECT"
        PYTHONPATH="$PROJECT/mirror" python3 -m compileall -q mirror/mirror_v2
    ) 2>&1 | tee -a "$WORK/compile.txt"
    echo "COMPILE_EXIT=${PIPESTATUS[0]}" | tee -a "$WORK/compile.txt"
fi

# Capture process/port state for recovery documentation only.
{
    echo "===== TIMESTAMP ====="
    date '+%F %T %z'
    echo
    echo "===== V1 PROCESS ====="
    pgrep -af 'mirror/mirror_v1.py' || true
    echo
    echo "===== V2 PROCESS ====="
    pgrep -af 'mirror_v2.mirror_v2' || true
    echo
    echo "===== LISTEN PORTS 8021/8022 ====="
    ss -lntp 2>/dev/null | grep -E '127\.0\.0\.1:(8021|8022)\b' || true
} > "$WORK/runtime_state.txt"

# Copy project code and relevant analysis/evidence without recursively copying the archive directory.
mkdir -p "$WORK/project"

# Core project files/code.
tar -C "$PROJECT" -cf - \
    mirror \
    config \
    2>/dev/null | tar -C "$WORK/project" -xf -

# Analysis evidence, if present.
for d in analysis/stage4 analysis/stage5 analysis/stage6; do
    if [[ -d "$PROJECT/$d" ]]; then
        mkdir -p "$WORK/project/$(dirname "$d")"
        tar -C "$PROJECT" -cf - "$d" 2>/dev/null | tar -C "$WORK/project" -xf -
    fi
done

# Generate a complete manifest for the staged backup.
(
    cd "$WORK"
    find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$WORK/FILES_SHA256.txt"

# Package and validate the archive.
tar -C "$ARCHIVE_DIR" -czf "$TAR" "$NAME"
tar -tzf "$TAR" >/dev/null
sha256sum "$TAR" | tee "$SHA"

# Final report.
echo
cat <<REPORT
============================================================
91PORNY STAGE 6 SERVER BACKUP COMPLETE
============================================================
ARCHIVE : $TAR
SHA256  : $SHA
TAR_TEST: PASS
V1      : NOT MODIFIED
V2      : NOT STOPPED / NOT STARTED
NETWORK : NONE
MEDIA   : NONE
============================================================
REPORT
