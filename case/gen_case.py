# Niphargus case, left half — the outline is read from the SVG drawn by Mae.
# freecad --console gen_case.py
import sys, re, math, os

LOG = open("/tmp/gen_case.log", "w", buffering=1)
def say(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")

# Chemins deduits de l'emplacement du script. Ils etaient absolus et pointaient
# vers .../GitHub/rili, l'ancien nom du projet : plus rien ne tournait apres le
# renommage. NIPHAR_CASE_OUT permet de forcer une autre sortie.
HERE   = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUTDIR = os.environ.get("NIPHAR_CASE_OUT", HERE)
REPO   = os.path.dirname(OUTDIR)
SRC    = f"{OUTDIR}/case_outline.svg"

# ── GARDE-FOU ───────────────────────────────────────────────────────────────
# Depuis le passage en PartDesign, niphar-case-left.FCStd est la SOURCE DE
# VERITE : il s'edite dans FreeCAD, et ce script l'ecraserait. Il ne sert plus
# qu'a re-amorcer le modele depuis le SVG et le PCB, ce qui efface toutes les
# retouches faites a la main.
#   - pour sortir les DXF/STEP/STL apres une edition : freecadcmd export_case.py
#   - pour vraiment re-amorcer :  NIPHAR_RESEED=1 freecadcmd gen_case.py
_FCSTD = f"{OUTDIR}/niphar-case-left.FCStd"
if os.path.exists(_FCSTD) and not os.environ.get("NIPHAR_RESEED"):
    # freecadcmd avale le message de sys.exit : on l'imprime nous-memes
    print(f"\n*** {_FCSTD} existe deja et fait foi. ***\n"
          f"  exporter les fichiers de fab : freecadcmd export_case.py\n"
          f"  re-amorcer malgre tout       : NIPHAR_RESEED=1 freecadcmd gen_case.py\n",
          flush=True)
    sys.exit(1)
# ────────────────────────────────────────────────────────────────────────────
PCB    = f"{REPO}/hardware/pcb/niphar.kicad_pcb"

# --- cotes ---
H        = 8.5     # cadre alu
T_PLATE  = 2.0     # plaques polycarbonate
H_TOP    = 3.4     # PCB -> dessous de la plaque haute
T_PCB    = 1.6
VIS_D    = 3.2     # trous de vis du sandwich (lus dans le SVG)
# trous de montage M3 de la carte, releves sur niphar.kicad_pcb (origine = centre, verifie)
PCB_M3   = [(40.25, 49.63), (43.65, 68.23), (139.45, 40.33), (157.85, 94.03)]
PCB_M3_D = 3.2
MX_HOLE  = 14.0
Z_PCB_TOP = H - H_TOP          # 5.1
Z_PCB_BOT = Z_PCB_TOP - T_PCB  # 3.5
# (nom, x, y, largeur, z0, z1, profondeur)
# profondeur None => calculee, distance au bord + 12 mm de marge.
# TRRS : profondeur 16 mm et decalage lateral de 1 mm releves au banc sur
# l'impression 3D. Le y vaut donc 81,23 et non les 80,23 de J6 : la decoche ne
# tombe PAS sur l'origine de l'empreinte du jack.
# La hauteur reste z 5,1 -> 8,5 (3,4 mm) : le jack est pose sur le DESSUS du
# PCB (Z_PCB_TOP = 5,1), donc encocher plus bas retire de la matiere du cadre
# la ou il n'y a rien a degager. Une decoche de 7 mm calee a 2 mm du bas avait
# ete essayee : elle descend 3,1 mm sous le jack et deborde de 0,5 mm le haut
# du cadre (8,5), qui ne peut pas la contenir.
OPENINGS = [
    ("USB_C",  181.36, 26.38, 9.6, Z_PCB_TOP - 0.3, Z_PCB_TOP + 3.9, None),
    ("TRRS",   186.86, 81.23, 7.5, Z_PCB_TOP,       H,               16.0),
    ("SWITCH",  27.76, 75.48, 9.0, 0.5,             Z_PCB_BOT,       None),
]
# calage valide a 0,009 mm sur les 26 decoupes de touches
DX, DY = -28.030, -137.600

import FreeCAD as App
import Part
from FreeCAD import Vector

def P(x, y, z=0.0):
    return Vector(x, -y, z)        # KiCad y vers le bas -> repere direct

# ---------------- lecture du SVG ----------------
def arc_pts(p0, rx, ry, phi, large, sweep, p1, n=16):
    """arc elliptique SVG -> points"""
    if rx == 0 or ry == 0:
        return [p1]
    phi = math.radians(phi)
    cs, sn = math.cos(phi), math.sin(phi)
    dx2, dy2 = (p0[0]-p1[0])/2.0, (p0[1]-p1[1])/2.0
    x1 =  cs*dx2 + sn*dy2
    y1 = -sn*dx2 + cs*dy2
    rx, ry = abs(rx), abs(ry)
    lam = x1*x1/(rx*rx) + y1*y1/(ry*ry)
    if lam > 1:
        s = math.sqrt(lam); rx *= s; ry *= s
    num = rx*rx*ry*ry - rx*rx*y1*y1 - ry*ry*x1*x1
    den = rx*rx*y1*y1 + ry*ry*x1*x1
    co = math.sqrt(max(num, 0)/den) if den else 0.0
    if large == sweep:
        co = -co
    cxp, cyp = co*rx*y1/ry, -co*ry*x1/rx
    cx = cs*cxp - sn*cyp + (p0[0]+p1[0])/2.0
    cy = sn*cxp + cs*cyp + (p0[1]+p1[1])/2.0
    def ang(ux, uy, vx, vy):
        d = (ux*vx + uy*vy) / (math.hypot(ux, uy)*math.hypot(vx, vy))
        a = math.acos(max(-1, min(1, d)))
        return -a if ux*vy - uy*vx < 0 else a
    th0 = ang(1, 0, (x1-cxp)/rx, (y1-cyp)/ry)
    dth = ang((x1-cxp)/rx, (y1-cyp)/ry, (-x1-cxp)/rx, (-y1-cyp)/ry)
    if not sweep and dth > 0:
        dth -= 2*math.pi
    elif sweep and dth < 0:
        dth += 2*math.pi
    out = []
    for i in range(1, n+1):
        th = th0 + dth*i/n
        out.append((cs*rx*math.cos(th) - sn*ry*math.sin(th) + cx,
                    sn*rx*math.cos(th) + cs*ry*math.sin(th) + cy))
    return out

def arc_params(p0, rx, ry, phi, large, sweep, p1):
    """arc SVG circulaire -> (cx, cy, r, th0, dth). Meme math que arc_pts, mais
    on garde les parametres au lieu d'echantillonner."""
    phi = math.radians(phi)
    cs, sn = math.cos(phi), math.sin(phi)
    dx2, dy2 = (p0[0]-p1[0])/2.0, (p0[1]-p1[1])/2.0
    x1 =  cs*dx2 + sn*dy2
    y1 = -sn*dx2 + cs*dy2
    rx, ry = abs(rx), abs(ry)
    lam = x1*x1/(rx*rx) + y1*y1/(ry*ry)
    if lam > 1:
        sc = math.sqrt(lam); rx *= sc; ry *= sc
    num = rx*rx*ry*ry - rx*rx*y1*y1 - ry*ry*x1*x1
    den = rx*rx*y1*y1 + ry*ry*x1*x1
    co = math.sqrt(max(num, 0)/den) if den else 0.0
    if large == sweep:
        co = -co
    cxp, cyp = co*rx*y1/ry, -co*ry*x1/rx
    cx = cs*cxp - sn*cyp + (p0[0]+p1[0])/2.0
    cy = sn*cxp + cs*cyp + (p0[1]+p1[1])/2.0
    def ang(ux, uy, vx, vy):
        d_ = (ux*vx + uy*vy) / (math.hypot(ux, uy)*math.hypot(vx, vy))
        a = math.acos(max(-1, min(1, d_)))
        return -a if ux*vy - uy*vx < 0 else a
    th0 = ang(1, 0, (x1-cxp)/rx, (y1-cyp)/ry)
    dth = ang((x1-cxp)/rx, (y1-cyp)/ry, (-x1-cxp)/rx, (-y1-cyp)/ry)
    if not sweep and dth > 0:
        dth -= 2*math.pi
    elif sweep and dth < 0:
        dth += 2*math.pi
    return cx, cy, rx, th0, dth

def parse_d(d):
    cur, cmds = None, []
    for c, v in re.findall(r'([MmLlHhVvCcSsQqAaZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)', d):
        if c:
            cur = c; cmds.append([c, []])
        elif cur:
            cmds[-1][1].append(float(v))
    pts, p, start, pc2 = [], (0.0, 0.0), None, None
    def bez(a, b, c, e, n=12):
        return [((1-t)**3*a[0] + 3*(1-t)**2*t*b[0] + 3*(1-t)*t*t*c[0] + t**3*e[0],
                 (1-t)**3*a[1] + 3*(1-t)**2*t*b[1] + 3*(1-t)*t*t*c[1] + t**3*e[1])
                for t in [i/n for i in range(1, n+1)]]
    for c, a in cmds:
        C, rel, i = c.upper(), c.islower(), 0
        if C == 'Z':
            if start: pts.append(start)
            continue
        need = {'M':2,'L':2,'H':1,'V':1,'C':6,'S':4,'Q':4,'A':7}[C]
        while i + need <= len(a):
            v = a[i:i+need]; i += need
            if C in ('M', 'L'):
                q = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1]); pts.append(q)
                if C == 'M' and start is None: start = q
                if C == 'M': C = 'L'
            elif C == 'H':
                q = (p[0]+v[0], p[1]) if rel else (v[0], p[1]); pts.append(q)
            elif C == 'V':
                q = (p[0], p[1]+v[0]) if rel else (p[0], v[0]); pts.append(q)
            elif C == 'A':
                q = (p[0]+v[5], p[1]+v[6]) if rel else (v[5], v[6])
                pts += arc_pts(p, v[0], v[1], v[2], int(v[3]), int(v[4]), q)
            elif C == 'C':
                c1 = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                c2 = (p[0]+v[2], p[1]+v[3]) if rel else (v[2], v[3])
                q  = (p[0]+v[4], p[1]+v[5]) if rel else (v[4], v[5])
                pts += bez(p, c1, c2, q); pc2 = c2
            elif C == 'S':
                c1 = (2*p[0]-pc2[0], 2*p[1]-pc2[1]) if pc2 else p
                c2 = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                q  = (p[0]+v[2], p[1]+v[3]) if rel else (v[2], v[3])
                pts += bez(p, c1, c2, q); pc2 = c2
            else:
                cq = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                q  = (p[0]+v[2], p[1]+v[3]) if rel else (v[2], v[3])
                pts += bez(p, (p[0]+2/3*(cq[0]-p[0]), p[1]+2/3*(cq[1]-p[1])),
                              (q[0]+2/3*(cq[0]-q[0]), q[1]+2/3*(cq[1]-q[1])), q)
            if C not in ('C', 'S'): pc2 = None
            p = q
    out = []
    for q in pts:
        if not out or math.hypot(q[0]-out[-1][0], q[1]-out[-1][1]) > 1e-4:
            out.append((q[0]+DX, q[1]+DY))
    return out

