# Rouge-Gorge v2 — Design de la refonte

**Date** : 2026-07-29 · **Statut** : BROUILLON — sections en attente de validation par Mae, 3 points ouverts · **Auteure des décisions** : Mae

---

## 1. Le produit

Rouge-Gorge v2 est un clavier split **petit, bas et durable**, full wireless, qui est aussi une
**trousse de secours d'informaticien**. C'est UN produit avec DES modes — pas des variantes :

| Mode | Déclencheur | Comportement |
|---|---|---|
| **Sans-fil** | pas de câble (VBUS absent) | Clavier pur et sobre : frappes → nRF24 → dongle KaSe. USB, SD, C6 éteints. Veille en µA. |
| **Filaire** | câble USB branché (VBUS présent) | Multi-outil : clavier USB HID direct (boot protocol, utilisable au BIOS) + coffre (stockage bootable, token PGP) + **recharge**. Alimentation par le câble. |

La bascule est automatique (détection VBUS), sans bouton ni réglage : « **rebrancher doit suffire** ».
Le système complet = **deux moitiés + le dongle**. Pas de troisième objet.

Ce qui disparaît de l'ancien design : le ProMicro, les LEDs SK6812 (per-key et underglow), l'OLED,
les headers.

## 2. Architecture système

```
┌──────────── moitié G ────────────┐        ┌──────────── moitié D ────────────┐
│ ESP32-S3 (cœur clavier)          │        │ ESP32-S3 (cœur clavier)          │
│  · matrice (scan ULP en sommeil) │        │  · matrice (scan ULP en sommeil) │
│  · nRF24L01+ (SPI)      16340 ▭  │        │  · nRF24L01+ (SPI)      16340 ▭  │
│  · USB-C (HID + charge)          │◄─lien─►│  · USB-C (HID + charge)          │
└───────────────┬──────────────────┘ filaire└──────────────┬───────────────────┘
                │ nRF24 ESB (protocole KaSe)                │
                ▼                                           ▼
        ┌─────────────────── dongle KaSe (ESP32-S3, 2 radios) ────────────────┐
        │ USB HID vers l'hôte · hub CH334R                                    │
        │ [OUVERT] coffre P4 greffé derrière le hub ?                         │
        └─────────────────────────────────────────────────────────────────────┘
```

- **Cœur de chaque moitié : ESP32-S3** (module WROOM soudé à plat). Rôle HID-seul + radio — le rôle
  exact du « smart keyboard » KaSe déjà éprouvé en production (routage `usb_presence`, relais nRF24,
  pairing). Sleep archi-connu (~7 µA deep / ~240 µA light), ULP-RISC-V pour scanner la matrice en
  sommeil sans perdre la première frappe.
- **Coffre : module JC-ESP32P4-M3** (stock Mae) — USB 2.0 **haute vitesse** + digital signature
  peripheral + key management unit. Il porte le stockage et le token PGP.
- **[OUVERT №1 — la maison du coffre]** : (D) greffé derrière le CH334R du dongle (révision du
  dongle ; moitiés pures et plates ; P4 alimenté par l'hôte → conso hors équation ; « une prise =
  clavier + ISO + identité » au BIOS) **ou** (C) en mezzanine dans le volume du tube 16340 d'une
  moitié (autonome, mais surface/volume dans l'objet le plus contraint). Donnée qui tranche :
  port libre/récupérable sur le CH334R du dongle actuel, et dongle révisable ou non.
- Leçon fondatrice (échec vécu sur le dongle S3 : composite HID+PGP → clavier qui lague) :
  **l'important et l'accessoire ne partagent jamais un même device USB**. D'où le hub (CH334R,
  USB2 HS, facile à souder — éprouvé par Mae) et les siliciums séparés.

## 3. Modes & stabilité — « le clavier est là coûte que coûte »

Hiérarchie de disponibilité à quatre étages :

| Étage | Mécanisme | Garantie |
|---|---|---|
| 0 | Matrice scannée par l'ULP du S3 | une frappe est toujours captée |
| 1 | **Deux chemins vers l'hôte sur siliciums séparés** : USB direct / radio→dongle | la panne d'un chemin n'emporte pas l'autre |
| 2 | Features sacrifiables ; boot **clavier-d'abord**, features après | un crash de feature = redémarrage de la feature, pas du clavier |
| 3 | Watchdog matériel + brown-out | pire cas absolu : clignement < 1 s, auto-réparé |

L'isolation absolue sur un même chip n'existe pas ; la garantie du produit est : **aucune panne de
feature ne prive le PC des frappes plus d'une seconde**. (En mode filaire, la radio peut rester en
veille chaude comme chemin de secours — le câble paie le courant.)

