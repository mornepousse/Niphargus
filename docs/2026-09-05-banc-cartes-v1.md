# Banc v1 — relevés et pistes ouvertes (5 septembre 2026)

Tout ce qui suit attend un multimètre. Rien n'est à faire avant d'avoir mesuré :
les deux pannes ci-dessous ont chacune plusieurs causes possibles, et deux
d'entre elles ne coûtent rien à écarter.

---

## 1. Point de chauffe sur U21 — RÉSOLU (LDO remplacé), PCB CORRIGÉ

> **U21 remplacé, la moitié droite fonctionne.** Le pontage de masque avait mis
> `GND`, l'entrée et la sortie `+3.3V_D` en court : le régulateur y est passé.
> Un HT7833 neuf et le rail remonte.
>
> ⚠️ **Le défaut de masque est TOUJOURS sur la carte.** Le composant neuf est
> posé sur les mêmes trois pastilles, sans vernis entre elles. Ça fonctionne
> aujourd'hui parce que la soudure ne ponte pas — rien ne garantit que ça tienne
> à un cycle thermique, une reprise au fer ou un choc. **Isoler les pastilles**
> (vernis, kapton) reste à faire, ici et sur toutes les moitiés droites déjà
> fabriquées.
>
> Le PCB est corrigé pour les fabrications suivantes (commit `53564e4`).


**Symptôme** : gros point de chauffe sur U21, le LDO 3,3 V de la moitié droite.

**Cause**, nommée par le DRC de KiCad lancé avec `--refill-zones` :

```
[error] L'ouverture du masque de soudure de dessous relie des elements
        de nets differents
    - Pad 1 [GND]         de U21
    - Pad 2 [Net-(D51-K)] de U21
[error] idem entre Pad 2 [Net-(D51-K)] et Pad 3 [+3.3V_D]
```

Les trois pastilles de U21 partageaient **une seule ouverture de masque** :
GND, l'entrée et la sortie 3,3 V sans vernis entre elles, du cuivre nu continu.
La soudure ponte toute seule.

**Origine** : les trois pads portaient une rotation de 180° que la sérigraphie
et le contour Fab n'avaient pas. Sur les pads 1 et 3, roundrect symétriques,
sans effet — **GND et la sortie ne sont PAS interverties, le composant est dans
le bon sens, ne le retourne pas.** Mais le pad 2 est un pad `custom` : son
polygone de languette, retourné, étalait une ouverture de masque par-dessus les
trois pastilles.

U20, le même LDO à gauche, n'avait pas l'anomalie : empreinte à 180 et pads à
180, soit 0 d'écart. U21 était à 0 avec des pads à 180.

**Corrigé** dans le commit `53564e4` : suppression des trois rotations de pad.
3 violations disparues, aucune nouvelle.

### Ce qui reste à faire sur la carte physique

C'est un défaut de fabrication, pas de montage — **toutes les moitiés droites
déjà fabriquées sont concernées**.

1. Dessouder le pontage entre les pastilles de U21 (tresse, puis loupe).
2. Le cuivre nu reste : un peu de vernis ou de kapton entre les pastilles évite
   que ça re-ponte au remontage.
3. Avant de réalimenter : pas de court franc entre pad 2 et pad 1, ni entre
   pad 2 et pad 3.

### Reste ouvert

`courtyards_overlap` entre **U21 et C23** — le condensateur chevauche le
régulateur depuis son déplacement. Le remettre à son ancienne position
supprime le chevauchement mais laisse une piste en l'air (`track_dangling` sur
`Net-(D51-K)`) : le routage a suivi la nouvelle place. À replacer proprement
dans KiCad, avec le routage.

---

## 2. Aucune tension sur la moitié gauche en mode batterie — RÉSOLU

> **CAUSE : la broche 1 de Q4 (FS8205) n'était pas soudée.**
>
> Broche 1 = `S1` = `-BATT`, la source du FET de décharge. Patte en l'air, donc
> aucun chemin de retour pour la batterie — ni en décharge, ni en charge.
> Ressoudée, la moitié gauche démarre sur batterie.
>
> **Pourquoi la continuité ne l'a pas vu.** `U23 pad 6 ↔ Q4 pad 1` bipait
> correctement : une broche non soudée **repose** sur sa pastille, et la pointe
> de touche l'y écrase. Le contact se fait pendant la mesure et disparaît dès
> qu'on retire la pointe. **Aucun test de continuité ne peut attraper une
> soudure froide sur une patte posée.** Il faut un contrôle visuel, ou pousser
> la patte latéralement pendant la mesure.
>
> **Ce qui a fini par le trahir** : le pont maintenu entre `-BATT` et `GND`
> faisait passer OD à 3,5 V, mais l'état ne tenait pas au retrait du pont. Or si
> FET1 conduisait, son canal maintiendrait `GND` sur `-BATT` et l'état
> s'auto-entretiendrait. Il ne tenait pas ⇒ la commande arrivait, le canal ne
> conduisait pas ⇒ le défaut était dans Q4 ou ses soudures de puissance, pas
> dans le pilotage.
>
> Le reste de la chaîne était sain et se comportait logiquement : `GND`
> flottait faute de retour, CS lisait 0,5 à 2,2 V selon la charge — bien
> au-dessus du seuil de 150 mV — donc le DW01A coupait la décharge et gardait la
> charge ouverte. Comportement conforme à sa datasheet du début à la fin.

### Ce qui reste vrai et vérifié dans l'analyse ci-dessous

Le brochage du DW01A et celui du FS8205 ont été contrôlés sur les datasheets
fabricant à cette occasion. **Ils sont justes** — c'est consigné plus bas et ça
reste valable pour toute panne future sur cette chaîne.

