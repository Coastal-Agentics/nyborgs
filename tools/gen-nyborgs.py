# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: MIT
# Writes ../nyborgs.svg: three Nyborgs for the splash header.
# Art reused (copied, unchanged colours) from the Nyborg mockup generator
# starscream-agentics/arena tools/nyborg/gen.py (revision 3: 2-4 yarn strands, no mouth).
import math, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nyborgs.svg')
HEAD = '#EADFCB'; LINE = '#5E544B'; EYE = '#2F2A26'
STRANDS = {2: [(-5,-22,34,-1,1.0),(6,26,30,1,1.25)],
           3: [(-9,-38,28,-1,1.25),(0,-4,36,1,1.0),(9,36,28,1,1.25)],
           4: [(-13,-50,24,-1,1.3),(-4.5,-20,31,-1,1.0),(4.5,18,31,1,1.0),(13,48,24,1,1.3)]}
def strand_points(x0, lean, L, curl, flop):
    side = 1 if lean > 0 else -1 if lean < 0 else curl
    pts = [(x0, 4.0)]; n = 48; ds = L / n
    for i in range(n):
        u = (i + 0.5) / n
        th = (lean + side*38*u**2 + 11*math.sin(2*math.pi*u)*(-side)
              + flop*1.8*u + curl*190*max(0.0, (u-0.66)/0.34)**1.3)
        th = math.radians(th)
        x, y = pts[-1]; pts.append((x + ds*math.sin(th), y - ds*math.cos(th)))
    return pts
def strand_svg(hair, pts):
    d = 'M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in pts)
    out = f'<path d="{d}" fill="none" stroke="{LINE}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
    out += f'<path d="{d}" fill="none" stroke="{hair}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    ticks = ''
    for i in range(3, len(pts)-3, 3):
        (xa, ya), (xb, yb) = pts[i-1], pts[i+1]
        tx, ty = xb-xa, yb-ya; m = math.hypot(tx, ty) or 1; tx, ty = tx/m, ty/m
        nx, ny = -ty, tx; x, y = pts[i]
        dx, dy = (nx*0.85+tx*0.55)*2.8, (ny*0.85+ty*0.55)*2.8
        ticks += f'M{x-dx:.2f},{y-dy:.2f} L{x+dx:.2f},{y+dy:.2f} '
    out += f'<path d="{ticks}" stroke="#000" stroke-opacity="0.18" stroke-width="1.2" stroke-linecap="round"/>'
    hl = [(x-1.3, y-0.6) for x, y in pts[2:int(len(pts)*0.6)]]
    out += '<path d="M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in hl) + '" fill="none" stroke="#fff" stroke-opacity="0.35" stroke-width="1.4" stroke-linecap="round"/>'
    return out
def nyborg(x, y, hair, count, s=1.0, lean=0, sway=0, ex=0):
    g = f'<g transform="translate({x},{y}) scale({s})">'
    g += '<ellipse cx="0" cy="0" rx="22" ry="4.2" fill="#1F3147" opacity="0.10"/>'
    g += f'<g transform="rotate({lean})"><use href="#head"/>'
    g += '<g transform="translate(0,-62)">' + ''.join(
        strand_svg(hair, strand_points(x0, ln + sway*0.35, L, c, sway*f)) for x0, ln, L, c, f in STRANDS[count]) + '</g>'
    g += f'<g transform="translate({ex},0)"><use href="#eyes"/></g></g></g>'
    return g
W, H = 300, 122  # viewBox starts at y=28 to crop empty sky
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 28 {W} {H}" role="img" aria-labelledby="t">',
     '<title id="t">Three Nyborgs with red, blue and yellow yarn hair</title>',
     '<defs>',
     f'<g id="head"><circle cx="0" cy="-31" r="31" fill="{HEAD}" stroke="{LINE}" stroke-width="2.6"/>'
     '<ellipse cx="-12" cy="-42" rx="8" ry="4.5" fill="#fff" opacity="0.30" transform="rotate(-25 -12 -42)"/></g>',
     f'<g id="eyes"><circle cx="-10" cy="-29" r="4" fill="{EYE}"/><circle cx="10" cy="-29" r="4" fill="{EYE}"/>'
     '<circle cx="-8.8" cy="-30.4" r="1.2" fill="#fff"/><circle cx="11.2" cy="-30.4" r="1.2" fill="#fff"/></g>',
     '</defs>']
o.append(nyborg(58, 140, '#3F6FD8', 2, s=0.95, lean=-4, sway=-4, ex=-2))   # Cobalt
o.append(nyborg(150, 136, '#D9534F', 3, s=1.08))                              # Yarn Red (default)
o.append(nyborg(242, 140, '#F2C14E', 4, s=0.95, lean=4, sway=4, ex=2))      # Sunny
o.append('</svg>')
open(OUT, 'w').write('\n'.join(o) + '\n')
print('wrote', os.path.normpath(OUT))

# favicon.svg: one Yarn Red Nyborg, square crop
FAV = os.path.join(os.path.dirname(OUT), 'favicon.svg')
f = ['<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="-45 -106 90 90">',
     '<defs>', o[3], o[4], '</defs>', nyborg(0, -18, '#D9534F', 3, s=0.82), '</svg>']
open(FAV, 'w').write('\n'.join(f) + '\n')
print('wrote', os.path.normpath(FAV))