def wire_of(pts):
    q = list(pts)
    if math.hypot(q[0][0]-q[-1][0], q[0][1]-q[-1][1]) > 1e-4:
        q.append(q[0])
    es = [Part.LineSegment(P(q[i][0], q[i][1]), P(q[i+1][0], q[i+1][1])).toShape()
          for i in range(len(q)-1)]
    return Part.Wire(Part.sortEdges(es)[0])

def bbox(pts):
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return min(xs), max(xs), min(ys), max(ys)

txt = open(SRC).read()
# on garde la chaine d d'origine : les esquisses parametriques la relisent pour
# conserver arcs et beziers, au lieu des centaines de segments de parse_d.
raw = [(m, parse_d(m)) for m in re.findall(r'<path[^>]*\bd="([^"]+)"', txt)]
raw = [p for p in raw if len(p[1]) >= 4]
say(f"SVG source : {len(raw)} contours lus")

vis, touches, gros, accu = [], [], [], None
for _d, pts in raw:
    x0, x1, y0, y1 = bbox(pts)
    w, h = x1-x0, y1-y0
    if abs(w - VIS_D) < 0.3 and abs(h - VIS_D) < 0.3:
        vis.append(((x0+x1)/2, (y0+y1)/2))
    elif 12.0 < w < 22.0 and 12.0 < h < 22.0:
        touches.append(pts)
    elif w > 100:
        gros.append((w*h, pts, _d))
    elif 25 < w < 60:
        accu = pts
gros.sort(key=lambda a: -a[0])
say(f"   {len(vis)} trous de vis, {len(touches)} decoupes de touches, "
    f"{len(gros)} grands contours, accu={'oui' if accu else 'NON'}")
if len(gros) < 3 or accu is None:
    sys.exit("SVG incomplet")
outer_p, inner_p, pcb_p = gros[0][1], gros[1][1], gros[2][1]
outer_d, inner_d = gros[0][2], gros[1][2]
for nm, pp in (("exterieur", outer_p), ("interieur", inner_p), ("PCB", pcb_p), ("accu", accu)):
    x0, x1, y0, y1 = bbox(pp)
    say(f"   {nm:10s} x {x0:7.2f}..{x1:7.2f}  y {y0:7.2f}..{y1:7.2f}  ({x1-x0:.2f} x {y1-y0:.2f})")
for k, (vx, vy) in enumerate(vis):
    say(f"   vis {k+1} : ({vx:.2f}, {vy:.2f})")

outer = wire_of(outer_p)
inner = wire_of(inner_p)
w_accu = wire_of(accu)
say(f"contours fermes : ext={outer.isClosed()} int={inner.isClosed()} accu={w_accu.isClosed()}")

