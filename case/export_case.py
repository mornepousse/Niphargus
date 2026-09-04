# Exporte les fichiers de fabrication DEPUIS le FCStd.
#   freecadcmd export_case.py
#
# C'est l'outil du quotidien depuis que le modele est passe en PartDesign :
# le FCStd est la source de verite, on l'edite dans FreeCAD, puis on ressort
# les DXF de decoupe et le STEP ici. gen_case.py, lui, ne sert plus qu'a
# re-amorcer le modele en repartant du SVG et du PCB — et il efface les
# retouches, donc on ne le relance pas par habitude.
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUTDIR = os.environ.get("NIPHAR_CASE_OUT", HERE)
FCSTD = f"{OUTDIR}/niphar-case-left.FCStd"
PLAQUES = ("plate_top_PC", "plate_bottom_PC")

import FreeCAD as App
import Part
from FreeCAD import Vector

LOG = open("/tmp/export_case.log", "w", buffering=1)
def say(*a):
    m = " ".join(str(x) for x in a)
    LOG.write(m + "\n")
    print(m)

if not os.path.exists(FCSTD):
    sys.exit(f"introuvable : {FCSTD}")

doc = App.openDocument(FCSTD)
say(f"ouvert : {FCSTD} ({len(doc.Objects)} objets)")


def dxf_write(path, wires, tol=0.02):
    """DXF R12. Cercles entiers en CIRCLE, arcs en ARC — le decoupeur garde de
    vraies courbes pour sa compensation de saignee. Le reste en segments."""
    e = []
    n_c = n_a = n_l = 0
    def line(a, b):
        e.append("0\nLINE\n8\n0\n10\n%.4f\n20\n%.4f\n30\n0.0\n"
                 "11\n%.4f\n21\n%.4f\n31\n0.0" % (a.x, a.y, b.x, b.y))
    for w in wires:
        for ed in w.Edges:
            crv = ed.Curve
            if isinstance(crv, Part.Circle) and ed.isClosed():
                c = crv.Center
                e.append("0\nCIRCLE\n8\n0\n10\n%.4f\n20\n%.4f\n30\n0.0\n40\n%.4f"
                         % (c.x, c.y, crv.Radius))
                n_c += 1
            elif isinstance(crv, Part.Circle):
                c = crv.Center
                a0 = math.degrees(math.atan2(ed.Vertexes[0].Point.y - c.y,
                                             ed.Vertexes[0].Point.x - c.x)) % 360
                a1 = math.degrees(math.atan2(ed.Vertexes[-1].Point.y - c.y,
                                             ed.Vertexes[-1].Point.x - c.x)) % 360
                # DXF parcourt l'arc en sens trigo de 50 vers 51
                if crv.Axis.z < 0:
                    a0, a1 = a1, a0
                e.append("0\nARC\n8\n0\n10\n%.4f\n20\n%.4f\n30\n0.0\n40\n%.4f\n"
                         "50\n%.4f\n51\n%.4f" % (c.x, c.y, crv.Radius, a0, a1))
                n_a += 1
            elif isinstance(crv, Part.Line):
                line(ed.Vertexes[0].Point, ed.Vertexes[-1].Point)
                n_l += 1
            else:
                pts = ed.discretize(Deflection=tol)
                for i in range(len(pts) - 1):
                    line(pts[i], pts[i + 1])
                n_l += len(pts) - 1
    open(path, "w").write("0\nSECTION\n2\nENTITIES\n"
                          + "".join(x + "\n" for x in e)
                          + "0\nENDSEC\n0\nEOF\n")
    return n_c, n_a, n_l


pieces = []
for nm in PLAQUES:
    o = doc.getObject(nm)
    if o is None:
        say(f"!! {nm} absent du document")
        continue
    sh = o.Shape
    bb = sh.BoundBox
    zmid = (bb.ZMin + bb.ZMax) / 2.0        # mi-epaisseur : vrai profil traversant
    wires = sh.slice(Vector(0, 0, 1), zmid)
    if not wires:
        say(f"!! {nm} : section vide a z={zmid:.2f}")
        continue
    comp = Part.Compound(wires)
    comp.translate(Vector(0, 0, -zmid))     # a plat sur z = 0
    p = f"{OUTDIR}/{nm}.dxf"
    n_c, n_a, n_l = dxf_write(p, comp.Wires)
    b2 = comp.BoundBox
    say(f"DXF  {nm}.dxf — {len(comp.Wires)} contours "
        f"({n_c} cercles, {n_a} arcs, {n_l} segments), "
        f"{b2.XLength:.1f} x {b2.YLength:.1f} mm, epaisseur {bb.ZLength:.2f} mm")

for nm in ("frame_alu",) + PLAQUES:
    o = doc.getObject(nm)
    if o is not None:
        pieces.append(o)

if pieces:
    st = f"{OUTDIR}/niphar-case-left.step"
    Part.export(pieces, st)
    say(f"STEP {st} ({len(pieces)} pieces)")
    try:
        import Mesh, MeshPart
        for o in pieces:
            m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05,
                                       AngularDeflection=0.15, Relative=False)
            m.write(f"{OUTDIR}/{o.Name}.stl")
        say(f"STL  {len(pieces)} fichiers")
    except Exception as ex:
        say(f"STL non generes ({ex})")

for o in pieces:
    say(f"   {o.Name:16s} {o.Shape.Volume/1000:7.3f} cm3  solides={len(o.Shape.Solids)}  "
        f"valide={o.Shape.isValid()}")
