# Boîtier Niphargus — conception mécanique

*Brainstorm du 2026-08-07 (Mae + Claude). Toutes les cotes internes sont mesurées sur
`rili/pcb/niphar.kicad_pcb` dans son état routé, pas estimées.*

## 1. Intention

Reprendre l'objectif d'origine — **fin et durable** — sans reproduire l'échec des v1 (coque
imprimée qui fend, PCB mal soutenu). Trois pièces, aucune imprimée, et une silhouette qui
tire parti du seul relief inévitable : la pile.

## 2. Structure retenue : cinq pièces

| Pièce | Matière | Épaisseur | Fabrication |
|---|---|---|---|
| Plaque à switchs | polycarbonate transparent | **2,0 mm** | découpe (26 ouvertures MX 14×14, orientées) |
| Cadre | **aluminium usiné** | **8,5 mm** | CNC — test JLCPCB |
| Fond | polycarbonate transparent | **2,0 mm** | découpe |
| Logement accu | aluminium (solidaire du cadre) | 19,5 mm local | CNC |
| Trappe accu | alu ou PC | 2,0 mm | découpe |

**Clavier plat à 12,5 mm hors tout**, sauf la bande de l'accu (19,5 mm, dépassant de 9 mm
sous le fond). Choix Mae du 2026-08-07 : plaque à 2 mm (et non 1,5) — les clips MX ne se
verrouillent donc pas, les switchs sont tenus par les sockets hotswap.

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

**Jack TRRS** (~6,3 mm, côté fond d'après le fichier) : ouverture pleine hauteur dans la
paroi. À confirmer sur pièce — Mae le pense côté touches, le fichier dit `B.Cu`.

## 4. Accu : À CÔTÉ de la carte, pas dessous

La 16340 (Ø16,5 × 34,5) est logée **hors du contour du PCB**, le long du bord inférieur
gauche (segment 27,4·90 → 81,4·80,3, pente −10°), sous les touches SW5/SW14/SW21 au sens
du plan. Centre à ~53,6 · 96,5, axe à 11 mm du bord. Le cadre s'élargit localement au lieu
de s'épaissir : **19,5 mm sur 44 mm de long** au lieu de 29,5 mm si l'accu passait sous la
carte. Poche cylindrique Ø17,5 ouverte par le dessous, fermée par une **trappe** (fixation
à définir) — l'accu se change sans ouvrir le clavier.

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

## 6. Modèle 3D — `boitier/`

`boitier/gen_pd.py` (lancé par `freecad --console`) génère `niphar-cadre-gauche.FCStd`,
le STEP et les plans SVG depuis le PCB. Paramètres en tête du fichier : `WALL`, `FIT`,
hauteurs, `SKIP_BOXES` (zones où le cadre ne suit pas le contour — le décrochement
d'antenne nRF24 en fait partie), `OPENINGS`, `BATT_*`. Les ouvertures sont des
**esquisses éditables** dans FreeCAD (`esq_USB_C`, `esq_TRRS`, `esq_SWITCH`) ; le contour
du cadre reste un solide calculé (PartDesign et Part::Extrusion plantent sur ses ~110
éléments d'offset).

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

- [ ] Trancher le sens du biseau (au proto)
- [ ] Trancher le mode de fixation et le nombre de points
- [ ] Dessiner les ouvertures aux vraies cotes des connecteurs
- [ ] Vérifier au pied à coulisse la hauteur réelle du jack MJ-4PP-9 (6,3 mm = valeur catalogue)
- [ ] Choisir la finition (anodisation : couleur, satiné/brossé)
- [ ] Générer le premier STEP et relever le devis JLC
