import os
from typing import Optional, Dict
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
import dateparser

BULAN_ID = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


def _detect_open_app_intent(text: str) -> Optional[Dict]:
    t = text.lower()
    # simple heuristics mapping
    apps = {
        "whatsapp": {"packages": ["com.whatsapp", "com.whatsapp.w4b"], "scheme": "whatsapp://send?text="},
        "telegram": {"packages": ["org.telegram.messenger"], "scheme": "tg://msg?text="},
        "chrome": {"packages": ["com.android.chrome"], "scheme": "googlechrome://"},
        "browser": {"packages": ["com.android.browser"], "scheme": "http://"},
        "instagram": {"packages": ["com.instagram.android"], "scheme": None },
    }
    for k, meta in apps.items():
        if k in t:
            packages = meta.get("packages") or []
            scheme = meta.get("scheme")
            # build Play Store and intent template candidates for Android clients
            play_store = [f"https://play.google.com/store/apps/details?id={p}" for p in packages]
            intent_templates = []
            for p in packages:
                # generic intent template with placeholders {text} and {package}
                # Android intent format: intent://...#Intent;package={package};scheme={scheme_without_colons};end
                scheme_name = None
                if scheme and "://" in scheme:
                    scheme_name = scheme.split("://")[0]
                elif scheme:
                    scheme_name = scheme.rstrip(":/")
                if scheme_name:
                    intent_templates.append(f"intent://send?text={{text}}#Intent;package={p};scheme={scheme_name};end")
            return {
                "type": "open_app",
                "target": k,
                "packages": packages,
                "scheme": scheme,
                "play_store": play_store,
                "intent_templates": intent_templates,
            }
    return None

# 
def handle_chat(user: Dict, message: str) -> Dict:
    username = user.get("username") if user else "Pengguna"

    # 1️⃣ PRIORITAS: TASK / REMINDER
    task_data = extract_task_from_chat(message)
    if task_data:
        return {
            "type": "create_task",
            "task": task_data,
            "reply": (
                f"Baik {username}, saya akan mengingatkan Anda pada "
                f"{task_data['due_date'].strftime('%d %B %Y pukul %H:%M')}."
            )
        }

    # 2️⃣ INTENT OPEN APP
    intent = _detect_open_app_intent(message)

    # 3️⃣ CHAT AI
    cloud_resp = _call_openrouter_api(message)
    if cloud_resp.get("reply"):
        return {
            "reply": cloud_resp["reply"],
            "action": intent
        }

    # 4️⃣ FALLBACK
    low = message.strip().lower()
    if low in ("hai", "halo", "hello"):
        return {
            "reply": f"Halo {username}, ada yang bisa saya bantu?",
            "action": intent
        }

    return {
        "reply": f"{username}, kamu bilang: {message}",
        "action": intent
    }



# 


def _call_openrouter_api(message: str) -> Dict:
    key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
    if not key:
        print("[OPENROUTER] API KEY TIDAK ADA")
        return {}

    model = os.getenv("OPENROUTER_MODEL") or "deepseek/deepseek-r1-0528:free"
    url = "https://api.openrouter.ai/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Kamu adalah asisten AI yang membantu percakapan umum."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 512,
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return {"reply": data["choices"][0]["message"]["content"]}
    except Exception as e:
        print("[OPENROUTER ERROR]", e)
        return {}


def extract_task_from_chat(message: str):
    print("[TASK PARSER] raw:", message)

    msg = message.lower()

    if "ingatkan saya" not in msg:
        return None

    now = datetime.now()

    # =====================
    # 1. PARSE JAM MANUAL
    # =====================
    hour = None
    minute = 0

    jam_match = re.search(r"jam\s*(\d{1,2})(?:[:.](\d{1,2}))?", msg)
    if jam_match:
        hour = int(jam_match.group(1))
        if jam_match.group(2):
            minute = int(jam_match.group(2))

        # malam / sore / pagi
        if "malam" in msg or "sore" in msg:
            if hour < 12:
                hour += 12
        elif "pagi" in msg:
            if hour == 12:
                hour = 0

    if hour is None:
        print("[TASK PARSER] JAM TIDAK DITEMUKAN")
        return None

    # =====================
    # 2. PARSE TANGGAL
    # =====================
    if "hari ini" in msg:
        date = now.date()
    elif "besok" in msg:
        date = (now + timedelta(days=1)).date()
    else:
        parsed = dateparser.parse(
            msg,
            languages=["id"],
            settings={"PREFER_DATES_FROM": "future"},
        )
        if not parsed:
            print("[TASK PARSER] TANGGAL GAGAL")
            return None
        date = parsed.date()

    due_date = datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=hour,
        minute=minute,
    )

    print("[TASK PARSER] FINAL due_date:", due_date)

    return {
        "title": "Reminder",
        "description": message,
        "due_date": due_date,
    }

def fallback_response(text: str):
    return (
        "Aku masih bisa membantu membuka aplikasi dan mengatur task.\n"
        "Untuk percakapan umum, koneksi AI sedang bermasalah.\n\n"
        f"Kamu barusan bertanya tentang: \"{text}\""
    )




