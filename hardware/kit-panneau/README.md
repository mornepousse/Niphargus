# Kit de fabrication

**Trois variantes de gerbers.** Après devis, on commande les deux cartes
**séparément** — le panneau commun revient plus cher (voir `COMPARATIF.md`).

| Zip | Ce que c'est | Designs | Prix |
|---|---|---|---|
| `niphargus-seul-gerbers.zip` | le clavier, 2 moitiés sécables | 2 | 56,68 € |
| `conchodytes-seul-gerbers.zip` | la souris | 1 | 6,06 € |
| `niphargus_conchodytes-gerbers.zip` | les deux dans un panneau — **non retenu** | 3 | 70,89 € |

## Tabs et mouse-bites

| | Position | Tabs | Perçages |
|---|---|---|---|
| Moitiés → rail droit | x 186,95 → 190,01 | 4 pattes de 3,1 mm, aux y 32-38, 81-87, 159-165, 209-215 | 32 |
| Moitiés → rail gauche | x 14,64 → 18,7 à 22,6 | 4 pattes aux y 40-46, 57-63, 184-190, 200-206 | 32 |
| Souris → rail gauche *(panneau commun seulement)* | x 14,64 → 18,00 | 3 tabs de 3 mm | 12 |

Les **64 perçages du clavier sont dans `niphar.kicad_pcb` lui-même**
(`scripts/mousebites.py`), donc présents que l'on commande le clavier seul ou le
panneau. Ils étaient auparavant posés par `merge_panel.py`, donc absents du
clavier seul — le zip livrait des pattes en matière pleine.

⚠️ **Les perçages vont au milieu du tab, pas au ras de la carte.** Au ras du bord
ils tombent dans le plan de masse : 35 violations `hole_clearance` (vérifié).

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
