# Panneau Niphargus + Conchodytes

Gerbers du panneau de fabrication : les **deux moitiés du clavier Niphargus** et
la **carte de la souris Conchodytes**, réunies dans un seul panneau.

Les deux projets restent **indépendants** — chacun son dépôt, son schéma, son
layout. Ils ne sont réunis qu'ici, à l'export, par `scripts/merge_panel.py` :

```sh
python3 scripts/merge_panel.py /tmp/panel/panel.kicad_pcb
```

Le script prend `hardware/pcb/niphar.kicad_pcb`, y insère
`Conchodytes/hardware/pcb/conchodytes.kicad_pcb` tourné de **−90°** et translaté
de (+170,85 · +26,15), ce qui pose la souris dans le vide entre les deux moitiés,
l'avant (le renflement de l'USB-C) vers la droite.
Tous les UUID sont régénérés pour éviter les collisions.

## Cotes

| | |
|---|---|
| Panneau | 185,4 × 212,3 mm, 4 couches |
| Souris dans le panneau | 84,35 × 39,0 mm, en (18 · 103) |
| Vide disponible mesuré | 112 × 42 mm — marge 27,7 mm en x, 3,0 mm en y |

La souris tient **dans l'espace déjà payé** du panneau : son PCB ne coûte
pratiquement rien.

## Tabs et mouse-bites

| | Position | Tabs | Perçages |
|---|---|---|---|
| Souris → rail gauche | x 14,64 → 18,00 | 3 tabs de 3 mm, aux y 115-118, 121-124, 127-130 | 12 |
| Moitiés → rail droit | x 186,95 → 190,01 | 4 pattes de 3,1 mm, aux y 32-38, 81-87, 159-165, 209-215 | 32 |
| Moitiés → rail gauche | x 14,64 → 18,7 à 22,6 | 4 pattes aux y 40-46, 57-63, 184-190, 200-206 | 32 |

Perçages **Ø 0,5 mm au pas de 0,75**, posés sur la ligne de rupture, côté carte,
pour que la tranche reste propre après séparation. **76 au total sur 11
jonctions.** Côté gauche, le bord de la carte est en biais (le biseau du
clavier) : les perçages suivent la pente au lieu d'une verticale.

Les quatre pattes du clavier n'avaient aucun perçage : le contour y était plein,
il aurait fallu les couper à l'outil.

⚠️ **Le contour du panneau doit rester une boucle fermée.** Interrompre les deux
bords de part et d'autre d'un tab laisse des extrémités libres, et un contour
ouvert n'est pas interprétable : le panneau ressort plein chez le fabricant.
Le vide est donc **refermé autour** de chaque tab par deux segments horizontaux,
ce qui délimite le pont de matière. Vérification : `0 extrémité libre`, comme le
panneau du clavier seul.

## À faire avant de commander

- vérifier que le contour de la souris est bien celui de la coque M100 — celui
  du dépôt vient du fork `USB-Mouse` ;
- nettoyer le DRC des deux cartes (18 `copper_edge_clearance` côté souris) ;
- confronter le diamètre et le pas des mouse-bites aux règles de JLCPCB.

## Note

Les zones ne sont **pas** refillées à la fusion : les plans de masse des deux
cartes s'étendraient l'un vers l'autre. Ne pas lancer de *refill* sur le panneau.
