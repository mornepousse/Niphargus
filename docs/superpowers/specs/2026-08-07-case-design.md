# Boîtier Niphargus — conception mécanique

*Brainstorm du 2026-08-07 (Mae + Claude). Toutes les cotes internes sont mesurées sur
`hardware/pcb/niphar.kicad_pcb` dans son état routé, pas estimées.*

## 1. Intention

Reprendre l'objectif d'origine — **fin et durable** — sans reproduire l'échec des v1 (coque
imprimée qui fend, PCB mal soutenu). Trois pièces, aucune imprimée, et une silhouette qui
tire parti du seul relief inévitable : la pile.

## 2. Structure retenue : trois pièces

| Pièce | Matière | Épaisseur | Fabrication |
|---|---|---|---|
| Plaque à switchs | polycarbonate transparent | **2,0 mm** | découpe |
| Cadre (logement accu compris) | **aluminium usiné** | **8,5 mm** | CNC — test JLCPCB |
| Fond | polycarbonate transparent | **2,0 mm** | découpe |

**Clavier plat à 12,5 mm hors tout.** Le logement de l'accu est usiné *dans* le bloc du
cadre, il n'est plus une pièce rapportée ; la trappe a disparu — l'accu dépasse par une
fenêtre de la plaque haute. Choix Mae du 2026-08-07 : plaque à 2 mm (et non 1,5) — les
clips MX ne se verrouillent donc pas, les switchs sont tenus par les sockets hotswap.

**Assemblage** : 6 vis M3 traversantes (Ø3,2) plaque → cadre → fond, positionnées par Mae.
Attention, les 4 vis de coin n'ont que **1,4 mm de matière** autour du perçage : à élargir
localement avant usinage (les 2 autres sont à +1,9 et +2,4 mm).

## 3. Empilage interne (cotes mesurées sur la carte routée)

```
        ┌───────────────────────┐  plaque PC 2,0        z 8,5 → 10,5
        │   3,4 mm  (norme MX)  │  ← module P4 (3,2) y tient à 0,2 près
   ─────┼───────────────────────┼─────  PCB 1,6         z 3,5 → 5,1
cadre   │   3,5 mm              │  ← module S3 3,1 · nRF24 · interrupteur · microSD
  8,5   └───────────────────────┘  fond PC 2,0          z -2 → 0
```

Jeu autour du PCB : **0,5 mm** (tolérance fraisage PCB ±0,2 + usinage ±0,1). Le PCB est
positionné par les 4 vis M3, pas par le cadre.

**Jack TRRS** : sort **par le dessus** (côté touches), décision Mae du 2026-08-07 —
ouverture de z=5,1 à 8,5 dans le chant, plus un dégagement de 7,5 mm dans la plaque haute.
Le fichier PCB place pourtant `J6` en `B.Cu` : si le jack est bien monté sur le dessus,
c'est **le footprint qui est sur la mauvaise face**, à corriger avant de commander.
Réserve de cote : au-dessus du PCB il n'y a que 3,4 + 2 = 5,4 mm, contre ~6,3 mm de jack
au catalogue — à mesurer au pied à coulisse.

## 4. Accu : À CÔTÉ de la carte, pas dessous

La 16340 (Ø16,5 × 34,5) est logée **hors du contour du PCB**, le long du bord inférieur
gauche (segment 27,4·90 → 81,4·80,3, pente −10°), sous les touches SW5/SW14/SW21 au sens
du plan. Centre à ~53,6 · 96,5, axe à 11 mm du bord. Le cadre s'élargit localement au lieu de s'épaissir, en restant à 8,5 mm.
Poche **rectangulaire débouchante** (37 × 17,5, coins R3 — une passe de fraise), l'accu
repose sur la plaque de fond transparente et dépasse par une fenêtre de la plaque haute.
Plus de fond à usiner, plus de trappe. La séparation entre la poche et la cavité du PCB
a été **supprimée** (123 mm²) pour gagner en encombrement, en gardant un **pontet de 6 mm
à chaque bout** — sans lui le bloc se détache du cadre.

**Repères** : KiCad et FreeCAD partagent x (horizontal), y (vertical), z (profondeur) ;
seule différence, y pointe vers le bas dans KiCad et vers le haut dans FreeCAD — le
générateur convertit (y_fc = −y_kicad), les plans SVG restent en repère KiCad.

## 5. Fabrication : prototype d'abord

1. **Proto plexi/PC découpé** : les trois pièces à plat (cadre en couches empilées pour
   simuler les 8,5 mm), pour valider ajustement, ouvertures, ergonomie et sens du biseau.
   Bon marché, jetable, aucun engagement.
