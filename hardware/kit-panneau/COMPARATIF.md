# Comparatif de commande — à remplir avec les devis JLCPCB

Trois variantes exportées pour comparer le coût réel du multi-design.

| Zip | Contenu | Dimensions | Surface | Designs déclarés | Prix (à remplir) |
|---|---|---|---|---|---|
| `niphargus_conchodytes-gerbers.zip` | clavier + souris | 185,4 × 212,3 | 393,5 cm² | **3** | |
| `niphargus-seul-gerbers.zip` | clavier seul, 2 moitiés | 185,4 × 212,3 | 393,5 cm² | **2** | |
| `conchodytes-seul-gerbers.zip` | souris seule | 39,0 × 81,5 | 31,8 cm² | **1** | |

La comparaison qui décide :

```
   commande unique            :  panneau 3 designs
   deux commandes séparées    :  clavier 2 designs  +  souris 1 design
```

**La surface du panneau ne change pas** entre les deux premières variantes : la
souris tient dans le vide déjà payé. L'écart de prix est donc *uniquement* le
surcoût du design supplémentaire — c'est exactement ce qu'on cherche à mesurer.

## Ce que dit JLCPCB

Sont comptés comme designs différents les cartes dont *« les pistes, la
sérigraphie ou le masque diffèrent, dès lors qu'elles peuvent être séparées »* —
v-cut, fraisage **ou trous de perçage**. Nos mouse-bites suffisent donc à
déclencher le comptage.

Les deux moitiés du clavier étant miroir l'une de l'autre, elles comptent pour
**deux designs** à elles seules : même sans la souris, on n'est jamais à 1.

La seule échappatoire documentée — *« placer les designs dans un contour
rectangulaire, sans v-cut, tabs ni fraisage »* — ne s'applique pas ici : notre
contour épouse la forme des claviers (438 mm de bord droit sur 795 mm de
périmètre) et comporte 147 segments de fraisage intérieur. On recevrait sinon
une plaque brute à découper soi-même.

Plafond : 10 designs par panneau. On est à 3.

Sources : [What Counts as Different Designs](https://jlcpcb.com/help/article/different-design-in-your-pcb-files) ·
[In what cases will there be charged extra?](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra)

## Non vérifié

Les cotes exigées pour les mouse-bites (diamètre, pas, nombre par tab)
n'apparaissent dans aucun de leurs articles — seul le v-cut est détaillé
(70 × 70 mm mini, 2 mm entre lignes parallèles). Les nôtres sont à **Ø 0,5 mm au
pas de 0,75**, valeurs d'usage courant. Si leur revue de fichiers tique, ce sont
`BITE_D` et `BITE_P` dans `scripts/merge_panel.py`.
