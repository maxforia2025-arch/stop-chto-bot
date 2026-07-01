#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Финальный неоновый логотип «Стоп, что?!». Два файла:
   logo_neon.svg         — полный (с подписью), для шапки/кросс-постов
   logo_neon_avatar.svg  — круг-safe аватарка (крупный «?!», без текста)
"""

W = H = 640

DEFS = '''
  <radialGradient id="cb" cx="0.5" cy="0.42" r="0.85">
    <stop offset="0" stop-color="#20214E"/>
    <stop offset="0.6" stop-color="#12142E"/>
    <stop offset="1" stop-color="#090B18"/>
  </radialGradient>
  <linearGradient id="cq" x1="0" y1="0" x2="0.9" y2="1">
    <stop offset="0" stop-color="#67E8F9"/>
    <stop offset="0.5" stop-color="#818CF8"/>
    <stop offset="1" stop-color="#E879F9"/>
  </linearGradient>
  <filter id="neon" x="-70%" y="-70%" width="240%" height="240%">
    <feGaussianBlur stdDeviation="9" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="softneon" x="-70%" y="-70%" width="240%" height="240%">
    <feGaussianBlur stdDeviation="14" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>'''


def bolts(lx, ly, rx, ry):
    """Две зеркальные неоновые молнии-зигзаги (fill none)."""
    left = f"M{lx},{ly} L{lx-30},{ly+62} L{lx-3},{ly+56} L{lx-26},{ly+122}"
    right = f"M{rx},{ry} L{rx+30},{ry+62} L{rx+3},{ry+56} L{rx+26},{ry+122}"
    return (f'  <g fill="none" stroke="#F0ABFC" stroke-width="11" stroke-linecap="round" '
            f'stroke-linejoin="round" filter="url(#neon)">\n'
            f'    <path d="{left}"/>\n    <path d="{right}"/>\n  </g>')


def build(with_text, cx, cy, ring_r, q_font, q_baseline):
    ring = (f'  <circle cx="{cx}" cy="{cy}" r="{ring_r}" fill="none" stroke="#22D3EE" '
            f'stroke-width="6" opacity="0.55" filter="url(#softneon)"/>')
    q = (f'  <text x="{cx}" y="{q_baseline}" text-anchor="middle" '
         f'font-family="\'Arial Black\', Impact, Arial, sans-serif" font-size="{q_font}" '
         f'font-weight="900" fill="url(#cq)" letter-spacing="-10" '
         f'filter="url(#neon)">?!</text>')
    body = [f'  <rect width="{W}" height="{H}" rx="140" fill="url(#cb)"/>',
            bolts(150, 118, 490, 118), ring, q]
    if with_text:
        body.append(
            '  <text x="320" y="572" text-anchor="middle" '
            'font-family="\'Arial Black\', Impact, Arial, sans-serif" font-size="60" '
            'font-weight="900" fill="#E0F2FE" letter-spacing="3" '
            'filter="url(#softneon)">СТОП, ЧТО?!</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n<defs>{DEFS}</defs>\n' + "\n".join(body) + "\n</svg>")


# полный (с текстом) — взрыв выше, чтобы влезла подпись
full = build(with_text=True, cx=320, cy=296, ring_r=196, q_font=250, q_baseline=380)
# аватарка (круг-safe) — крупный «?!» по центру, без текста
avatar = build(with_text=False, cx=320, cy=322, ring_r=222, q_font=300, q_baseline=428)

for name, svg in (("logo_neon.svg", full), ("logo_neon_avatar.svg", avatar)):
    with open(name, "w", encoding="utf-8") as f:
        f.write(svg)
    print(name, "записан")
