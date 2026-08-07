# Cadre Niphargus en PartDesign : esquisses editables + Pad/Pocket
# freecad --console gen_pd.py
import sys, re, math

LOG = open("/tmp/gen_pd.log", "w", buffering=1)
def say(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")

PCB = "/home/mae/Documents/GitHub/rili/rili/pcb/niphar.kicad_pcb"
OUTDIR = "/home/mae/Documents/GitHub/rili/boitier"

AX_MIRROR = 188.46048
Y_SPLIT = 125.0
X_RAIL = 15.0
SKIP_BOXES = [(157.5, 177.0, 21.0, 31.5)]     # decrochement antenne nRF24
BRIDGE_MAX = 20.0
WALL, FIT = 3.0, 0.5   # jeu 0,5 mm : tolerance fraisage PCB (+-0,2) + usinage (+-0,1)
H_TOP, T_PCB, H_UNDER = 3.4, 1.6, 3.5
H = H_TOP + T_PCB + H_UNDER                    # 8.5
M3_D = 3.2
T_PLATE = 2.0        # epaisseur des plaques PC
# --- logement accu 16340 le long du bord inferieur gauche ---
BATT_EDGE = (27.36, 89.996, 81.41, 80.32)   # segment de bord suivi par l'accu
BATT_D    = 17.5      # diametre de la poche (16,5 + jeu)
BATT_L    = 36.0      # longueur de la poche (34,5 + jeu)
BATT_OFF  = 11.0      # distance de l'axe au bord, VERS L'EXTERIEUR (accu a cote du PCB)
BATT_POS  = 0.45      # position le long du bord (0..1)
LID_T     = 2.0       # epaisseur de la trappe
Z_PCB_TOP = H - H_TOP
Z_PCB_BOT = Z_PCB_TOP - T_PCB

# nom, x_kicad, y_kicad, largeur, z0, z1
OPENINGS = [
    ("USB_C", 181.36, 26.38, 9.6, Z_PCB_TOP - 0.3, Z_PCB_TOP + 3.9),
    ("TRRS", 186.86, 80.23, 7.5, 0.0, H),          # pleine hauteur : passe que le jack soit dessus ou dessous
    ("SWITCH", 27.76, 75.48, 9.0, 0.5, Z_PCB_BOT),
]

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

t = open(PCB).read()
segs, arcs, holes, switches = [], [], [], []
for op in ('(gr_line', '(gr_arc'):
    for a, b in blocks(t, op):
        blk = t[a:b]
        if '(layer "Edge.Cuts")' not in blk:
            continue
        s = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk)
        e = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk)
        m = re.search(r'\(mid ([-\d.]+) ([-\d.]+)\)', blk)
        x1, y1, x2, y2 = float(s.group(1)), float(s.group(2)), float(e.group(1)), float(e.group(2))
        if max(x1, x2) > AX_MIRROR or max(y1, y2) > Y_SPLIT or min(x1, x2) < X_RAIL:
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
    if ('Hole' in lib or 'HOLE' in lib) and X_RAIL < x < AX_MIRROR and y < Y_SPLIT:
        holes.append((x, y))
    if lib.startswith('key:') and X_RAIL < x < AX_MIRROR and y < Y_SPLIT:
        rot = re.search(r'\(at [-\d.]+ [-\d.]+ ([-\d.]+)\)', blk)
        switches.append((x, y, float(rot.group(1)) if rot else 0.0))
say(f"contour brut : {len(segs)} segments, {len(arcs)} arcs, {len(holes)} trous M3, {len(switches)} switchs")

TOL = 0.05
reps = []
def rep(x, y):
    for rx, ry in reps:
        if abs(rx - x) < TOL and abs(ry - y) < TOL:
            return rx, ry
    reps.append((x, y))
    return x, y
s2, a2 = [], []
for x1, y1, x2, y2 in segs:
    p, q = rep(x1, y1), rep(x2, y2)
    if math.hypot(q[0]-p[0], q[1]-p[1]) >= TOL:
        s2.append((p[0], p[1], q[0], q[1]))
for x1, y1, xm, ym, x2, y2 in arcs:
    p, q = rep(x1, y1), rep(x2, y2)
    a2.append((p[0], p[1], xm, ym, q[0], q[1]))
segs, arcs = s2, a2
deg = {}
for x1, y1, x2, y2 in segs:
    for k in ((x1, y1), (x2, y2)):
        deg[k] = deg.get(k, 0) + 1
for x1, y1, xm, ym, x2, y2 in arcs:
    for k in ((x1, y1), (x2, y2)):
        deg[k] = deg.get(k, 0) + 1
free = [k for k, v in deg.items() if v == 1]
used = set()
for p in free:
    if p in used:
        continue
    cand = [q for q in free if q != p and q not in used]
    if not cand:
        continue
    q = min(cand, key=lambda z: math.hypot(z[0]-p[0], z[1]-p[1]))
    d = math.hypot(q[0]-p[0], q[1]-p[1])
    if d < BRIDGE_MAX:
        segs.append((p[0], p[1], q[0], q[1]))
        used.update((p, q))
