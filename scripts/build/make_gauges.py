from PIL import Image, ImageDraw, ImageFont
import math
T = 512
im = Image.new('RGB', (4*T, 2*T), (8, 8, 9))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTC = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
def dial(tile, face, ink, labels, a0=225, a1=-45, minor=4, title='', needle=0.05, big=False, sub=''):
    tu, tv = tile % 4, tile // 4
    ox, oy = tu*T, (1 - tv)*T          # image y down; uv v up -> row (1-tv)
    d = ImageDraw.Draw(im)
    cx, cy, R = ox + T/2, oy + T/2, T*0.48
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=face)
    # subtle radial shading ring
    for k in range(10):
        rr = R*(1 - 0.004*k)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=tuple(max(0, c - 3*k) for c in face))
    n = len(labels) - 1
    fnt = ImageFont.truetype(FONTC, int(T*(0.085 if big else 0.10)))
    for i, lab in enumerate(labels):
        a = math.radians(a0 + (a1 - a0)*i/n)
        ca, sa = math.cos(a), -math.sin(a)
        d.line([cx + ca*R*0.80, cy + sa*R*0.80, cx + ca*R*0.94, cy + sa*R*0.94], fill=ink, width=int(T*0.012))
        if lab != '':
            tx, ty = cx + ca*R*0.64, cy + sa*R*0.64
            w = d.textlength(lab, font=fnt)
            d.text((tx - w/2, ty - T*0.05), lab, font=fnt, fill=ink)
        if i < n:
            for m in range(1, minor+1):
                am = math.radians(a0 + (a1 - a0)*(i + m/(minor+1))/n)
                cm, sm = math.cos(am), -math.sin(am)
                d.line([cx + cm*R*0.86, cy + sm*R*0.86, cx + cm*R*0.94, cy + sm*R*0.94], fill=ink, width=int(T*0.005))
    ft = ImageFont.truetype(FONT, int(T*0.065))
    if title:
        w = d.textlength(title, font=ft); d.text((cx - w/2, cy + R*0.30), title, font=ft, fill=ink)
    if sub:
        w = d.textlength(sub, font=ft); d.text((cx - w/2, cy - R*0.42), sub, font=ft, fill=ink)
    a = math.radians(a0 + (a1 - a0)*needle)
    ca, sa = math.cos(a), -math.sin(a)
    d.line([cx - ca*R*0.12, cy - sa*R*0.12, cx + ca*R*0.84, cy + sa*R*0.84], fill=(235, 235, 225) if face[0] < 80 else (20, 20, 20), width=int(T*0.018))
    d.ellipse([cx - R*0.07, cy - R*0.07, cx + R*0.07, cy + R*0.07], fill=(30, 30, 30))
CREAM = (214, 206, 186); INK = (25, 25, 25); BLACK = (12, 12, 13); WHITE = (232, 232, 222)
dial(0, BLACK, WHITE, ['0', '5', '10', '15', '20', '25', '30', '35', '40', '45', '50'], 225, -45, 4, 'TR/MN x 100', 0.02, big=True)
dial(1, CREAM, INK, ['40', '60', '80', '100', '120'], 210, -30, 3, 'EAU', 0.35)
dial(2, CREAM, INK, ['0', '2', '4', '6', '8'], 210, -30, 3, 'HUILE  kg', 0.05)
dial(3, CREAM, INK, ['-30', '', '0', '', '+30'], 150, 30, 4, 'AMP', 0.5)
dial(4, CREAM, INK, ['0', '1/4', '1/2', '3/4', '1'], 210, -30, 1, 'ESSENCE', 0.6)
# clock
tu, tv = 5 % 4, 5 // 4
d = ImageDraw.Draw(im); cx, cy, R = tu*T + T/2, (1 - tv)*T + T/2, T*0.48
d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=CREAM)
fnt = ImageFont.truetype(FONTC, int(T*0.11))
for h in range(1, 13):
    a = math.radians(90 - 30*h); ca, sa = math.cos(a), -math.sin(a)
    w = d.textlength(str(h), font=fnt); d.text((cx + ca*R*0.72 - w/2, cy + sa*R*0.72 - T*0.06), str(h), font=fnt, fill=INK)
    d.line([cx + ca*R*0.88, cy + sa*R*0.88, cx + ca*R*0.96, cy + sa*R*0.96], fill=INK, width=6)
for ang, L in ((math.radians(90 - 30*10.2), 0.5), (math.radians(90 - 6*9), 0.78)):
    d.line([cx, cy, cx + math.cos(ang)*R*L, cy - math.sin(ang)*R*L], fill=INK, width=10)
# switch panel (black with ring + markings)
tu, tv = 6 % 4, 6 // 4
cx, cy, R = tu*T + T/2, (1 - tv)*T + T/2, T*0.48
d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=BLACK)
d.ellipse([cx - R*0.55, cy - R*0.55, cx + R*0.55, cy + R*0.55], outline=(120, 120, 120), width=8)
fnt = ImageFont.truetype(FONTC, int(T*0.09))
for lab, ang in (('0', 120), ('1', 90), ('2', 60)):
    a = math.radians(ang); w = d.textlength(lab, font=fnt)
    d.text((cx + math.cos(a)*R*0.75 - w/2, cy - math.sin(a)*R*0.75 - T*0.05), lab, font=fnt, fill=WHITE)
im.save('/home/claude/tank/build/tex/gauges_atlas.png')
print('ok', im.size)
