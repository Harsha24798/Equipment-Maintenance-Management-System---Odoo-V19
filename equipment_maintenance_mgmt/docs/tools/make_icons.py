"""Generate the app icon (static/description/icon.png + icon.svg) and banner.png.

Usage: python docs/tools/make_icons.py static/description
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
S = 1024  # supersampled canvas, downscaled for anti-aliasing

TOP = (0x1A, 0xB0, 0xA5)     # teal
BOTTOM = (0x0B, 0x5E, 0x7A)  # deep blue-teal
WHITE = (255, 255, 255, 255)
ACCENT = (0xFF, 0xB3, 0x2E, 255)  # amber


def gradient(size, top, bottom):
    img = Image.new('RGBA', size)
    w, h = size
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.35 + y / h * 0.65)
            px[x, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
    return img


def gear_polygon(cx, cy, r_out, r_in, teeth):
    pts = []
    steps = teeth * 4
    for i in range(steps):
        a = 2 * math.pi * i / steps
        r = r_out if (i % 4) in (0, 1) else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_symbol(d, cx, cy, scale):
    # gear
    d.polygon(gear_polygon(cx, cy, 300 * scale, 245 * scale, 10), fill=WHITE)
    d.ellipse([cx - 120 * scale, cy - 120 * scale, cx + 120 * scale, cy + 120 * scale],
              fill=(0, 0, 0, 0))
    # wrench across the gear (rotated bar + open jaw head)
    wrench = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wrench)
    length = 330 * scale
    bw = 62 * scale
    wd.rounded_rectangle([S / 2 - bw, S / 2 - length, S / 2 + bw, S / 2 + length * 0.95],
                         radius=bw, fill=ACCENT)
    hr = 120 * scale
    hx, hy = S / 2, S / 2 - length
    wd.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=ACCENT)
    wd.rectangle([hx - 48 * scale, hy - hr - 5, hx + 48 * scale, hy + 20 * scale], fill=(0, 0, 0, 0))
    return wrench.rotate(-45, resample=Image.BICUBIC, center=(S / 2, S / 2))


def make_icon():
    base = gradient((S, S), TOP, BOTTOM)
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=180, fill=255)
    icon = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    icon.paste(base, (0, 0), mask)

    layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    wrench = draw_symbol(d, S / 2, S / 2, 1.0)
    # punch the gear hole transparent then show background through it
    icon = Image.alpha_composite(icon, layer)
    hole = Image.new('L', (S, S), 0)
    ImageDraw.Draw(hole).ellipse([S / 2 - 120, S / 2 - 120, S / 2 + 120, S / 2 + 120], fill=255)
    icon.paste(base, (0, 0), hole)
    icon = Image.alpha_composite(icon, wrench)
    icon.resize((128, 128), Image.LANCZOS).save(os.path.join(OUT, 'icon.png'))
    return icon


def make_banner(icon):
    width, height = 1400, 700
    banner = gradient((width, height), TOP, BOTTOM)
    ic = icon.resize((360, 360), Image.LANCZOS)
    banner.alpha_composite(ic, (110, 170))
    d = ImageDraw.Draw(banner)
    try:
        f_big = ImageFont.truetype('segoeuib.ttf', 62)
        f_mid = ImageFont.truetype('segoeui.ttf', 30)
        f_small = ImageFont.truetype('segoeui.ttf', 30)
    except OSError:
        f_big = f_mid = f_small = ImageFont.load_default()
    d.text((540, 200), 'Equipment', font=f_big, fill=WHITE)
    d.text((540, 275), 'Maintenance Management', font=f_big, fill=WHITE)
    d.text((545, 380), 'Equipment | Requests | Activities | Spare Parts | Costs',
           font=f_mid, fill=(230, 250, 248, 255))
    d.text((545, 440), 'Odoo 19  -  by Harsha Madushan', font=f_small, fill=ACCENT)
    banner.convert('RGB').save(os.path.join(OUT, 'banner.png'))


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="#1AB0A5"/>
      <stop offset="1" stop-color="#0B5E7A"/>
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="22" fill="url(#g)"/>
  <path fill="#fff" fill-rule="evenodd" d="{gear}Z M64 49a15 15 0 1 0 0.01 0Z"/>
  <g transform="rotate(45 64 64)" fill="#FFB32E">
    <rect x="56.3" y="22.8" width="15.4" height="80" rx="7.7"/>
    <path d="M64 8a15 15 0 1 0 0.01 0Z M58 6h12v19h-12Z" fill-rule="evenodd"/>
  </g>
</svg>
"""


def svg_gear():
    pts = gear_polygon(64, 64, 37.5, 30.6, 10)
    return 'M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in pts)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    ic = make_icon()
    make_banner(ic)
    with open(os.path.join(OUT, 'icon.svg'), 'w', encoding='utf-8') as fh:
        fh.write(SVG.replace('{gear}', svg_gear()))
    sys.stdout.write(f'icons written to {OUT}\n')
