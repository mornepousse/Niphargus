# Kit de fabrication

Après devis, on commande les deux cartes **séparément**, et le clavier dans sa
version **compacte**.

| Zip | Ce que c'est | Dimensions | Designs | Prix |
|---|---|---|---|---|
| `niphargus-gerbers.zip` | le clavier, 2 moitiés sécables | 169,2 × 198,2 | 2 | 53,65 € |
| `conchodytes-seul-gerbers.zip` | la souris | 39,0 × 81,5 | 1 | 6,06 € |

**59,71 €**, contre 70,89 € pour le panneau commun de départ. Le raisonnement
chiffré est dans `COMPARATIF.md`.

## Le panneau du clavier

169,2 × 198,2 mm, 4 couches. La moitié droite est tournée à 180° et imbriquée
dans le creux de la gauche, les rails sont supprimés : 335 cm² au lieu de 393,5.
Les deux moitiés tiennent par des ponts encadrés de mouse-bites, autour de la
fenêtre centrale.

⚠️ **Les mouse-bites vont au milieu du tab, jamais au ras du bord de carte** :
là, ils tombent dans le plan de masse (35 `hole_clearance`, vérifié). Et après
en avoir posé, **refiller les zones** — sinon 28 `hole_clearance` de plus, que le
refill dissout.

Empreintes réutilisables dans `MaeLid` : `MouseBite_4x0.5mm`, `_5x0.5mm`,
`_6x0.5mm`.

## Le panneau commun, écarté

`scripts/merge_panel.py` sait loger la souris dans le vide du panneau clavier.
La technique fonctionne — contour refermé autour des tabs, 76 mouse-bites — mais
le surcoût du 3ᵉ design (14,21 €) dépasse le prix de la souris seule (6,06 €).
Conservé pour le jour où le rapport de prix changerait.
