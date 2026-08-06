v# Schéma KiCad des moitiés Rouge-Gorge v2 — Plan d'implémentation

> **Exécution en binôme** : Mae dessine dans KiCad (GUI), Claude fournit chaque bloc (composants,
> valeurs, table de connexions), vérifie au tripwire et relit le `.kicad_sch` (format texte).
> Les étapes utilisent des cases `- [ ]`. Une tâche = un bloc = un commit.

**But** : le schéma complet des deux moitiés Rouge-Gorge v2, ERC zéro erreur, prêt pour le layout.

**Architecture** (décision Mae 2026-07-29 : **pas de PCB réversible, pas de deuxième projet — un seul projet, un seul `.kicad_pcb` contenant les deux moitiés côte à côte**, deux contours sur Edge.Cuts) : projet KiCad neuf `rouge-gorge/`, feuille chapeau `moitie.kicad_sch` contenant les 4 feuilles (alim / mcu+radio / matrice / liens), instanciée 2× à la racine (gauche/droite) — les tâches 1-4 se font sur une seule instance, la 2ᵉ instance arrive en Tâche 5. Réf. : design doc `docs/superpowers/specs/2026-07-29-rouge-gorge-refonte-design.md`.

**Stack** : KiCad 10.0.x · tripwire (`./scripts/check.sh --fast` = ERC ratchet) · libs locales existantes (`rili/pcb/*.pretty`, `mae.kicad_sym`) + libs officielles KiCad.

## Contraintes globales

