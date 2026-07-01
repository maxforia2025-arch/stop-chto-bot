#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4 чистых минималистичных аватарки «Стоп, что?!». Вектор, stdlib.
Идея: минимум декора, крупный «?!», современный flat-стиль. Круг-safe."""

W = H = 640
FAM = "'Arial Black', Impact, Arial, sans-serif"


def svg(defs, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}"><defs>{defs}</defs>{body}</svg>')


def q(fill, y=430, font=330, extra=""):
    return (f'<text x="320" y="{y}" text-anchor="middle" font-family="{FAM}" '
            f'font-size="{font}" font-weight="900" letter-spacing="-14" '
            f'fill="{fill}"{extra}>?!</text>')


# ── D1. Коралловый минимал: белый ?! на тёплом градиенте ────────────────────
d1 = svg(
    '<linearGradient id="g" x1="0" y1="0" x2="0.4" y2="1">'
    '<stop offset="0" stop-color="#FF8A3D"/><stop offset="0.55" stop-color="#FF5A5F"/>'
    '<stop offset="1" stop-color="#E23E7A"/></linearGradient>'
    '<filter id="sh"><feDropShadow dx="0" dy="10" stdDeviation="10" '
    'flood-color="#7a0f2e" flood-opacity="0.35"/></filter>',
    '<rect width="640" height="640" rx="150" fill="url(#g)"/>'
    + q("#ffffff", extra=' filter="url(#sh)"'))

# ── D2. Дуотон-сплит: индиго/розовый по диагонали, белый ?! ─────────────────
d2 = svg(
    '<clipPath id="c"><rect width="640" height="640" rx="150"/></clipPath>',
    '<g clip-path="url(#c)">'
    '<rect width="640" height="640" fill="#4F46E5"/>'
    '<polygon points="640,0 640,640 0,640" fill="#EC4899"/>'
    '<polygon points="0,0 640,0 0,640" fill="#6366F1" opacity="0"/>'
    '</g>'
    + q("#ffffff", extra=' stroke="#312E81" stroke-width="0"'))

# ── D3. Тёмный минимал: градиентный ?! со свечением на графите ──────────────
d3 = svg(
    '<radialGradient id="bg" cx="0.5" cy="0.42" r="0.9">'
    '<stop offset="0" stop-color="#232338"/><stop offset="1" stop-color="#0D0D17"/>'
    '</radialGradient>'
    '<linearGradient id="q" x1="0" y1="0" x2="0.8" y2="1">'
    '<stop offset="0" stop-color="#8B5CF6"/><stop offset="0.5" stop-color="#EC4899"/>'
    '<stop offset="1" stop-color="#F59E0B"/></linearGradient>'
    '<filter id="gl" x="-60%" y="-60%" width="220%" height="220%">'
    '<feGaussianBlur stdDeviation="16" result="b"/>'
    '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    '<rect width="640" height="640" rx="150" fill="url(#bg)"/>'
    + q("url(#q)", extra=' filter="url(#gl)"'))

# ── D4. Стикер: белый ?! с толстым контуром на сочном фиолетовом ────────────
d4 = svg(
    '<linearGradient id="g" x1="0" y1="0" x2="0.5" y2="1">'
    '<stop offset="0" stop-color="#A855F7"/><stop offset="1" stop-color="#6D28D9"/>'
    '</linearGradient>'
    '<filter id="sh"><feDropShadow dx="0" dy="12" stdDeviation="8" '
    'flood-color="#2E1065" flood-opacity="0.5"/></filter>',
    '<rect width="640" height="640" rx="150" fill="url(#g)"/>'
    + q("#ffffff", extra=' stroke="#3B0764" stroke-width="16" paint-order="stroke" '
        'filter="url(#sh)"'))

for name, s in (("clean_d1.svg", d1), ("clean_d2.svg", d2),
                ("clean_d3.svg", d3), ("clean_d4.svg", d4)):
    with open(name, "w", encoding="utf-8") as f:
        f.write(s)
    print(name, "записан")
