"""Génère une vidéo verticale d'horreur interactive (style POV + téléphone).

Usage : python3 make_video.py  -> produit regle_du_3e_partie1.mp4
Tout est dessiné en code (PIL) et le son est synthétisé (numpy) : remplace
ensuite les décors par tes propres illustrations et ajoute ta voix off.
"""
import math, random, subprocess, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 720, 1280, 24
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regle_du_3e_partie1.mp4")
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}
def font(size, bold=True):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FB if bold else FR, size)
    return _fc[k]

YEL, RED, WHITE, VIO = (255, 226, 90), (255, 95, 95), (245, 245, 245), (190, 160, 255)

# ---------------------------------------------------------------- SCÉNARIO
# Chaque scène : durée, décor, téléphone (None/'small'/'big'), heure affichée,
# messages [(t, nom, texte)], sous-titres [(t0, t1, texte, couleur)],
# sons [(t, type)], secousses [(t0, t1)].
G = "Internat – Bât. B"
SCENES = [
    dict(d=4.5, bg="room", phone="small", clock=["02:59:57", "02:59:58", "02:59:59"], banner=True,
         subs=[(0.3, 4.4, "Trois… deux… un…", YEL)], sfx=[(0.3, "tick"), (1.8, "tick"), (3.3, "tick")]),
    dict(d=7, bg="room", phone="big", clock=["03:00"], chat=G,
         msgs=[(0.2, "Malik", "les gars il est 3h pile mdr"),
               (1.6, "Inès", "la règle du 3e étage, vous y croyez vraiment ?"),
               (3.4, "Sami", "à 3h l'interphone sonne… et c'est quelqu'un que tu connais")],
         subs=[(4.6, 6.9, "Encore leur rumeur débile…", YEL)]),
    dict(d=4, bg="corridor", phone="small", clock=["03:00"],
         subs=[(1.4, 3.9, "BZZZZZT", RED)], sfx=[(1.2, "buzz")], shake=[(1.2, 2.2)]),
    dict(d=5, bg="interphone", phone=None,
         subs=[(0.3, 4.9, "L'interphone du 3e. Mais il n'y a personne en bas.", YEL)]),
    dict(d=6.5, bg="corridor", phone="big", clock=["03:01"], chat=G,
         msgs=[(0.2, "Inès", "QUI A SONNÉ ???"),
               (1.6, "Malik", "pas moi je suis dans mon lit"),
               (3.2, "Sami", "Ne répondez pas. Surtout pas.")]),
    dict(d=6, bg="interphone", phone=None, sfx=[(0.1, "buzz")], shake=[(0.1, 0.8)],
         subs=[(1.0, 5.9, "« Allô ? C'est Yanis… j'ai oublié mon badge. Ouvre-moi. »", RED)]),
    dict(d=5, bg="corridor", phone="small", clock=["03:01"],
         subs=[(0.3, 4.9, "Yanis ? Il dort à l'infirmerie depuis ce soir…", YEL)]),
    dict(d=7, bg="corridor", phone="big", clock=["03:02"], chat="Yanis",
         msgs=[(0.2, "Yanis", "t'es réveillé ?"),
               (1.8, "Yanis", "j'ai entendu l'interphone sonner chez vous"),
               (3.6, "Yanis", "moi je suis toujours à l'infirmerie. je bouge pas.")]),
    dict(d=5.5, bg="interphone", phone=None, sfx=[(0.1, "buzz")],
         subs=[(0.6, 5.4, "« Pourquoi tu m'ouvres pas ? Il fait froid dehors… »", RED)]),
    dict(d=6, bg="door", phone="small", clock=["03:02"], sfx=[(0.6, "knock"), (1.2, "knock"), (1.8, "knock")],
         shake=[(0.6, 2.1)],
         subs=[(0.6, 2.6, "TOC. TOC. TOC.", RED), (2.8, 5.9, "Quelqu'un frappe à ma porte. La 312.", YEL)]),
    dict(d=5.5, bg="door", phone="big", clock=["03:03"], chat=G,
         msgs=[(0.2, "Sami", "il est plus en bas."),
               (2.0, "Sami", "il est DANS le bâtiment.")]),
    dict(d=7, bg="door", phone="small", clock=["03:03"], notif=(3.6, "Yanis", "N'OUVRE PAS. CE N'EST PAS MOI."),
         sfx=[(3.6, "notif"), (3.6, "sting")], shake=[(3.6, 4.6)],
         subs=[(0.3, 3.4, "« C'est moi… Yanis. Ouvre. »", RED)]),
    dict(d=3, bg="black", phone="small", clock=["03:04"], sfx=[(0.2, "heart"), (1.2, "heart"), (2.2, "heart")]),
    dict(d=9, bg="choice", phone="small", clock=["03:04"], sfx=[(0.2, "heart"), (1.2, "heart"), (2.2, "heart"),
                                                               (3.2, "heart"), (4.2, "heart")]),
]

