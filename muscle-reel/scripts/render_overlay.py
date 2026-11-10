#!/usr/bin/env python3
"""Render the UI overlay for a 3D muscle workout reel as a transparent PNG sequence.

  python3 render_overlay.py reel.json            -> <workdir>/ov/00000.png ... + <workdir>/timeline.json

What it draws (all measured from the reference reel, scaled to 1080x1920):
  - a frosted glass bar near the top holding a carousel of muscle-map icons
  - a fixed neon frame on the middle slot, in the current muscle's color, with glow
  - the muscle name above the bar: wipes in with a light flare when it's spoken, smears out before the switch
  - the carousel slides one slot left (with motion blur) at every section change
  - the end card: fade to black, app logo tile scales in, "Download on the App Store" under it
Timing comes from the clip durations in reel.json, so the overlay always matches the cut.
"""
import json, math, os, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, '..', 'assets', 'fonts', 'Archivo.ttf')  # variable font: wdth 62-125, wght 100-900
SF = '/System/Library/Fonts/SFNS.ttf'  # macOS system font, has the Apple logo glyph

W, H = 1080, 1920
BAR = (128, 225, 956, 445)        # frosted bar
BOX = (432, 199, 652, 473)        # neon frame (middle slot)
SLOT_CX, SLOT_CY, SPACING = 540, 335, 286
THUMB_H = 190
LABEL_CY = 146


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def font(size, wdth=125, wght=850):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([wght, wdth])
    except Exception:
        pass
    return f


def load_config(path):
    cfg = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    cfg['_base'] = base
    fps = cfg.get('fps', 30)
    t = 0.0
    secs = []
    for s in cfg['sections']:
        d = sum(c['dur'] for c in s['clips'])
        secs.append({**s, 'start': t, 'end': t + d})
        t += d
    end_start = t
    intro = cfg.get('intro_seconds', 4.6)  # first label waits for the intro line
    for i, s in enumerate(secs):
        s['label_in'] = s['start'] + (intro if i == 0 else cfg.get('label_delay', 1.3))
        s['label_out'] = s['end'] - (0.7 if i < len(secs) - 1 else 0.5)
    tl = {'fps': fps, 'sections': secs, 'end_start': end_start, 'end_seconds': cfg.get('end_card_seconds', 3.0)}
    tl['total'] = end_start + tl['end_seconds']
    return cfg, tl


# ---------- assets prepared once per process ----------
_A = {}