# ---------------- cadre ----------------
f_out, f_in = Part.Face(outer), Part.Face(inner)
frame = f_out.cut(f_in).extrude(Vector(0, 0, H))
frame = frame.cut(Part.Face(w_accu).extrude(Vector(0, 0, H + 2)))
say(f"cadre brut : {frame.Volume/1000:.1f} cm3")

# ouvertures dans le chant
def exit_dir(kx, ky):
    """normale sortante du bord le plus proche — donne un percage perpendiculaire au chant"""
    c = P(kx, ky)
    ctr = outer.BoundBox.Center
    best, nrm, dist = 1e9, Vector(1, 0, 0), 0.0
    for e in outer.Edges:
        pts = e.discretize(max(2, int(e.Length) + 2))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i+1]
            ab = Vector(b.x-a.x, b.y-a.y, 0)
            L2 = ab.x*ab.x + ab.y*ab.y
            if L2 < 1e-9:
                continue
            u = max(0.0, min(1.0, ((c.x-a.x)*ab.x + (c.y-a.y)*ab.y) / L2))
            px, py = a.x + u*ab.x, a.y + u*ab.y
            d = math.hypot(c.x-px, c.y-py)
            if d < best:
                n = Vector(ab.y, -ab.x, 0)
                n.normalize()
                if n.dot(Vector(px-ctr.x, py-ctr.y, 0)) < 0:
                    n = n.multiply(-1)
                best, nrm, dist = d, n, d
    return nrm, dist

for nm, kx, ky, w, z0, z1, prof in OPENINGS:
    d, dist = exit_dir(kx, ky)
    ang = math.degrees(math.atan2(d.y, d.x))
    # prof = penetration REELLE depuis le bord exterieur, pas la longueur de la
    # boite. Le bord est a `dist` du point du connecteur : on demarre donc a
    # dist - prof et on ressort de 2 mm pour garantir le debouche. Sans ca les
    # mm demandes partent dans le vide au-dela du chant.
    if prof:
        b = Part.makeBox(prof + 2, w, z1 - z0, Vector(dist - prof, -w/2, z0))
    else:
        b = Part.makeBox(dist + 12, w, z1 - z0, Vector(-4, -w/2, z0))
    b.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang)
    b.translate(P(kx, ky, 0))
    before = frame.Volume
    frame = frame.cut(b)
    say(f"   ouverture {nm}: bord a {dist:.2f} mm, dir {ang:.0f}deg, "
        f"z {z0:.1f}->{z1:.1f}, {(before-frame.Volume):.0f} mm3 retires")

for vx, vy in vis:
    frame = frame.cut(Part.makeCylinder(VIS_D/2, H + 4, P(vx, vy, -2), Vector(0, 0, 1)))
say(f"cadre perce : {frame.Volume/1000:.1f} cm3 (~{frame.Volume/1000*2.7:.0f} g d'alu)")
say(f"cadre : {len(frame.Solids)} solide(s), valide={frame.isValid()}")

# ---------------- plaques ----------------
def plate(z0):
    p = f_out.extrude(Vector(0, 0, T_PLATE))
    p.translate(Vector(0, 0, z0))
    for vx, vy in vis:
        p = p.cut(Part.makeCylinder(VIS_D/2, T_PLATE + 4, P(vx, vy, z0 - 2), Vector(0, 0, 1)))
    return p

top = plate(H)
for hx, hy in PCB_M3:
    top = top.cut(Part.makeCylinder(PCB_M3_D/2, T_PLATE + 4, P(hx, hy, H - 2), Vector(0, 0, 1)))
say(f"plaque haute : {len(PCB_M3)} trous M3 de la carte (H5-H8)")
for pts in touches:
    top = top.cut(Part.Face(wire_of(pts)).extrude(Vector(0, 0, T_PLATE + 4)).
                  translated(Vector(0, 0, H - 2)))
# fenetre pour l'accu qui depasse
top = top.cut(Part.Face(w_accu).extrude(Vector(0, 0, T_PLATE + 4)).
              translated(Vector(0, 0, H - 2)))
# le jack sort par le dessus
for nm, kx, ky, w, z0, z1, prof in OPENINGS:
    if nm != 'TRRS':
        continue
    d, dist = exit_dir(kx, ky)
    # traversant sur toute l'epaisseur : une decoupe laser passe ou ne passe pas,
    # elle ne s'arrete pas a mi-epaisseur comme le fraisage du cadre.
    if prof:
        b = Part.makeBox(prof + 2, w, T_PLATE + 4, Vector(dist - prof, -w/2, 0))
    else:
        b = Part.makeBox(dist + 12, w, T_PLATE + 4, Vector(-4, -w/2, 0))
    b.rotate(Vector(0, 0, 0), Vector(0, 0, 1), math.degrees(math.atan2(d.y, d.x)))
    b.translate(P(kx, ky, H - 2))
    top = top.cut(b)
# degagements imposes : module P4 et connecteur FPC de l'ecran
# emprise REELLE lue sur la carte : l'origine du footprint n'est pas son centre
# (U16 : 20,51 mm de decalage — verifie sur les pads)
DEGAGE_HAUT = [
    ("module_P4",        172.16, 53.68,   0.0, 27.8, 28.2, 0.5),
    ("connecteur_ecran", 171.46, 69.98,  90.0,  1.7, 11.9, 1.0),   # J12, header 1x05
]
for nm, kx, ky, rot, w, h, jeu in DEGAGE_HAUT:
    b = Part.makeBox(w + 2*jeu, h + 2*jeu, T_PLATE + 4,
                     Vector(-(w + 2*jeu)/2, -(h + 2*jeu)/2, 0))
    b.rotate(Vector(0, 0, 0), Vector(0, 0, 1), -rot)
    b.translate(P(kx, ky, H - 2))
    before = top.Volume
    top = top.cut(b)
    say(f"   degagement {nm}: {w+2*jeu:.1f} x {h+2*jeu:.1f} mm a ({kx:.1f},{ky:.1f}), "
        f"{(before-top.Volume)/T_PLATE:.0f} mm2 retires")
say(f"plaque haute : {len(touches)} decoupes de touches + {len(vis)} vis + fenetre accu "
    f"+ {len(DEGAGE_HAUT)} degagements")

bot = plate(-T_PLATE)
for hx, hy in PCB_M3:
    bot = bot.cut(Part.makeCylinder(PCB_M3_D/2, T_PLATE + 4, P(hx, hy, -T_PLATE - 2), Vector(0, 0, 1)))
say(f"plaque basse : {len(vis)} vis + {len(PCB_M3)} trous M3 de la carte")

