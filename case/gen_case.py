# Niphargus case, left half — the outline is read from the SVG drawn by Mae.
# freecad --console gen_case.py
import sys, re, math, os

LOG = open("/tmp/gen_case.log", "w", buffering=1)
def say(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")

OUTDIR = "/home/mae/Documents/GitHub/rili/case"
SRC    = f"{OUTDIR}/case_outline.svg"
PCB    = "/home/mae/Documents/GitHub/rili/hardware/pcb/niphar.kicad_pcb"

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
OPENINGS = [
    ("USB_C",  181.36, 26.38, 9.6, Z_PCB_TOP - 0.3, Z_PCB_TOP + 3.9),
    ("TRRS",   186.86, 80.23, 7.5, Z_PCB_TOP, H),
    ("SWITCH",  27.76, 75.48, 9.0, 0.5, Z_PCB_BOT),
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
raw = [parse_d(m) for m in re.findall(r'<path[^>]*\bd="([^"]+)"', txt)]
raw = [p for p in raw if len(p) >= 4]
say(f"SVG source : {len(raw)} contours lus")

vis, touches, gros, accu = [], [], [], None
for pts in raw:
    x0, x1, y0, y1 = bbox(pts)
    w, h = x1-x0, y1-y0
    if abs(w - VIS_D) < 0.3 and abs(h - VIS_D) < 0.3:
        vis.append(((x0+x1)/2, (y0+y1)/2))
    elif 12.0 < w < 22.0 and 12.0 < h < 22.0:
        touches.append(pts)
    elif w > 100:
        gros.append((w*h, pts))
    elif 25 < w < 60:
        accu = pts
gros.sort(key=lambda a: -a[0])
say(f"   {len(vis)} trous de vis, {len(touches)} decoupes de touches, "
    f"{len(gros)} grands contours, accu={'oui' if accu else 'NON'}")
if len(gros) < 3 or accu is None:
    sys.exit("SVG incomplet")
outer_p, inner_p, pcb_p = gros[0][1], gros[1][1], gros[2][1]
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

for nm, kx, ky, w, z0, z1 in OPENINGS:
    d, dist = exit_dir(kx, ky)
    ang = math.degrees(math.atan2(d.y, d.x))
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
for nm, kx, ky, w, z0, z1 in OPENINGS:
    if nm != 'TRRS':
        continue
    d, dist = exit_dir(kx, ky)
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

doc = App.newDocument("niphar_case_left")
for nm, sh in (('frame_alu', frame), ('plate_top_PC', top), ('plate_bottom_PC', bot)):
    o = doc.addObject('Part::Feature', nm)
    o.Shape = sh
    o.Label = nm          # sinon le STEP nomme les 3 pieces d'apres le document
    try:
        o.Visibility = True
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

_sk = [add_sketch('esq_frame_outer', outer_p),
       add_sketch('esq_frame_inner', inner_p),
       add_sketch('esq_pcb', pcb_p),
       add_sketch('esq_battery', accu),
       add_circles('esq_screws', vis, VIS_D/2),
       add_circles('esq_pcb_M3', PCB_M3, PCB_M3_D/2)]
say(f"esquisses de reference : {sum(1 for s in _sk if s)} sur {len(_sk)}")

doc.recompute()
fc = f"{OUTDIR}/niphar-case-left.FCStd"
st = f"{OUTDIR}/niphar-case-left.step"
doc.saveAs(fc)
Part.export([o for o in doc.Objects if o.TypeId == 'Part::Feature'], st)
for o in [x for x in doc.Objects if x.TypeId == 'Part::Feature']:
    b = o.Shape.BoundBox
    say(f"{o.Name:16s} {o.Shape.Volume/1000:6.1f} cm3  z {b.ZMin:6.2f}->{b.ZMax:6.2f}  "
        f"{b.XLength:.0f}x{b.YLength:.0f} mm  valide={o.Shape.isValid()} solides={len(o.Shape.Solids)}")
say(f"FCStd : {fc}")
say(f"STEP  : {st}")

# STL des 3 pieces (impression 3D). Gitignores, mais toujours presents sur disque.
try:
    import Mesh, MeshPart
    for o in [x for x in doc.Objects if x.TypeId == 'Part::Feature']:
        m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05,
                                   AngularDeflection=0.15, Relative=False)
        m.write(f"{OUTDIR}/{o.Name}.stl")
    say("STL   : 3 fichiers")
except Exception as ex:
    say(f"STL non generes ({ex})")

# Un document cree en --console n'a PAS de GuiDocument.xml : a l'ouverture,
# FreeCAD ne sait ni quoi afficher ni comment. On repasse dessus avec la GUI en
# mode offscreen pour poser visibilite et couleurs une bonne fois.
import subprocess, tempfile
_fix = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False)
_fix.write(f"""import FreeCAD as App, FreeCADGui as Gui
COL = {{'frame_alu': (0.72, 0.73, 0.75, 0),
        'plate_top_PC': (0.55, 0.75, 0.90, 55),
        'plate_bottom_PC': (0.55, 0.75, 0.90, 55)}}
d = App.openDocument({fc!r})
for o in d.Objects:
    o.ViewObject.Visibility = True
    r, g, b, tr = COL.get(o.Name, (0.8, 0.8, 0.8, 0))
    o.ViewObject.ShapeColor = (r, g, b)
    o.ViewObject.Transparency = tr
d.save()
""")
_fix.close()
try:
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    subprocess.run(['freecad', _fix.name], env=env, timeout=300,
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