def prep(cfg, tl):
    if _A:
        return _A
    thumbs = []
    for s in tl['sections']:
        im = Image.open(os.path.join(cfg['_base'], s['thumb'])).convert('RGB')
        # alpha from brightness (icons are rendered on black), then crop to the figure
        lum = im.convert('L')
        alpha = lum.point(lambda v: 0 if v < 10 else min(255, int((v - 10) * 6)))
        rgba = im.copy()
        rgba.putalpha(alpha)
        bbox = alpha.point(lambda v: 255 if v > 40 else 0).getbbox()
        rgba = rgba.crop(bbox)
        rgba = rgba.crop((0, 0, rgba.width, int(rgba.height * 0.70)))  # neck to hips, like the reference
        sc = THUMB_H / rgba.height
        rgba = rgba.resize((max(1, int(rgba.width * sc)), THUMB_H), Image.LANCZOS)
        if rgba.width > SPACING - 40:
            sc = (SPACING - 40) / rgba.width
            rgba = rgba.resize((SPACING - 40, int(rgba.height * sc)), Image.LANCZOS)
        a = rgba.getchannel('A')
        grey = rgba.convert('L').point(lambda v: int(v * 0.5)).convert('RGB')
        dim = grey.copy()
        dim.putalpha(a.point(lambda v: int(v * 0.85)))
        thumbs.append({'color': rgba, 'dim': dim})
    _A['thumbs'] = thumbs
    # label images: white wide bold caps with a soft shadow
    lf = font(cfg.get('label_size', 38))
    labels = []
    for s in tl['sections']:
        txt = s['name'].upper()
        bb = lf.getbbox(txt)
        tw, th = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        im = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
        sh = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((20 - bb[0], 22 - bb[1]), txt, font=lf, fill=(0, 0, 0, 170))
        ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), txt, font=lf, fill=(255, 255, 255, 255))
        labels.append(Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), im))
    _A['labels'] = labels
    # bar: translucent glass with a thin light border and top highlight
    bar = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(bar)
    d.rounded_rectangle(BAR, 26, fill=(120, 126, 138, 58), outline=(215, 220, 230, 95), width=2)
    d.line((BAR[0] + 26, BAR[1] + 2, BAR[2] - 26, BAR[1] + 2), fill=(255, 255, 255, 70), width=2)
    _A['bar'] = bar
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle((BAR[0] + 3, BAR[1] + 3, BAR[2] - 3, BAR[3] - 3), 24, fill=255)
    _A['bar_mask'] = m
    _A['glow_cache'] = {}
    # end card pieces
    app = cfg.get('app', {})
    _A['app'] = app
    tile = Image.new('RGBA', (240, 240), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.rounded_rectangle((0, 0, 239, 239), 54, fill=hexrgb(app.get('tile_color', '#1C1C1E')) + (255,), outline=(70, 70, 74, 255), width=2)
    words = app.get('logo_lines') or [app.get('name', 'APP').upper()]
    lf2 = font(int(app.get('logo_size', 64 if len(words) == 1 else 52)), wdth=118, wght=900)
    lines = [(w, lf2.getbbox(w)) for w in words]
    total_h = sum(b[3] - b[1] for _, b in lines) + 8 * (len(lines) - 1)
    y = (240 - total_h) / 2
    for w, b in lines:
        x = (240 - (b[2] - b[0])) / 2 - b[0]
        td.text((x, y - b[1]), w, font=lf2, fill=(255, 255, 255, 255))
        y += (b[3] - b[1]) + 8
    _A['tile'] = tile.transform(tile.size, Image.AFFINE, (1, 0.12, -14, 0, 1, 0), Image.BICUBIC) if app.get('italic', True) else tile
    badge = Image.new('RGBA', (520, 110), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    try:
        apple = ImageFont.truetype(SF, 62)
        small = ImageFont.truetype(SF, 20)
        big = ImageFont.truetype(SF, 38)
        bd.text((70, 18), '', font=apple, fill='white')
        bd.text((140, 22), 'Download on the', font=small, fill='white')
        bd.text((138, 44), 'App Store', font=big, fill='white')
    except Exception:
        f2 = font(30, wdth=100, wght=600)
        bd.text((60, 35), 'Download on the App Store', font=f2, fill='white')
    _A['badge'] = badge
    return _A


def neon(color):
    key = tuple(int(c) for c in color)
    if key in _A['glow_cache']:
        return _A['glow_cache'][key]
    pad = 40
    w, h = BOX[2] - BOX[0] + 2 * pad, BOX[3] - BOX[1] + 2 * pad
    r = (pad, pad, w - pad, h - pad)
    glow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(r, 18, outline=key + (255,), width=12)
    glow = glow.filter(ImageFilter.GaussianBlur(13))
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(r, 18, fill=key + (10,))
    layer = Image.alpha_composite(layer, glow)
    crisp = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(crisp).rounded_rectangle(r, 18, outline=tuple(min(255, c + 60) for c in key) + (255,), width=4)
    layer = Image.alpha_composite(layer, crisp)
    _A['glow_cache'][key] = (layer, pad)
    return layer, pad


def carousel_state(t, tl):
    """(index of selected section, slide progress 0..1 toward the next one)."""
    secs = tl['sections']
    for i, s in enumerate(secs[1:], start=1):
        a, b = s['start'] - 0.12, s['start'] + 0.16
        if a <= t < b:
            return i - 1, ease((t - a) / (b - a))
        if t < a:
            return i - 1, 0.0
    return len(secs) - 1, 0.0


def draw_strip(idx, p, tl):
    n = len(tl['sections'])
    strip = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for k in range(-2, 4):
        j = (idx + k) % n
        x = SLOT_CX + (k - p) * SPACING
        dist = abs(k - p)
        on = max(0.0, 1.0 - dist)
        th = _A['thumbs'][j]
        im = th['dim'] if on <= 0 else (th['color'] if on >= 1 else Image.blend(th['dim'], th['color'], on))
        strip.alpha_composite(im, (int(x - im.width / 2), int(SLOT_CY - im.height / 2)))
    speed = math.sin(math.pi * p) if 0 < p < 1 else 0
    if speed > 0.05:  # horizontal-only motion blur: squeeze the width, then stretch it back
        k = 1 + 14 * speed
        strip = strip.resize((max(1, int(W / k)), H), Image.BOX).resize((W, H), Image.BILINEAR)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(strip, (0, 0), ImageChops.multiply(strip.getchannel('A'), _A['bar_mask']))
    return out


def draw_label(frame, t, tl):
    for i, s in enumerate(tl['sections']):
        if not (s['label_in'] <= t < s['label_out'] + 0.32):
            continue
        lab = _A['labels'][i]
        x0, y0 = int(W / 2 - lab.width / 2), int(LABEL_CY - lab.height / 2)
        if t < s['label_in'] + 0.28:  # wipe in with a light flare at the edge
            q = ease((t - s['label_in']) / 0.28)
            cut = int(lab.width * q)
            part = lab.crop((0, 0, max(1, cut), lab.height))
            frame.alpha_composite(part, (x0, y0))
            fl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(fl).ellipse((x0 + cut - 90, LABEL_CY - 7, x0 + cut + 90, LABEL_CY + 7), fill=(255, 255, 255, int(230 * (1 - q * 0.6))))
            frame.alpha_composite(fl.filter(ImageFilter.GaussianBlur(6)))
        elif t >= s['label_out']:  # smear out to the right
            q = ease((t - s['label_out']) / 0.32)
            cut = int(lab.width * q)
            part = lab.crop((cut, 0, lab.width, lab.height))
            smear = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            for c in range(6):
                ghost = part.copy()
                ghost.putalpha(part.getchannel('A').point(lambda v, c=c: int(v * (1 - c / 6) * 0.6)))
                smear.alpha_composite(ghost, (x0 + cut + int(c * 22 * q), y0))
            frame.alpha_composite(smear)
        else:
            frame.alpha_composite(lab, (x0, y0))


def render(args):
    path, f0, f1, outdir = args
    cfg, tl = load_config(path)
    prep(cfg, tl)
    fps = tl['fps']
    E = tl['end_start']
    for f in range(f0, f1):
        t = f / fps
        frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ui_alpha = 1.0 if t < E - 0.45 else max(0.0, 1 - (t - (E - 0.45)) / 0.35)
        if ui_alpha > 0:
            ui = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ui.alpha_composite(_A['bar'])
            idx, p = carousel_state(t, tl)
            ui.alpha_composite(draw_strip(idx, p, tl))
            secs = tl['sections']
            c0 = hexrgb(secs[idx]['color'])
            c1 = hexrgb(secs[(idx + 1) % len(secs)]['color'])
            col = tuple(int(lerp(a, b, p)) for a, b in zip(c0, c1))
            layer, pad = neon(col)
            ui.alpha_composite(layer, (BOX[0] - pad, BOX[1] - pad))
            draw_label(ui, t, tl)
            if ui_alpha < 1:
                ui.putalpha(ui.getchannel('A').point(lambda v: int(v * ui_alpha)))
            frame.alpha_composite(ui)
        if t >= E - 0.5:  # end card
            k = min(1.0, (t - (E - 0.5)) / 0.5)
            black = Image.new('RGBA', (W, H), (0, 0, 0, int(255 * k)))
            frame = Image.alpha_composite(frame, black) if k < 1 else black
            if t >= E - 0.1:
                q = ease((t - (E - 0.1)) / 0.4)
                tile = _A['tile']
                s = 0.72 + 0.28 * q
                tw = int(tile.width * s)
                ti = tile.resize((tw, tw), Image.LANCZOS)
                ti.putalpha(ti.getchannel('A').point(lambda v: int(v * q)))
                frame.alpha_composite(ti, (W // 2 - tw // 2, 806 - tw // 2))
            if t >= E + 0.35:
                q = ease((t - (E + 0.35)) / 0.35)
                b = _A['badge'].copy()
                b.putalpha(b.getchannel('A').point(lambda v: int(v * q)))
                frame.alpha_composite(b, (W // 2 - b.width // 2 - 10, 1250))
        frame.save(os.path.join(outdir, f'{f:05d}.png'), compress_level=1)
    return f1 - f0


def main():
    path = sys.argv[1]
    cfg, tl = load_config(path)
    outdir = os.path.join(cfg['_base'], cfg.get('overlay_dir', 'ov'))
    os.makedirs(outdir, exist_ok=True)
    total = int(round(tl['total'] * tl['fps']))
    workers = os.cpu_count() or 4
    step = math.ceil(total / workers)
    jobs = [(path, a, min(total, a + step), outdir) for a in range(0, total, step)]
    with ProcessPoolExecutor(workers) as ex:
        done = sum(ex.map(render, jobs))
    json.dump({k: v for k, v in tl.items()}, open(os.path.join(cfg['_base'], 'timeline.json'), 'w'), indent=1)
    print(f'overlay: {done} frames -> {outdir}  ({tl["total"]:.2f}s)')


if __name__ == '__main__':
    main()
