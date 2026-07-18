#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Еженедельная реклама канала «Эвномия» в канале «Стоп, что?!».

Каждое воскресенье публикует промо-пост: мраморно-тёмная карточка (контраст
к коралловым фактам) + подпись со ссылкой. Креативы ротируются, чтобы реклама
не приедалась. Только stdlib.

Запуск:
    python3 promo.py --dry-run          # показать, не отправлять
    BOT_TOKEN=... CHANNEL_ID=... python3 promo.py
"""
import os
import json
import html
import argparse

import bot          # переиспользуем отправку из основного движка
import cards        # переиспользуем растеризацию SVG→PNG

HERE = os.path.dirname(os.path.abspath(__file__))
PROMO_PATH = os.path.join(HERE, "promo.json")
STATE_PATH = os.path.join(HERE, "promo_state.json")
W, H = 1080, 1350
FAM = "'Arial Black','Montserrat','DejaVu Sans','Helvetica',sans-serif"
MARGIN = 90


def load_promo():
    with open(PROMO_PATH, encoding="utf-8") as f:
        return json.load(f)


def read_counter():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return int(json.load(f).get("n", 0))
        except Exception:
            return 0
    return 0


def write_counter(n):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"n": n}, f, ensure_ascii=False)


def pick(cfg, n):
    """Один канал = одно воскресенье, по кругу.
    Креатив внутри канала меняется на каждом новом круге."""
    channels = cfg["channels"]
    ch = channels[n % len(channels)]
    variants = ch["variants"]
    v = variants[(n // len(channels)) % len(variants)]
    return ch, v


def channel_is_live(handle, token):
    """Проверить через Bot API, что рекламируемый канал существует."""
    if not token:
        return True   # без токена не проверяем (dry-run)
    import urllib.request, urllib.error, urllib.parse
    url = (f"https://api.telegram.org/bot{token}/getChat"
           f"?chat_id={urllib.parse.quote(handle)}")
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.load(r).get("ok", False)
    except Exception:
        return False


def build_promo_svg(v, ch):
    """Мраморно-тёмная карточка с золотом — визуально отличается от фактов."""
    handle = ch["handle"]
    parts = []

    # кикер-чип
    kicker = html.escape(v["kicker"])
    chip_w = 80 + len(kicker) * 24
    parts.append(
        f'<rect x="{MARGIN}" y="140" width="{chip_w}" height="62" rx="31" '
        f'fill="none" stroke="#C9A227" stroke-width="3"/>'
        f'<text x="{MARGIN + chip_w/2:.0f}" y="182" text-anchor="middle" '
        f'font-family="{FAM}" font-size="30" font-weight="900" fill="#E8C766" '
        f'letter-spacing="3">{kicker}</text>')

    y = 300
    tsvg, y = cards._tspans(v["title"], MARGIN, y, 64, 76, "#F5F0E6", 900, -1)
    parts.append(tsvg)

    y += 26
    parts.append(f'<rect x="{MARGIN}" y="{y:.0f}" width="110" height="5" rx="3" '
                 f'fill="#C9A227"/>')
    y += 50

    bsvg, y = cards._tspans(v["text"], MARGIN, y, 38, 52, "#C9C4BA", 500, 0)
    parts.append(bsvg)

    y += 40
    psvg, y = cards._tspans(v["pitch"], MARGIN, y, 38, 52, "#F5F0E6", 700, 0)
    parts.append(psvg)

    # CTA-плашка — плавает сразу под текстом
    cta = html.escape(v["cta"])
    box_y = y + 44
    parts.append(
        f'<rect x="{MARGIN}" y="{box_y:.0f}" width="{W - 2*MARGIN}" height="104" rx="26" '
        f'fill="#C9A227"/>'
        f'<text x="{W/2:.0f}" y="{box_y + 66:.0f}" text-anchor="middle" font-family="{FAM}" '
        f'font-size="40" font-weight="900" fill="#14141C">{cta}</text>')
    parts.append(
        f'<text x="{W/2:.0f}" y="{box_y + 180:.0f}" text-anchor="middle" font-family="{FAM}" '
        f'font-size="50" font-weight="900" fill="#E8C766">{html.escape(handle)}</text>')

    body = "\n  ".join(parts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <radialGradient id="bg" cx="0.5" cy="0.35" r="0.9">
      <stop offset="0" stop-color="#26262F"/>
      <stop offset="1" stop-color="#101016"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <text x="{W-40}" y="{H-330}" text-anchor="end" font-family="{FAM}" font-size="360"
        font-weight="900" fill="#C9A227" opacity="0.06">🏛</text>
  {body}
</svg>'''


def build_caption(v, ch):
    name = html.escape(ch["name"])
    handle = html.escape(ch["handle"])
    return (
        f"🏛 <b>{html.escape(v['kicker']).capitalize()}</b>\n\n"
        f"{html.escape(v['text'])}\n\n"
        f"<b>«{name}»</b> — {html.escape(v['pitch'].split('—', 1)[-1].strip())}\n\n"
        f"👉 {html.escape(v['cta'])}: {handle}"
    )


def main():
    ap = argparse.ArgumentParser(description="Еженедельная реклама Эвномии")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_promo()
    token = os.environ.get("BOT_TOKEN", "").strip()
    channel = os.environ.get("CHANNEL_ID", "").strip()
    n = read_counter()
    total = len(cfg["channels"])

    # выбираем канал этой недели; если он вдруг недоступен — берём следующий
    ch = v = None
    for step in range(total):
        cand_ch, cand_v = pick(cfg, n + step)
        if args.dry_run or channel_is_live(cand_ch["handle"], token):
            ch, v, n = cand_ch, cand_v, n + step
            break
        print(f"[promo] канал {cand_ch['handle']} недоступен — пропускаю")
    if ch is None:
        print("[promo] ни один канал не доступен — реклама не отправлена.")
        return

    caption = build_caption(v, ch)
    print(f"[promo] неделя #{n + 1}: канал {ch['name']} ({ch['handle']}), "
          f"креатив «{v['kicker']}»")

    if args.dry_run or not token or not channel:
        print("\n" + "═" * 48)
        print(caption)
        print("═" * 48)
        png = cards.rasterize(build_promo_svg(v, ch),
                              os.path.join(HERE, "promo_preview.png"), W, H)
        print(f"[promo] карточка: {png}")
        return

    png = cards.rasterize(build_promo_svg(v, ch),
                          os.path.join(HERE, "promo_tmp.png"), W, H)
    if png:
        bot.send_telegram_photo(token, channel, png, caption)
        print(f"[promo] опубликовано с фото: {ch['name']}")
    else:
        bot.send_telegram(token, channel, caption)
        print(f"[promo] опубликовано текстом: {ch['name']}")
    write_counter(n + 1)


if __name__ == "__main__":
    main()