- **Zéro header** — tout composant est SMD soudé ou en socket plat validé au design doc.
- **La radio WiFi/BLE du S3 ne sera jamais utilisée** (MCP1700 250 mA — décision Mae).
- **Hors périmètre de ce plan** : le coffre P4 (point ouvert №1), le firmware, le layout PCB.
- **Baseline tripwire neuve** : sur ce projet, vert = **0 erreur ERC** (pas d'héritage toléré).
- **Résidu DRC connu du choix « 2 moitiés, 1 PCB »** : les nets globaux (GND, +3V3, VSYS, +BATT, VBUS_5V) existent dans les deux moitiés sans cuivre entre elles → le DRC verra ~5 « unconnected items » incompressibles entre les deux planches. Piste vers le zéro : **exclusions DRC** posées une fois sur ces violations précises (stockées dans le `.kicad_pcb`, normalement honorées par `kicad-cli` — à vérifier au moment du layout) ; sinon le résidu est documenté et gelé dans la baseline. **Décision Mae 2026-07-29 : panneau sécable** — 1 seul gerber, les deux moitiés reliées par tabs + mouse-bites (ajoutés par script juste avant commande ; un tab peut porter le GND → résidu unconnected éliminable). Commande fab : « panel by customer, different designs : 2 ». Miroir du côté droit : script `mirror_panel.py` (positions x→2a−x, angle empreinte →−θ, angles internes absolus +δ, pads dé-netés, uuids neufs) — conservé en scratchpad, à archiver dans `scripts/` à la phase layout.
- Coordination : Mae peut garder corne-cherry ouvert (projet séparé) ; elle **sauvegarde** avant chaque revue de Claude.
- Le connecteur inter-moitiés est dessiné **générique 4 pins** (`J_LINK`) — le choix TRRS vs magnétique (point ouvert №2) se fera au layout, éventuellement en double empreinte.

## Carte des pins ESP32-S3-WROOM-1 (référence normative — MCU tranché par Mae 2026-07-29 ; remap depuis la version MINI-1 : GPIO33/34 non câblés sur WROOM-1, GPIO35-37 réservés PSRAM octale sur variantes R8/R16V → évités par prudence)

| Fonction | GPIO | Contrainte respectée |
|---|---|---|
| Lignes matrice ROW0-3 (sorties scan) | 1, 2, 4, 5 | RTC ✓ (scan ULP en sommeil) |
| Colonnes matrice COL0-6 (entrées, pull-down) | 6, 7, 8, 9, 10, 11, 12 | RTC ✓ (réveil EXT1 any-high) |
| Jauge batterie (ADC) | 13 | ADC2 — OK car WiFi jamais actif |
| ~~Détection VBUS~~ → **CS écran (net `CS_DPL`)** | 14 | VBUS_DET abandonné (2026-07-31) ; CS dédié, actif HAUT — câblé ✓ |
| UART lien TX / RX | 17 / 18 | — |
| USB D− / D+ | 19 / 20 | pins USB natifs (fixe) |
| EN du load switch 5 V (poignée de main) | 21 | — |
| nRF24 : CE / CSN | 15 / 16 | libres, hors strapping |
| SPI partagé nRF24+LCD : SCK / MOSI+SI / MISO / IRQ | 38 / **40** / 39 / 41 | GPIO matrix ; MOSI/MISO tels que dessinés par Mae ; le LCD (write-only) partage SCK et MOSI |
| TP_RDY (trackpad, gauche) | **42** | plus de partage — le CS écran a son pin dédié (14) ; CS LCD actif HAUT |
| Trackpad I2C : SDA / SCL (gauche) | **47 / 48** | ex-lien UART S3↔P4, abandonné (2026-07-30) |
| Boot / prog (J_PROG) | 0, 43, 44 | strapping — pull-up 10k sur 0 |
| Interdits | 3, 45, 46 (strapping), 35-37 (PSRAM octale), 33/34 (absents du module) | |

**Périphériques (décisions 2026-07-30)** : écran **Sharp LS011B7DH03** à droite (SCS=42 actif haut,
SCLK=38, SI=40, DISP→3V3, EXTMODE/EXTCOMIN→GND, VCOM logiciel) ; trackpad **Azoteq TPS43-201A-S**
à gauche (FPC 6-pin : RDY=42, NRST=RC pull-up+100nF, SDA=47, SCL=48) ; **le S3 est PLEIN** —
« batterie pleine » se lit via VBAT_SENSE en ADC (≥ ~4,15 V), pas de GPIO pour STDBY.
**Restructure Mae** : matrice gauche déplacée DANS la feuille s3 (câblage direct SW→100R→MCU,
nets anonymes) ; la feuille Matrix ne porte plus que la droite (`col*_d`/`row*_d`, en attente du 2ᵉ MCU).

---

### Tâche 0 : Scaffold du projet + bascule tripwire

**Fichiers :**
- Créer (Mae, GUI) : `rouge-gorge/rouge-gorge.kicad_pro`, `.kicad_sch`, `.kicad_pcb`
- Modifier (Claude) : `scripts/kicad-check.sh` (cibles SCH/PCB), `CLAUDE.md` (chemins surveillés déjà OK : `rouge-gorge/` n'y est pas → l'ajouter), `.tripwire-kicad-baseline` (reset)

**Interfaces :** produit le squelette de projet + 4 feuilles hiérarchiques vides nommées `alim`, `mcu_radio`, `matrice`, `liens` que les tâches 1-4 remplissent.

- [ ] **Étape 1 (Mae)** : KiCad → Fichier → Nouveau projet → `rouge-gorge/rouge-gorge` à la racine du repo. Dans le schéma racine, poser UNE feuille hiérarchique (Placer → Feuille) : `moitie.kicad_sch`, nommée `gauche`. Entrer dans `moitie` et y poser les 4 feuilles : `alim.kicad_sch`, `mcu_radio.kicad_sch`, `matrice.kicad_sch`, `liens.kicad_sch`. (La 2ᵉ instance `droite` de `moitie` sera posée en Tâche 5, une fois l'instance unique verte.) Recopier les tables de libs : Préférences → Gérer les librairies de symboles/empreintes → ajouter (projet) `mae.kicad_sym`, `rouge_gorge.kicad_sym` et les `.pretty` de `rili/pcb/` utiles (`key`, `MaeLid`, `EKR82-footprint`). Sauvegarder.
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

- [x] **Étape 1 (Claude)** : liste de courses livrée (2026-07-29, réfs LCSC vérifiées en ligne, symboles vérifiés dans les libs KiCad 10 installées) — voir annexe « Liste de courses feuille alim » en fin de plan. Symbole `FS8205` créé dans `rili/pcb/rouge_gorge.kicad_sym` (absent des libs officielles ; pinout SOT23-6 vérifié sur datasheet Fortune).
- [ ] **Étape 2 (Mae)** : dessiner la feuille selon la chaîne ci-dessus, netlabels exactement `+BATT`, `VSYS`, `+3V3`, `VBUS_5V`, `VBAT_SENSE`. PWR_FLAG sur `+BATT` et `VBUS_5V`. Sauvegarder.
- [ ] **Étape 3 (vérif)** : `./scripts/check.sh --fast` → vert (0 erreur ; le ratchet reste 0). Claude relit `alim.kicad_sch` (texte) et recoupe chaque net contre la chaîne ci-dessus — écarts signalés, corrigés, re-check.
- [ ] **Étape 4 (commit)** : `git add rouge-gorge/ .tripwire-kicad-baseline && git commit -m "feat(v2): feuille alim — 16340, protection, charge 500mA, load-sharing, MCP1700"`

### Tâche 2 : Feuille `mcu_radio` — S3-MINI-1 + nRF24

**Fichiers :** Modifier (Mae) : `rouge-gorge/mcu_radio.kicad_sch`

**Interfaces :** consomme `+3V3`, `GND`, `VBAT_SENSE`, `VBUS_5V` (via diviseur → `VBUS_DET`). Produit : `ROW0..ROW3`, `COL0..COL6` (vers `matrice`), `USB_DP`/`USB_DM`, `LINK_TX`/`LINK_RX`, `LINK_5V_EN` (vers `liens`).

Contenu (voir carte des pins en tête de plan — elle est normative) :

- `RF_Module:ESP32-S3-MINI-1` (déjà dans ton brouillon s3.kicad_sch — le reprendre). Découplage : C 10µF + 2× C 100nF sur 3V3.
- EN : R 10k vers +3V3 + C 1µF vers GND. GPIO0 : R 10k vers +3V3.
- **Connecteur de prog `J_PROG` 6 pins par moitié** (décision Mae 2026-07-29, remplace les pads TP_BOOT/TP_TX0/TP_RX0) — brochage ESP-Prog : 1=EN, 2=3V3, 3=TX0 (GPIO43), 4=GND, 5=RX0 (GPIO44), 6=IO0 (GPIO0). Symbole `Conn_02x03_Odd_Even` ou `Conn_01x06` ; « zéro header » réglé au layout (bas profil / pads / Tag-Connect).
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

- [ ] **Étape 1 (Mae)** : câbler les 4 feuilles à l'intérieur de `moitie` (pins hiérarchiques : `+3V3`, `GND`, `VBUS_5V`, `ROW/COL`, `USB_*`, `LINK_*`, `VBAT_SENSE`, `VBUS_DET`), puis poser la **2ᵉ instance** de `moitie.kicad_sch` à la racine (Placer → Feuille, même fichier, nom `droite`), annotation complète des deux instances (Outils → Annoter — les refs se dédoublent automatiquement), attribution des empreintes différée au layout SAUF celles déjà fixées (MCP1700 SOT-23, diodes SOD-123, TVS SOT-23-6/SOT-143, AO3407 SOT-23, TP4056 SOP-8, USB-C, MSK-12C02).
- [ ] **Étape 2 (vérif finale)** : `./scripts/check.sh` complet → **ERC 0 erreur / 0 warning visé** (les warnings restants se justifient un par un ou s'éliminent) ; baseline committée à son plancher.
- [ ] **Étape 3 (Claude)** : revue texte intégrale du projet (cohérence inter-feuilles des netlabels — le point faible classique des hiérarchies) + mise à jour du design doc (« schéma moitiés : FAIT »).
- [ ] **Étape 4 (commit)** : `git commit -m "feat(v2): schéma moitiés complet — ERC 0"` puis relecture d'ensemble par Mae dans KiCad avant d'attaquer le layout.

---

## Annexe — Liste de courses feuille `alim` (livrée 2026-07-29, réfs LCSC vérifiées)

| # | Composant | Boîtier | Symbole KiCad | LCSC | Note |
|---|---|---|---|---|---|
| 1 | DW01A (protection cellule) | SOT-23-6 | `Battery_Management:DW01A` ✓ officiel | C351410 (PUOLOP) | alt. C2927799 (YONGYUTAI) |
| 2 | FS8205 (dual N-FET, paire du DW01A) | **SOT23-6** | `rouge_gorge:FS8205` (créé, pinout 1=S1 2=D12 3=S2 4=G2 5=D12 6=G1) | C32254 (Fortune) | alt. TSSOP-8 FS8205A C16052 ; VGS(th) 0,45-1,2 V OK pour DW01A |
| 3 | TP4056 (chargeur, Rprog 2,4 kΩ → ~500 mA) | ESOP-8 | `Battery_Management:TP4056-42-ESOP8` ✓ officiel | C16581 (TOPPOWER) | pad thermique dessous |
| 4 | AO3407 (P-FET load sharing) | SOT-23 | `Transistor_FET:AO3401A` (même pinout G/S/D, mettre Value=AO3407) | C351408 (PUOLOP) | alt. C727158 (TWGMC, RDS 87 mΩ) |
| 5 | SS14 (Schottky VBUS→VSYS) | SMA | `Diode:SS14` ✓ officiel | C2480 (MDD) | générique multi-fab |
| 6 | MCP1700-3302E/TT (LDO 3,3 V 250 mA, 1,6 µA) | SOT-23 | `Regulator_Linear:MCP1700x-330xxTT` ✓ officiel | C39051 (Microchip) | |
| 7 | MSK-12C02 (slide switch coupure système) | SMD | `Switch:SW_SPDT` générique | C431540 (SHOU HAN) | empreinte au layout |
| 8 | R/C du bloc | 0603 sugg. | `Device:R`, `Device:C` | basic parts | 100Ω, 1k, 2,4k, 10k, 2×1M ; 100nF ×3, 1µF ×2, 10µF ×2 |
| 9 | Cellule 16340 (contacts/holder) | — | `Device:Battery_Cell` | — | contact ressort vs holder = décision layout (design doc) |

Composants `liens` déjà repérés au passage (Tâche 4) : `Power_Protection:USBLC6-2SC6` ✓, `Power_Protection:SRV05-4` ✓, `Connector:USB_C_Receptacle_USB2.0_16P` ✓, `Diode:1N4148W` ✓ (matrice), load switch : `SiP32431DR3` ✓ officiel (l'AP22802 n'a pas de symbole officiel — SiP32431 était l'alternative validée au design doc).

## Annexe — Liste de courses BOM complète v2 (2026-08-01, réfs LCSC vérifiées en ligne)

Complète l'annexe alim ci-dessus (DW01A, FS8205, TP4056, AO3407, SS14, MCP1700, MSK-12C02 déjà référencés). Quantités pour LE PANNEAU (2 moitiés) :

| Qté | Composant | Boîtier | LCSC | Note |
|---|---|---|---|---|
| 2 | ESP32-S3-WROOM-1-**N8R2** | module CMS | **C2913204** | ⚠️ l'empreinte au schéma est `WROOM-1U` (antenne externe u.FL) — si c'est voulu, prendre le 1U-N8R2 **C3013944** ; sinon corriger l'empreinte vers WROOM-1 (antenne PCB, reco clavier) et prendre C2913204 |
| 1 | CH334R (hub USB 2.0 4 ports) | QSOP-16 | **C4154405** | ~0,30 $ |
| 2 | USBLC6-2SC6 (ESD USB) | SOT-23-6 | **C7519** (ST) | éviter les clones à 2 lettres près |
| 2 | SRV05-4 (ESD TRRS) | SOT-23-6 | **C13612** (Semtech .TCT) | alt. budget : Leiditech C384887, Bourns C118757 |
| 1 | AMS1117-3.3 (LDO coffre P4) | SOT-223 | **C6186** (AMS) | |
| 2 | SiP32431DR3-T1GE3 (load switch 5 V lien) | SC-70-6 | **C141606** (Vishay) | |
| 2 | USB-C TYPE-C-31-M-12 (16P, USB 2.0) | CMS + 4 pattes | **C165948** (HRO) | = exactement l'empreinte `USB_C_Receptacle_HRO_TYPE-C-31-M-12` du schéma |
| 1 | microSD Würth 693072010801 (hinge) | CMS | — PAS sur LCSC | Mouser/Farnell/DigiKey ; alt. LCSC push-push TF-01A **C91145** (HRO) mais il faudra CHANGER l'empreinte avant routage |
| 2 | nRF24L01+ (module breakout 2×4) | module | — AliExpress | comme v1 ; empreinte `MaeLid:NRF24L01` |
| 1 | Module ESP32-P4 `JC-ESP32P4-M3` | module | — AliExpress/Taobao | empreinte V0.2 déjà sur le PCB |
| 2 | Écran Sharp LS011B7DH03 | FPC | — Mouser/DigiKey | 1 monté à droite (populate-per-half) |
| 1 | Trackpad Azoteq TPS43-201A-S | FPC 6 pin ZIF | — Mouser/DigiKey | gauche seulement + connecteur ZIF 6P 0,5 mm à référencer au layout |
| 52+4 | Switchs Choc/MX + diodes matrice + jack TRRS MJ-4PP-9 | — | — AliExpress | filière v1 (README) ; diodes matrice hors BOM kicad (symboles legacy) |
| ~60 | R/C/LED 0603-0805-1206 (100Ω, 100k, 10k, 1k, 2k4, 4,7k, 5k1, 1M ; 100nF, 1µF, 10µF, 22µF ; LED 0805) | 0603/0805/1206 | basic parts JLC | prendre les « Basic » du catalogue pour éviter les frais extended si assemblage JLC |

## Auto-revue du plan (faite)

- **Couverture du spec** : §4 alim ✓ (T1) ; §2 cœur S3 + nRF24 ✓ (T2) ; matrice/ULP ✓ (carte des pins + T3) ; §5 lien poignée de main ✓ (T4) ; §6 ESD couches 1-3 ✓ (T1/T3/T4 ; couche 0 = layout, hors plan) ; §7 zéro header ✓ (contraintes globales) ; coffre/§8 exclus explicitement (points ouverts) ; §10 tripwire ✓ (T0 + chaque tâche).
- **Placeholders** : les réfs LCSC exactes des composants sont livrées à la Tâche 1 Étape 1 (dépendance stock/dispo du jour — donnée externe, pas un TBD de conception).
- **Cohérence des noms** : nets normatifs définis une fois (interfaces de tâche) et réutilisés à l'identique ; carte des pins unique en tête.

## Annexe — Brochage matrice RÉEL et conventions firmware (revue 2026-08-06, source netlist)

La carte des pins « normative » ci-dessus reste valable pour tout SAUF la matrice : Mae a
permuté rows/cols au routage (liberté actée — tout reste en GPIO1-12, domaine RTC, réveil
EXT1 possible). **Le firmware doit porter DEUX tables** :

| ligne | GAUCHE (U6) | DROITE (U5) |
|---|---|---|
| row0 | GPIO1 | GPIO2 |
| row1 | GPIO2 | GPIO12 |
| row2 | GPIO8 | GPIO4 |
| row3 | GPIO6 | GPIO5 |
| col0 | GPIO4 | GPIO6 |
| col1 | GPIO5 | GPIO7 |
| col2 | GPIO7 | GPIO8 |
| col3 | GPIO9 | GPIO9 |
| col4 | GPIO10 | GPIO11 |
| col5 | GPIO11 | GPIO10 |
| col6 | GPIO12 | GPIO1 |

Conventions actées :
- **Sens de scan** : chaîne réelle COL→SW→anode-diode-cathode→ROW. Le firmware PILOTE les
  colonnes et LIT les rows ; le réveil sommeil profond (EXT1) s'arme sur les ROWS.
- **TRRS** : câble droit, R1↔R1/R2↔R2 → TX arrive sur TX. Le croisement est fait en
  FIRMWARE (matrice GPIO : une moitié échange U1TXD/U1RXD). Ne jamais activer les deux TX
  push-pull sans ce swap (contention limitée par les 2×100Ω, mais contention quand même).
- **Tip TRRS** protégé par le canal 3 du SRV05 (net TIP_5V) depuis la revue.
- **microSD du coffre** : cartes insérées/retirées HORS TENSION uniquement (décision Mae
  2026-08-06 — pas de TVS sur les lignes SD). Card-detect absent (connecteur Würth) :
  détection logicielle par polling CMD.
- **LDO moitiés = HT7833** (SOT-89 : 1=GND 2=VIN 3=VOUT) depuis la revue ; CH334R en mode
  sans quartz avec R48/R49 SUPPRIMÉS par Mae (RESET# a un pull-up interne 25k).
- Jauge batterie sur ADC2_CH2 : ADC2 inutilisable si le WiFi est actif (nRF24-only : OK).
