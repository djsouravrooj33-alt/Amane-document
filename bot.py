import os
import aiohttp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))
CHANNEL = os.getenv("CHANNEL")  # @amane_friends

FOOTER = "\n\n━━━━━━━━━━━━━━\nAPI by @amane_friends\nOwner @amane_friends"

# ===== AUTH CHECK =====
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id == OWNER_ID:
        return True

    if chat_id != GROUP_ID:
        await update.message.reply_text("❌ This bot works only in authorized group.")
        return False

    member = await context.bot.get_chat_member(CHANNEL, user_id)
    if member.status in ["left", "kicked"]:
        await update.message.reply_text(
            f"🚫 Join {CHANNEL} first to use this bot."
        )
        return False

    return True


# ===== API FETCH =====
async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=15) as r:
            return await r.text()


# ===== COMMANDS =====
async def num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /num 9876543210")
        return
    num = context.args[0]
    url = f"https://usesirosint.vercel.app/api/numinfo?key=land&num={num}"
    data = await fetch(url)
    await update.message.reply_text(data + FOOTER)


async def adh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /adh 123412341234")
        return
    adh = context.args[0]
    url = f"https://usesirosint.vercel.app/api/aadhar?key=land&aadhar={adh}"
    data = await fetch(url)
    await update.message.reply_text(data + FOOTER)


async def vec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /vec WB12AB1234")
        return
    rc = context.args[0]
    url = f"https://usesirosint.vercel.app/api/rcnum?key=land&rc={rc}"
    data = await fetch(url)
    await update.message.reply_text(data + FOOTER)


async def upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /upi name@bank")
        return
    upi = context.args[0]
    url = f"https://api.upi-api.example/lookup?upi={upi}"  # placeholder
    data = await fetch(url)
    await update.message.reply_text(data + FOOTER)


async def ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /ifsc SBIN0000001")
        return
    ifsc = context.args[0]
    url = f"https://ifsc.razorpay.com/{ifsc}"
    data = await fetch(url)
    await update.message.reply_text(data + FOOTER)


# ===== MAIN =====
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("num", num))
app.add_handler(CommandHandler("adh", adh))
app.add_handler(CommandHandler("vec", vec))
app.add_handler(CommandHandler("upi", upi))
app.add_handler(CommandHandler("ifsc", ifsc))

print("🤖 Bot Started")
app.run_polling()
