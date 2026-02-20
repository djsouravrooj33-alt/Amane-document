import os
import json
import aiohttp
import asyncio
from threading import Thread
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ================= FLASK (Render Port Bind) =================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 Telegram Bot Running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ Flask server started")

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not set")

OWNER_ID = 8145485145
CHANNEL_USERNAME = "@amane_friends"
ALLOWED_GROUP_ID = -1003296016362
API_BY = "@amane_friends"

NUM_API = "https://num.proportalxc.workers .dev/?mobile={}"
AADHAR_API = "https://api.paanel.shop/numapi.php?action=api&key=SALAAR&aadhar={}"
RC_API = "https://org.proportalxc.workers.dev/?rc={}"

# ================= AUTH SYSTEM =================
AUTH_FILE = "authorized_users.json"

def load_users():
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE) as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_users(users):
    with open(AUTH_FILE, "w") as f:
        json.dump(list(users), f)

AUTHORIZED_USERS = load_users()

async def is_authorized(update: Update):
    uid = update.effective_user.id
    if uid == OWNER_ID:
        return True
    return uid in AUTHORIZED_USERS

# ================= HELPERS =================
async def check_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME, update.effective_user.id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def fetch_text(url):
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=20) as r:
            return await r.text()

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        await update.message.reply_text("❌ You are not authorized")
        return

    if not await check_channel(update, context):
        btn = [[InlineKeyboardButton("🔔 Join Channel", url="https://t.me/amane_friends")]]
        await update.message.reply_text(
            "❌ Join channel first",
            reply_markup=InlineKeyboardMarkup(btn),
        )
        return

    await update.message.reply_text(
        "🤖 *Bot Ready!*\n\n"
        "📱 /num 9XXXXXXXXX\n"
        "🆔 /adh XXXXXXXXXXXX\n"
        "🚗 /vec UP78FU3511\n"
        "💳 /upi name@bank\n"
        "🏦 /ifsc SBIN0001234\n\n"
        f"⚡ API BY {API_BY}",
        parse_mode="Markdown",
    )

# ---------- OWNER ----------
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    uid = int(context.args[0])
    AUTHORIZED_USERS.add(uid)
    save_users(AUTHORIZED_USERS)
    await update.message.reply_text(f"✅ Added `{uid}`", parse_mode="Markdown")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    uid = int(context.args[0])
    AUTHORIZED_USERS.discard(uid)
    save_users(AUTHORIZED_USERS)
    await update.message.reply_text(f"❌ Removed `{uid}`", parse_mode="Markdown")

async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = "\n".join(map(str, AUTHORIZED_USERS)) or "No users"
    await update.message.reply_text(text)

# ---------- NUM ----------
async def num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    number = context.args[0]
    msg = await update.message.reply_text("🔄 Fetching number info...")
    data = await fetch_text(NUM_API.format(number))
    await msg.edit_text(f"{data}\n\n⚡ API BY {API_BY}")

# ---------- AADHAR ----------
async def adh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    aadhar = context.args[0]
    msg = await update.message.reply_text("🔄 Fetching aadhar info...")
    data = await fetch_text(AADHAR_API.format(aadhar))
    await msg.edit_text(f"{data}\n\n⚡ API BY {API_BY}")

# ---------- VEHICLE ----------
async def vec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    rc = context.args[0].upper()
    msg = await update.message.reply_text("🔄 Fetching RC info...")

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(RC_API.format(rc), timeout=20) as r:
                data = await r.json()

        owner = data["data"]["ownership_profile_analytics"]
        tech = data["data"]["technical_structural_blueprint"]

        await msg.edit_text(
            f"🚗 *RC DETAILS*\n"
            f"👤 Owner: `{owner.get('legal_asset_holder')}`\n"
            f"🏭 Model: `{tech.get('manufacturer_origin')}`\n"
            f"⛽ Fuel: `{tech.get('propulsion_energy_source')}`\n\n"
            f"⚡ API BY {API_BY}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await msg.edit_text(str(e))

# ---------- UPI ----------
async def upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    upi_id = context.args[0]
    psp = upi_id.split("@")[1].upper()
    await update.message.reply_text(
        f"💳 *UPI INFO*\n"
        f"UPI: `{upi_id}`\n"
        f"Provider: `{psp}`\n\n"
        f"⚠️ Owner name not public\n"
        f"⚡ API BY {API_BY}",
        parse_mode="Markdown",
    )

# ---------- IFSC ----------
async def ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return

    code = context.args[0].upper()
    msg = await update.message.reply_text("🔄 Fetching IFSC...")

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://ifsc.razorpay.com/{code}") as r:
                if r.status != 200:
                    await msg.edit_text("❌ Invalid IFSC")
                    return
                d = await r.json()

        await msg.edit_text(
            f"🏦 *{d['BANK']}*\n"
            f"📍 {d['BRANCH']}\n"
            f"{d['CITY']}, {d['STATE']}\n\n"
            f"⚡ API BY {API_BY}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await msg.edit_text(str(e))

# ================= MAIN =================
def main():
    keep_alive()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num))
    app.add_handler(CommandHandler("adh", adh))
    app.add_handler(CommandHandler("vec", vec))
    app.add_handler(CommandHandler("upi", upi))
    app.add_handler(CommandHandler("ifsc", ifsc))

    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("listusers", listusers))

    print("✅ Bot Started")
    app.run_polling()

if __name__ == "__main__":
    main()