# Acces au connecteur de programmation de l'ESP32-S3, par le dessous.
# J1 est en B.Cu (sous la carte) et porte les nets /s3/* : c'est celui de la
# moitie GAUCHE. J2, meme empreinte, porte les nets /right/* — les deux moities
# sont cote a cote dans niphar.kicad_pcb, ce ne sont pas deux variantes en
# miroir. Pour le boitier droit, utiliser J2 a (227.471, 41.050).
#
# Comme pour DEGAGE_HAUT, on vise le CENTRE reel et non l'origine de
# l'empreinte : J1 est a (151.990, 40.648) mais ses pastilles sont centrees
# 1,42 mm plus loin. Transform verifie sur J12, qui redonne la valeur deja
# retenue pour connecteur_ecran.
# Jeu genereux : ce n'est pas un simple degagement, il faut y passer un clip ou
# des pointes de test.
DEGAGE_BAS = [
    ("prog_S3", 153.26, 41.28, -90.0, 5.0, 10.0, 0.5),   # J1, header 2x03 pas 1,27
    # 5 x 10 = le connecteur AVEC sa partie plastique, mesure par Mae. Le cuivre
    # seul ne fait que 2,27 x 3,54 : c'est le capot qui impose l'ouverture.
    # Le 10 est place sur le local Y, l'axe des 3 rangees — le capot est plus
    # long du cote ou il y a le plus de broches.
]
for nm, kx, ky, rot, w, h, jeu in DEGAGE_BAS:
    b = Part.makeBox(w + 2*jeu, h + 2*jeu, T_PLATE + 4,
                     Vector(-(w + 2*jeu)/2, -(h + 2*jeu)/2, 0))
    b.rotate(Vector(0, 0, 0), Vector(0, 0, 1), -rot)
    b.translate(P(kx, ky, -T_PLATE - 2))
    before = bot.Volume
    bot = bot.cut(b)
    say(f"   degagement {nm}: {w+2*jeu:.1f} x {h+2*jeu:.1f} mm a ({kx:.1f},{ky:.1f}), "
        f"{(before-bot.Volume)/T_PLATE:.0f} mm2 retires")

doc = App.newDocument("niphar_case_left")

# ---------------- arbre parametrique ----------------
# Les trois pieces sont construites comme un arbre Part (esquisses ->
# Part::Extrusion -> Part::MultiFuse -> Part::Cut) et non comme des formes
# figees. On peut donc ouvrir le FCStd, editer une esquisse ou une cote de
# boite, et recalculer — ce que des Part::Feature a forme figee ne permettent
# pas.
#
# Le script reste la source de verite : une regeneration realigne tout sur
# case_outline.svg et sur niphar.kicad_pcb, et ecrase les retouches faites a la
# main. Editer dans FreeCAD sert a ajuster et a essayer, pas a archiver.
#
# NB : le commentaire historique disait que Part::Extrusion crashait au-dela
# de ~110 elements. Verifie sur FreeCAD 1.1.3 : faux. L'extrusion passe a 66,
# 110, 300, 605 et 1000 segments, et sur des arcs.

def sk_loops(nm, loops, z=0.0):
    """une esquisse portant plusieurs contours fermes (les 26 touches tiennent
    ainsi dans un seul objet au lieu de 26)"""
    sk = doc.addObject('Sketcher::SketchObject', nm)
    sk.Label = nm
    sk.Placement = App.Placement(Vector(0, 0, z), App.Rotation(0, 0, 0, 1))
    geo = []
    for pts in loops:
        q = list(pts)
        if math.hypot(q[0][0]-q[-1][0], q[0][1]-q[-1][1]) > 1e-4:
            q.append(q[0])
        geo += [Part.LineSegment(App.Vector(q[i][0], -q[i][1], 0),
                                 App.Vector(q[i+1][0], -q[i+1][1], 0))
                for i in range(len(q)-1)]
    sk.addGeometry(geo, False)
    return sk

def parse_edges(d):
    """SVG -> geometrie FreeCAD en gardant arcs et beziers. C'est ce qui rend
    l'esquisse editable : le contour exterieur tombe de ~605 segments a ~66
    elements. parse_d, lui, echantillonne tout en droites (arc_pts n=16,
    bez n=12) — parfait pour le solide, inutilisable dans le Sketcher.
    Les beziers sont converties en B-splines : Sketcher refuse les
    Part::GeomBezierCurve mais accepte les B-splines, qui les representent
    exactement."""
    T = lambda x, y: App.Vector(x + DX, -(y + DY), 0)   # meme repere que P() apres DX/DY
    cur, cmds = None, []
    for c, v in re.findall(r'([MmLlHhVvCcSsQqAaZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)', d):
        if c:
            cur = c; cmds.append([c, []])
        elif cur:
            cmds[-1][1].append(float(v))
    geo, p, start, pc2 = [], (0.0, 0.0), None, None
    def seg(a, b):
        if math.hypot(a[0]-b[0], a[1]-b[1]) > 1e-7:
            geo.append(Part.LineSegment(T(*a), T(*b)))
    for c, a in cmds:
        C, rel, i = c.upper(), c.islower(), 0
        if C == 'Z':
            if start: seg(p, start); p = start
            continue
        need = {'M':2,'L':2,'H':1,'V':1,'C':6,'S':4,'Q':4,'T':2,'A':7}[C]
        while i + need <= len(a):
            v = a[i:i+need]; i += need
            if C in ('M', 'L'):
                q = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                if C == 'M':
                    if start is None: start = q
                    C = 'L'
                else:
                    seg(p, q)
            elif C == 'H':
                q = (p[0]+v[0], p[1]) if rel else (v[0], p[1]); seg(p, q)
            elif C == 'V':
                q = (p[0], p[1]+v[0]) if rel else (p[0], v[0]); seg(p, q)
            elif C == 'A':
                q = (p[0]+v[5], p[1]+v[6]) if rel else (v[5], v[6])
                cx, cy, r, th0, dth = arc_params(p, v[0], v[1], v[2],
                                                 int(v[3]), int(v[4]), q)
                circ = Part.Circle(T(cx, cy), App.Vector(0, 0, 1), r)
                # le repere cible est mirroir en y : un angle th devient -th et
                # le sens de parcours s'inverse. ArcOfCircle va toujours en sens
                # trigo de son premier angle vers le second.
                a0, a1 = -th0, -(th0 + dth)
                geo.append(Part.ArcOfCircle(circ, a1, a0) if dth > 0
                           else Part.ArcOfCircle(circ, a0, a1))
            elif C in ('C', 'S'):
                if C == 'C':
                    c1 = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                    c2 = (p[0]+v[2], p[1]+v[3]) if rel else (v[2], v[3])
                    q  = (p[0]+v[4], p[1]+v[5]) if rel else (v[4], v[5])
                else:
                    c1 = (2*p[0]-pc2[0], 2*p[1]-pc2[1]) if pc2 else p
                    c2 = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                    q  = (p[0]+v[2], p[1]+v[3]) if rel else (v[2], v[3])
                bz = Part.BezierCurve()
                bz.setPoles([T(*p), T(*c1), T(*c2), T(*q)])
                geo.append(bz.toBSpline()); pc2 = c2
            elif C in ('Q', 'T'):
                if C == 'Q':
                    c1 = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                    q  = (p[0]+v[2], p[1]+v[3]) if rel else (v[2], v[3])
                else:
                    c1 = (2*p[0]-pc2[0], 2*p[1]-pc2[1]) if pc2 else p
                    q  = (p[0]+v[0], p[1]+v[1]) if rel else (v[0], v[1])
                bz = Part.BezierCurve()
                bz.setPoles([T(*p), T(*c1), T(*q)])
                geo.append(bz.toBSpline()); pc2 = c1
            if C not in ('C', 'S', 'Q', 'T'):
                pc2 = None
            p = q
    return geo