# ---------------------------------------------------------------- DÉCORS
def vgrad(w, h, top, bot):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(top)[None, None] * (1 - a) + np.array(bot)[None, None] * a
    return Image.fromarray(np.repeat(arr, w, 1).astype(np.uint8))

def bg_room(w, h):
    im = vgrad(w, h, (26, 32, 62), (14, 18, 36)); d = ImageDraw.Draw(im)
    d.polygon([(0, h * .72), (w, h * .70), (w, h), (0, h)], fill=(40, 30, 34))         # parquet
    for i in range(12):
        d.line([(i * w / 11, h * .71), (i * w / 11 - 80, h)], fill=(30, 22, 26), width=3)
    wx, wy, ww, wh = w * .30, h * .14, w * .48, h * .36                                # fenêtre
    d.rectangle([wx - 14, wy - 14, wx + ww + 14, wy + wh + 14], fill=(20, 22, 40))
    d.rectangle([wx, wy, wx + ww, wy + wh], fill=(10, 14, 38))
    d.ellipse([wx + ww * .68, wy + 40, wx + ww * .68 + 48, wy + 88], fill=(240, 236, 200))
    d.ellipse([wx + ww * .68 + 14, wy + 34, wx + ww * .68 + 62, wy + 82], fill=(10, 14, 38))
    rnd = random.Random(3)
    x = wx
    while x < wx + ww:                                                                 # immeubles
        bw, bh = rnd.randint(40, 90), rnd.randint(80, 220)
        d.rectangle([x, wy + wh - bh, x + bw, wy + wh], fill=(22, 26, 52))
        for yy in range(int(wy + wh - bh + 12), int(wy + wh - 10), 22):
            for xx in range(int(x + 8), int(x + bw - 10), 16):
                if rnd.random() < .25:
                    d.rectangle([xx, yy, xx + 7, yy + 10], fill=(255, 210, 120))
        x += bw + 4
    d.line([(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], fill=(20, 22, 40), width=10)
    d.line([(wx, wy + wh / 2), (wx + ww, wy + wh / 2)], fill=(20, 22, 40), width=10)
    d.polygon([(wx, h * .72), (wx + ww, h * .72), (wx + ww + 160, h), (wx - 60, h)], fill=(52, 46, 70))  # clair de lune
    d.rectangle([w * .62, h * .56, w * 1.05, h * .78], fill=(48, 30, 36))             # lit
    d.rectangle([w * .62, h * .53, w * 1.05, h * .60], fill=(70, 72, 110))
    d.ellipse([w * .66, h * .50, w * .84, h * .57], fill=(200, 200, 215))
    d.rectangle([-10, h * .50, w * .22, h * .53], fill=(60, 40, 34))                  # bureau
    d.rectangle([w * .02, h * .53, w * .05, h * .72], fill=(50, 34, 30))
    d.rectangle([w * .17, h * .53, w * .20, h * .72], fill=(50, 34, 30))
    return im

def bg_corridor(w, h):
    im = Image.new("RGB", (w, h), (28, 36, 70)); d = ImageDraw.Draw(im)
    vx, vy = w / 2, h * .42; bx0, by0, bx1, by1 = vx - 90, vy - 150, vx + 90, vy + 150
    d.polygon([(0, 0), (w, 0), (bx1, by0), (bx0, by0)], fill=(20, 26, 52))           # plafond
    d.polygon([(0, h), (w, h), (bx1, by1), (bx0, by1)], fill=(38, 34, 44))           # sol
    for k in range(1, 14):                                                            # carrelage
        t = k / 14
        y = by1 + (h - by1) * t ** 1.8
        x0 = bx0 + (0 - bx0) * t ** 1.8; x1 = bx1 + (w - bx1) * t ** 1.8
        d.line([(x0, y), (x1, y)], fill=(28, 26, 34), width=2)
    for k in range(-6, 7):
        d.line([(vx + k * 30, by1), (vx + k * 240, h)], fill=(28, 26, 34), width=2)
    d.polygon([(0, 0), (bx0, by0), (bx0, by1), (0, h)], fill=(34, 44, 84))           # murs
    d.polygon([(w, 0), (bx1, by0), (bx1, by1), (w, h)], fill=(30, 40, 78))
    d.rectangle([bx0, by0, bx1, by1], fill=(14, 18, 36))
    d.rectangle([vx - 34, by0 + 20, vx + 34, by0 + 42], fill=(40, 200, 110))         # sortie
    for side in (-1, 1):                                                              # portes
        for t0, t1, num in ((.08, .30, 308), (.42, .58, 310), (.68, .78, 312)):
            def P(t, yy):
                ex = 0 if side < 0 else w
                bx = bx0 if side < 0 else bx1
                x = ex + (bx - ex) * t
                top = 0 + (by0 - 0) * t; bot = h + (by1 - h) * t
                return (x, top + (bot - top) * yy)
            n = num + (0 if side < 0 else 1)
            poly = [P(t0, .30), P(t1, .30), P(t1, .86), P(t0, .86)]
            d.polygon(poly, fill=(58, 40, 42), outline=(20, 16, 20))
            hx, hy = P(t1 - (t1 - t0) * .15, .60)
            d.ellipse([hx - 5, hy - 5, hx + 5, hy + 5], fill=(190, 160, 90))
            px, py = P((t0 + t1) / 2, .36)
            sz = max(10, int(26 * (1 - t0)))
            d.text((px, py), str(n), font=font(sz), fill=(220, 190, 110), anchor="mm")
    for t in (.15, .5, .75):                                                          # néons
        y = by0 * t; x0 = bx0 * t; x1 = w + (bx1 - w) * t
        d.rectangle([vx - 60 * (1 - t * .6), y + 6, vx + 60 * (1 - t * .6), y + 16], fill=(230, 230, 200))
    return im

def bg_interphone(w, h):
    im = vgrad(w, h, (36, 44, 80), (22, 26, 48)); d = ImageDraw.Draw(im)
    for y in range(0, h, 64):
        d.line([(0, y), (w, y)], fill=(32, 40, 72), width=2)
    x0, y0, x1, y1 = w * .22, h * .18, w * .78, h * .74
    d.rounded_rectangle([x0 + 14, y0 + 18, x1 + 14, y1 + 18], 30, fill=(12, 14, 26))
    d.rounded_rectangle([x0, y0, x1, y1], 30, fill=(150, 150, 160), outline=(90, 90, 100), width=6)
    d.rounded_rectangle([x0 + 40, y0 + 50, x1 - 40, y0 + 330], 16, fill=(20, 20, 24))  # écran
    for i in range(9):                                                                   # grille HP
        yy = y0 + 380 + i * 18
        d.line([(x0 + 90, yy), (x1 - 90, yy)], fill=(70, 70, 80), width=7)
    d.ellipse([w / 2 - 60, y1 - 190, w / 2 + 60, y1 - 70], fill=(110, 110, 120), outline=(70, 70, 80), width=6)
    d.text((w / 2, y1 - 130), "🔔" if False else "APPEL", font=font(22), fill=(40, 40, 50), anchor="mm")
    d.text((w / 2, y0 + 360), "BÂT. B — 3e ÉTAGE", font=font(20), fill=(60, 60, 70), anchor="mm")
    return im

def bg_door(w, h):
    im = vgrad(w, h, (34, 42, 80), (20, 24, 46)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = w * .14, h * .06, w * .86, h * .90
    d.rectangle([x0 - 26, y0 - 26, x1 + 26, y1], fill=(36, 26, 28))
    d.rectangle([x0, y0, x1, y1], fill=(70, 46, 44))
    for (a, b, c, e) in ((.08, .06, .92, .40), (.08, .48, .92, .92)):
        d.rectangle([x0 + (x1 - x0) * a, y0 + (y1 - y0) * b, x0 + (x1 - x0) * c, y0 + (y1 - y0) * e],
                    outline=(52, 34, 34), width=8)
    d.rounded_rectangle([w / 2 - 70, y0 + 60, w / 2 + 70, y0 + 120], 8, fill=(200, 170, 100))
    d.text((w / 2, y0 + 90), "312", font=font(40), fill=(60, 40, 20), anchor="mm")
    d.ellipse([w / 2 - 16, y0 + 170, w / 2 + 16, y0 + 202], fill=(30, 30, 30), outline=(190, 160, 90), width=5)
    d.rounded_rectangle([x1 - 120, h * .50, x1 - 30, h * .53], 8, fill=(190, 160, 90))
    d.rectangle([0, y1, w, h], fill=(30, 28, 36))
    return im

BG_FUN = dict(room=bg_room, corridor=bg_corridor, interphone=bg_interphone, door=bg_door)
_bgc = {}
def background(kind):
    if kind not in _bgc:
        _bgc[kind] = BG_FUN[kind](int(W * 1.15), int(H * 1.15))
    return _bgc[kind]

# ---------------------------------------------------------------- TÉLÉPHONE + MAIN
def wrap(text, f, maxw, d):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = wd
    lines.append(cur); return lines

NAME_COL = {"Malik": (230, 120, 60), "Inès": (200, 80, 160), "Sami": (40, 150, 110), "Yanis": (60, 120, 220)}

def phone_screen(pw, ph, sc, t):
    s = Image.new("RGB", (pw, ph)); d = ImageDraw.Draw(s)
    clocks = sc.get("clock", ["03:00"])
    clk = clocks[min(int(t / (sc["d"] / len(clocks))), len(clocks) - 1)]
    if sc.get("chat"):
        s.paste(vgrad(pw, ph, (236, 229, 221), (226, 219, 211)))
        d.rectangle([0, 0, pw, 70], fill=(30, 40, 60))
        d.text((16, 8), clk, font=font(14), fill=WHITE)
        d.text((16, 30), sc["chat"], font=font(20), fill=WHITE)
        d.text((16, 52), "en ligne" if sc["chat"] == "Yanis" else "Malik, Inès, Sami, toi", font=font(12, False), fill=(190, 200, 220))
        shown = [m for m in sc["msgs"] if t >= m[0]]
        f = font(20, False); fn = font(15)
        blocks = []
        for (_, name, text) in shown:
            lines = wrap(text, f, pw - 70, d)
            blocks.append((name, lines, 30 + 25 * len(lines) + 12))
        y = ph - 66 - sum(b[2] + 10 for b in blocks)
        for name, lines, bh in blocks:
            bw = max(max(d.textlength(l, font=f) for l in lines), d.textlength(name, font=fn)) + 28
            d.rounded_rectangle([12, y, 12 + bw, y + bh], 14, fill=(255, 255, 255))
            d.text((26, y + 8), name, font=fn, fill=NAME_COL.get(name, (80, 80, 80)))
            for i, l in enumerate(lines):
                d.text((26, y + 30 + 25 * i), l, font=f, fill=(25, 25, 25))
            y += bh + 10
        d.rounded_rectangle([12, ph - 52, pw - 12, ph - 14], 18, fill=(255, 255, 255))
        d.text((30, ph - 33), "Message", font=font(15, False), fill=(150, 150, 150), anchor="lm")
    else:
        s.paste(vgrad(pw, ph, (40, 30, 70), (12, 10, 26)))
        d.text((pw / 2, ph * .22), clk, font=font(int(pw * .22)), fill=WHITE, anchor="mm")
        d.text((pw / 2, ph * .33), "lundi 16 novembre", font=font(int(pw * .06), False), fill=(210, 210, 230), anchor="mm")
        nt = sc.get("notif")
        if nt and t >= nt[0]:
            d.rounded_rectangle([10, ph * .40, pw - 10, ph * .40 + 104], 16, fill=(250, 250, 250))
            d.text((22, ph * .40 + 18), nt[1] + " · maintenant", font=font(13), fill=(60, 60, 60), anchor="lm")
            for i, l in enumerate(wrap(nt[2], font(17), pw - 40, d)):
                d.text((22, ph * .40 + 36 + 22 * i), l, font=font(17), fill=(200, 20, 20))
    return s

SKIN, SKIN_D, SLEEVE = (176, 112, 76), (140, 84, 56), (150, 30, 40)
def phone_layer(sc, t, size):
    cw, ch = (W, H)
    lay = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if size == "big":
        pw, ph = int(W * .62), int(W * 1.18); px, py = int(W * .19), int(H * .30)
    else:
        pw, ph = int(W * .34), int(W * .66); px, py = int(W * .08), int(H * .70)
    # manche + paume
    d.polygon([(px + pw * .55, py + ph * .75), (px + pw * 1.45, py + ph * .55), (cw + 200, ch + 50), (px + pw * .70, ch + 50)], fill=SLEEVE)
    d.ellipse([px + pw * .15, py + ph * .55, px + pw * 1.05, py + ph * 1.15], fill=SKIN)
    d.rounded_rectangle([px - 8, py - 8, px + pw + 8, py + ph + 8], int(pw * .12), fill=(15, 15, 18))
    lay.paste(phone_screen(pw - 16, ph - 16, sc, t), (px + 8 - 8 + 8, py + 8 - 8 + 8))
    d.rounded_rectangle([px + pw / 2 - pw * .14, py + 6, px + pw / 2 + pw * .14, py + 6 + pw * .05], 8, fill=(15, 15, 18))
    # doigts (gauche) et pouce (droite)
    fw, fh = pw * .22, ph * .085
    for i in range(4):
        fy = py + ph * (.42 + .11 * i)
        d.rounded_rectangle([px - fw * .75, fy, px + fw * .35, fy + fh], int(fh / 2), fill=SKIN, outline=SKIN_D, width=2)
    d.rounded_rectangle([px + pw - fw * .3, py + ph * .62, px + pw + fw * .55, py + ph * .62 + fh * 1.1], int(fh / 2), fill=SKIN, outline=SKIN_D, width=2)
    return lay.rotate(-5 if size == "small" else -3, resample=Image.BICUBIC, center=(px + pw / 2, py + ph / 2))

# ---------------------------------------------------------------- TEXTES
def outlined(d, xy, text, f, fill, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=5, stroke_fill=(0, 0, 0))

def subtitle(img, text, col, y):
    d = ImageDraw.Draw(img); f = font(36)
    lines = wrap(text, f, W * .82, d)
    for i, l in enumerate(lines):
        outlined(d, (W / 2, y + i * 46), l, f, col)

def choice_screen(img, t):
    d = ImageDraw.Draw(img)
    a = min(1, t / .6)
    outlined(d, (W / 2, H * .25), "TU FAIS QUOI ?", font(64), WHITE)
    for k, (lab, col, y) in enumerate((("OUVRIR LA PORTE", (190, 30, 40), .38), ("APPELER YANIS", (30, 90, 110), .48))):
        if t > .5 + k * .5:
            d.rounded_rectangle([W * .1, H * y, W * .9, H * y + 100], 14, fill=col, outline=WHITE, width=3)
            d.text((W / 2, H * y + 50), lab, font=font(40), fill=WHITE, anchor="mm")
    if t > 1.8:
        outlined(d, (W / 2, H * .62), "Commente ici ↓", font(34), YEL)
    d.text((W / 2, H * .97), "Fiction. Toute ressemblance avec des faits réels est une coïncidence.",
           font=font(14, False), fill=(150, 150, 150), anchor="mm")

# ---------------------------------------------------------------- RENDU IMAGE
def frame(sc, t, gt):
    kind = sc["bg"]
    if kind in ("black", "choice"):
        img = Image.new("RGB", (W, H), (6, 6, 10))
    else:
        bg = background(kind)
        z = 1.15 - 0.10 * (t / sc["d"])                   # zoom lent (Ken Burns)
        cw, ch = int(W * z), int(H * z)
        ox, oy = (bg.width - cw) // 2, (bg.height - ch) // 2
        sx = sy = 0
        for a, b in sc.get("shake", []):
            if a <= t <= b:
                sx, sy = random.randint(-14, 14), random.randint(-14, 14)
        img = bg.crop((ox + sx, oy + sy, ox + sx + cw, oy + sy + ch)).resize((W, H), Image.BILINEAR)
        d = ImageDraw.Draw(img)
        if kind == "interphone":                           # écran parasité + LED
            x0, y0 = int(W * .22 + 40), int(H * .18 + 50)
            nz = (np.random.rand(140, 180) * 70).astype(np.uint8)
            st = Image.fromarray(nz).resize((int(W * .56 - 80), 280)).convert("RGB")
            img.paste(st, (x0, y0))
            if int(gt * 3) % 2 == 0:
                d.ellipse([W * .70, H * .70, W * .70 + 22, H * .70 + 22], fill=(255, 40, 40))
        if kind == "door":                                 # lumière sous la porte + ombre de pieds
            y = int(H * .90) - 6
            d.rectangle([W * .14, y, W * .86, y + 6], fill=(255, 210, 130))
            if sc.get("msgs") or sc.get("notif") or t > 0.6:
                d.rectangle([W * .40, y, W * .46, y + 6], fill=(10, 8, 8))
                d.rectangle([W * .53, y, W * .59, y + 6], fill=(10, 8, 8))
    arr = np.asarray(img).astype(np.float32)
    flick = 1.0 if random.random() > .04 else .7          # néon qui grésille
    arr *= flick
    img = Image.fromarray(np.clip(arr * VIGNETTE[..., None] + np.random.normal(0, 6, arr.shape), 0, 255).astype(np.uint8))
    if sc.get("phone"):
        img.paste(lay := phone_layer(sc, t, sc["phone"]), (0, 0), lay)
    if kind == "choice":
        choice_screen(img, t)
    if sc.get("banner") and t < 3.5:
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([30, 40, 240, 100], 10, fill=(220, 30, 40))
        d.text((135, 70), "PARTIE 1", font=font(32), fill=WHITE, anchor="mm")
    for t0, t1, text, col in sc.get("subs", []):
        if t0 <= t <= t1:
            subtitle(img, text, col, H * (.16 if sc.get("phone") == "big" else .50))
    if kind == "black" and int(t * 4) % 2 == 0:
        subtitle(img, "…", WHITE, H * .45)
    return img

yy, xx = np.mgrid[0:H, 0:W]
VIGNETTE = np.clip(1.25 - 0.9 * (((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .7)) ** 2), .25, 1).astype(np.float32)

# ---------------------------------------------------------------- SON
SR = 44100
def synth(total, events):
    n = int(total * SR); tt = np.arange(n) / SR
    rng = np.random.default_rng(1)
    noise = np.convolve(rng.normal(0, 1, n), np.ones(400) / 400, "same")
    drone = (.18 * np.sin(2 * np.pi * 55 * tt) + .12 * np.sin(2 * np.pi * 58.3 * tt) + .07 * np.sin(2 * np.pi * 110.7 * tt))
    out = drone * (.7 + .3 * np.sin(2 * np.pi * .07 * tt)) + noise * 1.2
    def add(at, sig):
        i = int(at * SR); j = min(n, i + len(sig))
        if i < n: out[i:j] += sig[: j - i]
    for at, kind in events:
        if kind == "buzz":
            k = np.arange(int(1.1 * SR)) / SR
            add(at, .35 * np.sign(np.sin(2 * np.pi * 180 * k)) * (np.sin(2 * np.pi * 9 * k) > -.3) * np.minimum(1, (1.1 - k) * 8))
        elif kind == "knock":
            k = np.arange(int(.35 * SR)) / SR
            add(at, (np.sin(2 * np.pi * 90 * k) + .5 * rng.normal(0, 1, len(k))) * np.exp(-k * 28) * 1.1)
        elif kind == "notif":
            k = np.arange(int(.3 * SR)) / SR
            add(at, .25 * (np.sin(2 * np.pi * 880 * k) * (k < .12) + np.sin(2 * np.pi * 1320 * k) * (k >= .12)) * np.exp(-k * 6))
        elif kind == "tick":
            k = np.arange(int(.08 * SR)) / SR
            add(at, .3 * np.sin(2 * np.pi * 2000 * k) * np.exp(-k * 80))
        elif kind == "heart":
            k = np.arange(int(.5 * SR)) / SR
            b = np.sin(2 * np.pi * 50 * k) * np.exp(-k * 18)
            add(at, .9 * (b + np.concatenate([np.zeros(int(.22 * SR)), b])[: len(k)] * .7))
        elif kind == "sting":
            k = np.arange(int(2.5 * SR)) / SR
            s = sum(np.sin(2 * np.pi * f * k) for f in (311, 330, 466, 622)) * .12
            add(at, (s + .3 * rng.normal(0, 1, len(k))) * np.exp(-k * 1.4))
    out = out / max(1e-6, np.abs(out).max()) * .9
    return (out * 32767).astype(np.int16)

# ---------------------------------------------------------------- MAIN
def main():
    total = sum(s["d"] for s in SCENES)
    events, g = [], 0.0
    for sc in SCENES:
        events += [(g + a, k) for a, k in sc.get("sfx", [])]
        events += [(g + m[0], "notif") for m in sc.get("msgs", [])]
        g += sc["d"]
    wav = OUT.replace(".mp4", ".wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(synth(total, events).tobytes())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                          "-crf", "28", "-preset", "slow", "-c:a", "aac", "-b:a", "160k", "-shortest", OUT],
                         stdin=subprocess.PIPE)
    g = 0.0
    for sc in SCENES:
        for f in range(int(round(sc["d"] * FPS))):
            t = f / FPS
            p.stdin.write(frame(sc, t, g + t).tobytes())
        g += sc["d"]
    p.stdin.close(); p.wait(); os.remove(wav)
    print("OK ->", OUT, f"({total:.1f}s)")

if __name__ == "__main__":
    random.seed(7); np.random.seed(7)
    main()
