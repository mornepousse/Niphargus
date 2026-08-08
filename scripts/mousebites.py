#!/usr/bin/env python3
"""Pose les mouse-bites sur les pattes du panneau Niphargus.

Les perçages sont sur la ligne de rupture, cote carte, pour que la tranche
reste propre apres separation. Cote gauche le bord de la carte est en biais
(le biseau du clavier) : le percage suit la pente.

Utilise aussi par scripts/merge_panel.py — ne pas dupliquer les cotes.
"""
import re, sys, uuid as U

BITE_D = 0.5      # diametre du percage
BITE_P = 0.75     # pas

# Les percages vont au MILIEU du tab, dans la matiere nue entre la carte et le
# rail. Au ras du bord de carte ils tombent dans le plan de masse : 35
# violations hole_clearance (verifie).
RAIL_R_X    = 190.01           # bord interieur du rail droit
RAIL_L_X    = 14.64            # bord interieur du rail gauche
KBD_BREAK_X = 186.95
KBD_TABS_R  = [(32.0, 38.0), (81.0, 87.0), (159.0, 165.0), (209.0, 215.0)]
# cote gauche : bord en biais, (y0, y1, x_au_debut, x_a_la_fin)
KBD_TABS_L  = [(40.42, 46.42, 18.67, 19.73),
               (56.86, 62.86, 21.55, 22.61),
               (183.59, 189.59, 22.61, 21.55),
               (200.03, 206.03, 19.73, 18.67)]

def bite(x, y):
    return f'''\t(footprint "MouseBite"
\t\t(layer "F.Cu")
\t\t(uuid "{U.uuid4()}")
\t\t(at {round(x,3)} {round(y,3)})
\t\t(attr through_hole exclude_from_pos_files exclude_from_bom)
\t\t(pad "" np_thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size {BITE_D} {BITE_D})
\t\t\t(drill {BITE_D})
\t\t\t(layers "F&B.Cu" "*.Mask")
\t\t\t(uuid "{U.uuid4()}")
\t\t)
\t)'''

def positions():
    """toutes les positions de mouse-bite du clavier"""
    out = []
    xm = (KBD_BREAK_X + RAIL_R_X) / 2
    for y0, y1 in KBD_TABS_R:
        y = y0 + BITE_P/2
        while y < y1:
            out.append((xm, y)); y += BITE_P
    for y0, y1, x0, x1 in KBD_TABS_L:
        y = y0 + BITE_P/2
        while y < y1:
            f = (y - y0) / (y1 - y0)
            xc = x0 + (x1-x0)*f              # bord de la carte, en biais
            out.append(((RAIL_L_X + xc) / 2, y)); y += BITE_P
    return out

def pose(path):
    t = open(path).read()
    if '"MouseBite"' in t:
        n = t.count('"MouseBite"')
        print(f"  {path} : {n} mouse-bites deja poses, rien fait")
        return 0
    pts = positions()
    k = t.rstrip().rfind(")")
    t = t[:k] + "\n" + "\n".join(bite(x, y) for x, y in pts) + "\n" + t[k:]
    open(path, 'w').write(t)
    print(f"  {path} : {len(pts)} mouse-bites poses "
          f"({len(KBD_TABS_R)} pattes a droite, {len(KBD_TABS_L)} a gauche)")
    return len(pts)

if __name__ == '__main__':
    pose(sys.argv[1] if len(sys.argv) > 1 else "hardware/pcb/niphar.kicad_pcb")
