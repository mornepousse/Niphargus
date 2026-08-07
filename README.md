# Niphargus

*The cave shrimp: blind, discreet, indestructible.*
*La crevette des cavernes : aveugle, discrète, indestructible.*

![Niphargus PCB v2](images/nipharPCB.png)

---

## English

Niphargus is a thin, unkillable wireless split keyboard.

- **Two self-contained halves** — one ESP32-S3-WROOM-1 + nRF24L01+ and a 16340
  cell each, matrix scanning in deep sleep (RTC domain), KaSe dongle on the host side.
- **Wired fallback** — direct USB-C plus a TRRS jack between halves: *plugging it
  back in must be enough*. A 5 V handshake on the link makes hot-plug spark-free.
- **ESD hardening throughout** — TVS diodes on USB and TRRS, 100 Ω in series on
  every matrix line, careful ground planes. The static discharge you bring back
  to the keyboard will no longer crash it.
- **Sharp Memory LCD** (right half) for layer and battery status: holds its image
  at a few µA and never flickers. **Azoteq TPS43 trackpad** (left half), over I²C.
- **The survival kit** — an ESP32-P4 vault behind a CH334R USB hub: multi-ISO boot
  key, PGP token, storage. It only powers up when the keyboard is plugged in.

A complete redesign of the **Rouge-Gorge** (v1, 2022, below). This repository
carries the full history: Rouge-Gorge → rili → Niphargus.

**Status (2026-08)** — v2 schematic complete and reviewed, board routed, ERC and
DRC clean. Case in progress (see below). Firmware to follow.

## Français

Niphargus est un clavier split sans fil, fin et increvable.

- **Deux moitiés autonomes** — ESP32-S3-WROOM-1 + nRF24L01+ et une batterie 16340
  chacune, scan de la matrice en sommeil profond (domaine RTC), dongle KaSe côté hôte.
- **Repli filaire** — USB-C direct et jack TRRS entre les moitiés : *rebrancher
  doit suffire*. Une poignée de main 5 V sur le lien évite les étincelles au branchement à chaud.
- **Robustesse ESD partout** — TVS sur USB et TRRS, 100 Ω série sur chaque ligne
  de matrice, plans de masse soignés. La décharge que vous ramenez au clavier ne
  le plantera plus.
- **Écran Sharp Memory LCD** (moitié droite) pour le calque et l'état des batteries :
  tient l'image à quelques µA sans jamais clignoter. **Trackpad Azoteq TPS43**
  (moitié gauche), en I²C.
- **La trousse de secours** — un coffre ESP32-P4 derrière un hub USB CH334R : clé
  bootable multi-ISO, token PGP, stockage. Il ne s'allume qu'en filaire.

Refonte complète du **Rouge-Gorge** (v1, 2022, ci-dessous). Le dépôt porte tout
l'historique : Rouge-Gorge → rili → Niphargus.

**État (2026-08)** — schéma v2 terminé et relu, carte routée, ERC et DRC au vert.
Boîtier en cours (ci-dessous). Firmware à suivre.

---

## Repository layout · Organisation du dépôt

| Path | Contents |
|---|---|
| `hardware/pcb/` | KiCad project — `niphar.kicad_pro` (schematic, board, footprints) |
| `hardware/order-*.csv` | Part orders: TME, LCSC, AliExpress |
| `hardware/kit-jlcpcb/` | Gerbers, BOM and CPL for JLCPCB |
| `case/` | Case generator and CAD output |
| `scripts/` | Anti-regression checks |
| `docs/` | Design specs and plans |

### Case · Boîtier

Three parts: a **CNC-machined 8.5 mm aluminium frame**, sandwiched between two
**2 mm polycarbonate plates**, 12.5 mm overall. The 16340 cell sits *beside* the
board, in a pocket milled into the frame itself.

Trois pièces : un **cadre aluminium usiné de 8,5 mm** pris entre deux **plaques
polycarbonate de 2 mm**, 12,5 mm hors tout. La 16340 se loge *à côté* de la carte,
dans une poche fraisée à même le cadre.

The frame outline is **not computed — it is drawn**. Edit `case/case_outline.svg`
(KiCad coordinates, 1 unit = 1 mm), then run:

Le contour du cadre n'est **pas calculé, il est dessiné**. Éditez
`case/case_outline.svg` (repère KiCad, 1 unité = 1 mm), puis lancez :

```sh
freecad --console case/gen_case.py
```

This regenerates the `.FCStd`, the STEP, the STL files and `case_plan.svg`.

### Anti-regression · Anti-régression