def sk_edges(nm, d, secours, z=0.0):
    """esquisse a partir du SVG en gardant les courbes ; retombe sur le
    polygone echantillonne si la conversion ne ferme pas le contour"""
    sk = None
    try:
        sk = doc.addObject('Sketcher::SketchObject', nm)
        sk.Label = nm
        sk.Placement = App.Placement(Vector(0, 0, z), App.Rotation(0, 0, 0, 1))
        g = parse_edges(d)
        sk.addGeometry(g, False)
        sk.recompute()          # sans ca sk.Shape est vide en mode console
        edges = sk.Shape.Edges
        if not edges:
            raise ValueError("esquisse vide apres recompute")
        groupes = Part.sortEdges(edges)
        if len(groupes) != 1:
            raise ValueError(f"{len(groupes)} chaines d'aretes au lieu d'une")
        if not Part.Wire(groupes[0]).isClosed():
            raise ValueError("contour non ferme")
        say(f"   esquisse {nm} : {len(g)} elements (courbes conservees)")
        return sk
    except Exception as ex:
        say(f"   esquisse {nm} : conversion en courbes abandonnee ({ex}), "
            f"repli sur le polygone")
        if sk is not None:
            try: doc.removeObject(sk.Name)
            except Exception: pass
        return sk_loops(nm, [secours], z)

def sk_circles(nm, centres, r, z=0.0):
    sk = doc.addObject('Sketcher::SketchObject', nm)
    sk.Label = nm
    sk.Placement = App.Placement(Vector(0, 0, z), App.Rotation(0, 0, 0, 1))
    sk.addGeometry([Part.Circle(App.Vector(c[0], -c[1], 0), App.Vector(0, 0, 1), r)
                    for c in centres], False)
    return sk

def extrude(nm, base, length, z0=0.0):
    e = doc.addObject('Part::Extrusion', nm)
    e.Label = nm
    e.Base = base
    e.DirMode = 'Custom'
    e.Dir = Vector(0, 0, 1)
    e.LengthFwd = length
    e.Solid = True
    e.Placement = App.Placement(Vector(0, 0, z0), App.Rotation(0, 0, 0, 1))
    return e

def box(nm, lg, wd, ht, place):
    b = doc.addObject('Part::Box', nm)
    b.Label = nm
    b.Length, b.Width, b.Height = lg, wd, ht
    b.Placement = place
    return b

def fuse(nm, objs):
    f = doc.addObject('Part::MultiFuse', nm)
    f.Label = nm
    f.Shapes = objs
    return f

def cut(nm, base, tool):
    c = doc.addObject('Part::Cut', nm)
    c.Label = nm
    c.Base, c.Tool = base, tool
    return c

# --- esquisses pilotes ---
sk_ext  = sk_edges('esq_contour_ext', outer_d, outer_p)
sk_int  = sk_edges('esq_contour_int', inner_d, inner_p)
sk_accu = sk_loops('esq_fenetre_accu', [accu])
sk_tch  = sk_loops('esq_touches', touches)
sk_vis  = sk_circles('esq_vis', vis, VIS_D/2)
sk_m3   = sk_circles('esq_pcb_M3', PCB_M3, PCB_M3_D/2)

def opening_box(nm, kx, ky, w, z0, z1, prof, ht=None):
    """meme construction que la coupe figee, exprimee en Placement"""
    d, dist = exit_dir(kx, ky)
    ang = math.degrees(math.atan2(d.y, d.x))
    lg = (prof + 2) if prof else (dist + 12)
    x0 = (dist - prof) if prof else -4.0
    h  = ht if ht is not None else (z1 - z0)
    pl = (App.Placement(P(kx, ky, 0), App.Rotation(Vector(0, 0, 1), ang))
          * App.Placement(Vector(x0, -w/2, z0), App.Rotation(0, 0, 0, 1)))
    return box(nm, lg, w, h, pl)

def degage_box(nm, kx, ky, rot, w, h, jeu, z0):
    W, H_ = w + 2*jeu, h + 2*jeu
    pl = (App.Placement(P(kx, ky, z0), App.Rotation(Vector(0, 0, 1), -rot))
          * App.Placement(Vector(-W/2, -H_/2, 0), App.Rotation(0, 0, 0, 1)))
    return box(nm, W, H_, T_PLATE + 4, pl)

# --- cadre alu ---
p_frame = cut('frame_alu',
              cut('cadre_brut', extrude('ext_contour_ext', sk_ext, H),
                                extrude('ext_contour_int', sk_int, H)),
              fuse('outils_cadre',
                   [extrude('ext_accu_cadre', sk_accu, H + 2),
                    extrude('ext_vis_cadre', sk_vis, H + 4, -2)]
                   + [opening_box(f'ouv_{nm}', kx, ky, w, z0, z1, prof)
                      for nm, kx, ky, w, z0, z1, prof in OPENINGS]))

# --- plaque haute ---
outils_top = ([extrude('ext_vis_haut',   sk_vis, T_PLATE + 4, H - 2),
               extrude('ext_M3_haut',    sk_m3,  T_PLATE + 4, H - 2),
               extrude('ext_touches',    sk_tch, T_PLATE + 4, H - 2),
               extrude('ext_accu_haut',  sk_accu, T_PLATE + 4, H - 2)]
              + [opening_box(f'ouv_haut_{nm}', kx, ky, w, z0, z1, prof, ht=T_PLATE + 4)
                 for nm, kx, ky, w, z0, z1, prof in OPENINGS if nm == 'TRRS']
              + [degage_box(f'deg_haut_{nm}', kx, ky, rot, w, h, jeu, H - 2)
                 for nm, kx, ky, rot, w, h, jeu in DEGAGE_HAUT])
p_top = cut('plate_top_PC', extrude('ext_plaque_haute', sk_ext, T_PLATE, H),
            fuse('outils_plaque_haute', outils_top))

# --- plaque basse ---
outils_bot = ([extrude('ext_vis_bas', sk_vis, T_PLATE + 4, -T_PLATE - 2),
               extrude('ext_M3_bas',  sk_m3,  T_PLATE + 4, -T_PLATE - 2)]
              + [degage_box(f'deg_bas_{nm}', kx, ky, rot, w, h, jeu, -T_PLATE - 2)
                 for nm, kx, ky, rot, w, h, jeu in DEGAGE_BAS])
p_bot = cut('plate_bottom_PC', extrude('ext_plaque_basse', sk_ext, T_PLATE, -T_PLATE),
            fuse('outils_plaque_basse', outils_bot))

doc.recompute()

