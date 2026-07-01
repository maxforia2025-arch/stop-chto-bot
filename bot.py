#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДОФАМИН-КАНАЛ — движок шок-фактов для Telegram.

Задача: максимальный органический рост.
Главный двигатель роста в Telegram — ПЕРЕСЫЛКИ (forwards). Поэтому каждый пост
собирается по формуле, которая вызывает дофамин и желание переслать другу:

    [эмодзи-крючок] ЗАГОЛОВОК (петля любопытства)
    факт (микро-награда — быстро, ярко)
    👉 вау-добивка (пик дофамина, «не может быть!»)
    ——— CTA на подписку + пересылку

Механики дофамина, зашитые в движок:
  • curiosity gap  — заголовок обрывает мысль, мозг требует закрыть петлю (Зейгарник)
  • микро-награда   — короткий пост, факт «заходит» за 5 секунд
  • переменное вознаграждение — ротация форматов и категорий (непредсказуемость)
  • социальный статус — контентом хочется поделиться, чтобы казаться интересным
  • CTA на forward   — прямой призыв переслать = рост канала

Зависимости: только стандартная библиотека Python. Работает в GitHub Actions.

Запуск:
    BOT_TOKEN=... CHANNEL_ID=@your_channel python3 bot.py          # 1 пост
    python3 bot.py --dry-run                                       # показать, не постить
    python3 bot.py --count 3                                       # 3 поста подряд
    N=5 python3 bot.py --dry-run                                   # предпросмотр 5 постов
"""

import os
import sys
import json
import html
import time
import argparse
import urllib.parse
import urllib.request
import cards

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACTS_PATH = os.path.join(BASE_DIR, "facts.json")
HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
UA = "Mozilla/5.0 (dopamine-channel-bot)"

# --- детерминированный псевдослучай (без random, чтобы легко тестировать) -----
# GitHub Actions запускается по расписанию; используем время как источник ротации.
_seed = int(time.time())


def _rand(n):
    """Вернуть псевдослучайное число 0..n-1 (линейный конгруэнтный генератор)."""
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed % n if n else 0


def _pick(seq):
    return seq[_rand(len(seq))]


def log(msg):
    print(f"[dopamine] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Конфиг / данные
# ---------------------------------------------------------------------------

def load_config():
    cfg = {
        "channel_handle": "@your_channel",      # для CTA в подписи
        "channel_name": "Вынос мозга",
        "cta_variants": [
            "🧠 <b>{name}</b> — подпишись, тут взрывают мозг каждый день:",
            "🔥 Не веришь? Проверь сам. Подписка на <b>{name}</b>:",
            "⚡️ Хочешь ещё такого? Ты знаешь, что делать:",
            "🤯 <b>{name}</b> — факты, от которых мурашки. Подпишись:",
        ],
        "share_variants": [
            "♻️ Перешли другу — проверь его реакцию.",
            "📲 Скинь тому, кто в это не поверит.",
            "👥 Отправь другу, который любит такое.",
            "💬 Кому бы взорвать этим мозг? Перешли ему.",
        ],
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            log(f"config.json не прочитан ({e}), беру дефолт")
    # ENV перекрывает файл
    cfg["channel_handle"] = os.environ.get("CHANNEL_HANDLE", cfg["channel_handle"])
    return cfg


def load_facts():
    with open(FACTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history[-1000:], f, ensure_ascii=False, indent=0)


# ---------------------------------------------------------------------------
# Выбор факта (не повторяем, пока не исчерпан банк)
# ---------------------------------------------------------------------------

def choose_fact(facts, history):
    """Берём факт, который постили давнее всего (или ни разу).

    history — список id в порядке публикации. Свежие в конце.
    """
    posted = set(history)
    unseen = [f for f in facts if f["id"] not in posted]
    if unseen:
        return _pick(unseen)
    # Все показаны хотя бы раз — берём тот, что не появлялся дольше всех.
    order = {fid: i for i, fid in enumerate(history)}  # больше индекс = свежее
    facts_sorted = sorted(facts, key=lambda f: order.get(f["id"], -1))
    return facts_sorted[0]


# ---------------------------------------------------------------------------
# Дофаминовое форматирование поста
# ---------------------------------------------------------------------------

HOOK_EMOJI = ["🤯", "😳", "🔥", "⚡️", "🌀", "👀", "🧠", "❗️", "🚨", "🤔"]

# Разные «обёртки» заголовка — переменное вознаграждение, посты не приедаются.
TITLE_TEMPLATES = [
    "{emoji} <b>{title}</b>",
    "{emoji} <b>{title}</b>\n<i>(да, это правда)</i>",
    "{emoji} А ты знал?\n\n<b>{title}</b>",
    "{emoji} <b>{title}</b>\n<i>Сейчас объясню.</i>",
    "{emoji} Стоп. <b>{title}</b>",
]

# Как подать «вау-добивку» — пик дофамина.
WOW_LEAD = ["👉", "💥", "⚡️", "🎯", "🤯"]


def format_post(fact, cfg):
    """Собрать HTML-пост из факта по дофаминовой формуле."""
    emoji = _pick(HOOK_EMOJI)
    title_tpl = _pick(TITLE_TEMPLATES)
    wow_lead = _pick(WOW_LEAD)

    title = html.escape(fact["title"])
    body = html.escape(fact["fact"])
    wow = html.escape(fact.get("wow", "")).strip()

    parts = [title_tpl.format(emoji=emoji, title=title)]
    parts.append("")
    parts.append(body)
    if wow:
        parts.append("")
        parts.append(f"{wow_lead} <b>{wow}</b>")

    # --- Хвост: подписка + призыв к пересылке (двигатель роста) ---------------
    name = html.escape(cfg.get("channel_name", "канал"))
    handle = cfg.get("channel_handle", "@your_channel")
    cta = _pick(cfg["cta_variants"]).format(name=name)
    share = _pick(cfg["share_variants"])

    parts.append("")
    parts.append("➖➖➖➖➖")
    parts.append(f"{cta} {html.escape(handle)}")
    parts.append(share)

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(token, channel_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        resp = json.loads(r.read().decode("utf-8"))
    if not resp.get("ok"):
        raise RuntimeError(resp)
    return resp


def send_telegram_photo(token, channel_id, photo_path, caption):
    """Отправить фото-карточку с подписью (multipart/form-data, stdlib)."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = "----DopamineBoundary7MA4YWxkTrZu0gW"
    with open(photo_path, "rb") as f:
        img = f.read()

    def field(name, value):
        return (f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n").encode("utf-8")

    body = b""
    body += field("chat_id", str(channel_id))
    body += field("caption", caption[:1024])
    body += field("parse_mode", "HTML")
    body += (f"--{boundary}\r\n"
             f'Content-Disposition: form-data; name="photo"; filename="card.png"\r\n'
             f"Content-Type: image/png\r\n\r\n").encode("utf-8")
    body += img + b"\r\n"
    body += f"--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": UA,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read().decode("utf-8"))
    if not resp.get("ok"):
        raise RuntimeError(resp)
    return resp