2. **Cadre alu CNC** ensuite, une fois la géométrie éprouvée. Devis instantané et gratuit
   chez JLC en téléversant un STEP. Ordre de grandeur attendu : **60-150 € les deux
   moitiés** anodisées. Leviers de prix : épaisseur brute, nombre de bridages, rayons
   intérieurs (viser **R ≥ 3 mm**), anodisation.
3. **Repli** si le devis pique : cadre en deux couches découpées (profil en escalier au
   lieu du coin).

**Règle de dessin CNC** : pas d'angle intérieur vif — la fraise est ronde. Un dessin pensé
pour l'impression 3D ne s'usine pas.

## 6. Modèle 3D — `case/`

**Le contour du cadre n'est plus calculé, il est dessiné.** `case/gen_case.py`
(`freecad --console`) lit `case/case_outline.svg`, le SVG que Mae édite, et en tire
les trois solides + `case_plan.svg` de contrôle.

Ce que le script lit dans le SVG, identifié par la taille de l'emprise : contour extérieur,
contour intérieur, contour du PCB (repère), 26 découpes de touches, rectangle de l'accu,
et les trous Ø3,2 des vis. Le calage sur le repère KiCad est `DX,DY = -28,030 / -137,600`,
**validé à 0,009 mm** en recoupant les 26 découpes avec la position des switchs.

Ce que le script ajoute lui-même : les ouvertures USB-C / TRRS / interrupteur, percées
**perpendiculairement au chant** (normale au bord le plus proche — prendre la direction du
point le plus proche donnait un angle faux), et les dégagements de la plaque haute.

**Piège vérifié** : l'origine d'un footprint KiCad n'est pas son centre. `U16` (module P4)
est décalé de **20,51 mm**, `J12` de 5,08 mm. Toujours calculer l'emprise réelle des pads.
Dégagements actuels : module P4 28,8 × 29,2 à (172,16 · 53,68) ; connecteur écran `J12`
(header 1×05) 3,7 × 13,9 à (171,46 · 69,98).

L'ancien générateur paramétrique `gen_pd.py` (contour par offset du PCB) a été supprimé
le 2026-08-07 ; il reste dans l'historique git si besoin.

**Contenu du dossier** : `gen_case.py` et `case_outline.svg` sont les deux **sources** —
tout le reste est régénéré à partir d'elles (`.FCStd`, `.step`, `.stl`, `case_plan.svg`).

Généré **par script paramétrique** (CadQuery/build123d ou `freecadcmd`, en shell éphémère
NixOS) à partir des cotes réelles du PCB : contour, trous de montage, positions des
connecteurs. Un paramètre change → le STEP se régénère. `kicad-cli pcb export step` fournit
en plus le PCB complet avec ses composants comme référence d'encombrement.

## 7. Points de fixation

4 trous M3 par moitié, déjà sur la carte : (40,3 · 49,6) (43,7 · 68,2) (139,5 · 40,3)
(157,9 · 94,0) — repère KiCad. Ce sont des `MountingHole_3.2mm_M3_DIN965_Pad`, donc
**reliés à GND** : les vis participent au chemin ESD dès que le cadre est en alu.

**Non tranché** : vis traversantes plaque→fond avec le cadre en compression, ou taraudage
dans le cadre alu. Le nombre de points est peut-être à revoir (4 par moitié sur
177 × 108 mm, à confirmer au proto — une plaque PC de 2 mm fléchit).

## 8. Ouvertures à dessiner

Dans le chant du cadre : **USB-C** (côté touches), **jack TRRS** (côté fond),
**interrupteur à glissière** (accès latéral, doit pouvoir être actionné). Dans les plaques :
**trackpad** (43 mm, côté gauche), **écran Sharp** (côté droit), **fente microSD** (accès
au coffre P4), découpe-berceau du jack dans le fond, éventuelles lucarnes de dégagement.

Positions relevées sur la carte (repère KiCad, moitié gauche) : USB-C (181 · 26) ·
TRRS (187 · 80) · interrupteur (28 · 76) · trackpad (182 · 73) · microSD (145 · 64) ·
module P4 (158 · 68) · connecteur pile (67 · 80).

## 9. Reste à faire

- [ ] **Élargir la paroi autour des 4 vis de coin** (1,4 mm de matière, trop peu pour du PC)
- [ ] **Capot polycarbonate de protection** par-dessus le module P4 et l'écran (Mae, plus tard)
- [ ] Vérifier la face de `J6` dans KiCad (`B.Cu` alors que le jack sort par le dessus)
- [ ] Trancher le sens du biseau (au proto)
- [ ] Dessiner les ouvertures aux vraies cotes des connecteurs
- [ ] Vérifier au pied à coulisse la hauteur réelle du jack MJ-4PP-9 (6,3 mm = valeur catalogue)
- [ ] Choisir la finition (anodisation : couleur, satiné/brossé)
- [ ] Générer le premier STEP et relever le devis JLC
