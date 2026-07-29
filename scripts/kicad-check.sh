#!/usr/bin/env bash
# Oracle KiCad Rouge-Gorge — ERC/DRC en baseline ratchet.
# Usage: kicad-check.sh erc | kicad-check.sh drc
#
# Vert = pas PLUS de violations (erreurs et warnings comptés séparément) que la
# référence committée .tripwire-kicad-baseline. Une baisse met à jour la
# baseline (à committer — la baisser à la main = diff visible en review).
# Objectif : zéro à la fin de la refonte ESP32/nRF24.
#
# Caveat : les comptes dépendent de la version de KiCad (règles par défaut).
# Baseline établie avec KiCad 10.0.x — garder local et CI sur la même mineure.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR" || exit 1

SCH="rili/pcb/rili.kicad_sch"
PCB="rili/pcb/rili.kicad_pcb"
# La CI pointe TRIPWIRE_BASELINE vers .tripwire-kicad-baseline-ci : l'environnement
# conteneur décale les comptes de warnings (fontes/libs globales) — même design,
# même ratchet, référence par environnement.
BASELINE="${TRIPWIRE_BASELINE:-.tripwire-kicad-baseline}"

MODE="${1:-}"
case "$MODE" in erc|drc) ;; *) echo "usage: $0 erc|drc" >&2; exit 2 ;; esac

command -v kicad-cli >/dev/null 2>&1 || { echo "✗ kicad-cli introuvable — impossible de vérifier le design (pas de faux vert)" >&2; exit 1; }
command -v python3   >/dev/null 2>&1 || { echo "✗ python3 introuvable — impossible de compter les violations" >&2; exit 1; }

GITDIR="$(git rev-parse --git-dir 2>/dev/null || echo .git)"
OUTDIR="$GITDIR/tripwire"
mkdir -p "$OUTDIR" 2>/dev/null || OUTDIR="${TMPDIR:-/tmp}"
REPORT="$OUTDIR/kicad-$MODE.json"
rm -f "$REPORT"

# Sans --exit-code-violations : exit != 0 = vrai échec (fichier illisible, crash).
if [ "$MODE" = "erc" ]; then
  kicad-cli sch erc --format json -o "$REPORT" "$SCH" >/dev/null 2>&1
else
  kicad-cli pcb drc --format json -o "$REPORT" "$PCB" >/dev/null 2>&1
fi
rc=$?
[ "$rc" -eq 0 ] && [ -s "$REPORT" ] || { echo "✗ kicad-cli $MODE a échoué (rc=$rc) — fichier corrompu ?" >&2; exit 1; }

# unconnected_items du DRC comptés comme des erreurs (rats nest = vrai problème).
COUNTS="$(python3 - "$MODE" "$REPORT" <<'PYEOF'
import json, sys
mode, path = sys.argv[1], sys.argv[2]
d = json.load(open(path))
if mode == "erc":
    v = [x for s in d.get("sheets", []) for x in s.get("violations", [])]
    extra = 0
else:
    v = d.get("violations", [])
    extra = len(d.get("unconnected_items", [])) + len(d.get("schematic_parity", []))
err = sum(1 for x in v if x.get("severity") == "error") + extra
warn = sum(1 for x in v if x.get("severity") == "warning")
print(err, warn)
PYEOF
)" || { echo "✗ parse du rapport $REPORT impossible" >&2; exit 1; }
ERR="${COUNTS% *}"; WARN="${COUNTS#* }"

get_ref() { grep -E "^$1=" "$BASELINE" 2>/dev/null | head -1 | cut -d= -f2; }
set_ref() {
  local tmp="$BASELINE.tmp.$$"
  { grep -vE "^$1=" "$BASELINE" 2>/dev/null; printf '%s=%s\n' "$1" "$2"; } | LC_ALL=C sort > "$tmp" \
    && mv "$tmp" "$BASELINE"
}

REF_ERR="$(get_ref "${MODE}_errors")"; REF_WARN="$(get_ref "${MODE}_warnings")"
case "$REF_ERR"  in ''|*[!0-9]*) REF_ERR="" ;; esac
case "$REF_WARN" in ''|*[!0-9]*) REF_WARN="" ;; esac

if [ -z "$REF_ERR" ] || [ -z "$REF_WARN" ]; then
  set_ref "${MODE}_errors" "$ERR"; set_ref "${MODE}_warnings" "$WARN"
  echo "» baseline $MODE initialisée : $ERR erreur(s), $WARN warning(s) ($BASELINE — à committer)"
  exit 0
fi

# Jitter DRC : le test hole_clearance de KiCad 10 est non-déterministe sur ce
# board hérité (mesuré : 814/817/819 erreurs sur le même fichier, violations
# uniques différentes d'un run à l'autre). Tolérance sur les ERREURS DRC :
# rouge seulement si > réf + TOL ; le ratchet ne descend que sous réf - TOL
# (évite de verrouiller un run chanceux). ERC déterministe -> TOL 0.
# Garde-fou : quand la réf atteint 0, zéro veut dire zéro (TOL forcée à 0).
TOL_ERR=0
[ "$MODE" = "drc" ] && [ "$REF_ERR" -gt 0 ] && TOL_ERR=10

rc=0
if [ "$ERR" -gt $((REF_ERR + TOL_ERR)) ] || [ "$WARN" -gt "$REF_WARN" ]; then
  echo "✗ $MODE : $ERR erreur(s) (réf $REF_ERR, tolérance +$TOL_ERR), $WARN warning(s) (réf $REF_WARN) — régression vs baseline" >&2
  echo "  détail : $REPORT" >&2
  rc=1
else
  NEW_ERR="$REF_ERR"; NEW_WARN="$REF_WARN"
  [ "$ERR" -lt $((REF_ERR - TOL_ERR)) ] && NEW_ERR="$ERR"
  [ "$WARN" -lt "$REF_WARN" ] && NEW_WARN="$WARN"
  if [ "$NEW_ERR" != "$REF_ERR" ] || [ "$NEW_WARN" != "$REF_WARN" ]; then
    set_ref "${MODE}_errors" "$NEW_ERR"; set_ref "${MODE}_warnings" "$NEW_WARN"
    echo "» ratchet $MODE : $REF_ERR→$NEW_ERR erreur(s), $REF_WARN→$NEW_WARN warning(s) ($BASELINE mis à jour — à committer)"
  fi
  echo "✓ $MODE : $ERR erreur(s), $WARN warning(s) — dans la baseline"
fi
exit "$rc"
