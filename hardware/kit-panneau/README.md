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

## À faire avant de commander

- **tabs et mouse-bites** reliant la souris au panneau : elle est actuellement
  posée dans le vide, sans attache. À placer sur ses longs côtés ;
- vérifier que le contour de la souris est bien celui de la coque M100 — celui
  du dépôt vient du fork `USB-Mouse` ;
- nettoyer le DRC des deux cartes (18 `copper_edge_clearance` côté souris).

## Note

Les zones ne sont **pas** refillées à la fusion : les plans de masse des deux
cartes s'étendraient l'un vers l'autre. Ne pas lancer de *refill* sur le panneau.