## 4. Alimentation

**Cellule : 16340 (~700 mAh), en tube le long d'un bord du PCB** — le corps du clavier reste bas,
la bosse est un cylindre assumé en bordure (arrière = tilt naturel ; bord exact à dessiner).
Cellules souvent non protégées → protection sur PCB.

Chaîne : `16340 → DW01A+FS8205 (protection) → TP4056 SOP-8 (~500 mA) + load-sharing P-FET
→ régulateur 3,3 V → système`

- **Load-sharing obligatoire** : brancher = utiliser ET charger (le mode filaire l'exige).
- **Régulateur : MCP1700-3302 (SOT-23)** [VALIDÉ Mae] — 1,6 µA de repos (l'auto-décharge de la
  cellule fuit ~20× plus), 250 mA, soudable au fer, banal et remplaçable. Conséquence assumée :
  la radio WiFi/BLE du S3 ne sera jamais utilisée (pics 350-500 mA hors budget) — le lien est le
  nRF24, les mises à jour passent par USB. Coût vs buck-boost : ~3-4 jours d'autonomie par cycle.
- Jauge : diviseur haute impédance → ADC → champ `batt_dV` du heartbeat KaSe (déjà prévu au protocole).
- **Interrupteur : slide mécanique (type MSK-12C02), coupure côté système** [VALIDÉ Mae] — la
  charge reste possible clavier éteint (~3 µA résiduels), état visible, zéro firmware ; encastré
  dans le chant pour survivre au sac. Raison d'être : le transport (touches martelées = réveils +
  retries radio), pas la veille.
- Budget : ~50-80 mAh/jour de bureau → **1 à 3 semaines** d'autonomie.

## 5. Lien inter-moitiés (mode filaire uniquement)

En sans-fil, les moitiés ne se parlent pas (chacune → dongle). Le lien ne sert qu'au fallback
filaire : la moitié branchée reçoit les frappes de l'autre. **4 lignes : GND, UART croisé (TX/RX),
5 V commuté.**

