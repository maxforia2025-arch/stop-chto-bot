#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Еженедельная сверка списка рекламируемых каналов Maxforia Group.

Что делает:
  1. Читает channels.txt (список хендлов) + опционально ловит каналы,
     куда бота добавили админом (getUpdates → my_chat_member).
  2. Проверяет каждый канал через getChat: живой? как называется? о чём?
  3. Мёртвые/недоступные — убирает из ротации.
  4. Для НОВЫХ каналов сам пишет 3 креатива под их тему (Claude), либо,
     если ключа нет, — аккуратный запасной креатив из описания канала.
  5. Переписывает promo.json.

Запуск:
    python3 refresh_channels.py --dry-run
    BOT_TOKEN=... python3 refresh_channels.py
"""
import os
import json
import argparse
import urllib.parse
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
PROMO_PATH = os.path.join(HERE, "promo.json")
LIST_PATH = os.path.join(HERE, "channels.txt")
MODEL = "claude-opus-4-8"
HOST_CHANNEL = "@stop_chto_daily"   # сама площадка — рекламировать не нужно

VARIANTS_SCHEMA = {
    "type": "object",
    "properties": {
        "variants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kicker": {"type": "string"},
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "pitch": {"type": "string"},
                    "cta": {"type": "string"},
                },
                "required": ["kicker", "title", "text", "pitch", "cta"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["variants"],
    "additionalProperties": False,
}


def api(token, method, **params):
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return json.load(e)
        except Exception:
            return {"ok": False}
    except Exception:
        return {"ok": False}


def read_list():
    handles = []
    if os.path.exists(LIST_PATH):
        with open(LIST_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                handles.append(line if line.startswith("@") else "@" + line)
    return handles


def discover_from_updates(token):
    """Каналы, куда бота добавили админом (если событие ещё не протухло)."""
    found = []
    if not token:
        return found
    d = api(token, "getUpdates")
    for upd in d.get("result", []) if d.get("ok") else []:
        for key in ("my_chat_member", "channel_post"):
            chat = (upd.get(key) or {}).get("chat") or {}
            if chat.get("type") == "channel" and chat.get("username"):
                found.append("@" + chat["username"])
    return found


def describe(token, handle):
    """Вернуть (title, description) или None, если канал недоступен."""
    d = api(token, "getChat", chat_id=handle)
    if not d.get("ok"):
        return None
    r = d["result"]
    if r.get("type") != "channel":
        return None
    return r.get("title") or handle, (r.get("description") or "").strip()


def fallback_variants(name, desc):
    """Запасные креативы, если Claude недоступен — честные и нейтральные."""
    short = desc.split(".")[0].strip() if desc else "канал, который стоит твоей подписки"
    return [
        {"kicker": "РЕКОМЕНДАЦИЯ",
         "title": f"«{name}» — советуем заглянуть",
         "text": "Мы редко что-то советуем. Но этот канал читаем сами.",
         "pitch": f"«{name}» — {short}.",
         "cta": "Открыть канал"},
        {"kicker": "СОВЕТУЕМ",
         "title": f"Ещё один повод сказать «стоп, что?!»",
         "text": "Если тебе заходят наши факты, этот канал тоже зайдёт.",
         "pitch": f"«{name}» — {short}.",
         "cta": "Подписаться"},
    ]


def ai_variants(name, handle, desc):
    """Сгенерировать 3 креатива под тему канала через Claude."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"   [ai] нет ANTHROPIC_API_KEY — беру запасные креативы")
        return None
    try:
        import anthropic
    except ImportError:
        print("   [ai] пакет anthropic не установлен — беру запасные креативы")
        return None

    prompt = (
        f"Ты — редактор Telegram-канала «Стоп, что?!» с шок-фактами "
        f"(космос, тело, деньги, история, наука). Аудитория любит удивляться.\n\n"
        f"Напиши 3 РАЗНЫХ рекламных креатива для дружественного канала:\n"
        f"- Название: {name}\n- Хендл: {handle}\n"
        f"- О чём канал: {desc or 'описание не указано'}\n\n"
        f"Правила:\n"
        f"1. Каждый креатив строит МОСТ от шок-фактов к теме этого канала — "
        f"начинай с чего-то из мира фактов и переходи к пользе канала.\n"
        f"2. Реклама честная: обещай ровно то, что в канале есть. "
        f"Не выдумывай темы, которых нет в описании.\n"
        f"3. Тон живой, на «ты», без канцелярита и без слова «уникальный».\n\n"
        f"Поля каждого креатива:\n"
        f"- kicker: 1-2 слова ЗАГЛАВНЫМИ (например РЕКОМЕНДАЦИЯ, СОВЕТУЕМ, ПОЛЕЗНОЕ)\n"
        f"- title: заголовок-крючок, 4-8 слов\n"
        f"- text: 1-2 предложения-подводка от фактов к теме канала\n"
        f"- pitch: 1-2 предложения, начинается с «{name}» — и говорит, что даёт канал\n"
        f"- cta: призыв к действию, 2-4 слова\n\n"
        f"Без markdown и эмодзи внутри полей."
    )
    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            output_config={"format": {"type": "json_schema", "schema": VARIANTS_SCHEMA}},
            messages=[{"role": "user", "content": prompt}],
        )
        text = next((b.text for b in resp.content if b.type == "text"), "")
        variants = json.loads(text).get("variants", [])
        return variants or None
    except Exception as e:
        print(f"   [ai] ошибка генерации ({e}) — беру запасные креативы")
        return None


