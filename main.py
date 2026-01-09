import logging
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest

# =========================
# НАСТРОЙКИ ИЗ .ENV
# =========================
from dotenv import load_dotenv
load_dotenv()  # Загружаем .env файл

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-bot.onrender.com/webhook")  # fallback на случай

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# =========================
# ВРЕМЯ ЗАПУСКА
# =========================
START_TIME = datetime.now()

# =========================
# ЛОГИ
# =========================
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | user_id=%(message)s"
)

# =========================
# TELEGRAM APP С РЕАЛЬНЫМ ПИНГОМ
# =========================
# Создаём кастомный request с таймаутом, чтоб мерить реальный пинг
request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)

telegram_app = Application.builder() \
    .token(BOT_TOKEN) \
    .request(request) \
    .build()

# =========================
# FASTAPI
# =========================
app = FastAPI()

# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info(user_id)
    await update.message.reply_text(
        "Бот запущен.\n"
        "Команда: /status"
    )

# =========================
# /status С РЕАЛЬНЫМ ПИНГОМ ДО TELEGRAM
# =========================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Реальный пинг — делаем запрос к Telegram API (getMe — самый лёгкий)
    t1 = time.perf_counter()
    try:
        bot_info = await telegram_app.bot.get_me()
        success = True
    except Exception:
        success = False
    
    t2 = time.perf_counter()
    real_ping_ms = round((t2 - t1) * 1000, 2)

    uptime = datetime.now() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

    if success:
        ping_text = f"⚡ Реальный пинг: {real_ping_ms} ms"
    else:
        ping_text = "⚡ Реальный пинг: ошибка соединения"

    await update.message.reply_text(
        "🟢 Статус: ONLINE\n"
        f"{ping_text}\n"
        f"🕒 Запущен: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"⏱ Uptime: {uptime_str}"
    )

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("status", status))

# =========================
# WEBHOOK ENDPOINT
# =========================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# =========================
# STARTUP / SHUTDOWN
# =========================
@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook установлен: {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.bot.delete_webhook()
    await telegram_app.shutdown()