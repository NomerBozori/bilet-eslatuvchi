#!/usr/bin/env python3
"""Telegram orqali takroriy eslatmalar. Faqat Python standart kutubxonasi kerak."""
import json
import logging
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request

DB_PATH = os.environ.get("DATABASE_PATH", "reminders.db")
TOKEN = os.environ.get("BOT_TOKEN", "")
MIN_INTERVAL = 60
MAX_INTERVAL = 365 * 24 * 3600
UNITS = {
    "daqiqa": 60, "minut": 60, "minute": 60, "minutes": 60,
    "soat": 3600, "hour": 3600, "hours": 3600,
    "kun": 86400, "day": 86400, "days": 86400,
    "hafta": 604800, "week": 604800, "weeks": 604800,
}


def parse_interval(text):
    match = re.fullmatch(r"\s*(\d+)\s*([a-zA-Z]+)\s*", text)
    if not match:
        return None
    seconds = int(match.group(1)) * UNITS.get(match.group(2).lower(), 0)
    return seconds if MIN_INTERVAL <= seconds <= MAX_INTERVAL else None


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.execute("PRAGMA busy_timeout = 10000")
    return db


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            interval_seconds INTEGER NOT NULL,
            next_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversations (
            chat_id INTEGER PRIMARY KEY,
            pending_text TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS reminders_due ON reminders(next_at);
        """)


def api(method, data):
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    # Never log the exception: it may contain the bot token in the URL.
    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError("Telegram API so'rovi muvaffaqiyatsiz")
    return result.get("result")


def send(chat_id, text):
    return api("sendMessage", {"chat_id": chat_id, "text": text})


def handle_message(message):
    # Private chats only: a group member must not manage another user's reminders.
    chat = message.get("chat", {})
    if chat.get("type") != "private" or not isinstance(message.get("text"), str):
        return
    chat_id, text = chat["id"], message["text"].strip()
    if not text:
        return
    command = text.split()[0].split("@")[0].lower()
    if command in ("/start", "/help"):
        send(chat_id, "Assalomu alaykum! Eslatish kerak bo'lgan matnni yuboring. "
             "Keyin qancha vaqtda bir eslatishni so'rayman.\n\n"
             "/list — eslatmalar ro'yxati\n/delete ID — eslatmani o'chirish\n"
             "/cancel — joriy amalni bekor qilish")
        return
    if command == "/cancel":
        with connect() as db:
            db.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))
        send(chat_id, "Joriy amal bekor qilindi. Yangi eslatma matnini yuboring.")
        return
    if command == "/list":
        with connect() as db:
            rows = db.execute("SELECT id, text, interval_seconds FROM reminders WHERE chat_id = ? ORDER BY id", (chat_id,)).fetchall()
        if not rows:
            send(chat_id, "Sizda eslatmalar yo'q. Yangi eslatma matnini yuboring.")
        else:
            # Send separately to stay within Telegram's message length limit.
            send(chat_id, "Eslatmalaringiz:")
            for rid, reminder, interval in rows:
                send(chat_id, f"#{rid} — {reminder}\nHar {interval // 60} daqiqada. O'chirish: /delete {rid}")
        return
    if command == "/delete":
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            send(chat_id, "Eslatma raqamini kiriting: /delete 1")
            return
        with connect() as db:
            deleted = db.execute("DELETE FROM reminders WHERE id = ? AND chat_id = ?", (parts[1], chat_id)).rowcount
        send(chat_id, "Eslatma o'chirildi." if deleted else "Eslatma topilmadi.")
        return
    if text.startswith("/"):
        send(chat_id, "Noma'lum buyruq. Yordam uchun /help ni bosing.")
        return
    with connect() as db:
        row = db.execute("SELECT pending_text FROM conversations WHERE chat_id = ?", (chat_id,)).fetchone()
        if row:
            interval = parse_interval(text)
            if interval is None:
                reply = "Vaqtni masalan 30 daqiqa, 2 soat, 1 kun yoki 1 hafta shaklida kiriting (1 daqiqadan 365 kungacha)."
            else:
                db.execute("INSERT INTO reminders (chat_id, text, interval_seconds, next_at) VALUES (?, ?, ?, ?)",
                           (chat_id, row[0], interval, time.time() + interval))
                db.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))
                reply = "✅ Eslatma saqlandi! Birinchi xabar belgilangan vaqt o'tgach yuboriladi. Yana eslatma qo'shish uchun matn yuboring."
        elif len(text) > 3500:
            reply = "Matn juda uzun. 3500 ta belgidan oshmagan matn yuboring."
        else:
            db.execute("INSERT INTO conversations (chat_id, pending_text) VALUES (?, ?)", (chat_id, text))
            reply = "Qancha vaqtda bir eslatay? Masalan: 30 daqiqa, 2 soat, 1 kun yoki 1 hafta."
    send(chat_id, reply)


def scheduler():
    while True:
        try:
            with connect() as db:
                due = db.execute("SELECT id, chat_id, text, interval_seconds FROM reminders WHERE next_at <= ? ORDER BY next_at LIMIT 100", (time.time(),)).fetchall()
            for rid, chat_id, text, interval in due:
                # Check again in case the user deleted the reminder while it was queued.
                with connect() as db:
                    exists = db.execute("SELECT 1 FROM reminders WHERE id = ?", (rid,)).fetchone()
                if not exists:
                    continue
                try:
                    send(chat_id, f"🔔 Eslatma #{rid}:\n{text}")
                except Exception:
                    logging.warning("Eslatmani yuborib bo'lmadi (ID %s); keyinroq qayta uriniladi", rid)
                    # Avoid a busy retry loop when Telegram is unavailable.
                    with connect() as db:
                        db.execute("UPDATE reminders SET next_at = ? WHERE id = ?", (time.time() + 60, rid))
                else:
                    with connect() as db:
                        db.execute("UPDATE reminders SET next_at = ? WHERE id = ?", (time.time() + interval, rid))
        except Exception:
            logging.error("Eslatmalarni tekshirishda xatolik yuz berdi")
        time.sleep(5)


def main():
    if not TOKEN:
        raise SystemExit("BOT_TOKEN muhit o'zgaruvchisini kiriting.")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_db()
    threading.Thread(target=scheduler, daemon=True).start()
    offset = None
    logging.info("Bot ishga tushdi")
    while True:
        try:
            updates = api("getUpdates", {"offset": offset, "timeout": 30, "allowed_updates": ["message"]})
            for update in updates:
                # Advance even for an unsupported message, so it cannot block polling.
                offset = update["update_id"] + 1
                try:
                    if "message" in update:
                        handle_message(update["message"])
                except Exception:
                    logging.error("Xabarni qayta ishlashda xatolik")
        except Exception:
            logging.error("Telegram bilan aloqa xatosi; qayta urinilmoqda")
            time.sleep(5)


if __name__ == "__main__":
    main()
