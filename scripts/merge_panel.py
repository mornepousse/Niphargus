# Fusionne le PCB Conchodytes dans le vide du panneau Niphargus, pour l'export
# gerber uniquement. Les deux projets restent independants.
import re, math, uuid as U, sys

KBD  = "/home/mae/Documents/GitHub/rili/hardware/pcb/niphar.kicad_pcb"
MOUSE= "/home/mae/Documents/GitHub/Conchodytes/hardware/pcb/conchodytes.kicad_pcb"
OUT  = sys.argv[1] if len(sys.argv)>1 else "/tmp/panel/panel.kicad_pcb"
ROT  = 90.0
DX, DY = -50.50, 218.85     # calcules : la souris tournee se pose en (18,103)

def bal(x,i):
    d=0;j=i;s=False
    while True:
        c=x[j]
        if s:
            if c=='\\': j+=1
            elif c=='"': s=False
        elif c=='"': s=True
        elif c=='(': d+=1
        elif c==')':
            d-=1
            if d==0: return j+1
        j+=1

def blocks(t, op):
    """blocs de PREMIER NIVEAU seulement (profondeur 1 dans le fichier)"""
    out=[]; i=0; depth=0; s=False
    while i < len(t):
        c=t[i]
        if s:
            if c=='\\': i+=1
            elif c=='"': s=False
        elif c=='"': s=True
        elif c=='(':
            if depth==1 and t.startswith(op, i):
                e=bal(t,i); out.append((i,e)); i=e; continue
            depth+=1
        elif c==')': depth-=1
        i+=1
    return out

a=math.radians(ROT)
CA, SA = math.cos(a), math.sin(a)
def tr(x, y):
    """rotation +90 deg en repere KiCad (y vers le bas) puis translation"""
    nx =  x*CA + y*SA
    ny = -x*SA + y*CA
    return round(nx+DX, 4), round(ny+DY, 4)

def move_coords(blk, skip_first_at=False):
    """transforme toutes les paires de coordonnees absolues du bloc"""
    def rep(m):
        x,y = float(m.group(2)), float(m.group(3))
        nx,ny = tr(x,y)
        return f"({m.group(1)} {nx} {ny}"
    return re.sub(r'\((start|end|mid|center|at|xy) (-?[\d.]+) (-?[\d.]+)', rep, blk)

mouse = open(MOUSE).read()
body_parts = []
counts = {}
for op in ('(footprint ','(segment','(via','(zone','(gr_line','(gr_arc','(gr_circle',
           '(gr_poly','(gr_rect','(gr_text','(arc','(dimension'):
    for i,e in blocks(mouse, op):
        blk = mouse[i:e]
        name = op.strip('(').strip()
        counts[name] = counts.get(name,0)+1
        if name == 'footprint':
            # le (at ...) principal est au premier niveau du bloc : on le traite
            # a part, puis on laisse les coordonnees internes intactes (relatives)
            m = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', blk)
            if m:
                x,y = float(m.group(1)), float(m.group(2))
                rot = float(m.group(3) or 0)
                nx,ny = tr(x,y)
                nrot = (rot + ROT) % 360
                blk = blk[:m.start()] + f'\n\t\t(at {nx} {ny} {nrot:g})' + blk[m.end():]
            # les (at) internes restent relatifs : on ne touche a rien d'autre
        else:
            blk = move_coords(blk)
        # uuid neufs pour ne pas entrer en collision avec le clavier
        blk = re.sub(r'\(uuid "[0-9a-fA-F-]{36}"\)', lambda _: f'(uuid "{U.uuid4()}")', blk)
        body_parts.append(blk)

print("  elements repris de la souris :")
for k,v in sorted(counts.items(), key=lambda z:-z[1]):
    print(f"     {v:4d}  {k}")

kbd = open(KBD).read()
k = kbd.rstrip().rfind(")")
merged = kbd[:k] + "\n" + "\n".join(body_parts) + "\n" + kbd[k:]
open(OUT,'w').write(merged)
print(f"\n  panneau ecrit : {OUT}  ({len(merged)//1024} ko)")