---

### Analyse d'origine (conservée)

**Symptôme** : rien en batterie sur la gauche. Tout fonctionne sur USB.

### Le design est hors de cause — vérifié, sourcé

C'était l'inquiétude légitime : si le symbole maison `rouge_gorge:FS8205` avait
un brochage faux, c'était toutes les cartes à refaire. **Ce n'est pas le cas.**

**DW01A** — datasheet H&M Semiconductor, celle citée dans le schéma
(`https://hmsemi.com/downfile/DW01A.PDF`), section *Pin Configuration* :

| Broche | Symbole | Câblage de U23 | |
|---|---|---|---|
| 1 | OD — grille du FET de décharge | `Net-(Q4-G1)` | OK |
| 2 | CS — sense de courant | → R73 **1 k** → `GND` | OK |
| 3 | OC — grille du FET de charge | `Net-(Q4-G2)` | OK |
| 4 | TD — broche de test | non connectée | OK |
| 5 | VCC — via une résistance R1 | ← R70 **100 Ω** ← `+BATT` | OK |
| 6 | GND | `-BATT` | OK |

Le *Typical Application Circuit* de la même datasheet donne R1 = 100 Ω et
R2 = 1 kΩ : les valeurs de la carte au composant près. Et la masse du DW01A va
bien au négatif de la **cellule** pendant que CS va au négatif du **système**.

**FS8205** — deux fabricants indépendants, tous deux avec un dessin numéroté :

- JSCJ/JCET *CJL8205A Rev 2.0*, section *Equivalent Circuit*, broches
  numérotées directement sur le schéma
- UMW *8205A*, dessin *SOT23-6 top view* avec le repère de broche 1

| pad | Câblage de Q4 | Fonction | UMW | JSCJ |
|---|---|---|---|---|
| 1 | `-BATT` | S1 | OK | OK |
| 2 | drains | D1/D2 | OK | OK |
| 3 | `GND` | S2 | OK | OK |
| 4 | `Net-(Q4-G2)` | G2 | OK | OK |
| 5 | drains | D1/D2 | OK | OK |
| 6 | `Net-(Q4-G1)` | G1 | OK | OK |

> **Ne pas se fier aux recherches web sur ce composant.** Trois recherches ont
> donné trois brochages différents, tous faux, dont un qui inversait précisément
> les broches 1 et 6 — de quoi condamner un lot de cartes à tort. Seuls les PDF
> lus directement font foi. Même leçon que pour le XC6206 sur Conchodytes.

### La topologie, et pourquoi le symptôme est cohérent

```
J10 pad1 = -BATT ──> Q4 FS8205 ──> GND
J10 pad2 = +BATT ──> Q2 AO3407 ──> SW54 ──> D52-K ──> U20 VIN
                └──> R70 100R ──> VCC du DW01A
```

**Le FS8205 est dans le chemin de MASSE**, entre `-BATT` et `GND`. S'il ne
conduit pas, la batterie n'a aucun retour : on lit la cellule sur J10 et zéro
partout ailleurs. Sur USB tout marche, la masse venant du connecteur. C'est
exactement le symptôme.

### Mesures à faire, batterie branchée et USB débranché

| # | Mesure | Attendu | Sinon |
|---|---|---|---|
| 1 | `-BATT` ↔ `GND` | ≈ 0 V | tension pleine → chemin de masse ouvert, c'est là |
| 2 | J10 pad 2 ↔ pad 1 | 3,0 – 4,2 V | < 2,4 V → cellule sous le seuil, protection verrouillée |
| 3 | U23 broche 5 (bornes de R70) | ≈ Vbat | 0 V → R70 ou DW01A absent/mort |
| 4 | U23 broches 1 et 3 | ≈ Vbat | 0 V → protection en sécurité, ou pas de VCC |

**Commencer par la 1**, c'est elle qui oriente tout le reste.

### Le test gratuit, à faire en premier

Le **verrouillage par décharge profonde** du DW01A : détection à 2,40 V,
remise en service à 3,0 V (datasheet, *Product Name List*). Sous le seuil la
protection coupe la masse et ne se réarme **qu'à l'application d'un chargeur**.
Symptôme : rien en batterie, tout va bien en USB, indéfiniment.

Brancher l'USB dix minutes, débrancher, retenter. Si ça repart, c'était ça, et
il n'y a rien à réparer.

### La question qui vaut dix mesures

**Est-ce que la moitié droite fonctionne sur batterie ?** Même circuit, mêmes
composants, même symbole. Si la droite marche, la panne est locale à gauche.

---

## 3. Le ratchet de check.sh n'a pas vu le défaut de U21

Quand le déplacement de C23 a été poussé (`15e3549`), `check.sh` était vert. Le
DRC était pourtant passé de 473 à 164 violations : un recalcul de zones avait
effacé des centaines de warnings de remplissage, et **quatre erreurs neuves sont
passées sous cette amélioration globale**, dont le chevauchement U21/C23.

Le ratchet compare des **comptes**. Il ne peut pas voir une erreur critique
apparaître pendant qu'une centaine d'autres disparaissent.

Deux corrections à envisager pour `scripts/check.sh` :

1. Lancer le DRC **avec `--refill-zones`**. Sans ça le résultat dépend de l'état
   de remplissage sauvegardé, qui n'est pas déterministe d'une session KiCad à
   l'autre — c'est ce qui a masqué le vrai défaut pendant tout ce temps.
2. Suivre les violations **par type**, pas seulement leur total. Une nouvelle
   `clearance` ou un nouveau `solder_mask_bridge` doit être rouge même si le
   total baisse.