def main():
    ap = argparse.ArgumentParser(description="Сверка списка рекламируемых каналов")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        print("[refresh] нет BOT_TOKEN — сверка невозможна.")
        return

    with open(PROMO_PATH, encoding="utf-8") as f:
        promo = json.load(f)
    known = {c["handle"].lower(): c for c in promo.get("channels", [])}

    # 1. кандидаты: файл-список + авто-подхват
    handles, seen = [], set()
    for h in read_list() + discover_from_updates(token):
        k = h.lower()
        if k in seen or k == HOST_CHANNEL.lower():
            continue
        seen.add(k)
        handles.append(h)
    print(f"[refresh] кандидатов: {len(handles)}")

    # 2-4. проверяем каждый, для новых пишем креативы
    channels, dropped = [], []
    for h in handles:
        info = describe(token, h)
        if not info:
            dropped.append(h)
            print(f"  [нет ] {h} — недоступен, в ротацию не берём")
            continue
        name, desc = info
        existing = known.get(h.lower())
        if existing and existing.get("variants"):
            existing["handle"], existing["name"] = h, name
            channels.append(existing)
            print(f"  [есть] {h} — «{name}», креативы на месте")
        else:
            print(f"  [НОВЫЙ] {h} — «{name}» — пишу креативы...")
            variants = ai_variants(name, h, desc) or fallback_variants(name, desc)
            channels.append({"handle": h, "name": name, "variants": variants})
            print(f"          готово: {len(variants)} креативов")

    if not channels:
        print("[refresh] ни одного живого канала — promo.json не трогаю.")
        return

    # каналы, что были в ротации, но пропали из списка
    for k, c in known.items():
        if k not in {ch["handle"].lower() for ch in channels}:
            print(f"  [убран] {c['handle']} — больше не в списке")

    promo["channels"] = channels
    if args.dry_run:
        print(f"\n[dry-run] итог: {len(channels)} каналов в ротации "
              f"(цикл {len(channels) * min(len(c['variants']) for c in channels)} недель)")
        for c in channels:
            print(f"   • {c['name']} ({c['handle']}): {len(c['variants'])} креативов")
        return

    with open(PROMO_PATH, "w", encoding="utf-8") as f:
        json.dump(promo, f, ensure_ascii=False, indent=2)
    print(f"[refresh] promo.json обновлён: {len(channels)} каналов в ротации")


if __name__ == "__main__":
    main()
