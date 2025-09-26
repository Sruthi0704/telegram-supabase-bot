import os
import logging
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- Load environment variables ----------------
load_dotenv()  # loads .env from same folder

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- Read secrets from environment ----------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not (SUPABASE_URL and SUPABASE_KEY and BOT_TOKEN):
    raise RuntimeError("Missing env var: SUPABASE_URL, SUPABASE_KEY or BOT_TOKEN")

logging.info("Environment variables loaded successfully.")  # safe log

# ---------------- Supabase client ----------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- Helper function ----------------
def get_answer_from_db_sync(user_message: str) -> str:
    """Fetch answer from Supabase faq table"""
    resp = supabase.table("faq").select("answer").ilike("question_keyword", f"%{user_message}%").execute()
    data = None
    if isinstance(resp, dict):
        data = resp.get("data")
    else:
        data = getattr(resp, "data", None)
    if data and len(data) > 0:
        return data[0].get("answer", "Sorry, no answer found.")
    return "Sorry, I don't have an answer for that yet. Please ask something else about Agritech."

# ---------------- Telegram Handlers ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! 👋 How can I help you with Agritech today?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text or ""
    loop = asyncio.get_running_loop()
    answer = await loop.run_in_executor(None, get_answer_from_db_sync, user_text)
    await update.message.reply_text(answer)

# ---------------- Main ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("Bot started. Polling Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()
