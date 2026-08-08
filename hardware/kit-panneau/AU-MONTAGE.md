# À lire avant de souder

Cartes commandées le **2026-08-08** chez JLCPCB, 4 couches vert, 60,83 € les
deux designs du clavier plus la souris Conchodytes. Assemblage **à la main**.

## ⚠️ J6 se soude PAR LE DESSOUS

Les deux jacks TRRS ne sont pas sur la même face :

| Connecteur | Face dans le fichier | Moitié |
|---|---|---|
| J5 | `F.Cu` — dessus | droite |
| **J6** | **`B.Cu` — DESSOUS** | **gauche** |

Les deux USB-C (J7, J8) sont en `F.Cu` tous les deux : l'asymétrie ne touche que
le TRRS, et porte la signature d'un basculement de face lors du placement
miroir. Le routage est cohérent avec cette face — l'ERC et le DRC sont verts.

**Souder J6 par le dessus casserait le clavier.** Un jack traversant monté sur
l'autre face a son brochage en miroir : Tip et Sleeve s'échangent, donc les 5 V
du lien inter-moitiés arrivent sur la masse. Le brochage n'est juste que si le
corps du connecteur sort **sous** la carte.

Conséquence pour le boîtier — il n'est pas usiné, c'est encore rattrapable : la
moitié gauche a besoin de son ouverture TRRS **sous** la carte, la droite
**au-dessus**.

## Autres points non vérifiés

- **Hauteur du MJ-4PP-9** : 5,4 mm disponibles dans le cadre alu de 8,5 mm,
  contre ~6,3 mm au catalogue. À mesurer sur la pièce réelle avant d'usiner.
- **Vis du sandwich** : 6 des 8 n'ont que 1,4 mm de matière autour du perçage.
  Ça tient en aluminium ; c'est le polycarbonate de 2 mm qui cassera.
- **Souris Conchodytes** : le rail +1,8 V du PMW3360 vient de la consigne de
  Mae, pas d'une lecture de datasheet. À confirmer avant de mettre sous tension.
  Lentille **LM19-LSI** à commander séparément.

## Séparer le panneau

Deux ponts de ~6,5 mm reliant les moitiés, chacun avec un `MouseBite-Slot` à
double rang : casser le long des deux rangées, la bandelette centrale de 1,5 mm
part à la chute et chaque carte garde un bord net. Ébavurer à la lime douce.
