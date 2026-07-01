#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Три альтернативных концепта логотипа «Стоп, что?!» — чистый вектор, stdlib.
Каждый оптимизирован под круглую аватарку (главный элемент в центре)."""

W = H = 640


def wrap(defs, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n<defs>{defs}</defs>\n{body}\n</svg>')


# ── A. Речевой пузырь (Telegram-native) ────────────────────────────────────
concept_a = wrap(
    '''
    <linearGradient id="ab" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#22D3EE"/>
      <stop offset="0.55" stop-color="#3B82F6"/>
      <stop offset="1" stop-color="#6366F1"/>
    </linearGradient>
    <filter id="ash" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#0b1030" flood-opacity="0.35"/>
    </filter>''',
    '''  <rect width="640" height="640" rx="140" fill="url(#ab)"/>
  <g filter="url(#ash)">
    <rect x="112" y="120" width="416" height="300" rx="60" fill="#ffffff"/>
    <path d="M 250 400 L 250 500 L 340 408 Z" fill="#ffffff"/>
  </g>
  <text x="320" y="352" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="210"
        font-weight="900" fill="#2563EB" letter-spacing="-8">?!</text>
  <text x="320" y="576" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="60"
        font-weight="900" fill="#ffffff" stroke="#0b1030" stroke-width="6"
        paint-order="stroke">СТОП, ЧТО?!</text>''')


# ── B. Красный алерт / STOP ────────────────────────────────────────────────
concept_b = wrap(
    '''
    <radialGradient id="bb" cx="0.5" cy="0.4" r="0.75">
      <stop offset="0" stop-color="#F87171"/>
      <stop offset="0.5" stop-color="#DC2626"/>
      <stop offset="1" stop-color="#7F1D1D"/>
    </radialGradient>
    <filter id="bsh" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#450a0a" flood-opacity="0.45"/>
    </filter>''',
    # правильный восьмиугольник (знак STOP), r=205, центр (320,290)
    '''  <rect width="640" height="640" rx="140" fill="url(#bb)"/>
  <polygon points="509.4,368.4 398.4,479.4 241.6,479.4 130.6,368.4 130.6,211.6 241.6,100.6 398.4,100.6 509.4,211.6"
           fill="none" stroke="#ffffff" stroke-width="22" stroke-linejoin="round"
           filter="url(#bsh)"/>
  <text x="320" y="368" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="230"
        font-weight="900" fill="#ffffff" letter-spacing="-8"
        filter="url(#bsh)">?!</text>
  <text x="320" y="566" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="62"
        font-weight="900" fill="#ffffff" letter-spacing="2">СТОП, ЧТО?!</text>''')


# ── C. Неон в темноте (премиум) ────────────────────────────────────────────
concept_c = wrap(
    '''
    <radialGradient id="cb" cx="0.5" cy="0.42" r="0.8">
      <stop offset="0" stop-color="#1E1B4B"/>
      <stop offset="1" stop-color="#0B1020"/>
    </radialGradient>
    <filter id="neon" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="12" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="cq" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#22D3EE"/>
      <stop offset="1" stop-color="#E879F9"/>
    </linearGradient>''',
    '''  <rect width="640" height="640" rx="140" fill="url(#cb)"/>
  <g stroke="#F0ABFC" stroke-width="7" stroke-linecap="round" opacity="0.9" filter="url(#neon)">
    <path d="M 150 120 L 120 210 L 175 205"/>
    <path d="M 500 130 L 540 210 L 486 214"/>
  </g>
  <circle cx="320" cy="300" r="188" fill="none" stroke="#22D3EE" stroke-width="6"
          opacity="0.6" filter="url(#neon)"/>
  <text x="320" y="378" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="250"
        font-weight="900" fill="url(#cq)" letter-spacing="-8"
        filter="url(#neon)">?!</text>
  <text x="320" y="566" text-anchor="middle"
        font-family="'Arial Black', Impact, Arial, sans-serif" font-size="60"
        font-weight="900" fill="#E0F2FE" letter-spacing="3">СТОП, ЧТО?!</text>''')


for name, svg in (("concept_a.svg", concept_a),
                  ("concept_b.svg", concept_b),
                  ("concept_c.svg", concept_c)):
    with open(name, "w", encoding="utf-8") as f:
        f.write(svg)
    print(name, "записан")
