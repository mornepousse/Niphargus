# Niphargus — claude instructions

Clavier split (dérivé Jorne/Kyria), 100 % KiCad pour l'instant : schéma et PCB
dans `hardware/pcb/` (projet KiCad `niphar` — nom complet du produit : **Niphargus**,
ex-Rouge-Gorge/rili), footprints dans
`hardware/pcb/EKR82-footprint.pretty/`.

## Refonte en cours — cahier des charges

Le projet sort de sa tombe pour une refonte complète :
- Remplacer le ProMicro par **ESP32 + nRF24L01+**, fonctionnement **full wireless**.
- **Fallback filaire conservé** : jack TRRS entre les deux moitiés + USB vers
  l'hôte — rebrancher doit suffire à utiliser le clavier.
- **Robustesse ESD obligatoire** : les claviers précédents plantaient à la
  décharge électrostatique quand l'utilisateur revenait au clavier. Le nouveau
  design doit prévoir TVS sur USB/TRRS et toute ligne exposée (matrice,
  touches), plans de masse soignés, chemin de décharge vers GND.
- Objectif mécanique : **fin et durable**.
- Retirer « les sw » (à préciser avec l'utilisateur au moment de la refonte du schéma).
- Le firmware ESP32/nRF24 **ne vit PAS dans ce repo** : il est développé dans
  `~/Documents/GitHub/KaSe_firmware` (KeSp_firmware), aux côtés du dongle dont il
  réutilise la pile RF et le moteur keymap. Design :
  `KaSe_firmware/docs/superpowers/specs/2026-08-19-niphargus-firmware-design.md`.
  Ce repo reste le matériel : schéma, PCB, boîtier. Pas de `MODULE_FAST` à
  renseigner ici.

## Workflow anti-régression (OBLIGATOIRE)

Source unique de vérité : `scripts/check.sh`.
- `./scripts/check.sh --fast` — ERC du schéma vs baseline (.tripwire-kicad-baseline) (~secondes)
- `./scripts/check.sh` — fast + le DRC complet du PCB

**Vert = baseline ratchet KiCad.** Le design hérité est plein de violations
(règles KiCad 10 sur un board KiCad 6) : vert signifie « jamais PLUS d'erreurs
ni de warnings ERC/DRC que la référence committée `.tripwire-kicad-baseline` ».
Toute baisse est enregistrée automatiquement dans la baseline → **committer le
fichier**. La baisser à la main = diff visible en review. Objectif : zéro à la
fin de la refonte ESP32/nRF24. Caveat : les comptes dépendent de la version de
KiCad ET de l'environnement (fontes, libs globales) — la CI est épinglée sur la
version exacte du poste (10.0.4) et a sa propre référence committée
`.tripwire-kicad-baseline-ci` (env `TRIPWIRE_BASELINE`) : +19 warnings ERC / +5
DRC en conteneur, même design. Les deux baselines suivent le même ratchet ; les
deux objectifs sont zéro. Le DRC `hole_clearance` de KiCad 10 étant
non-déterministe (±quelques erreurs par run), l'oracle tolère ±10 erreurs DRC
(tolérance forcée à 0 quand la référence atteint 0).

**Activation des hooks git (une fois par clone)** :
```bash
./scripts/install-hooks.sh   # ou: git config core.hooksPath scripts/hooks
```
`pre-push` lance le check complet et bloque le push si rouge. WIP : `git push --no-verify`.

**Hooks Claude Code** (`.claude/settings.json`, automatiques) :
- `PostToolUse` sur édition d'un fichier surveillé (`hardware/`, `case/`)
  → `check.sh --fast`.
- `Stop` → `check.sh --fast` (garde-fou ~1 s avant de conclure). Le build complet
  (ERC/DRC kicad-cli) n'est PAS relancé à chaque fin de tour : il reste garanti
  au pre-push git.

### Norme TDD
Ce repo n'héberge pas de logique exécutable : l'oracle est le ratchet ERC/DRC
ci-dessus. La norme TDD sur la logique pure (protocole radio, matrice, modes
filaire/sans-fil) s'applique côté KeSp_firmware, où vit le firmware.

### Économie de modèles (subagents)
Le pipeline check.sh permet de descendre en gamme SANS risque d'hallucination,
mais seulement là où un oracle rattrape l'erreur :
- **Modèle économique (haiku) OK** : transcription de code déjà spécifié,
  refactors mécaniques, extraction citée (`fichier:ligne` obligatoire) — le
  check, la compilation ou le recoupement des citations attrapent la dérive.
- **Jamais en dessous de sonnet** : review, audit, debug, **et l'écriture
  d'assertions de test** — une assertion tautologique ou un verdict halluciné
  passent l'oracle mécanique au vert. Le jugement ne descend pas en gamme.
- Toute tâche économique DOIT finir par `./scripts/check.sh --fast` vert, et
  un test rewiré/écrit DOIT prouver qu'il mord (bug transitoire → rouge → revert).
