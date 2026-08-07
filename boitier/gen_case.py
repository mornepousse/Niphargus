# Génère le cadre alu du boîtier Niphargus (moitié gauche) en STEP.
# Lancement : freecad --console gen_frame.py
import sys, re, math
LOG = open("/tmp/gen_frame.log", "w", buffering=1)
def say(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    print(*a)

PCB = "/home/mae/Documents/GitHub/rili/rili/pcb/niphar.kicad_pcb"
OUT = "/tmp/claude-1000/-home-mae-Documents-GitHub-rili/80a807e1-d856-46ee-af0a-52292e43ca9c/scratchpad/case/niphar-cadre-gauche.step"

# ---- paramètres (tout est là) ----
AX_MIRROR = 188.46048     # axe du panneau : la moitié gauche est à x <
Y_SPLIT   = 125.0         # la moitié gauche est à y <
X_RAIL    = 15.0          # au-dela : la carte ; en deca : le rail du panneau
WALL      = 3.0           # épaisseur de paroi du cadre
FIT       = 0.2           # jeu autour du PCB
H_TOP     = 3.4           # PCB -> dessous de la plaque (norme MX)
T_PCB     = 1.6
H_UNDER   = 3.5           # sous la carte, partie courante
H_BATT    = 3.5           # = H_UNDER -> cadre plat (pas de logement pile pour l'instant)
BEVEL     = False         # True = cadre biseaute (logement pile), False = plat
BEVEL_FROM = 'arriere'    # 'arriere' | 'avant' | 'exterieur' | 'interieur'
M3_D      = 3.2
# zones ou le cadre NE suit PAS le contour du PCB (il passe droit) : (xmin,xmax,ymin,ymax)
SKIP_BOXES = [(157.5, 177.0, 21.0, 31.5)]   # decrochement d'antenne nRF24 : pas d'alu devant
BRIDGE_MAX = 20.0        # portee max d'un pont automatique

H_MIN = H_TOP + T_PCB + H_UNDER          # 8.5
H_MAX = H_TOP + T_PCB + H_BATT           # 22.5

def read_edges():
    t = open(PCB).read()
    def blocks(text, opener):
        out, i = [], 0
        while True:
            i = text.find(opener, i)
            if i < 0:
                return out
            depth, j, instr = 0, i, False
            while True:
                c = text[j]
                if instr:
                    if c == '\\':
                        j += 1
                    elif c == '"':
                        instr = False
                elif c == '"':
                    instr = True
                elif c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            out.append((i, j + 1))
            i = j
    segs, arcs, holes = [], [], []
    for op in ('(gr_line', '(gr_arc'):
        for a, b in blocks(t, op):
            blk = t[a:b]
            if '(layer "Edge.Cuts")' not in blk:
                continue
            s = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk)
            e = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk)
            m = re.search(r'\(mid ([-\d.]+) ([-\d.]+)\)', blk)
            x1, y1, x2, y2 = float(s.group(1)), float(s.group(2)), float(e.group(1)), float(e.group(2))
            if max(x1, x2) > AX_MIRROR or max(y1, y2) > Y_SPLIT:
                continue
            if min(x1, x2) < X_RAIL:      # rail gauche du panneau
                continue
            if any(bx0 <= min(x1, x2) and max(x1, x2) <= bx1 and by0 <= min(y1, y2) and max(y1, y2) <= by1
                   for bx0, bx1, by0, by1 in SKIP_BOXES):
                continue
            if m:
                arcs.append((x1, y1, float(m.group(1)), float(m.group(2)), x2, y2))
            else:
                segs.append((x1, y1, x2, y2))
    for a, b in blocks(t, '(footprint '):
        blk = t[a:b]
        lib = re.match(r'\(footprint "([^"]+)"', blk).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', blk)
        x, y = float(at.group(1)), float(at.group(2))
        if ('Hole' in lib or 'HOLE' in lib) and x < AX_MIRROR and y < Y_SPLIT:
            holes.append((x, y))
    return segs, arcs, holes

import FreeCAD as App
import Part
from FreeCAD import Vector

segs, arcs, holes = read_edges()
say(f"contour : {len(segs)} segments + {len(arcs)} arcs ; {len(holes)} trous M3")

def P(x, y, z=0.0):
    return Vector(x, -y, z)      # KiCad y vers le bas -> repère direct

# fusion des extremites proches (clustering) : recolle le contour sans le deformer
TOL = 0.05
reps = []
def rep(x, y):
    for rx, ry in reps:
        if abs(rx - x) < TOL and abs(ry - y) < TOL:
            return rx, ry
    reps.append((x, y))
    return x, y
segs2, arcs2 = [], []
for x1, y1, x2, y2 in segs:
    a = rep(x1, y1); b = rep(x2, y2)
    if math.hypot(b[0]-a[0], b[1]-a[1]) >= TOL:
        segs2.append((a[0], a[1], b[0], b[1]))
for x1, y1, xm, ym, x2, y2 in arcs:
    a = rep(x1, y1); b = rep(x2, y2)
    arcs2.append((a[0], a[1], xm, ym, b[0], b[1]))
say(f"points uniques : {len(reps)} ; segments {len(segs)} -> {len(segs2)} (micro-aretes fondues)")
segs, arcs = segs2, arcs2
deg = {}
for x1, y1, x2, y2 in segs:
    for k in ((x1, y1), (x2, y2)):
        deg[k] = deg.get(k, 0) + 1
for x1, y1, xm, ym, x2, y2 in arcs:
    for k in ((x1, y1), (x2, y2)):
        deg[k] = deg.get(k, 0) + 1
