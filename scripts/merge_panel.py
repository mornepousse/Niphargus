# Fusionne le PCB Conchodytes dans le vide du panneau Niphargus, pour l'export
# gerber uniquement. Les deux projets restent independants.
import re, math, uuid as U, sys

KBD  = "/home/mae/Documents/GitHub/rili/hardware/pcb/niphar.kicad_pcb"
MOUSE= "/home/mae/Documents/GitHub/Conchodytes/hardware/pcb/conchodytes.kicad_pcb"
OUT  = sys.argv[1] if len(sys.argv)>1 else "/tmp/panel/panel.kicad_pcb"
ROT  = -90.0
DX, DY = 170.85, 26.15      # calcules : la souris tournee se pose en (18,103)

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

# ---------------------------------------------------------------------------
# Tabs a mouse-bites : la souris est posee dans le vide, il faut la rattacher
# au rail gauche du panneau. Rail a x=14.640, bord gauche de la souris a
# x=18.000 sur y 112..133 -> 3,36 mm de pont, la cote idéale.
# ---------------------------------------------------------------------------
RAIL_X   = 14.640
MOUSE_X  = 18.000
TABS     = [(115.0, 118.0), (121.0, 124.0), (127.0, 130.0)]   # 3 tabs de 3 mm
BITE_D   = 0.5      # diametre des trous
BITE_P   = 0.75     # pas

panel = open(OUT).read()

def edge_seg(x1,y1,x2,y2):
    return f'''\t(gr_line
\t\t(start {x1} {y1})
\t\t(end {x2} {y2})
\t\t(stroke
\t\t\t(width 0.05)
\t\t\t(type solid)
\t\t)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{U.uuid4()}")
\t)'''

def split_vertical(txt, x, ymin, ymax, holes):
    """coupe un segment vertical en morceaux, en sautant les zones de tab"""
    k=0
    while True:
        k=txt.find('(gr_line',k)
        if k<0: return txt, False
        e=bal(txt,k); b=txt[k:e]
        if '"Edge.Cuts"' in b:
            s=re.search(r'\(start (-?[\d.]+) (-?[\d.]+)\)',b)
            en=re.search(r'\(end (-?[\d.]+) (-?[\d.]+)\)',b)
            X1,Y1,X2,Y2=[float(g) for g in (s.group(1),s.group(2),en.group(1),en.group(2))]
            if abs(X1-x)<0.01 and abs(X2-x)<0.01 and min(Y1,Y2)<=ymin+0.01 and max(Y1,Y2)>=ymax-0.01:
                lo,hi = min(Y1,Y2), max(Y1,Y2)
                cuts = sorted(holes)
                parts=[]; cur=lo
                for a,bb in cuts:
                    if a>cur: parts.append((cur,a))
                    cur=bb
                if cur<hi: parts.append((cur,hi))
                new="\n".join(edge_seg(x,p0,x,p1) for p0,p1 in parts)
                return txt[:k]+new+txt[e:], True
        k=e

panel, ok1 = split_vertical(panel, MOUSE_X, 112.0, 133.0, TABS)
panel, ok2 = split_vertical(panel, RAIL_X, 62.86, 183.59, TABS)
say = print
say(f"  contour souris interrompu : {ok1}    rail interrompu : {ok2}")

# mouse-bites : rangee de trous sur la ligne de rupture, cote souris
bites=[]
n=0
for y0,y1 in TABS:
    y=y0+BITE_P/2
    while y < y1:
        bites.append(f'''\t(footprint "MouseBite"
\t\t(layer "F.Cu")
\t\t(uuid "{U.uuid4()}")
\t\t(at {MOUSE_X} {round(y,3)})
\t\t(attr through_hole exclude_from_pos_files exclude_from_bom)
\t\t(pad "" np_thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size {BITE_D} {BITE_D})
\t\t\t(drill {BITE_D})
\t\t\t(layers "F&B.Cu" "*.Mask")
\t\t\t(uuid "{U.uuid4()}")
\t\t)
\t)''')
        y += BITE_P
        n += 1
k = panel.rstrip().rfind(")")
panel = panel[:k] + "\n" + "\n".join(bites) + "\n" + panel[k:]
open(OUT,'w').write(panel)
say(f"  souris : {len(TABS)} tabs de 3 mm, {n} trous de mouse-bite (D{BITE_D} pas {BITE_P})")

# --- tabs du CLAVIER : 4 pattes reliant les moities au rail droit, sans
#     percage jusqu'ici. Ligne de rupture au ras de la moitie (x = 186.95).
KBD_BREAK_X = 186.95
KBD_TABS = [(32.0, 38.0), (81.0, 87.0), (159.0, 165.0), (209.0, 215.0)]
panel = open(OUT).read()
bites2=[]; n2=0
for y0,y1 in KBD_TABS:
    y = y0 + BITE_P/2
    while y < y1:
        bites2.append(f'''\t(footprint "MouseBite"
\t\t(layer "F.Cu")
\t\t(uuid "{U.uuid4()}")
\t\t(at {KBD_BREAK_X} {round(y,3)})
\t\t(attr through_hole exclude_from_pos_files exclude_from_bom)
\t\t(pad "" np_thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size {BITE_D} {BITE_D})
\t\t\t(drill {BITE_D})
\t\t\t(layers "F&B.Cu" "*.Mask")
\t\t\t(uuid "{U.uuid4()}")
\t\t)
\t)''')
        y += BITE_P
        n2 += 1
k = panel.rstrip().rfind(")")
panel = panel[:k] + "\n" + "\n".join(bites2) + "\n" + panel[k:]
open(OUT,'w').write(panel)
say(f"  clavier : {len(KBD_TABS)} tabs, {n2} trous de mouse-bite a x={KBD_BREAK_X}")
say(f"  TOTAL mouse-bites : {n + n2}")
