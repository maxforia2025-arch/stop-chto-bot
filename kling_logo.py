#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генерация логотипа канала «Стоп, что?!» через Kling Open API (text-to-image / Kolors).
JWT(HS256) из общих ключей wrong_word_channel/kling/creds.json. Только stdlib.
"""
import sys, os, json, time, hmac, hashlib, base64, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(HERE, "..", "wrong_word_channel", "kling", "creds.json")
CREDS = json.load(open(CREDS_PATH))
AK, SK = CREDS["access_key"], CREDS["secret_key"]
HOSTS = ["https://api-singapore.klingai.com", "https://api.klingai.com"]


def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def make_token():
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"iss": AK, "exp": now + 1800, "nbf": now - 5}
    seg = b64url(json.dumps(header, separators=(",", ":")).encode()) + b"." + \
          b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SK.encode(), seg, hashlib.sha256).digest()
    return (seg + b"." + b64url(sig)).decode()


def req(method, host, path, body=None):
    url = host + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Bearer " + make_token())
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode())
        except Exception:
            payload = {"raw": "<unreadable>"}
        return e.code, payload
    except Exception as e:
        return None, {"error": str(e)}


PROMPT = (
    "Flat vector app icon logo, bold comic pop-art explosion. A glossy golden-yellow "
    "spiky starburst badge in the center with a thick dark-navy outline. Inside the burst, "
    "a huge bold dark-navy question mark and exclamation mark together. Vibrant electric "
    "gradient background from violet to hot magenta to electric blue, small yellow sparkles "
    "around. Mind-blown surprise reaction, dopamine, playful, very high contrast, clean crisp "
    "edges, centered symmetric composition, sticker style, no photorealism, no human face."
)
NEG = "text, words, letters, caption, watermark, signature, blurry, low quality, realistic photo, gradient banding, jpeg artifacts, extra symbols"


def submit(host, model):
    body = {
        "model_name": model,
        "prompt": PROMPT,
        "negative_prompt": NEG,
        "n": 4,
        "aspect_ratio": "1:1",
    }
    return req("POST", host, "/v1/images/generations", body)


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "kling-v1-5"
    host = None
    code = resp = None
    for h in HOSTS:
        code, resp = submit(h, model)
        print(f"[submit @ {h}] HTTP {code}: {json.dumps(resp, ensure_ascii=False)[:400]}")
        if code == 200 and resp.get("code") == 0:
            host = h
            break
    if not host:
        print("НЕ УДАЛОСЬ отправить задачу. Проверь модель/эндпоинт выше.")
        sys.exit(1)

    task_id = resp["data"]["task_id"]
    print(f"task_id = {task_id}  — жду результат...")
    urls = []
    for i in range(60):
        time.sleep(5)
        c, r = req("GET", host, f"/v1/images/generations/{task_id}")
        if c != 200:
            print(f"  poll HTTP {c}: {r}")
            continue
        data = r.get("data", {})
        status = data.get("task_status")
        print(f"  [{i}] status={status}")
        if status == "succeed":
            urls = [im["url"] for im in data["task_result"]["images"]]
            break
        if status == "failed":
            print("  ЗАДАЧА ПРОВАЛЕНА:", data.get("task_status_msg"))
            sys.exit(1)

    for idx, u in enumerate(urls):
        out = os.path.join(HERE, f"logo_kling_{idx+1}.png")
        urllib.request.urlretrieve(u, out)
        print(f"  сохранён {out}")
    print("ГОТОВО. Вариантов:", len(urls))


if __name__ == "__main__":
    main()
