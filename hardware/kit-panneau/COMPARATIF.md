# Comparatif de commande — à remplir avec les devis JLCPCB

Trois variantes exportées pour comparer le coût réel du multi-design.

| Zip | Contenu | Dimensions | Surface | Designs | Prix (vert, 2026-08) |
|---|---|---|---|---|---|
| `niphargus-gerbers.zip` | **clavier horizontal, retenu** | 340,9 × 104,8 | 357,3 cm² | **2** | **54,78 €** |
| *(clavier compact empilé)* | même design, moitiés imbriquées | 169,2 × 198,2 | 335 cm² | 2 | 53,65 € |
| `conchodytes-seul-gerbers.zip` | **souris, retenue** | 39,0 × 81,5 | 31,8 cm² | **1** | **6,06 €** |
| *(ancien panneau 185,4 × 212,3)* | clavier avant re-panneautage | | 393,5 cm² | 2 | 56,68 € |
| *(panneau commun, écarté)* | clavier + souris | 185,4 × 212,3 | 393,5 cm² | 3 | 70,89 € |

## Décision : commander séparément, avec le panneau compact

Devis JLCPCB, 4 couches vert, août 2026 :

```
   A  panneau commun 3 designs                        70,89 EUR
   B  clavier 394 cm2 empile   + souris        56,68 + 6,06 = 62,74 EUR
   C  clavier 335 cm2 empile   + souris        53,65 + 6,06 = 59,71 EUR
   D  clavier 357 cm2 horizontal + souris      54,78 + 6,06 = 60,84 EUR  <-- retenu
```

**10,05 EUR d'economie** entre le point de depart et la solution retenue.

Le panneau horizontal coute **1,13 EUR de plus** que l'empile (option C) : il a
6,4 % de surface en plus, l'imbrication verticale des deux moities n'etant pas
reproductible cote a cote. Il a ete retenu pour sa forme, pas pour son prix.

La repartition est instructive :

- **8,15 EUR** viennent du seul fait de **ne pas panneauter la souris avec le
  clavier**. Ajouter la souris au panneau coute 14,21 EUR de surcout
  multi-design alors que la carte seule vaut 6,06 EUR : on la paierait 2,3 fois
  son prix, pour une surface identique au millimetre.
- **1,90 EUR** viennent du **re-panneautage du clavier**, passe de 394 a
  357 cm2 en posant les deux moities cote a cote, la droite tete-beche, rails
  supprimes. Le prix ne suit pas la surface : le surcout multi-design est un
  forfait qui pese davantage que les cm2 gagnes — un detour par un panneau
  empile a 335 cm2 n'a rendu que 1,13 EUR de plus.

Le second point vaut d'etre retenu pour la suite : **sur un petit panneau,
economiser un design rapporte plus qu'economiser de la surface.**

Le panneau commun et `scripts/merge_panel.py` sont conserves — la technique est
au point et resservira si le rapport de prix change — mais ce n'est pas ce
qu'on commande.

### Conséquence heureuse

La souris n'est plus contrainte par le panneau du clavier. La limite de **42 mm**
de largeur, qui pesait sur la mesure de la coque M100, **disparait** : son
contour definitif pourra faire la taille necessaire.

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