open_pts = [k for k, v in deg.items() if v == 1]
say(f"entailles de tabs a refermer : {len(open_pts)} extremites libres")
used = set()
for a in open_pts:
    if a in used:
        continue
    cands = [b for b in open_pts if b != a and b not in used]
    if not cands:
        continue
    b = min(cands, key=lambda q: math.hypot(q[0]-a[0], q[1]-a[1]))
    d = math.hypot(b[0]-a[0], b[1]-a[1])
    if d < BRIDGE_MAX:
        segs.append((a[0], a[1], b[0], b[1]))
        used.add(a); used.add(b)
        say(f"   pont {d:.1f} mm entre ({a[0]:.1f},{a[1]:.1f}) et ({b[0]:.1f},{b[1]:.1f})")
edges = [Part.LineSegment(P(x1, y1), P(x2, y2)).toShape() for x1, y1, x2, y2 in segs]
for x1, y1, xm, ym, x2, y2 in arcs:
    edges.append(Part.Arc(P(x1, y1), P(xm, ym), P(x2, y2)).toShape())
say(f"aretes construites : {len(edges)}")

loops = Part.sortEdges(edges)
wires = []
for grp in loops:
    try:
        w = Part.Wire(grp)
        wires.append(w)
    except Exception as ex:
        say("boucle ignoree :", ex)
wires.sort(key=lambda w: -w.BoundBox.DiagonalLength)
say(f"boucles trouvees : {len(wires)}")
for k, w in enumerate(wires):
    say(f"   boucle {k}: {len(w.Edges)} aretes, perimetre {w.Length:.1f} mm, fermee={w.isClosed()}")
wire = wires[0]
cutouts = wires[1:]
if not wire.isClosed():
    sys.exit("contour exterieur non ferme — abandon")

say("offset interieur...")
inner = wire.makeOffset2D(FIT)          # PCB + jeu
say("offset exterieur...")
outer = wire.makeOffset2D(WALL + FIT)   # + paroi
say("faces...")
frame_face = Part.Face(outer).cut(Part.Face(inner))
solid = frame_face.extrude(Vector(0, 0, H_MAX))


# ---------- direction de sortie : calculee depuis le bord le plus proche ----------
def exit_dir(kx, ky):
    best = None
    for x1, y1, x2, y2 in segs:
        dx, dy = x2 - x1, y2 - y1
        L2 = dx*dx + dy*dy
        u = 0 if L2 == 0 else max(0.0, min(1.0, ((kx-x1)*dx + (ky-y1)*dy) / L2))
        px, py = x1 + u*dx, y1 + u*dy
        d = math.hypot(px-kx, py-ky)
        if best is None or d < best[0]:
            best = (d, px, py)
    d, px, py = best
    ang = math.degrees(math.atan2(-(py-ky), px-kx))   # repere 3D (y inverse)
    return ang, d

Z_PCB_TOP = H_MIN - H_TOP
Z_PCB_BOT = Z_PCB_TOP - T_PCB

OPENINGS = [
    # nom,        x,      y,      largeur, z0,            z1,              profondeur
    ("USB_C",   181.36,  26.38,   9.6,  Z_PCB_TOP-0.3, Z_PCB_TOP+3.9,  14.0),
    ("TRRS",    186.86,  80.23,   7.5,  0.0,           Z_PCB_BOT,      14.0),
    ("SWITCH",   27.76,  75.48,   9.0,  0.5,           Z_PCB_BOT,      14.0),
]

import traceback
# ---------- document FreeCAD editable ----------
say("construction du document...")
doc = App.newDocument("niphar_case")

wref = doc.addObject("Part::Feature", "contour_PCB")
wref.Shape = wire

base = doc.addObject("Part::Feature", "cadre_brut")
base.Shape = solid

boxes = []
say("ouvertures (direction calculee automatiquement) :")
for name, kx, ky, w, z0, z1, depth in OPENINGS:
    ang, dist = exit_dir(kx, ky)
    b = doc.addObject("Part::Box", "ouv_" + name)
    b.Length = depth
    b.Width = w
    b.Height = z1 - z0
    rot = App.Rotation(App.Vector(0, 0, 1), ang)
    off = rot.multVec(App.Vector(0, -w/2.0, 0))
    b.Placement = App.Placement(App.Vector(kx + off.x, -ky + off.y, z0), rot)
    boxes.append(b)
    say(f"   {name:7s} bord a {dist:.2f} mm, sortie {ang:+.0f}deg, larg {w} mm, z {z0:.1f}->{z1:.1f}")

fus = doc.addObject("Part::MultiFuse", "ouvertures")
fus.Shapes = boxes
cut = doc.addObject("Part::Cut", "cadre")
cut.Base = base
cut.Tool = fus
doc.recompute()

# visibilite explicite (sinon rien ne s'affiche a l'ouverture d'un doc cree sans GUI)
for obj, vis in ((cut, True), (base, False), (fus, False), (wref, True)):
    try:
        obj.Visibility = vis
    except Exception as ex:
        say("visibilite non applicable :", ex)
doc.recompute()

FCSTD = OUT.replace(".step", ".FCStd")
doc.saveAs(FCSTD)
Part.export([cut], OUT)
say(f"volume final {cut.Shape.Volume/1000:.1f} cm3 (~{cut.Shape.Volume/1000*2.7:.0f} g)")
say(f"projet FreeCAD : {FCSTD}")
say(f"STEP          : {OUT}")
