#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор логотипа канала «Стоп, что?!» — чистый вектор, без внешних зависимостей.

Стиль: комикс-«взрыв мозга». Жёлтый старбёрст на электрик-градиенте,
жирный «?!» в центре, подпись «СТОП, ЧТО?!». Пишет logo.svg.
"""
import math

W = H = 640
SPIKES = 14                # количество лучей взрыва


def starburst(cx, cy, outer, inner, spikes, rot=0.0):
    pts = []
    for i in range(spikes * 2):
        r = outer if i % 2 == 0 else inner
        a = math.pi * i / spikes + rot
        pts.append(f"{cx + r*math.cos(a):.1f},{cy + r*math.sin(a):.1f}")
    return " ".join(pts)


DEFS = '''  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0"   stop-color="#7C3AED"/>
      <stop offset="0.5" stop-color="#DB2777"/>
      <stop offset="1"   stop-color="#2563EB"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.42" r="0.65">
      <stop offset="0"   stop-color="#ffffff" stop-opacity="0.28"/>
      <stop offset="1"   stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="star" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#FDE047"/>
      <stop offset="1"   stop-color="#F59E0B"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#1e1b4b" flood-opacity="0.35"/>
    </filter>
  </defs>'''

SPARKS = '''  <g fill="#FDE047" opacity="0.9">
    <circle cx="118" cy="150" r="9"/><circle cx="540" cy="128" r="6"/>
    <circle cx="90"  cy="470" r="6"/><circle cx="560" cy="500" r="9"/>
    <circle cx="150" cy="560" r="5"/><circle cx="500" cy="360" r="5"/>
  </g>'''


def burst_group(cx, cy, outer, inner, qfont):
    o = starburst(cx, cy, outer, inner, SPIKES, rot=-math.pi/2)
    i = starburst(cx, cy, outer - 22, inner - 14, SPIKES, rot=-math.pi/2)
    return f'''  <polygon points="{o}" fill="url(#star)" stroke="#1e1b4b" stroke-width="10"
           stroke-linejoin="round" filter="url(#soft)"/>
  <polygon points="{i}" fill="none" stroke="#ffffff" stroke-width="4"
           stroke-linejoin="round" opacity="0.55"/>
  <text x="{cx}" y="{cy + qfont*0.34:.0f}" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="{qfont}"
        font-weight="900" fill="#1e1b4b" letter-spacing="-6">?!</text>'''


def frame(inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n{DEFS}\n'
            f'  <rect width="{W}" height="{H}" rx="140" fill="url(#bg)"/>\n'
            f'  <rect width="{W}" height="{H}" rx="140" fill="url(#glow)"/>\n'
            f'{SPARKS}\n{inner}\n</svg>')


# --- Полный логотип: взрыв сверху + подпись «СТОП, ЧТО?!» -------------------
full_inner = burst_group(320, 286, 268, 206, 250) + f'''
  <text x="320" y="558" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="74"
        font-weight="900" fill="#ffffff" stroke="#1e1b4b" stroke-width="7"
        paint-order="stroke" letter-spacing="1">СТОП, ЧТО?!</text>'''

# --- Аватарка: только взрыв + «?!», крупно по центру (безопасно для круга) ---
avatar_inner = burst_group(320, 320, 300, 232, 300)

for name, inner in (("logo.svg", full_inner), ("logo_avatar.svg", avatar_inner)):
    with open(name, "w", encoding="utf-8") as f:
        f.write(frame(inner))
    print(f"{name} записан")
