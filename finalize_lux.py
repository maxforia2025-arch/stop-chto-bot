#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Люксовый логотип «Стоп, что?!» — глянцевое золото + неон-медальон, чистый вектор.
Пишет logo_lux.svg (полный) и logo_lux_avatar.svg (круг-safe аватарка)."""

W = H = 640


def sparkle(x, y, s, fill="#FFF7DC", op=0.95):
    """4-конечная искра (вогнутый ромб)."""
    k = s * 0.16
    d = (f"M{x},{y-s} C{x+k},{y-k} {x+k},{y-k} {x+s},{y} "
         f"C{x+k},{y+k} {x+k},{y+k} {x},{y+s} "
         f"C{x-k},{y+k} {x-k},{y+k} {x-s},{y} "
         f"C{x-k},{y-k} {x-k},{y-k} {x},{y-s} Z")
    return f'<path d="{d}" fill="{fill}" opacity="{op}"/>'


DEFS = '''
  <radialGradient id="bg" cx="0.5" cy="0.4" r="0.95">
    <stop offset="0" stop-color="#1C2150"/>
    <stop offset="0.55" stop-color="#0E1130"/>
    <stop offset="1" stop-color="#05060F"/>
  </radialGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.10"/>
    <stop offset="0.4" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <!-- глянцевое золото для ?! -->
  <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFF6D5"/>
    <stop offset="0.32" stop-color="#FFE08A"/>
    <stop offset="0.55" stop-color="#F4B740"/>
    <stop offset="0.78" stop-color="#D9891B"/>
    <stop offset="1" stop-color="#9C5A12"/>
  </linearGradient>
  <!-- верхний блик -->
  <linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.9"/>
    <stop offset="0.42" stop-color="#ffffff" stop-opacity="0.05"/>
    <stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#FFE9A8"/>
    <stop offset="0.5" stop-color="#E0A733"/>
    <stop offset="1" stop-color="#8A5A16"/>
  </linearGradient>
  <linearGradient id="txt" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFFDF5"/>
    <stop offset="1" stop-color="#F3D9A0"/>
  </linearGradient>
  <filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="10" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="cyanglow" x="-90%" y="-90%" width="280%" height="280%">
    <feGaussianBlur stdDeviation="7" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="drop" x="-60%" y="-60%" width="220%" height="220%">
    <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000000" flood-opacity="0.55"/>
  </filter>
  <radialGradient id="bok" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.5"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </radialGradient>'''


def qmark(cx, y, font, gloss=True):
    """Глянцевый золотой ?! со свечением, тенью и верхним бликом."""
    fam = "'Arial Black', Impact, Arial, sans-serif"
    layers = []
    # тёплое свечение под знаком
    layers.append(
        f'<text x="{cx}" y="{y}" text-anchor="middle" font-family="{fam}" '
        f'font-size="{font}" font-weight="900" letter-spacing="-10" '
        f'fill="#F4B740" opacity="0.45" filter="url(#glow)">?!</text>')
    # основной золотой знак с падающей тенью
    layers.append(
        f'<text x="{cx}" y="{y}" text-anchor="middle" font-family="{fam}" '
        f'font-size="{font}" font-weight="900" letter-spacing="-10" '
        f'fill="url(#gold)" stroke="#7A4A11" stroke-width="2.5" '
        f'filter="url(#drop)">?!</text>')
    # верхний глянцевый блик
    if gloss:
        layers.append(
            f'<text x="{cx}" y="{y}" text-anchor="middle" font-family="{fam}" '
            f'font-size="{font}" font-weight="900" letter-spacing="-10" '
            f'fill="url(#gloss)">?!</text>')
    return "\n  ".join(layers)


def medallion(cx, cy, r):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r+16}" fill="none" stroke="#22D3EE" '
        f'stroke-width="3" opacity="0.35" filter="url(#cyanglow)"/>\n  '
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#ring)" '
        f'stroke-width="7" filter="url(#glow)"/>\n  '
        f'<circle cx="{cx}" cy="{cy}" r="{r-9}" fill="none" stroke="#FFF3C4" '
        f'stroke-width="1.5" opacity="0.5"/>')


BOKEH = '''
  <g>
    <circle cx="130" cy="150" r="70" fill="url(#bok)" opacity="0.25"/>
    <circle cx="520" cy="140" r="55" fill="url(#bok)" opacity="0.20"/>
    <circle cx="540" cy="470" r="80" fill="url(#bok)" opacity="0.18"/>
    <circle cx="110" cy="500" r="50" fill="url(#bok)" opacity="0.16"/>
  </g>'''


def sparkles():
    return "  " + "\n  ".join([
        sparkle(150, 132, 20), sparkle(505, 120, 15, op=0.8),
        sparkle(540, 300, 12, op=0.7), sparkle(112, 360, 13, op=0.7),
        sparkle(470, 470, 10, "#BFEFFF", 0.7), sparkle(190, 505, 9, op=0.6),
    ])


def build(with_text, cx, cy, ring_r, font, baseline):
    body = [
        f'<rect width="{W}" height="{H}" rx="150" fill="url(#bg)"/>',
        f'<rect width="{W}" height="{H}" rx="150" fill="url(#sheen)"/>',
        BOKEH,
        sparkles(),
        medallion(cx, cy, ring_r),
        qmark(cx, baseline, font),
    ]
    if with_text:
        body.append(
            '<text x="320" y="582" text-anchor="middle" '
            'font-family="\'Arial Black\', Impact, Arial, sans-serif" font-size="58" '
            'font-weight="900" fill="url(#txt)" letter-spacing="6" '
            'filter="url(#glow)">СТОП, ЧТО?!</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n<defs>{DEFS}</defs>\n  ' + "\n  ".join(body) + "\n</svg>")


full = build(True, cx=320, cy=292, ring_r=182, font=232, baseline=372)
avatar = build(False, cx=320, cy=322, ring_r=214, font=290, baseline=424)

for name, svg in (("logo_lux.svg", full), ("logo_lux_avatar.svg", avatar)):
    with open(name, "w", encoding="utf-8") as f:
        f.write(svg)
    print(name, "записан")