# --- verification : le parametrique doit redonner les formes figees ---
FIGE = {'frame_alu': frame, 'plate_top_PC': top, 'plate_bottom_PC': bot}
for o in (p_frame, p_top, p_bot):
    ref = FIGE[o.Name]
    try:
        vp, vr = o.Shape.Volume, ref.Volume
        ecart = abs(vp - vr)
        ok = o.Shape.isValid() and len(o.Shape.Solids) == 1 and ecart < 1.0
        say(f"   {o.Name:16s} parametrique {vp/1000:7.3f} cm3  vs fige {vr/1000:7.3f} cm3  "
            f"ecart {ecart:.3f} mm3  {'OK' if ok else 'DIVERGE'}")
        if not ok:
            o.Shape = ref
            say(f"   !! {o.Name} : arbre parametrique ecarte, forme figee conservee")
    except Exception as ex:
        say(f"   !! {o.Name} verification impossible ({ex})")

_finaux = {p_frame.Name, p_top.Name, p_bot.Name}
for o in doc.Objects:
    try:
        o.Visibility = o.Name in _finaux
    except Exception:
        pass

# --- esquisses de reference (contours a plat, pour mesurer et construire dessus) ---
# Le contour reste pilote par case_outline.svg ; ces esquisses en sont la trace
# dans FreeCAD. PAS de Pad dessus : PartDesign et Part::Extrusion crashent sur
# ces ~110 elements (verifie).
def add_sketch(nm, pts, z=0.0):
    try:
        sk = doc.addObject('Sketcher::SketchObject', nm)
        sk.Label = nm
        pl = App.Placement(Vector(0, 0, z), App.Rotation(0, 0, 0, 1))
        sk.Placement = pl
        q = list(pts)
        if math.hypot(q[0][0]-q[-1][0], q[0][1]-q[-1][1]) > 1e-4:
            q.append(q[0])
        geo = [Part.LineSegment(App.Vector(q[i][0], -q[i][1], 0),
                                App.Vector(q[i+1][0], -q[i+1][1], 0))
               for i in range(len(q)-1)]
        sk.addGeometry(geo, False)
        return sk
    except Exception as ex:
        say(f"   esquisse {nm} impossible ({ex})")
        return None

def add_circles(nm, centres, r, z=0.0):
    try:
        sk = doc.addObject('Sketcher::SketchObject', nm)
        sk.Label = nm
        sk.Placement = App.Placement(Vector(0, 0, z), App.Rotation(0, 0, 0, 1))
        sk.addGeometry([Part.Circle(App.Vector(c[0], -c[1], 0), App.Vector(0, 0, 1), r)
                        for c in centres], False)
        return sk
    except Exception as ex:
        say(f"   esquisse {nm} impossible ({ex})")
        return None

_sk = [add_sketch('esq_pcb', pcb_p)]   # seule reference sans equivalent parametrique
say(f"esquisse de reference PCB : {sum(1 for s_ in _sk if s_)} sur {len(_sk)}")

doc.recompute()

# ============================================================================
# Mode PartDesign : NIPHAR_PARTDESIGN=1 freecadcmd gen_case.py
# ----------------------------------------------------------------------------
# Sort un SECOND fichier, ou chaque piece est un PartDesign::Body : un Pad sur
# l'esquisse de contour, puis UNE POCHE PAR PERCEMENT, chacune pilotee par sa
# propre esquisse. C'est le geste FreeCAD normal — double-clic sur une poche,
# on edite son esquisse, ca recalcule.
#
# Ce fichier est une AMORCE : une fois genere, c'est lui la source de verite.
# Le lien avec niphar.kicad_pcb est rompu — les 26 touches, les trous M3 et les
# positions de connecteurs y sont figes. Un composant deplace sur le PCB ne s'y
# propagera plus. C'est le choix assume en echange de la vraie editabilite.
# ============================================================================
if True:   # amorcage PartDesign
    pdoc = App.newDocument("niphar_case_left_pd")

    def pd_body(nm):
        return pdoc.addObject('PartDesign::Body', nm)

    def pd_sk(body, nm, geo, place):
        sk = pdoc.addObject('Sketcher::SketchObject', nm)
        sk.Label = nm
        body.addObject(sk)
        sk.Placement = place
        sk.addGeometry(geo, False)
        pdoc.recompute()
        return sk

    def geo_loops(loops):
        g = []
        for pts in loops:
            q = list(pts)
            if math.hypot(q[0][0]-q[-1][0], q[0][1]-q[-1][1]) > 1e-4:
                q.append(q[0])
            g += [Part.LineSegment(App.Vector(q[i][0], -q[i][1], 0),
                                   App.Vector(q[i+1][0], -q[i+1][1], 0))
                  for i in range(len(q)-1)]
        return g

    def geo_circles(centres, r):
        return [Part.Circle(App.Vector(c[0], -c[1], 0), App.Vector(0, 0, 1), r)
                for c in centres]

    def geo_rect(w, h, cx=0.0, cy=0.0):
        p = [(cx-w/2, cy-h/2), (cx+w/2, cy-h/2), (cx+w/2, cy+h/2), (cx-w/2, cy+h/2)]
        return [Part.LineSegment(App.Vector(*p[i], 0), App.Vector(*p[(i+1) % 4], 0))
                for i in range(4)]

    def plan(z):
        return App.Placement(Vector(0, 0, z), App.Rotation(0, 0, 0, 1))

    def pd_pad(body, sk, length):
        f = pdoc.addObject('PartDesign::Pad', f'pad_{body.Name}')
        body.addObject(f); f.Profile = sk; f.Length = length
        pdoc.recompute(); return f

    def pd_poche(body, sk, nm, longueur=None, inverse=True):
        f = pdoc.addObject('PartDesign::Pocket', nm)
        body.addObject(f); f.Profile = sk
        if longueur is None:
            f.Type = 1                      # ThroughAll
        else:
            f.Type = 0; f.Length = longueur
        f.Reversed = inverse
        pdoc.recompute(); return f

    def esq_laterale(body, nm, kx, ky, w, z0, z1, prof):
        """esquisse verticale devant le chant, pour une poche d'ouverture"""
        d, dist = exit_dir(kx, ky)
        ang = math.degrees(math.atan2(d.y, d.x))
        lg = (prof if prof else dist + 8) + 2.0
        base = P(kx, ky, 0) + d.multiply(dist + 2.0)
        rot = App.Rotation(Vector(0, 0, 1), ang + 90) * App.Rotation(Vector(1, 0, 0), 90)
        sk = pd_sk(body, nm, geo_rect(w, z1 - z0, 0.0, (z0 + z1)/2), App.Placement(base, rot))
        return sk, lg

    # ---------- cadre alu ----------
    b_cadre = pd_body('frame_alu')
    pd_pad(b_cadre, pd_sk(b_cadre, 'esq_cadre_contour', parse_edges(outer_d), plan(0)), H)
    pd_poche(b_cadre, pd_sk(b_cadre, 'esq_cadre_interieur', parse_edges(inner_d), plan(0)),
             'poche_interieur')
    pd_poche(b_cadre, pd_sk(b_cadre, 'esq_cadre_accu', geo_loops([accu]), plan(0)),
             'poche_accu')
    pd_poche(b_cadre, pd_sk(b_cadre, 'esq_cadre_vis', geo_circles(vis, VIS_D/2), plan(0)),
             'poche_vis')
    for nm, kx, ky, w, z0, z1, prof in OPENINGS:
        sk, lg = esq_laterale(b_cadre, f'esq_ouv_{nm}', kx, ky, w, z0, z1, prof)
        pd_poche(b_cadre, sk, f'poche_ouv_{nm}', longueur=lg, inverse=False)

    # ---------- plaque haute ----------
    b_haut = pd_body('plate_top_PC')
    pd_pad(b_haut, pd_sk(b_haut, 'esq_haut_contour', parse_edges(outer_d), plan(H)), T_PLATE)
    for nm, geo in (('vis', geo_circles(vis, VIS_D/2)),
                    ('M3', geo_circles(PCB_M3, PCB_M3_D/2)),
                    ('touches', geo_loops(touches)),
                    ('accu', geo_loops([accu]))):
        pd_poche(b_haut, pd_sk(b_haut, f'esq_haut_{nm}', geo, plan(H)), f'poche_haut_{nm}')
    for nm, kx, ky, w, z0, z1, prof in OPENINGS:
        if nm != 'TRRS':
            continue
        d, dist = exit_dir(kx, ky)
        ang = math.degrees(math.atan2(d.y, d.x))
        lg = (prof if prof else dist + 8)
        rot = App.Rotation(Vector(0, 0, 1), ang)
        base = P(kx, ky, H) + d.multiply(dist + 2.0)
        sk = pd_sk(b_haut, f'esq_haut_ouv_{nm}',
                   geo_rect(lg + 2.0, w, -(lg + 2.0)/2, 0.0), App.Placement(base, rot))
        pd_poche(b_haut, sk, f'poche_haut_ouv_{nm}')
    for nm, kx, ky, rot, w, h, jeu in DEGAGE_HAUT:
        pl = App.Placement(P(kx, ky, H), App.Rotation(Vector(0, 0, 1), -rot))
        pd_poche(b_haut, pd_sk(b_haut, f'esq_haut_deg_{nm}',
                               geo_rect(w + 2*jeu, h + 2*jeu), pl), f'poche_haut_deg_{nm}')

    # ---------- plaque basse ----------
    b_bas = pd_body('plate_bottom_PC')
    pd_pad(b_bas, pd_sk(b_bas, 'esq_bas_contour', parse_edges(outer_d), plan(-T_PLATE)), T_PLATE)
    for nm, geo in (('vis', geo_circles(vis, VIS_D/2)),
                    ('M3', geo_circles(PCB_M3, PCB_M3_D/2))):
        pd_poche(b_bas, pd_sk(b_bas, f'esq_bas_{nm}', geo, plan(-T_PLATE)), f'poche_bas_{nm}')
    for nm, kx, ky, rot, w, h, jeu in DEGAGE_BAS:
        pl = App.Placement(P(kx, ky, -T_PLATE), App.Rotation(Vector(0, 0, 1), -rot))
        pd_poche(b_bas, pd_sk(b_bas, f'esq_bas_deg_{nm}',
                              geo_rect(w + 2*jeu, h + 2*jeu), pl), f'poche_bas_deg_{nm}')

    pdoc.recompute()
    say("PartDesign :")
    for b, ref in ((b_cadre, frame), (b_haut, top), (b_bas, bot)):
        try:
            v = b.Shape.Volume
            say(f"   {b.Name:16s} {v/1000:7.3f} cm3  vs reference {ref.Volume/1000:7.3f} cm3  "
                f"ecart {abs(v-ref.Volume):8.3f} mm3  solides={len(b.Shape.Solids)}  "
                f"features={len(b.Group)}")
        except Exception as ex:
            say(f"   {b.Name}: mesure impossible ({ex})")
    fpd = _FCSTD          # le PartDesign EST le modele desormais
    pdoc.saveAs(fpd)
    say(f"FCStd PartDesign : {fpd}")

