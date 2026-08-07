# Boîtier Niphargus — conception mécanique

*Brainstorm du 2026-08-07 (Mae + Claude). Toutes les cotes internes sont mesurées sur
`rili/pcb/niphar.kicad_pcb` dans son état routé, pas estimées.*

## 1. Intention

Reprendre l'objectif d'origine — **fin et durable** — sans reproduire l'échec des v1 (coque
imprimée qui fend, PCB mal soutenu). Trois pièces, aucune imprimée, et une silhouette qui
tire parti du seul relief inévitable : la pile.

## 2. Structure retenue : sandwich à trois pièces

| Pièce | Matière | Épaisseur | Fabrication |
|---|---|---|---|
| Plaque à switchs | polycarbonate transparent | **2,0 mm** | découpe |
| Cadre | **aluminium usiné** | **8,5 mm** (partie courante) | CNC — test JLCPCB |
| Fond | polycarbonate transparent | **2,0 mm** | découpe |

**Total : 12,5 mm hors tout** (hors keycaps), **≈21,5 mm** au bord de la pile.

Le polycarbonate haut et bas donne la transparence (l'électronique et la sérigraphie sont
visibles) et une frappe plus douce que le FR4 ou l'alu. Le cadre alu apporte la rigidité,
le chant métal et un chemin de masse pour l'ESD (§6 du design doc v2).

## 3. Empilage interne (les cotes qui coûtent cher si on les perd)

```
        ┌───────────────────────┐  plaque PC 2,0
        │   3,4 mm  (norme MX)  │  ← module P4 (3,2) y tient à 0,2 près
   ─────┼───────────────────────┼─────  PCB 1,6
cadre   │   3,5 mm              │  ← module S3 3,1 · nRF24 ~3 · interrupteur 2,5 · microSD 1,9
  8,5   └───────────────────────┘  fond PC 2,0
```

- **3,4 mm PCB → plaque** : cote normalisée MX. Contrainte forte : le **module P4 est côté
  touches** (3,2 mm) — vérifié sans conflit avec aucun switch.
- **3,5 mm sous la carte** : couvre tout le côté fond **sauf le jack TRRS**.
- **Jack TRRS (~6,3 mm, côté fond)** : plonge dans une **découpe ajustée du fond**, dépasse
  de **0,8 mm** sous le clavier. La découpe sert de berceau et le tient latéralement.
  Pieds caoutchouc de 3 mm → il ne touche jamais la table.
- **Plaque de 2 mm** (choix Mae) : les clips MX ne se verrouillent pas (cote de clipsage =
  1,5 mm). Les switchs sont tenus par les sockets hotswap et guidés par la plaque ;
  conséquence assumée : un switch peut suivre un keycap qu'on retire.

## 4. Silhouette : la pile porte l'inclinaison

La 16340 (Ø16,5 × 34,5) ne rentre dans aucun boîtier de 12,5 mm. Plutôt que de la subir,
elle devient le parti pris : le cadre s'épaissit **en coin** jusqu'à ~21,5 mm le long du
bord qui la loge, et redescend à 12,5 mm à l'opposé. Inclinaison intégrée, **aucun pied
rapporté**.

Marges libres autour du champ de touches (moitié gauche, carte 177,3 × 107,9 mm) :

| Bord | Marge | Conséquence si la pile y va |
|---|---|---|
| extérieur (auriculaire) | 19 mm | place facile ; pente descendant vers le centre |
| intérieur (pouce) | 14 mm, chargé (USB-C, TRRS, trackpad) | vrai tenting ergonomique |
| arrière | 9 mm | tilt classique ~5° ; la pile empiète sous les touches du haut |
| avant | 16 mm | tilt inversé, déconseillé |

**Non tranché** — sera décidé sur le prototype plexi, à l'essai.

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

## 6. Modèle 3D

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