# ---------------------------------------------------------------------------
# Главный проход
# ---------------------------------------------------------------------------

def run_once(cfg, facts, history, token, channel_id, dry_run=False):
    fact = choose_fact(facts, history)
    text = format_post(fact, cfg)

    if dry_run or not token or not channel_id:
        if not dry_run:
            log("НЕТ BOT_TOKEN/CHANNEL_ID — показываю пост, но не отправляю:")
        print("\n" + "═" * 48)
        print(text)
        print("═" * 48 + "\n")
    else:
        card = None
        try:
            card = cards.render_card(fact)
        except Exception as e:
            log(f"карточка не собралась ({e}) — шлю текстом")
        if card:
            try:
                send_telegram_photo(token, channel_id, card, text)
                log(f"опубликовано с фото: {fact['id']} ({fact['cat']})")
            except Exception as e:
                log(f"фото не ушло ({e}) — шлю текстом")
                send_telegram(token, channel_id, text)
        else:
            send_telegram(token, channel_id, text)
            log(f"опубликовано (текст): {fact['id']} ({fact['cat']})")

    history.append(fact["id"])
    return fact


def main():
    ap = argparse.ArgumentParser(description="Дофамин-канал: постинг шок-фактов")
    ap.add_argument("--dry-run", action="store_true", help="показать посты, не отправлять")
    ap.add_argument("--count", type=int, default=None, help="сколько постов за запуск")
    args = ap.parse_args()

    count = args.count or int(os.environ.get("N", "1"))
    token = os.environ.get("BOT_TOKEN", "").strip()
    channel_id = os.environ.get("CHANNEL_ID", "").strip()

    cfg = load_config()
    if channel_id:
        cfg["channel_handle"] = channel_id if channel_id.startswith("@") else cfg["channel_handle"]

    facts = load_facts()
    history = load_history()
    log(f"банк фактов: {len(facts)} | опубликовано ранее: {len(history)}")

    for i in range(count):
        run_once(cfg, facts, history, token, channel_id, dry_run=args.dry_run)
        if not args.dry_run and i < count - 1:
            time.sleep(2)

    if not args.dry_run and token and channel_id:
        save_history(history)
    log("готово.")


if __name__ == "__main__":
    main()
