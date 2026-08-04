# Niphargus v2 — notes de commande (compagnon des CSV)

Stratégie (2026-08-04) : **TME d'abord** (réductions de Mae) via `commande-tme.csv`
(colonne `Symbol` = MPN fabricant, à coller dans la recherche ou l'import panier TME) ;
`commande-lcsc.csv` ne garde que l'introuvable hors Chine (WCH, TP4056, DW01A, FS8205,
AO3407, MSK-12C02) + l'USB-C HRO verrouillé par l'empreinte. Quantités = commande pour
2 builds ; `Qty per board` = besoin réel d'un clavier.

MàJ 2026-08-04 : liens TME remplacés par les VRAIES pages produit (vérifiées une à une
par recherche web — l'URL de recherche `?search=` ne marche pas). Les CONDENSATEURS
Samsung CL sont retournés au CSV LCSC : chez TME toute la série NNNC est en fin de vie
(« hardly available », remplaçants NNND, deux réfs retirées). Résistances 1M et 100k en
0805 : série W absente de TME → série S équivalente (0805S8F...). microSD : ligne TME
= Hirose DM3AT-SF-PEJM5(40) — suppose le changement d'empreinte (option A, patch p4 à
demander) ; sinon option B = Würth 693072010801 chez Farnell/RS.

Substitutions faites pour TME : AMS1117-3.3 → **LD1117S33TR** (ST, même boîtier/pinout,
mettre à jour la Value du symbole U17 un jour) ; SD05C-01FTG → **SD05C.TCT** (Semtech,
même fonction/boîtier). Le trackpad Azoteq existe aussi chez LCSC (C7073363, ~7 $) mais
était en rupture au 2026-08-04 — keycapsss reste le plan A (nappe incluse).

## ⚠️ Décision antenne AVANT de commander la ligne WROOM

L'empreinte posée sur la carte est la **WROOM-1U** (antenne externe u.FL — cohérent avec
le décrochement de contour fait le 03/08 ?).

- Antenne externe assumée → remplacer C2913204 par **C3013944** (1U-N8R2) + acheter 2
  antennes u.FL 2,4 GHz.
- Antenne PCB intégrée → garder C2913204 **et** échanger l'empreinte des deux modules
  (WROOM-1U → WROOM-1) avant commande du PCB.

## LED témoin de charge (×2)

Couleur au goût : chercher « LED 0805 » chez LCSC et prendre une référence Basic
(rouge/verte, ~0,01 €). Résistance 1k déjà dans le CSV.

## Hors LCSC

| Qté | Quoi | Où | Note |
|---|---|---|---|
| 2 | module nRF24L01+ (2×4 pin) | AliExpress | filière v1 (README) |
| 1 | module ESP32-P4 JC-ESP32P4-M3 V0.2 | AliExpress/Taobao | empreinte V0.2 sur le PCB |
| 2 | jack TRRS MJ-4PP-9 | [AliExpress](https://fr.aliexpress.com/item/33029465106.html) | filière v1 |
| 1 | microSD Würth 693072010801 (hinge) | Mouser/Farnell | alt. LCSC TF-01A C91145 mais CHANGER l'empreinte avant |
| 1 | trackpad Azoteq TPS43-201A-S | keycapsss / Mouser | nappe FFC 50 mm incluse chez keycapsss |
| 1 | écran Sharp LS011B7DH03 | Mouser/DigiKey | connecteur FPC 10P 0,5 mm à traiter comme le trackpad (J7 encore en header placeholder) |
| 52 | switchs MX/Choc + keycaps | AliExpress | tableau du README v1 |
| 2 | cellule 16340 + contacts/holder | — | décision layout en attente (design doc) |
| — | pin headers 1×02 / 1×05 / 2×03 P1.27 | LCSC ou fond de tiroir | batterie / écran / prog |