```sh
./scripts/check.sh --fast   # schematic ERC against the committed baseline
./scripts/check.sh          # + full board DRC
./scripts/install-hooks.sh  # once per clone: pre-push runs the full check
```

Green means *never more ERC/DRC errors or warnings than the committed baseline*
(`.tripwire-kicad-baseline`). CI is pinned to KiCad 10.0.4 with its own reference.

Vert signifie *jamais plus d'erreurs ni de warnings ERC/DRC que la référence
committée*. La CI est épinglée sur KiCad 10.0.4 avec sa propre référence.

---

## Rouge-Gorge (v1, 2022)

<img src="images/robinlogo.png" alt="Rouge-Gorge logo" width="300" height="300">

**en** — A derivative of the Jorne and the Kyria rev2, two keyboards well loved in
the mechanical keyboard community. I took what suited me best from each. The PCB
was never tested and the QMK firmware never written — Niphargus supersedes it.

**fr** — Un dérivé du Jorne et du Kyria rev2, deux claviers très appréciés dans la
communauté des claviers mécaniques. J'ai pris de chacun ce qui me convenait le
mieux. Le PCB n'a jamais été testé ni le firmware QMK écrit — Niphargus lui succède.

![](images/TestBuild.jpg)

![](images/PCB.PNG)

Creation date: 02/12/2022

Ordering at [JLCPCB](https://cart.jlcpcb.com/quote?orderType=1&stencilLayer=2&stencilWidth=100&stencilLength=100&stencilCounts=5):
x 5 = 10.60 $ — u = 2.12 $ x 2 = 4.24 $

| Id | Reference | Package | Qty | Designation | Supplier | Price |
|----|-----------|---------|-----|-------------|----------|-------|
| 1  | D1,D2,D3…| Diode_TH_SOD123EKR | 26 | D | [aliexpress](https://fr.aliexpress.com/item/1005003631407506.html), [TME](https://www.tme.eu/fr/details/1n5711w-7-f/diodes-schottky-smd/diodes-incorporated/) | 0.0546 € × 26 = 1.42 € |
| 2  | L1,L2,L3…| SK6812MINI_rev | 26 | SK6812MINI | [aliexpress](https://fr.aliexpress.com/item/1005003021596311.html) | 0.0704 € × 26 = 1.83 € |
| 3  | SW1,SW2,SW3…| MX_Socket_18mm | 26 | SW_PUSH | [aliexpress](https://fr.aliexpress.com/item/1005003873653184.html) | 0.1285 € × 26 = 3.34 € |
| 5  | U1 | ProMicro_v2 | 1 | ProMicro | [aliexpress](https://fr.aliexpress.com/item/1005003622414316.html) | 6.155 € |
| 8  | JP1 | JPC2 | 1 | 1x4 Pin | [aliexpress](https://fr.aliexpress.com/item/4000979967513.html) | 0.182 € |
| 9  | J2 | OLED | 1 | OLED | [aliexpress](https://fr.aliexpress.com/item/33024849277.html) | 3.10 € |
| 10 | J1 | MJ-4PP-9 | 1 | MJ-4PP-9 | [aliexpress](https://fr.aliexpress.com/item/33029465106.html) | 0.246 € |
| 11 | RSW1 | ResetSW | 1 | SW_PUSH | [aliexpress](https://fr.aliexpress.com/item/1005004067514307.html) | 0.137 € |
| 12 | L22,L23,L24… | SK6812MINI_underglow_rev | 7 | SK6812MINI | [aliexpress](https://fr.aliexpress.com/item/1005003021596311.html) | 0.0704 € × 7 = 0.49 € |

Total: 16.45 € × 2 = 32.90 €

Other parts · Autres pièces:

| Name | Links |
|------|-------|
| TRRS jack cable | [ali1](https://fr.aliexpress.com/item/1005003415667083.html) · [ali2](https://fr.aliexpress.com/item/33006667627.html) · [ali3](https://fr.aliexpress.com/item/1005002888851426.html) |
| Switches | [ali1](https://fr.aliexpress.com/item/1005003436102892.html) · [Kailh Cream](https://fr.aliexpress.com/item/1005003694230110.html) |
| Keycaps | [AF SA](https://fr.aliexpress.com/item/1005003935785708.html) · [cerise](https://fr.aliexpress.com/item/1005003932690197.html) |

Simulated final price (case not included) · Prix final simulé (boîtier non compris) :

| PCB | SMDs | Switches | Keycaps | Total |
|-----|------|----------|---------|-------|
| 3.97 € | 32.90 € | 18.06 € | 48.98 € | 103.91 € |

[BOM](docs/BOM.md) · [Firmware (v1, QMK)](https://github.com/mornepousse/Rouge-Gorge_QMX_Part)
