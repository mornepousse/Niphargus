# Schéma KiCad des moitiés Rouge-Gorge v2 — Plan d'implémentation

> **Exécution en binôme** : Mae dessine dans KiCad (GUI), Claude fournit chaque bloc (composants,
> valeurs, table de connexions), vérifie au tripwire et relit le `.kicad_sch` (format texte).
> Les étapes utilisent des cases `- [ ]`. Une tâche = un bloc = un commit.

**But** : le schéma complet d'une moitié Rouge-Gorge v2 (les deux moitiés partagent le même schéma), ERC zéro erreur, prêt pour le layout.

**Architecture** : projet KiCad neuf `rouge-gorge/`, schéma hiérarchique 4 feuilles (alim / mcu+radio / matrice / liens). Réf. : design doc `docs/superpowers/specs/2026-07-29-rouge-gorge-refonte-design.md`.

**Stack** : KiCad 10.0.x · tripwire (`./scripts/check.sh --fast` = ERC ratchet) · libs locales existantes (`corne-cherry/pcb/*.pretty`, `mae.kicad_sym`) + libs officielles KiCad.

## Contraintes globales

- **Zéro header** — tout composant est SMD soudé ou en socket plat validé au design doc.
- **La radio WiFi/BLE du S3 ne sera jamais utilisée** (MCP1700 250 mA — décision Mae).
- **Hors périmètre de ce plan** : le coffre P4 (point ouvert №1), le firmware, le layout PCB.
- **Baseline tripwire neuve** : sur ce projet, vert = **0 erreur ERC** (pas d'héritage toléré).
- Coordination : Mae peut garder corne-cherry ouvert (projet séparé) ; elle **sauvegarde** avant chaque revue de Claude.
- Le connecteur inter-moitiés est dessiné **générique 4 pins** (`J_LINK`) — le choix TRRS vs magnétique (point ouvert №2) se fera au layout, éventuellement en double empreinte.

## Carte des pins ESP32-S3-MINI-1 (référence pour toutes les tâches)

| Fonction | GPIO | Contrainte respectée |
|---|---|---|
| Lignes matrice ROW0-3 (sorties scan) | 1, 2, 4, 5 | RTC ✓ (scan ULP en sommeil) |
| Colonnes matrice COL0-6 (entrées, pull-down) | 6, 7, 8, 9, 10, 11, 12 | RTC ✓ (réveil EXT1 any-high) |
| Jauge batterie (ADC) | 13 | ADC2 — OK car WiFi jamais actif |
| Détection VBUS | 14 | RTC ✓ (réveil au branchement) |
| UART lien TX / RX | 17 / 18 | — |
| USB D− / D+ | 19 / 20 | pins USB natifs (fixe) |
| EN du load switch 5 V (poignée de main) | 21 | — |
| nRF24 : CE / CSN / MOSI / SCK / MISO / IRQ | 33 / 34 / 35 / 36 / 37 / 38 | SPI logiciel/matériel, hors RTC (pas besoin) |
| Boot (pad de test) | 0 | strapping — pull-up 10k, pad |
| Interdits | 3, 45, 46 (strapping), 43/44 (UART0 debug → pads de test) | |

---

### Tâche 0 : Scaffold du projet + bascule tripwire

**Fichiers :**
- Créer (Mae, GUI) : `rouge-gorge/rouge-gorge.kicad_pro`, `.kicad_sch`, `.kicad_pcb`
- Modifier (Claude) : `scripts/kicad-check.sh` (cibles SCH/PCB), `CLAUDE.md` (chemins surveillés déjà OK : `rouge-gorge/` n'y est pas → l'ajouter), `.tripwire-kicad-baseline` (reset)

**Interfaces :** produit le squelette de projet + 4 feuilles hiérarchiques vides nommées `alim`, `mcu_radio`, `matrice`, `liens` que les tâches 1-4 remplissent.

- [ ] **Étape 1 (Mae)** : KiCad → Fichier → Nouveau projet → `rouge-gorge/rouge-gorge` à la racine du repo. Dans le schéma racine, poser 4 feuilles hiérarchiques (Placer → Feuille) : `alim.kicad_sch`, `mcu_radio.kicad_sch`, `matrice.kicad_sch`, `liens.kicad_sch`. Recopier les tables de libs : Préférences → Gérer les librairies de symboles/empreintes → ajouter (projet) `mae.kicad_sym`, `rouge_gorge.kicad_sym` et les `.pretty` de `corne-cherry/pcb/` utiles (`key`, `MaeLid`, `EKR82-footprint`). Sauvegarder.
- [ ] **Étape 2 (Claude)** : retarget `scripts/kicad-check.sh` : `SCH="rouge-gorge/rouge-gorge.kicad_sch"`, `PCB="rouge-gorge/rouge-gorge.kicad_pcb"` ; supprimer `.tripwire-kicad-baseline` (la baseline se ré-initialise au premier run) ; ajouter `rouge-gorge/` à la puce chemins surveillés de CLAUDE.md.
- [ ] **Étape 3 (vérif)** : `./scripts/check.sh --fast` → vert, baseline ré-initialisée à ~0/0 (schéma quasi vide). `./scripts/check.sh` → DRC : le PCB vide initialisera sa référence (probablement 1 erreur `invalid_outline` — c'est la référence de départ, elle fondra au layout).
- [ ] **Étape 4 (commit)** : `git add rouge-gorge/ scripts/kicad-check.sh CLAUDE.md .tripwire-kicad-baseline && git commit -m "feat(v2): projet KiCad rouge-gorge + bascule tripwire"`

### Tâche 1 : Feuille `alim` — 16340 → système

**Fichiers :** Modifier (Mae) : `rouge-gorge/alim.kicad_sch`

**Interfaces :** produit les nets `+BATT` (cellule), `VSYS` (aval load-sharing), `+3V3` (sortie MCP1700), `VBUS_5V` (entrée USB), `VBAT_SENSE` (vers GPIO13), `GND`. Consomme `VBUS_5V` de la feuille `liens`.

Chaîne complète et valeurs :

```
16340 (+) ─ B+ ─┬─ DW01A(+FS8205 dual-FET) protection ─ +BATT
                │    DW01A : VCC via R 100Ω + C 100nF ; CS via R 1kΩ ; FS8205 entre B− et GND
+BATT ─┬─ TP4056 (BAT) ← VBUS_5V (VCC, C 10µF)   Rprog = 2,4 kΩ → ~500 mA
       │    TEMP→GND (désactivé) ; CE→VCC ; CHRG → LED rouge + R 1 kΩ vers VBUS_5V
       └─ Q1 AO3407 (P-FET, load sharing) ─ VSYS
            gate Q1 → VBUS_5V via R 10k (VBUS présent = FET bloqué)
VBUS_5V ─ D1 Schottky SS14 ─ VSYS        (câble branché : le système mange le 5 V… via 3V3)
VSYS ─ SW1 slide MSK-12C02 (coupure côté système) ─ MCP1700-3302E/TT ─ +3V3
            MCP1700 : Cin 1µF, Cout 1µF céramique
+BATT ─ R 1M ─┬─ R 1M ─ GND   (jauge)    ┬ = VBAT_SENSE, + C 100nF vers GND
```

- [ ] **Étape 1 (Claude)** : livrer la liste de courses du bloc (réfs LCSC/mouser des 9 composants) en commentaire de la PR/du commit — symboles KiCad : `Battery_Management:TP4056` (ou équiv. dans libs officielles ; sinon je fournis le symbole dans `rouge_gorge.kicad_sym`), `Power_Protection:DW01A`? (sinon fourni), `Transistor_FET:AO3407`, `Diode:SS14`, `Regulator_Linear:MCP1700-3302E_SOT23`, `Switch:SW_SPDT` (MSK-12C02), `Device:R`, `Device:C`, `Device:Battery_Cell`.
- [ ] **Étape 2 (Mae)** : dessiner la feuille selon la chaîne ci-dessus, netlabels exactement `+BATT`, `VSYS`, `+3V3`, `VBUS_5V`, `VBAT_SENSE`. PWR_FLAG sur `+BATT` et `VBUS_5V`. Sauvegarder.
- [ ] **Étape 3 (vérif)** : `./scripts/check.sh --fast` → vert (0 erreur ; le ratchet reste 0). Claude relit `alim.kicad_sch` (texte) et recoupe chaque net contre la chaîne ci-dessus — écarts signalés, corrigés, re-check.
- [ ] **Étape 4 (commit)** : `git add rouge-gorge/ .tripwire-kicad-baseline && git commit -m "feat(v2): feuille alim — 16340, protection, charge 500mA, load-sharing, MCP1700"`

### Tâche 2 : Feuille `mcu_radio` — S3-MINI-1 + nRF24

**Fichiers :** Modifier (Mae) : `rouge-gorge/mcu_radio.kicad_sch`

**Interfaces :** consomme `+3V3`, `GND`, `VBAT_SENSE`, `VBUS_5V` (via diviseur → `VBUS_DET`). Produit : `ROW0..ROW3`, `COL0..COL6` (vers `matrice`), `USB_DP`/`USB_DM`, `LINK_TX`/`LINK_RX`, `LINK_5V_EN` (vers `liens`).

Contenu (voir carte des pins en tête de plan — elle est normative) :

- `RF_Module:ESP32-S3-MINI-1` (déjà dans ton brouillon s3.kicad_sch — le reprendre). Découplage : C 10µF + 2× C 100nF sur 3V3.
- EN : R 10k vers +3V3 + C 1µF vers GND. GPIO0 : R 10k vers +3V3 + pad de test `TP_BOOT`. Pads de test `TP_TX0`/`TP_RX0` sur GPIO43/44.
- Détection VBUS : `VBUS_5V ─ R 100k ─┬─ R 100k ─ GND`, ┬ = net `VBUS_DET` → GPIO14, + C 100nF.
- `VBAT_SENSE` → GPIO13.
- nRF24 : symbole `RF:NRF24L01_Breakout` (celui de KaSe V2), connecteur 2×4 femelle bas profil ou soudé à plat — empreinte au layout. Alim module : C 10µF + 100nF au plus près. CE/CSN/MOSI/SCK/MISO/IRQ → GPIO 33/34/35/36/37/38.
- Netlabels de sortie : `ROW0..3`, `COL0..6`, `USB_DP` (GPIO20), `USB_DM` (GPIO19), `LINK_TX` (17), `LINK_RX` (18), `LINK_5V_EN` (21).

- [ ] **Étape 1 (Mae)** : dessiner ; sauvegarder.
- [ ] **Étape 2 (vérif)** : `./scripts/check.sh --fast` vert + revue texte Claude (chaque GPIO contre la carte des pins — c'est LA revue critique du projet : une matrice hors RTC = réveil cassé, découvert au firmware).
- [ ] **Étape 3 (commit)** : `git commit -m "feat(v2): feuille mcu_radio — S3-MINI-1, nRF24, pinout RTC"` (avec `git add rouge-gorge/ .tripwire-kicad-baseline`).

### Tâche 3 : Feuille `matrice` — 26 touches hybrides

**Fichiers :** Modifier (Mae) : `rouge-gorge/matrice.kicad_sch`

**Interfaces :** consomme `ROW0..3`, `COL0..6`. Rien d'autre ne la touche.

- 26 × (`SW_Push` + diode **1N4148W SOD-123 SMD**). Convention : ROW (sortie) → switch → diode → COL, **cathode côté colonne** (scan rows-drive + réveil EXT1 cohérents).
- **R 100Ω série sur chacune des 11 lignes** (4 ROW + 7 COL), côté MCU (couche 3 du plan ESD) — placées sur cette feuille, entre le netlabel entrant et le peigne de la matrice ; les nets côté touches s'appellent `ROW0_SW..`/`COL0_SW..`.
- Grille électrique 4×7 = 28 positions, 26 peuplées (2 libres en réserve). L'affectation physique des touches (layout, mix MX/Choc) est une décision de layout — ici seule l'électricité compte.
- Empreintes hybrides MX/Choc existantes (`EKR82-footprint`) assignées au layout, pas maintenant.

- [ ] **Étape 1 (Mae)** : dessiner (astuce : dessiner 1 cellule switch+diode propre, puis répéter/coller en grille 4×7).
- [ ] **Étape 2 (vérif)** : `./scripts/check.sh --fast` vert + revue texte Claude (26 diodes, orientation, 11 résistances série, nets `_SW`).
- [ ] **Étape 3 (commit)** : `git commit -m "feat(v2): feuille matrice — 4x7, diodes SOD-123, 100R ESD série"`.

### Tâche 4 : Feuille `liens` — USB-C, lien inter-moitiés, ESD

**Fichiers :** Modifier (Mae) : `rouge-gorge/liens.kicad_sch`

**Interfaces :** consomme `USB_DP/DM`, `LINK_TX/RX`, `LINK_5V_EN`, produit `VBUS_5V`.

- **USB-C** (USB 2.0, 16 pads, ex. HRO TYPE-C-31-M-12) : CC1 et CC2 → R 5,1k vers GND chacune ; VBUS → net `VBUS_5V` ; D+/D− → **USBLC6-2SC6** (à 2 mm du connecteur au layout) → `USB_DP`/`USB_DM` ; SHIELD → GND via R 1M ∥ C 100nF.
- **Lien inter-moitiés `J_LINK`** : symbole `Connector_Generic:Conn_01x04` — brochage normatif : 1=GND, 2=LINK_RX, 3=LINK_TX, 4=LINK_5V. (Empreinte TRRS MJ-4PP-9 et/ou magnétique 4P : au layout, double empreinte possible — point ouvert №2.)
- **Poignée de main 5 V** : `VBUS_5V → U_LS AP22802AW5-7 (load switch, courant limité) → LINK_5V`, EN ← `LINK_5V_EN` + R 100k pull-down (mort par défaut). **Et le chemin retour** : `LINK_5V → D2 Schottky SS14 → VBUS_5V` (la moitié non branchée est nourrie par sa sœur : son TP4056 charge, son VBUS_DET monte — même mécanique que le câble).
- **ESD lien** : **SRV05-4** (SOT-23-6) sur les 4 lignes du J_LINK, au plus près du connecteur. R 100Ω série sur LINK_TX et LINK_RX (côté MCU).
- Le slide switch et le TP4056 étant sur `alim`, cette feuille ne produit que `VBUS_5V` — un seul PWR_FLAG (déjà posé en alim).

- [ ] **Étape 1 (Mae)** : dessiner ; sauvegarder.
- [ ] **Étape 2 (vérif)** : `./scripts/check.sh --fast` vert + revue texte Claude (sens du load switch, pull-down EN, diode retour, TVS sur les 4 lignes).
- [ ] **Étape 3 (commit)** : `git commit -m "feat(v2): feuille liens — USB-C, J_LINK poignée de main 5V, TVS"`.

### Tâche 5 : Racine, ERC zéro, clôture

**Fichiers :** Modifier (Mae) : `rouge-gorge/rouge-gorge.kicad_sch` (racine) ; Modifier (Claude) : design doc (§ statut), plan (cases cochées)

- [ ] **Étape 1 (Mae)** : câbler les 4 feuilles au niveau racine (pins hiérarchiques : `+3V3`, `GND`, `VBUS_5V`, `ROW/COL`, `USB_*`, `LINK_*`, `VBAT_SENSE`, `VBUS_DET`), annotation complète (Outils → Annoter), attribution des empreintes différée au layout SAUF celles déjà fixées (MCP1700 SOT-23, diodes SOD-123, TVS SOT-23-6/SOT-143, AO3407 SOT-23, TP4056 SOP-8, USB-C, MSK-12C02).
- [ ] **Étape 2 (vérif finale)** : `./scripts/check.sh` complet → **ERC 0 erreur / 0 warning visé** (les warnings restants se justifient un par un ou s'éliminent) ; baseline committée à son plancher.
- [ ] **Étape 3 (Claude)** : revue texte intégrale du projet (cohérence inter-feuilles des netlabels — le point faible classique des hiérarchies) + mise à jour du design doc (« schéma moitiés : FAIT »).
- [ ] **Étape 4 (commit)** : `git commit -m "feat(v2): schéma moitiés complet — ERC 0"` puis relecture d'ensemble par Mae dans KiCad avant d'attaquer le layout.

---

## Auto-revue du plan (faite)

- **Couverture du spec** : §4 alim ✓ (T1) ; §2 cœur S3 + nRF24 ✓ (T2) ; matrice/ULP ✓ (carte des pins + T3) ; §5 lien poignée de main ✓ (T4) ; §6 ESD couches 1-3 ✓ (T1/T3/T4 ; couche 0 = layout, hors plan) ; §7 zéro header ✓ (contraintes globales) ; coffre/§8 exclus explicitement (points ouverts) ; §10 tripwire ✓ (T0 + chaque tâche).
- **Placeholders** : les réfs LCSC exactes des composants sont livrées à la Tâche 1 Étape 1 (dépendance stock/dispo du jour — donnée externe, pas un TBD de conception).
- **Cohérence des noms** : nets normatifs définis une fois (interfaces de tâche) et réutilisés à l'identique ; carte des pins unique en tête.
