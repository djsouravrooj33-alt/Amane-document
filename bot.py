import os
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
OWNER_ID = 8145485145
GROUP_ID = -1003296016362
CHANNEL_USERNAME = "@amane_friends"

OWNER_TAG = "@amane_friends"
API_BY = "@amane_friends"

# ================= API URLS =================
NUM_API = "https://usesirosint.vercel.app/api/numinfo?key=land&num={}"
AADHAR_API = "https://usesirosint.vercel.app/api/aadhar?key=land&aadhar={}"
RC_API = "https://usesirosint.vercel.app/api/rcnum?key=land&rc={}"

# ================= HELPERS =================
async def check_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def fetch_api(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=20) as r:
            return await r.text()


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_channel(update, context):
        btn = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")]]
        await update.message.reply_text(
            "❌ Bot ব্যবহার করতে হলে channel join করতে হবে",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    text = (
        "🤖 *Welcome to Document Bot*\n\n"
        "🔍 Available Commands:\n"
        "/num <number>\n"
        "/adh <aadhar>\n"
        "/vec <vehicle>\n"
        "/upi <upi_id>\n"
        "/ifsc <ifsc>\n\n"
        f"👑 Owner: {OWNER_TAG}\n"
        f"⚡ API BY: {API_BY}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ================= COMMANDS =================
async def num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /num 9XXXXXXXXX")
        return
    data = await fetch_api(NUM_API.format(context.args[0]))
    await update.message.reply_text(f"{data}\n\nAPI BY {API_BY}")


async def adh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /adh XXXXXXXXXXXX")
        return
    data = await fetch_api(AADHAR_API.format(context.args[0]))
    await update.message.reply_text(f"{data}\n\nAPI BY {API_BY}")


async def vec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /vec WBXX1234")
        return
    data = await fetch_api(RC_API.format(context.args[0]))
    await update.message.reply_text(f"{data}\n\nAPI BY {API_BY}")


async def upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /upi name@bank")
        return

    upi_id = context.args[0]
    if "@" not in upi_id:
        await update.message.reply_text("❌ Invalid UPI ID")
        return

    bank = upi_id.split("@")[1].upper()
    await update.message.reply_text(
        f"✅ UPI ID: `{upi_id}`\n🏦 Bank: {bank}\n\nAPI BY {API_BY}",
        parse_mode="Markdown"
    )


async def ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /ifsc SBIN0000001")
        return

    code = context.args[0]
    url = f"https://ifsc.razorpay.com/{code}"

    try:
        data = await fetch_api(url)
        await update.message.reply_text(f"{data}\n\nAPI BY {API_BY}")
    except:
        await update.message.reply_text("❌ Invalid IFSC Code")


# ================= MENU HANDLER =================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Coming Soon")


# ================= MAIN =================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num))
    app.add_handler(CommandHandler("adh", adh))
    app.add_handler(CommandHandler("vec", vec))
    app.add_handler(CommandHandler("upi", upi))
    app.add_handler(CommandHandler("ifsc", ifsc))
    app.add_handler(CallbackQueryHandler(menu_handler))

    print("🤖 Telegram Bot Running...")

    await app.initialize()
    await app.start()
    await asyncio.Event().wait()  # keep alive


if __name__ == "__main__":
    asyncio.run(main())