fc = f"{OUTDIR}/niphar-case-left-booleens.FCStd"   # reference interne, pas le modele
st = f"{OUTDIR}/niphar-case-left.step"
doc.saveAs(fc)
# Les 3 pieces sont des Part::Cut depuis le passage en arbre parametrique :
# filtrer sur Part::Feature ne renvoyait plus rien et exportait un STEP vide.
PIECES = [p_frame, p_top, p_bot]
Part.export(PIECES, st)
for o in PIECES:
    b = o.Shape.BoundBox
    say(f"{o.Name:16s} {o.Shape.Volume/1000:6.1f} cm3  z {b.ZMin:6.2f}->{b.ZMax:6.2f}  "
        f"{b.XLength:.0f}x{b.YLength:.0f} mm  valide={o.Shape.isValid()} solides={len(o.Shape.Solids)}")
say(f"FCStd : {fc}")
say(f"STEP  : {st}")

# STL des 3 pieces (impression 3D). Gitignores, mais toujours presents sur disque.
try:
    import Mesh, MeshPart
    _n = 0
    for o in PIECES:
        m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05,
                                   AngularDeflection=0.15, Relative=False)
        m.write(f"{OUTDIR}/{o.Name}.stl")
        _n += 1
    say(f"STL   : {_n} fichiers")   # compte reel, le message etait en dur
except Exception as ex:
    say(f"STL non generes ({ex})")

# DXF des deux plaques polycarbonate, pour la decoupe laser.
# On coupe chaque solide a mi-epaisseur plutot que de prendre une face : la
# section donne le vrai profil traversant — contour exterieur, vis, trous M3,
# decoupes de touches, fenetre accu, degagements — en un seul jeu de contours.
# Le cadre alu n'est pas exporte : 8,5 mm d'epaisseur, ce n'est pas une piece
# de decoupe laser, et ses ouvertures sont a des hauteurs differentes.
#
# Ecriture directe en DXF R12 plutot que via importDXF : ce module tire la GUI
# et fait planter freecadcmd. R12 est aussi le dialecte le plus surement lu par
# les logiciels de decoupe. Cercles entiers -> CIRCLE (le decoupeur garde un
# vrai cercle pour sa compensation de saignee), le reste -> LINE.
def _dxf_write(path, wires, tol=0.02):
    e = []
    def line(a, b):
        e.append("0\nLINE\n8\n0\n10\n%.4f\n20\n%.4f\n30\n0.0\n"
                 "11\n%.4f\n21\n%.4f\n31\n0.0" % (a.x, a.y, b.x, b.y))
    n_circ = n_seg = 0
    for w in wires:
        for ed in w.Edges:
            crv = ed.Curve
            if isinstance(crv, Part.Circle) and ed.isClosed():
                c = crv.Center
                e.append("0\nCIRCLE\n8\n0\n10\n%.4f\n20\n%.4f\n30\n0.0\n40\n%.4f"
                         % (c.x, c.y, crv.Radius))
                n_circ += 1
            elif isinstance(crv, Part.Line):
                line(ed.Vertexes[0].Point, ed.Vertexes[-1].Point)
                n_seg += 1
            else:
                pts = ed.discretize(Deflection=tol)
                for i in range(len(pts) - 1):
                    line(pts[i], pts[i + 1])
                n_seg += len(pts) - 1
    open(path, "w").write("0\nSECTION\n2\nENTITIES\n"
                          + "".join(x + "\n" for x in e)
                          + "0\nENDSEC\n0\nEOF\n")
    return n_circ, n_seg