say(f"contour recolle : {len(segs)} segments + {len(arcs)} arcs")

import FreeCAD as App
import Part
from FreeCAD import Vector

def P(x, y, z=0.0):
    return Vector(x, -y, z)

edges = [Part.LineSegment(P(*s[:2]), P(*s[2:])).toShape() for s in segs]
for x1, y1, xm, ym, x2, y2 in arcs:
    edges.append(Part.Arc(P(x1, y1), P(xm, ym), P(x2, y2)).toShape())
wires = [Part.Wire(g) for g in Part.sortEdges(edges)]
wires.sort(key=lambda w: -w.BoundBox.DiagonalLength)
wire = wires[0]
say(f"contour ferme : {wire.isClosed()} ; {len(wire.Edges)} aretes")
inner = wire.makeOffset2D(FIT)
outer = wire.makeOffset2D(WALL + FIT)
say("offsets ok")

doc = App.newDocument("niphar_cadre_gauche")

# --- cadre : solide calcule (contour issu du PCB, pas destine a etre edite) ---
frame_face = Part.Face(outer).cut(Part.Face(inner))
solid = frame_face.extrude(Vector(0, 0, H))
for hx, hy in holes:
    solid = solid.cut(Part.makeCylinder(M3_D/2, H + 10, P(hx, hy, -5), Vector(0, 0, 1)))
base = doc.addObject('Part::Feature', 'cadre_brut')
base.Shape = solid
say(f"cadre brut : {solid.Volume/1000:.1f} cm3")

# --- contour en esquisse, pour reference et retouches eventuelles ---
sk_ref = doc.addObject('Sketcher::SketchObject', 'contour_PCB_reference')
n = 0
for e in wire.Edges:
    c = e.Curve
    if isinstance(c, Part.Line):
        sk_ref.addGeometry(Part.LineSegment(e.Vertexes[0].Point, e.Vertexes[-1].Point), False)
        n += 1
    elif isinstance(c, Part.Circle):
        sk_ref.addGeometry(Part.ArcOfCircle(c, e.FirstParameter, e.LastParameter), False)
        n += 1
say(f"esquisse de reference : {n} elements")

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
    v = Vector(px - kx, -(py - ky), 0)
    v.normalize()
    return v, d

# --- ouvertures : esquisse verticale + extrusion (100% editables) ---
tools = []
for name, kx, ky, w, z0, z1 in OPENINGS:
    d, dist = exit_dir(kx, ky)
    X = Vector(-d.y, d.x, 0); Y = Vector(0, 0, 1); Z = d
    m = App.Matrix(X.x, Y.x, Z.x, kx,
                   X.y, Y.y, Z.y, -ky,
                   X.z, Y.z, Z.z, 0,
                   0, 0, 0, 1)
    sk = doc.addObject('Sketcher::SketchObject', 'esq_' + name)
    sk.Placement = App.Placement(m)
    pts = [(-w/2, z0), (w/2, z0), (w/2, z1), (-w/2, z1)]
    for i in range(4):
        sk.addGeometry(Part.LineSegment(Vector(pts[i][0], pts[i][1], 0),
                                        Vector(pts[(i+1) % 4][0], pts[(i+1) % 4][1], 0)), False)
    e = doc.addObject('Part::Extrusion', 'perce_' + name)
    e.Base = sk
    e.DirMode = "Normal"
    e.LengthFwd = 12.0
    e.LengthRev = 12.0
    e.Solid = True
    tools.append(e)
    say(f"ouverture {name} : bord a {dist:.2f} mm, larg {w} mm, z {z0:.1f}->{z1:.1f}")
doc.recompute()
for e in tools:
    say(f"   {e.Name} : {'OK' if hasattr(e,'Shape') and e.Shape.Volume > 0 else 'ECHEC'}")

fus = doc.addObject('Part::MultiFuse', 'ouvertures')
fus.Shapes = tools
cut = doc.addObject('Part::Cut', 'cadre')
cut.Base = base
cut.Tool = fus
doc.recompute()
# tout masquer sauf le resultat : les outils de coupe ne doivent pas apparaitre
for o in doc.Objects:
    try:
        o.Visibility = o.Name in ('cadre', 'plaque_haut_PC', 'plaque_bas_PC', 'logement_accu', 'trappe_accu')
    except Exception:
        pass
say("visibilite : seul 'cadre' est affiche")
doc.recompute()

# ---------------- plaques PC haut et bas ----------------
MX_HOLE = 14.0

plate_face = Part.Face(outer)
# plaque haute : decoupes des switchs
top = plate_face.extrude(Vector(0, 0, T_PLATE))
top.translate(Vector(0, 0, H))
for sx, sy, srot in switches:
    c = P(sx, sy, H - 1)
    b = Part.makeBox(MX_HOLE, MX_HOLE, T_PLATE + 2, Vector(-MX_HOLE/2, -MX_HOLE/2, 0))
    b.rotate(Vector(0, 0, 0), Vector(0, 0, 1), -srot)
    b.translate(c)
    top = top.cut(b)
