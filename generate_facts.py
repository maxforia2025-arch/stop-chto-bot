#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Автогенерация новых шок-фактов для канала «Стоп, что?!» через Claude API.

Пополняет facts.json проверенными «вау»-фактами в точном формате банка,
избегая повторов с уже существующими. Модель claude-opus-4-8.

Запуск:
    python3 generate_facts.py                 # добить банк до порога (по умолчанию)
    python3 generate_facts.py --count 15      # ровно 15 новых фактов
    python3 generate_facts.py --ensure 30     # генерировать, только если «непоказанных» < 30
    GEN_N=20 python3 generate_facts.py

Требует переменную окружения ANTHROPIC_API_KEY (в облаке — GitHub Secret).
Зависимость: пакет `anthropic` (в CI ставится через pip).
"""
import os
import re
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
FACTS_PATH = os.path.join(HERE, "facts.json")
HISTORY_PATH = os.path.join(HERE, "history.json")
MODEL = "claude-opus-4-8"

FACTS_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "cat": {"type": "string"},
                    "title": {"type": "string"},
                    "fact": {"type": "string"},
                    "wow": {"type": "string"},
                },
                "required": ["id", "cat", "title", "fact", "wow"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["facts"],
    "additionalProperties": False,
}


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (s or "fact")[:40]


def norm_title(t):
    return re.sub(r"\s+", " ", t.lower()).strip()


# --- смысловая дедупликация (тот же стеммер, что в bot.py) -------------------
_STOP = {"который", "которые", "которых", "которое", "этого", "этот", "самый",
         "самая", "самое", "почти", "около", "более", "менее", "есть", "было",
         "были", "просто", "каждый", "каждую", "каждое", "прямо", "сейчас",
         "весь", "всей", "всего", "один", "одна", "одно", "даже", "чтобы",
         "после", "между", "через", "когда", "только", "может", "можно",
         "нужно", "человек", "человека"}
_SUF = ("ившись", "ывшись", "ами", "ями", "ах", "ях", "ов", "ев", "ий", "ой",
        "ый", "ые", "ая", "яя", "ое", "ем", "ам", "ом", "ешь", "ишь", "ет",
        "ит", "ут", "ют", "ат", "ят", "ла", "ло", "ли", "ть", "ы", "и", "а",
        "я", "о", "е", "у", "ю", "ь", "й")


def _stem(w):
    for s in _SUF:
        if len(w) - len(s) >= 4 and w.endswith(s):
            return w[:-len(s)]
    return w


def sig(fact):
    blob = (fact.get("title", "") + " " + fact.get("fact", "")).lower()
    return {_stem(w) for w in re.findall(r"[а-яёa-z0-9]{5,}", blob) if w not in _STOP}


def similar(a_sig, b_sig, thr=0.30):
    return bool(a_sig) and bool(b_sig) and len(a_sig & b_sig) / len(a_sig | b_sig) >= thr


def build_prompt(existing_titles, n):
    titles_block = "\n".join(f"- {t}" for t in existing_titles)
    return (
        f"Ты — редактор Telegram-канала «Стоп, что?!» с шок-фактами, "
        f"которые вызывают реакцию «не может быть!» и желание переслать другу.\n\n"
        f"Сгенерируй {n} НОВЫХ фактов на русском языке. Жёсткие требования:\n"
        f"1. Каждый факт ДОЛЖЕН быть ПРАВДОЙ и проверяемым. Никаких мифов, "
        f"городских легенд или сомнительных утверждений. Если не уверен в факте — не включай его.\n"
        f"2. Факты должны быть максимально «вау»: неожиданные, контринтуитивные, "
        f"заставляющие сказать «стоп, что?!».\n"
        f"3. Разные категории: космос, тело, мозг, деньги, история, природа, "
        f"технологии, числа, психология, земля, время, наука.\n"
        f"4. НЕ повторяй эти уже существующие факты — ни дословно, ни ПЕРЕСКАЗОМ "
        f"другими словами. Если суть факта совпадает с любым из списка — это "
        f"запрещённый повтор, даже если формулировка новая:\n{titles_block}\n\n"
        f"Формат каждого факта (строго):\n"
        f"- id: короткий уникальный слаг на английском (латиница, нижний регистр, "
        f"подчёркивания), например \"space_black_hole_time\"\n"
        f"- cat: одна категория одним словом с большой буквы, например \"Космос\"\n"
        f"- title: цепляющий заголовок-крючок (4–8 слов), обрывающий мысль\n"
        f"- fact: суть факта в 1–3 предложениях, простым языком\n"
        f"- wow: короткая добивка (1 предложение), от которой мурашки\n\n"
        f"Тон — живой, на «ты». Без markdown, без эмодзи внутри полей."
    )


def generate(n, existing):
    import anthropic  # импорт здесь: нужен только при реальной генерации

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[gen] НЕТ ANTHROPIC_API_KEY — пропускаю генерацию (не ошибка).")
        return []

    # даём модели заголовок + суть каждого факта, чтобы она не пересказывала
    existing_titles = [f"{f['title']} — {f['fact'][:60]}" for f in existing]
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        output_config={"format": {"type": "json_schema", "schema": FACTS_SCHEMA}},
        messages=[{"role": "user", "content": build_prompt(existing_titles, n)}],
    )
    text = next((b.text for b in resp.content if b.type == "text"), "")
    data = json.loads(text)
    return data.get("facts", [])


def merge(existing, new):
    seen_ids = {f["id"] for f in existing}
    seen_titles = {norm_title(f["title"]) for f in existing}
    sigs = [sig(f) for f in existing]     # смысловые сигнатуры всего банка
    added = []
    for f in new:
        if not all(k in f and f[k].strip() for k in ("cat", "title", "fact", "wow")):
            continue
        fid = slugify(f.get("id") or f["title"])
        base = fid
        i = 2
        while fid in seen_ids:
            fid = f"{base}_{i}"
            i += 1
        if norm_title(f["title"]) in seen_titles:
            continue
        # смысловой дубль? (разные слова, но тот же факт)
        s = sig(f)
        if any(similar(s, ps) for ps in sigs):
            print(f"   [dup] пропускаю смысловой повтор: {f['title']}")
            continue
        f["id"] = fid
        seen_ids.add(fid)
        seen_titles.add(norm_title(f["title"]))
        sigs.append(s)
        added.append({"id": fid, "cat": f["cat"].strip(), "title": f["title"].strip(),
                      "fact": f["fact"].strip(), "wow": f["wow"].strip()})
    return added


def main():
    ap = argparse.ArgumentParser(description="Автогенерация фактов через Claude")
    ap.add_argument("--count", type=int, default=None, help="сколько новых фактов сгенерировать")
    ap.add_argument("--ensure", type=int, default=None,
                    help="генерировать, только если непоказанных фактов меньше порога")
    args = ap.parse_args()

    facts = load_json(FACTS_PATH, [])
    history = load_json(HISTORY_PATH, [])
    posted = set(history)
    unseen = sum(1 for f in facts if f["id"] not in posted)
    print(f"[gen] в банке {len(facts)} фактов, непоказанных {unseen}")

    if args.ensure is not None and unseen >= args.ensure:
        print(f"[gen] непоказанных ({unseen}) >= порога ({args.ensure}) — генерация не нужна.")
        return

    n = args.count or int(os.environ.get("GEN_N", "15"))
    print(f"[gen] запрашиваю {n} новых фактов у {MODEL}...")
    new = generate(n, facts)
    if not new:
        print("[gen] ничего не сгенерировано.")
        return

    added = merge(facts, new)
    if not added:
        print("[gen] все сгенерированные — дубли, ничего не добавлено.")
        return

    facts.extend(added)
    with open(FACTS_PATH, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)
    print(f"[gen] добавлено {len(added)} фактов. Всего в банке: {len(facts)}")
    for a in added:
        print(f"   + [{a['cat']}] {a['title']}")


if __name__ == "__main__":
    main()