try:
    for _nm, _sh, _zmid in (("plate_top_PC",    top, H + T_PLATE/2),
                            ("plate_bottom_PC", bot, -T_PLATE/2)):
        _wires = _sh.slice(Vector(0, 0, 1), _zmid)
        if not _wires:
            say(f"DXF   : {_nm} — section vide a z={_zmid}, non genere")
            continue
        _comp = Part.Compound(_wires)
        _comp.translate(Vector(0, 0, -_zmid))          # a plat sur z = 0
        _p = f"{OUTDIR}/{_nm}.dxf"
        _c, _l = _dxf_write(_p, _comp.Wires)
        _bb = _comp.BoundBox
        say(f"DXF   : {_nm}.dxf — {len(_comp.Wires)} contours "
            f"({_c} cercles, {_l} segments), {_bb.XLength:.1f}x{_bb.YLength:.1f} mm")
except Exception as ex:
    say(f"DXF non generes ({ex})")

# Un document cree en --console n'a PAS de GuiDocument.xml : a l'ouverture,
# FreeCAD ne sait ni quoi afficher ni comment. On repasse dessus avec la GUI en
# mode offscreen pour poser visibilite et couleurs une bonne fois.
import subprocess, tempfile
_fix = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False)
_fix.write(f"""import FreeCAD as App, FreeCADGui as Gui
COL = {{'frame_alu': (0.72, 0.73, 0.75, 0),
        'plate_top_PC': (0.55, 0.75, 0.90, 55),
        'plate_bottom_PC': (0.55, 0.75, 0.90, 55)}}
VISIBLE = {{'frame_alu', 'plate_top_PC', 'plate_bottom_PC'}}
d = App.openDocument({fc!r})
for o in d.Objects:
    # arbre parametrique : seules les 3 pieces finales sont visibles, sinon on
    # ouvre le fichier sur une pile de boites de coupe posees sur les pieces.
    o.ViewObject.Visibility = o.Name in VISIBLE
    r, g, b, tr = COL.get(o.Name, (0.8, 0.8, 0.8, 0))
    o.ViewObject.ShapeColor = (r, g, b)
    o.ViewObject.Transparency = tr
d.save()
""")
_fix.close()
try:
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    subprocess.run(['freecad', _fix.name], env=env, timeout=900,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import zipfile
    ok = 'GuiDocument.xml' in zipfile.ZipFile(fc).namelist()
    say(f"vue enregistree dans le FCStd : {'oui' if ok else 'NON — le doc souvrira vide'}")
except Exception as ex:
    say(f"passe GUI impossible ({ex}) — le FCStd souvrira sans affichage")
finally:
    os.unlink(_fix.name)


# ---------------- plan de controle ----------------
def d_of(w):
    out = []
    for e in w.Edges:
        pts = e.discretize(2 if e.Length < 1.5 else 14)
        for k, v in enumerate(pts):
            out.append(("M " if not out else "L ") + f"{v.x:.2f},{-v.y:.2f}")
    return " ".join(out) + " Z"

LAY = [(1.0, "#cc3333", "sous la carte"), (4.0, "#3399cc", "hauteur PCB"), (7.0, "#33aa55", "au-dessus")]
cuts = []
for z, col, lab in LAY:
    try:
        for w in frame.slice(Vector(0, 0, 1), z):
            cuts.append((col, d_of(w)))
    except Exception:
        pass
xs = [q[0] for q in outer_p]; ys = [q[1] for q in outer_p]
x0, y0 = min(xs)-8, min(ys)-24
w_, h_ = max(xs)-x0+8, max(ys)-y0+8
L = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_}mm" height="{h_}mm" '
     f'viewBox="{x0:.2f} {y0:.2f} {w_:.2f} {h_:.2f}">',
     f'<rect x="{x0}" y="{y0}" width="{w_}" height="{h_}" fill="#fdfdff"/>',
     '<path d="M ' + ' L '.join(f'{q[0]:.2f},{q[1]:.2f}' for q in pcb_p) +
     ' Z" fill="none" stroke="#ccc" stroke-width="0.3" stroke-dasharray="2,1.5"/>']
for pts in touches:
    L.append('<path d="M ' + ' L '.join(f'{q[0]:.2f},{q[1]:.2f}' for q in pts) +
             ' Z" fill="none" stroke="#dcdcdc" stroke-width="0.3"/>')
for col, d in cuts:
    L.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="0.45"/>')
L.append('<path d="M ' + ' L '.join(f'{q[0]:.2f},{q[1]:.2f}' for q in accu) +
         ' Z" fill="#ffd9a0" fill-opacity="0.4" stroke="#e08000" stroke-width="0.5"/>')
for k, (vx, vy) in enumerate(vis):
    L.append(f'<circle cx="{vx:.2f}" cy="{vy:.2f}" r="{VIS_D/2:.2f}" fill="#fff" '
             'stroke="#cc0000" stroke-width="0.4"/>')
    L.append(f'<text x="{vx:.2f}" y="{vy-2.6:.2f}" font-size="3.2" fill="#c00" '
             f'text-anchor="middle">V{k+1}</text>')
for hx, hy in PCB_M3:
    L.append(f'<circle cx="{hx:.2f}" cy="{hy:.2f}" r="{PCB_M3_D/2:.2f}" fill="#fff" '
             'stroke="#0080c0" stroke-width="0.4"/>')
for nm, kx, ky, *_ in OPENINGS:
    L.append(f'<circle cx="{kx:.2f}" cy="{ky:.2f}" r="1.5" fill="none" stroke="#bb00ff" stroke-width="0.4"/>')
    L.append(f'<text x="{kx-2.5:.2f}" y="{ky-2.5:.2f}" font-size="3.8" fill="#bb00ff" '
             f'text-anchor="end">{nm}</text>')
ty = y0 + 6
L.append(f'<text x="{x0+3:.1f}" y="{ty:.1f}" font-size="5.5" fill="#111">'
         'Niphargus — cadre gauche, contour dessine par Mae</text>')
for i, (z, col, lab) in enumerate(LAY):
    xx = x0 + 3 + i*48
    L.append(f'<line x1="{xx:.1f}" y1="{ty+6:.1f}" x2="{xx+6:.1f}" y2="{ty+6:.1f}" stroke="{col}" stroke-width="1"/>')
    L.append(f'<text x="{xx+8:.1f}" y="{ty+7.4:.1f}" font-size="3.6" fill="#666">z={z:.0f} {lab}</text>')
L.append(f'<text x="{x0+3:.1f}" y="{ty+13:.1f}" font-size="3.6" fill="#666">'
         f'{len(vis)} vis du sandwich (rouge) - {len(PCB_M3)} trous M3 de la carte (bleu) - '
         'accu (orange) - ouvertures percees (violet)</text>')
L.append('</svg>')
open(f"{OUTDIR}/case_plan.svg", 'w').write("\n".join(L))
say(f"plan : {OUTDIR}/case_plan.svg")
