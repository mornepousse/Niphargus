# Kit de fabrication

Après devis, on commande les deux cartes **séparément**, et le clavier dans sa
version **compacte**.

| Zip | Ce que c'est | Dimensions | Designs | Prix |
|---|---|---|---|---|
| `niphargus-gerbers.zip` | le clavier, 2 moitiés sécables | 340,9 × 104,8 | 2 | 54,78 € |
| `conchodytes-seul-gerbers.zip` | la souris | 39,0 × 81,5 | 1 | 6,06 € |

**60,84 €**, contre 70,89 € pour le panneau commun de départ. Le raisonnement
chiffré est dans `COMPARATIF.md`.

## Le panneau du clavier

340,9 × 104,8 mm, 4 couches, **357,3 cm²**. Les deux moitiés sont côte à côte,
la droite tête-bêche, séparées par une fente de 2,5 mm et reliées par deux
ponts de ~6,5 mm munis chacun d'un `MouseBite-Slot` à double rang.

Le tête-bêche n'est pas cosmétique : remise dans le même sens, la moitié droite
ne touche la gauche que sur **1,75 mm** — les deux bords en vis-à-vis sont
biseautés et divergents. Tête-bêche ils sont parallèles sur **70 mm**, de quoi
poser de vrais ponts, pour 1,6 cm² de plus.

⚠️ **Les mouse-bites vont au milieu du tab, jamais au ras du bord de carte** :
là, ils tombent dans le plan de masse (35 `hole_clearance`, vérifié). Ici les
perçages sont à 0,45 mm du bord, au-dessus du minimum JLC de 0,3. Et après en
avoir posé, **refiller les zones** — sinon 28 `hole_clearance` de plus, que le
refill dissout.

Empreintes réutilisables dans `MaeLid` : `MouseBite_4x0.5mm`, `_5x0.5mm`,
`_6x0.5mm`.

## Le panneau commun, écarté

`scripts/merge_panel.py` sait loger la souris dans le vide du panneau clavier.
La technique fonctionne — contour refermé autour des tabs, 76 mouse-bites — mais
le surcoût du 3ᵉ design (14,21 €) dépasse le prix de la souris seule (6,06 €).
Conservé pour le jour où le rapport de prix changerait.
