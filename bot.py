import os
import aiohttp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))
CHANNEL = os.getenv("CHANNEL")  # @amane_friends

FOOTER = "\n\n━━━━━━━━━━━━━━\nAPI by @amane_friends\nOwner @amane_friends"

# ================= AUTH =================
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id == OWNER_ID:
        return True

    if chat_id != GROUP_ID:
        await update.message.reply_text("❌ This bot works only in authorized group.")
        return False

    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        if member.status in ("left", "kicked"):
            await update.message.reply_text(
                f"🚫 Join {CHANNEL} first to use this bot."
            )
            return False
    except:
        await update.message.reply_text(
            f"⚠️ Please join {CHANNEL} first."
        )
        return False

    return True


# ================= FETCH =================
async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=15) as r:
            return await r.text()


# ================= START + MENU =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📱 Number Info", callback_data="num")],
        [InlineKeyboardButton("🆔 Aadhaar Info", callback_data="adh")],
        [InlineKeyboardButton("🚗 Vehicle Info", callback_data="vec")],
        [InlineKeyboardButton("💳 UPI Info", callback_data="upi")],
        [InlineKeyboardButton("🏦 IFSC Info", callback_data="ifsc")],
    ]

    await update.message.reply_text(
        "🔍 Select search option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    msg = {
        "num": "📱 Use:\n/num 9876543210",
        "adh": "🆔 Use:\n/adh 123412341234",
        "vec": "🚗 Use:\n/vec WB12AB1234",
        "upi": "💳 Use:\n/upi name@bank",
        "ifsc": "🏦 Use:\n/ifsc SBIN0000001"
    }

    await q.edit_message_text(msg.get(q.data, "Invalid option"))


# ================= COMMANDS =================
async def num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /num 9876543210")
        return
    url = f"https://usesirosint.vercel.app/api/numinfo?key=land&num={context.args[0]}"
    await update.message.reply_text(await fetch(url) + FOOTER)


async def adh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /adh 123412341234")
        return
    url = f"https://usesirosint.vercel.app/api/aadhar?key=land&aadhar={context.args[0]}"
    await update.message.reply_text(await fetch(url) + FOOTER)


async def vec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /vec WB12AB1234")
        return
    url = f"https://usesirosint.vercel.app/api/rcnum?key=land&rc={context.args[0]}"
    await update.message.reply_text(await fetch(url) + FOOTER)


# ================= UPI (REALISTIC) =================
BANK_MAP = {
    "okhdfc": "HDFC Bank",
    "okicici": "ICICI Bank",
    "oksbi": "State Bank of India",
    "ybl": "Yes Bank",
    "paytm": "Paytm Payments Bank",
    "ibl": "IDBI Bank",
    "axl": "Axis Bank",
    "upi": "Generic UPI"
}

async def upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return

    if not context.args or "@" not in context.args[0]:
        await update.message.reply_text("Usage: /upi name@bank")
        return

    upi_id = context.args[0].lower()
    handle = upi_id.split("@")[-1]
    bank = BANK_MAP.get(handle, "Unknown Bank")

    text = (
        f"🔎 UPI ID INFO\n\n"
        f"• UPI ID: {upi_id}\n"
        f"• Bank: {bank}\n"
        f"• Account Holder: Not publicly available\n"
        f"• IFSC: Not available"
        f"{FOOTER}"
    )

    await update.message.reply_text(text)


async def ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /ifsc SBIN0000001")
        return
    url = f"https://ifsc.razorpay.com/{context.args[0]}"
    await update.message.reply_text(await fetch(url) + FOOTER)


# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num))
    app.add_handler(CommandHandler("adh", adh))
    app.add_handler(CommandHandler("vec", vec))
    app.add_handler(CommandHandler("upi", upi))
    app.add_handler(CommandHandler("ifsc", ifsc))
    app.add_handler(CallbackQueryHandler(menu_handler))

    print("🤖 Telegram Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()