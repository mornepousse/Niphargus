"""Génère la moitié droite (miroir) de rili.kicad_pcb : switches, diodes,
trous M3 et contour Edge.Cuts, dans le même fichier (panneau côte à côte).
Transformation : x -> 2a - x, angle empreinte -> -angle, angles internes
(absolus dans le format kicad_pcb) -> +delta, pads dé-netés, uuids neufs.
Usage: mirror_panel.py IN OUT [gap_mm]
"""
import re, sys, uuid

SRC, DST = sys.argv[1], sys.argv[2]
GAP = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
MIRROR_FP = ('EKR82-footprint:MX_Socket_18mm',
             'EKR82-footprint:Diode_TH_SOD123EKR',
             'EKR82-footprint:HOLE_M3-3.2-3.5')

txt = open(SRC).read()

def blocks(text, opener):
    """Rend les (start, end_exclu) des blocs s-expr commençant par opener."""
    out, i = [], 0
    while True:
        i = text.find(opener, i)
        if i < 0: return out
        depth, j, instr = 0, i, False
        while True:
            c = text[j]
            if instr:
                if c == '\\': j += 1
                elif c == '"': instr = False
            elif c == '"': instr = True
            elif c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: break
            j += 1
        out.append((i, j + 1))
        i = j

def fnum(v):
    s = f"{v:.6f}".rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'

def norm_ang(a):
    a = (a + 180.0) % 360.0 - 180.0
    if a == -180.0: a = 180.0
    return a

# --- 1. bbox Edge.Cuts (niveau board) -> axe de symétrie ---
fp_spans = blocks(txt, '(footprint ')
def in_fp(i): return any(a <= i < b for a, b in fp_spans)

edge_spans = []
for op in ('(gr_line', '(gr_arc', '(gr_rect', '(gr_circle', '(gr_poly'):
    for a, b in blocks(txt, op):
        if not in_fp(a) and '"Edge.Cuts"' in txt[a:b]:
            edge_spans.append((a, b))
xs = []
for a, b in edge_spans:
    for m in re.finditer(r'\((?:start|end|mid|center) ([-\d.]+) ([-\d.]+)\)', txt[a:b]):
        xs.append(float(m.group(1)))
X_MAX = max(xs)
AXIS = X_MAX + GAP / 2.0
sys.stderr.write(f"axe miroir x={AXIS} (x_max contour {X_MAX}, gap {GAP} mm)\n")

def mx(x): return 2 * AXIS - x

# --- 2. refs existantes -> numérotation de la moitié droite ---
all_refs = re.findall(r'\(property "Reference" "([A-Za-z_]+)(\d+)"', txt)
maxnum = {}
for p, n in all_refs:
    maxnum[p] = max(maxnum.get(p, 0), int(n))
counters = dict(maxnum)

def next_ref(old):
    m = re.match(r'([A-Za-z_]+)(\d+)$', old)
    if not m: return old + '_R'
    p = m.group(1)
    counters[p] = counters.get(p, 0) + 1
    return f"{p}{counters[p]}"

NEW_UUID = lambda: str(uuid.uuid4())

def fresh_uuids(s):
    return re.sub(r'\(uuid "?[0-9a-fA-F-]+"?\)', lambda m: f'(uuid "{NEW_UUID()}")', s)

# --- 3. transformation d'un bloc footprint ---
def mirror_footprint(block):
    # localiser les (at ...) avec leur profondeur relative au bloc
    ats = []  # (start, end, depth, vals)
    depth, i, instr = 0, 0, False
    while i < len(block):
        c = block[i]
        if instr:
            if c == '\\': i += 1
            elif c == '"': instr = False
        elif c == '"': instr = True
        elif c == '(':
            depth += 1
            m = re.match(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', block[i:])
            if m:
                vals = [float(m.group(1)), float(m.group(2)),
                        float(m.group(3)) if m.group(3) else 0.0]
                ats.append((i, i + m.end(), depth, vals))
        elif c == ')': depth -= 1
        i += 1
    if not ats or ats[0][2] != 2:
        raise SystemExit("footprint sans (at) de niveau 1 ?!")
    fx, fy, fr = ats[0][3]
    nr = norm_ang(-fr)
    delta = nr - fr
    repl = {ats[0][0]: (ats[0][1], f"(at {fnum(mx(fx))} {fnum(fy)}" +
                        (f" {fnum(nr)})" if nr else ")"))}
    for s, e, d, vals in ats[1:]:
        na = norm_ang(vals[2] + delta)
        repl[s] = (e, f"(at {fnum(vals[0])} {fnum(vals[1])}" +
                   (f" {fnum(na)})" if na else ")"))
    out, last = [], 0
    for s in sorted(repl):
        e, txt_new = repl[s]
        out.append(block[last:s]); out.append(txt_new); last = e
    out.append(block[last:])
    b = ''.join(out)
    # dé-neter les pads (les nets seront réassignés par le schéma v2)
    b = re.sub(r'\s*\(net (?:\d+ )?"(?:[^"\\]|\\.)*"\)', '', b)
    # délier du schéma : une copie ne doit pas revendiquer le symbole de
    # l'originale (le (path) est unique par symbole), sinon lien PCB<->schéma cassé
    b = re.sub(r'\s*\(path "[^"]*"\)', '', b)
    for name in ('Sheetname', 'Sheetfile'):
        spans = blocks(b, f'(property "{name}"')
        if spans:
            pa, pb = spans[0]
            b = b[:pa] + b[pb:]
    # ref neuve
    old = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
    new = next_ref(old)
    b = b.replace(f'"Reference" "{old}"', f'"Reference" "{new}"')
    return fresh_uuids(b), old, new

# --- 4. transformation Edge.Cuts ---
def mirror_edge(block):
    def f(m):
        return f"({m.group(1)} {fnum(mx(float(m.group(2))))} {m.group(3)})"
    b = re.sub(r'\((start|end|mid|center) ([-\d.]+) ([-\d.]+\)?)',
               lambda m: f"({m.group(1)} {fnum(mx(float(m.group(2))))} {m.group(3)}",
               block)
    return fresh_uuids(b)

additions, mapping = [], []
for a, b in fp_spans:
    head = txt[a:a+120]
    if any(f'"{n}"' in head for n in MIRROR_FP):
        nb, old, new = mirror_footprint(txt[a:b])
        additions.append(nb); mapping.append((old, new))
for a, b in edge_spans:
    additions.append(mirror_edge(txt[a:b]))

sys.stderr.write(f"{len(mapping)} empreintes miroir : " +
                 ", ".join(f"{o}->{n}" for o, n in mapping[:6]) + " …\n")
sys.stderr.write(f"{len(edge_spans)} éléments Edge.Cuts miroir\n")

# --- 5. insertion avant la parenthèse finale ---
close = txt.rstrip()
assert close.endswith(')')
ins = "\n".join("  " + a.replace("\n", "\n") for a in additions)
out = close[:-1].rstrip() + "\n" + ins + "\n)\n"
open(DST, 'w').write(out)
sys.stderr.write(f"écrit : {DST}\n")