for hx, hy in holes:
    top = top.cut(Part.makeCylinder(M3_D/2, T_PLATE + 4, P(hx, hy, H - 1), Vector(0, 0, 1)))
o_top = doc.addObject('Part::Feature', 'plaque_haut_PC')
o_top.Shape = top
say(f"plaque haute : {len(switches)} decoupes MX 14x14 + {len(holes)} trous M3")

# plaque basse : trous M3 + degagement du jack
bot = plate_face.extrude(Vector(0, 0, T_PLATE))
bot.translate(Vector(0, 0, -T_PLATE))
for hx, hy in holes:
    bot = bot.cut(Part.makeCylinder(M3_D/2, T_PLATE + 4, P(hx, hy, -T_PLATE - 1), Vector(0, 0, 1)))
for name, kx, ky, w, z0, z1 in OPENINGS:
    if name != 'TRRS':
        continue
    d, _ = exit_dir(kx, ky)
    ang = math.degrees(math.atan2(d.y, d.x))
    b = Part.makeBox(20, w, T_PLATE + 4, Vector(-10, -w/2, 0))
    b.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang)
    b.translate(P(kx, ky, -T_PLATE - 1))
    bot = bot.cut(b)
o_bot = doc.addObject('Part::Feature', 'plaque_bas_PC')
o_bot.Shape = bot
say("plaque basse : trous M3 + degagement jack")
doc.recompute()
for o in (o_top, o_bot):
    try:
        o.Visibility = True
    except Exception:
        pass

# ---------------- logement accu A COTE du PCB ----------------
ax, ay, bx, by = BATT_EDGE
Lb = math.hypot(bx-ax, by-ay)
ux, uy = (bx-ax)/Lb, (by-ay)/Lb
nx, ny = -uy, ux                     # normale VERS L'EXTERIEUR (hors du PCB)
cx = ax + ux*Lb*BATT_POS + nx*BATT_OFF
cy = ay + uy*Lb*BATT_POS + ny*BATT_OFF
ang3d = math.degrees(math.atan2(-uy, ux))
say(f"accu A COTE : centre ({cx:.1f}, {cy:.1f}) axe {ang3d:.1f}deg, {BATT_OFF} mm hors du bord")

BOSS_W = BATT_D + 5.0                # 22,5 mm de large
BOSS_L = BATT_L + 8.0                # 44 mm de long
Z_TOP_BOSS = H + T_PLATE             # affleure le dessus de la plaque haute
Z_BOT_BOSS = Z_TOP_BOSS - (BATT_D + 2.0)
say(f"bossage lateral : {BOSS_L:.0f} x {BOSS_W:.0f} mm, z {Z_BOT_BOSS:.1f} -> {Z_TOP_BOSS:.1f} "
    f"(depasse de {abs(Z_BOT_BOSS):.1f} mm sous le cadre)")

def placed_box(l, w, h, cx_k, cy_k, z0, angle):
    b = Part.makeBox(l, w, h, Vector(-l/2, -w/2, 0))
    b.rotate(Vector(0, 0, 0), Vector(0, 0, 1), angle)
    b.translate(P(cx_k, cy_k, z0))
    return b

boss = placed_box(BOSS_L, BOSS_W, Z_TOP_BOSS - Z_BOT_BOSS, cx, cy, Z_BOT_BOSS, ang3d)
axis = Vector(math.cos(math.radians(ang3d)), math.sin(math.radians(ang3d)), 0)
z_axe = Z_BOT_BOSS + 1.0 + BATT_D/2
cyl = Part.makeCylinder(BATT_D/2, BATT_L, P(cx, cy, z_axe) - axis*(BATT_L/2), axis)
# ouverture par le dessous pour glisser l'accu (fermee par la trappe)
slot = placed_box(BATT_L, BATT_D, BATT_D/2 + 1.0, cx, cy, Z_BOT_BOSS, ang3d)
boss_final = boss.cut(cyl).cut(slot)
o_boss = doc.addObject('Part::Feature', 'logement_accu')
o_boss.Shape = boss_final
say(f"logement accu : {boss_final.Volume/1000:.1f} cm3")

lid = placed_box(BOSS_L - 1, BOSS_W - 1, LID_T, cx, cy, Z_BOT_BOSS - LID_T, ang3d)
o_lid = doc.addObject('Part::Feature', 'trappe_accu')
o_lid.Shape = lid
say("trappe accu creee")
doc.recompute()

fc = f"{OUTDIR}/niphar-cadre-gauche.FCStd"
st = f"{OUTDIR}/niphar-cadre-gauche.step"
doc.saveAs(fc)
Part.export([cut, o_top, o_bot, o_boss, o_lid], st)
say(f"volume final : {cut.Shape.Volume/1000:.1f} cm3 (~{cut.Shape.Volume/1000*2.7:.0f} g)")
say(f"FCStd : {fc}")
say(f"STEP  : {st}")
