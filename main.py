import logging
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
# =========================
# НАСТРОЙКИ
# =========================
BOT_TOKEN = "6410092302:AAFp1lFVxUOU2GU5VJNviYY2nAHDWnGcyfA"
WEBHOOK_URL = "https://your-domain.com/webhook" # ОБЯЗАТЕЛЬНО HTTPS
# =========================
# ВРЕМЯ ЗАПУСКА
# =========================
START_TIME = datetime.now()
# =========================
# ЛОГИ (ТОЛЬКО user_id)
# =========================
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | user_id=%(message)s"
)
# =========================
# TELEGRAM APP
# =========================
telegram_app = Application.builder().token(BOT_TOKEN).build()
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
# /status
# =========================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t1 = time.perf_counter()
    uptime = datetime.now() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))
    t2 = time.perf_counter()
    ping_ms = round((t2 - t1) * 1000, 2)
    await update.message.reply_text(
        "🟢 Статус: ONLINE\n"
        f"⚡ Ping: {ping_ms} ms\n"
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
# STARTUP
# =========================
@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.bot.delete_webhook()
    await telegram_app.shutdown()
