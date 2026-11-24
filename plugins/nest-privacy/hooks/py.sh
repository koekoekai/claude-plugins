#!/bin/sh
# Start een Python-script met de Python 3 die er is: `python` (Windows, de meeste installaties) of `python3` (Linux-servers).
# Geen Python 3 gevonden: melden en de hook niet laten blokkeren (exit 0); de CI is de echte poort.
script="$1"; shift
for py in python python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
    exec "$py" "$(dirname "$0")/$script" "$@"
  fi
done
echo "Nest-privacy: geen Python 3 gevonden (python of python3); de hook is overgeslagen." >&2
exit 0