**Décision : 5 V « en poignée de main »** — le contact d'alim est mort par défaut ; après
reconnaissance UART (« t'es bien ma moitié ? »), la moitié nourrie au câble ferme un **load switch
intégré** (classe AP22802/SiP32431 : limitation de courant + soft-start) et envoie le 5 V, qui
**recharge la moitié d'en face**. Un court-circuit de branchement à chaud est physiquement
impossible — c'est la réponse définitive au tueur historique de splits.

**[OUVERT №2 — le connecteur]** : jack TRRS (banal, câble remplaçable partout, mais raclage à
l'insertion et vulnérable à l'arrachage) **vs** magnétique pogo (hot-plug sûr mécaniquement,
se détache au lieu de casser, ~3 mm de haut, mais câble propriétaire ; candidat AliExpress trouvé
par Mae — specs à relever : ≥ 4 contacts, ≥ 0,5-1 A, forme embase/câble, détrompage).
Option protos : **double empreinte**, l'usage tranche.

## 6. ESD — l'exigence historique

Le scénario à tuer : l'utilisateur revient chargé de quelques kV, touche le clavier, le clavier
plante jusqu'au débranchage. Défense en couches, de l'extérieur vers l'intérieur :

| Couche | Mesure | Note |
|---|---|---|
| 0 · paratonnerre | plans de masse pleins cousus de vias ; vis sur pads GND ; plaque (alu de préférence) reliée à GND | le châssis avale la décharge avant les pistes |
| 1 · douaniers | TVS à **2 mm de chaque connecteur** : USBLC6-2 (USB-C), array 4 lignes type SRV05-4 (lien inter-moitiés), array sur SD si slot exposé | ~1 €, trois boîtiers |
| 2 · organes vitaux | CHIP_PU / lignes boot : RC + pistes courtes (+ TVS si proches d'un connecteur) | la ligne qui fait « planté sans reset » |
| 3 · matrice | ~100 Ω série sur les 11 lignes de matrice | les clamps internes digèrent le résidu |
| 4 · curatif | la hiérarchie de stabilité (§3) | une décharge exotique = clignement, pas une mort |

Surcoût total ≈ 2 €, zéro épaisseur. L'ancien design comptait 199 violations de cuivre en bord de
PCB (amorçages potentiels) — déjà en cours d'éradication dans le chantier KiCad, mesurée par la
baseline tripwire.

## 7. Mécanique

La leçon des claviers précédents : **le PCB trop haut casse les boîtiers** — coupable : le ProMicro
sur headers (12-14 mm sous PCB). Règles de la v2 :

- **Zéro header.** Tout SMD soudé à plat ; modules en découpe de PCB si besoin ; USB-C mid-mount ;
  le jack/connecteur inter-moitiés peut vivre côté touches sous la plaque (5 mm d'air en MX).
- **Dégagement sous PCB ≈ 3,5 mm** (plancher naturel = sockets hotswap 1,9 mm ; modules 3,2-3,4 mm).
- **Construction sandwich** : plaque + entretoises + fond, vis en compression pure — plus de coque
  imprimée qui fend. Plaque alu = collecteur ESD en bonus.
- Switches : **mix MX/Choc par position** (footprints hybrides existants) — en sachant que la
  hauteur du case suit le plus haut des deux.
- Le tube 16340 en bordure est le seul relief ; il peut porter le tilt.

## 8. USB filaire — la trousse de secours

Une prise branchée au BIOS d'une machine quelconque donne :

- **Le clavier** : HID *boot protocol* (dialecte BIOS) depuis le S3 de la moitié branchée — ou
  depuis le dongle.
- **Le médium d'installation** : le coffre P4 expose la SD en MSC (SDIO 4 bits, ~20-40 Mo/s réels
  — classe « bonne clé USB 2 », largement suffisant pour booter/installer). **Multi-ISO par Ventoy
  sur la SD** : le firmware reste un MSC bête, la collection d'ISO se gère par glisser-déposer.
  Volume « config » possible en plus sur la flash 16 Mo du module (keymap éditable en fichier).
- **L'identité** : token PGP sur le silicium crypto du P4 (DS peripheral + KMU : clé privée jamais
  lisible par le firmware ; secure boot + flash encryption). Confirmation de présence par
  appui-touche — le clavier a déjà les boutons.
- **Mode lecture seule** (switch physique ou bascule) : la clé de secours devient inviolable sur
  machine douteuse.
- Débit et latence cohabitent sans se gêner : le HID (8 ko/s, endpoints interrupt réservés par le
  protocole USB) est intouchable par les transferts bulk ; le plafond réel est la SD, pas le hub.
- La SD est **coupée électriquement en mode sans-fil** (transistor commandé par VBUS) : zéro fuite
  sur la batterie.

## 9. Radio

- nRF24L01+ du stock, posés à plat (découpe PCB), **protocole KaSe intact** : ESB 1 Mbps, CRC 16,
  adresses 5 octets, DPL, ARC 15/ARD 500 µs ; trames PKT_KEY/PKT_HEARTBEAT (bitmap 5×7 — couvre la
  matrice, batt_dV, link_q).
- **Pairing runtime KaSe** (canal 40, set_id dérivé du MAC du dongle, canaux 80-119) : l'isolation
  entre Rouge-Gorge et les claviers KaSe voisins est déjà résolue par construction.
- Rouge-Gorge occupe **les 2 slots d'un dongle** → dongle dédié à ce clavier.
- Plus tard, optionnel : canal ESP-NOW « info » via le C6 du module P4 (antenne IPEX déjà sur le
  module) — coût hardware nul aujourd'hui.

## 10. Chantier & validation

- **Tripwire** : la baseline ERC/DRC (`.tripwire-kicad-baseline`) mesure la fonte des violations
  pendant la refonte — objectif **zéro** à la fin. Arbre rouge en cours de chirurgie = normal ;
  push WIP : `--no-verify`.
- **Si le coffre finit en moitié** (option C) : manip « composite sous charge » sur carte porteuse
  P4 obligatoire avant routage (leçon S3 : on ne croit plus le papier, on mesure). Si coffre au
  dongle (option D) : cette manip disparaît, chaque micro n'a qu'un rôle.
- **Ordre des protos** : PCB des moitiés d'abord (le cœur ne dépend d'aucun point ouvert) ; la
  maison du coffre se décide en parallèle.
- Après validation de ce design : plan d'implémentation détaillé (schéma → layout → case), puis le
  firmware (hors périmètre de ce document).

## Points ouverts (récapitulatif)

1. **Maison du coffre P4** : dongle révisé (D) vs mezzanine dans la bosse (C) — donnée décisive :
   port libre sur le CH334R du dongle, dongle révisable ?
2. **Connecteur inter-moitiés** : TRRS vs magnétique pogo (specs du candidat AliExpress à relever) ;
   option double empreinte sur protos.
3. **Micro-choix de schéma restants** : bord exact du tube 16340 et type de contacts cellule,
   layout final des touches. (Régulateur et interrupteur : tranchés — voir §4.)
