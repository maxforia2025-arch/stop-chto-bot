#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор фирменных карточек-картинок к постам «Стоп, что?!».
Каждый факт → красивый PNG в стиле аватарки (коралловый градиент).
Рендер SVG→PNG: rsvg-convert → cairosvg → Chrome (что найдётся).
Только stdlib (+ опц. системные утилиты рендера)."""

import os
import html
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CARD_W, CARD_H = 1080, 1350
MARGIN = 90
FONT_STACK = "'Arial Black','Montserrat','DejaVu Sans','Helvetica',sans-serif"


def wrap(text, font_px, max_w=CARD_W - 2 * MARGIN, cw=0.62):
    """Простой перенос по словам (оценка ширины символа; Arial Black широкий)."""
    max_chars = max(6, int(max_w / (font_px * cw)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _tspans(text, x, y, font_px, lh, fill, weight=900, spacing=0, extra=""):
    out = []
    for i, line in enumerate(wrap(text, font_px)):
        out.append(
            f'<text x="{x}" y="{y + i*lh:.0f}" font-family="{FONT_STACK}" '
            f'font-size="{font_px}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{spacing}"{extra}>{html.escape(line)}</text>')
    return "\n  ".join(out), y + len(wrap(text, font_px)) * lh


def build_card_svg(fact):
    cat = html.escape(fact.get("cat", "").upper())
    title = fact["title"]
    body = fact["fact"]
    wow = fact.get("wow", "").strip()

    y = 250  # курсор
    parts = []

    # категория-чип
    chip_w = 90 + len(cat) * 26
    parts.append(
        f'<rect x="{MARGIN}" y="150" width="{chip_w}" height="66" rx="33" fill="#ffffff"/>'
        f'<text x="{MARGIN + chip_w/2:.0f}" y="196" text-anchor="middle" '
        f'font-family="{FONT_STACK}" font-size="34" font-weight="900" '
        f'fill="#E23E7A" letter-spacing="2">{cat}</text>')

    # заголовок
    tsvg, y = _tspans(title, MARGIN, 330, 76, 86, "#ffffff", 900, -1)
    parts.append(tsvg)
    y += 20

    # разделитель
    parts.append(f'<rect x="{MARGIN}" y="{y:.0f}" width="120" height="8" rx="4" '
                 f'fill="#ffffff" opacity="0.85"/>')
    y += 56

    # текст факта
    bsvg, y = _tspans(body, MARGIN, y + 10, 44, 60, "#FFF2EC", 600, 0)
    parts.append(bsvg)

    # вау-плашка (плавает сразу под текстом)
    if wow:
        wow_lines = wrap(wow, 44, max_w=CARD_W - 2 * MARGIN - 88)
        box_h = 66 + len(wow_lines) * 58
        box_y = y + 30
        parts.append(
            f'<rect x="{MARGIN}" y="{box_y:.0f}" width="{CARD_W - 2*MARGIN}" '
            f'height="{box_h}" rx="34" fill="#ffffff"/>')
        ty = box_y + 74
        for i, line in enumerate(wow_lines):
            parts.append(
                f'<text x="{MARGIN + 44}" y="{ty + i*58:.0f}" font-family="{FONT_STACK}" '
                f'font-size="44" font-weight="800" fill="#C21F5B">'
                f'{html.escape(line)}</text>')

    # футер-бренд
    parts.append(
        f'<text x="{MARGIN}" y="{CARD_H - 120}" font-family="{FONT_STACK}" '
        f'font-size="52" font-weight="900" fill="#ffffff">СТОП, ЧТО?!</text>'
        f'<text x="{CARD_W - MARGIN}" y="{CARD_H - 120}" text-anchor="end" '
        f'font-family="{FONT_STACK}" font-size="38" font-weight="700" '
        f'fill="#FFE0D6">@stop_chto_daily</text>')

    body_svg = "\n  ".join(parts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="#FF8A3D"/>
      <stop offset="0.5" stop-color="#FF5A5F"/>
      <stop offset="1" stop-color="#E23E7A"/>
    </linearGradient>
  </defs>
  <rect width="{CARD_W}" height="{CARD_H}" fill="url(#bg)"/>
  <text x="{CARD_W-40}" y="{CARD_H-260}" text-anchor="end" font-family="{FONT_STACK}"
        font-size="420" font-weight="900" fill="#ffffff" opacity="0.08"
        letter-spacing="-20">?!</text>
  {body_svg}
</svg>'''


def render_card(fact, out_path=None):
    """Собрать SVG факта и растеризовать в PNG. Вернуть путь к PNG или None."""
    out_path = out_path or os.path.join(HERE, "card_tmp.png")
    svg_path = os.path.join(HERE, "card_tmp.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(build_card_svg(fact))

    # 1) rsvg-convert (быстро, идеально для CI)
    if shutil.which("rsvg-convert"):
        r = subprocess.run(["rsvg-convert", "-w", str(CARD_W), "-h", str(CARD_H),
                            svg_path, "-o", out_path], capture_output=True)
        if r.returncode == 0 and os.path.exists(out_path):
            return out_path

    # 2) cairosvg (python)
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=out_path,
                         output_width=CARD_W, output_height=CARD_H)
        if os.path.exists(out_path):
            return out_path
    except Exception:
        pass

    # 3) Chrome headless (локально на Mac)
    for chrome in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   shutil.which("google-chrome"), shutil.which("chromium")):
        if chrome and os.path.exists(chrome) if chrome else False:
            r = subprocess.run([chrome, "--headless", "--disable-gpu",
                                "--force-device-scale-factor=1", "--hide-scrollbars",
                                f"--window-size={CARD_W},{CARD_H}",
                                f"--screenshot={out_path}", svg_path],
                               capture_output=True)
            if os.path.exists(out_path):
                return out_path
    return None


if __name__ == "__main__":
    import json
    facts = json.load(open(os.path.join(HERE, "facts.json"), encoding="utf-8"))
    p = render_card(facts[0], os.path.join(HERE, "card_preview.png"))
    print("PNG:", p)
