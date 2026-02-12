import os
import asyncio
import aiohttp
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========== Render HTTP Server for Port Binding ==========
from flask import Flask
from threading import Thread

# Flask app for Render port detection
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "🤖 Telegram Bot is Running!"

@app_flask.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    """Starts HTTP server for Render port binding"""
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print(f"✅ HTTP Server started on port {os.environ.get('PORT', 8080)}")

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")

OWNER_ID = 8145485145
GROUP_ID = -1003296016362
CHANNEL_USERNAME = "@amane_friends"

OWNER_TAG = "@amane_friends"
API_BY = "@amane_friends"

# ================= AUTHORIZED USERS SYSTEM =================
AUTH_FILE = "authorized_users.json"

def load_authorized_users():
    """Load authorized users from JSON file"""
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_authorized_users(users):
    """Save authorized users to JSON file"""
    with open(AUTH_FILE, 'w') as f:
        json.dump(list(users), f)

# Load authorized users on startup
AUTHORIZED_USERS = load_authorized_users()
print(f"✅ Loaded {len(AUTHORIZED_USERS)} authorized users")

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is authorized to use the bot"""
    user_id = update.effective_user.id
    
    # Owner always authorized
    if user_id == OWNER_ID:
        return True
    
    # Check if in group and authorized
    if update.effective_chat.type in ["group", "supergroup"]:
        return user_id in AUTHORIZED_USERS
    
    # Private chat - only owner
    return user_id == OWNER_ID

# ================= API URLS =================
NUM_API = "https://usesirosint.vercel.app/api/numinfo?key=land&num={}"
AADHAR_API = "https://usesirosint.vercel.app/api/aadhar?key=land&aadhar={}"
RC_API = "https://usesirosint.vercel.app/api/rcnum?key=land&rc={}"

# ================= HELPERS =================
async def check_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has joined the channel"""
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Channel check error: {e}")
        return False

async def fetch_api(url):
    """Fetch data from API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return f"❌ API Error: {response.status}"
    except asyncio.TimeoutError:
        return "❌ Request timeout! API is slow."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ================= AUTHORIZATION COMMANDS =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add user to authorized list (Owner only)"""
    # Check if owner
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can use this command!")
        return
    
    # Check if user ID provided
    if not context.args:
        await update.message.reply_text("📝 *Usage:* `/adduser 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        
        # Add to authorized users
        AUTHORIZED_USERS.add(user_id)
        save_authorized_users(AUTHORIZED_USERS)
        
        await update.message.reply_text(
            f"✅ *User Authorized Successfully!*\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"📊 Total Authorized: `{len(AUTHORIZED_USERS)}`",
            parse_mode="Markdown"
        )
        
        # Try to notify the user
        try:
            await context.bot.send_message(
                user_id,
                "✅ You have been authorized to use the bot in the group!"
            )
        except:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove user from authorized list (Owner only)"""
    # Check if owner
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can use this command!")
        return
    
    if not context.args:
        await update.message.reply_text("📝 *Usage:* `/removeuser 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        
        # Remove from authorized users
        if user_id in AUTHORIZED_USERS:
            AUTHORIZED_USERS.remove(user_id)
            save_authorized_users(AUTHORIZED_USERS)
            await update.message.reply_text(
                f"✅ *User Removed!*\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"📊 Total Authorized: `{len(AUTHORIZED_USERS)}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ User not in authorized list!")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID!")

async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all authorized users (Owner only)"""
    # Check if owner
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can use this command!")
        return
    
    if not AUTHORIZED_USERS:
        await update.message.reply_text("📭 No authorized users found!")
        return
    
    user_list = "\n".join([f"• `{uid}`" for uid in AUTHORIZED_USERS])
    
    await update.message.reply_text(
        f"📋 *Authorized Users List*\n\n"
        f"{user_list}\n\n"
        f"📊 Total: `{len(AUTHORIZED_USERS)}`",
        parse_mode="Markdown"
    )

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    
    # Private chat - only owner
    if update.effective_chat.type == "private":
        if user.id != OWNER_ID:
            await update.message.reply_text(
                "❌ This bot only works in authorized groups!\n"
                "Contact owner for access: @amane_friends"
            )
            return
    
    # Check authorization for group
    if update.effective_chat.type in ["group", "supergroup"]:
        if not await is_authorized(update, context):
            await update.message.reply_text(
                "❌ *You are not authorized to use this bot!*\n\n"
                "Contact owner for access: @amane_friends",
                parse_mode="Markdown"
            )
            return
    
    # Check channel membership
    if not await check_channel(update, context):
        btn = [[
            InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")
        ]]
        await update.message.reply_text(
            "❌ *You must join our channel to use this bot!*\n\n"
            "👇 Click the button below to join",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode="Markdown"
        )
        return

    # Welcome message
    welcome_text = (
        f"🤖 *Welcome {user.first_name}!*\n\n"
        "🔍 *Available Commands:*\n"
        "━━━━━━━━━━━━━━━━\n"
        "📱 `/num 9XXXXXXXXX` - Mobile number info\n"
        "🆔 `/adh XXXXXXXXXXXX` - Aadhar card info\n"
        "🚗 `/vec WBXX1234567` - Vehicle RC info\n"
        "💳 `/upi name@bank` - UPI ID info\n"
        "🏦 `/ifsc SBIN0001234` - IFSC code info\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"👑 *Owner:* {OWNER_TAG}\n"
        f"⚡ *Powered by:* {API_BY}"
    )
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# ================= COMMAND HANDLERS =================
async def num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mobile number info command"""
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You are not authorized to use this bot!")
        return
    
    if not context.args:
        await update.message.reply_text("📱 *Usage:* `/num 9XXXXXXXXX`", parse_mode="Markdown")
        return
    
    if not await check_channel(update, context):
        await update.message.reply_text("❌ Please join the channel first! /start")
        return
    
    num = context.args[0]
    msg = await update.message.reply_text("🔄 *Fetching number information...*", parse_mode="Markdown")
    
    data = await fetch_api(NUM_API.format(num))
    await msg.edit_text(f"{data}\n\n━━━━━━━━━━━━━━━━\n⚡ API BY {API_BY}")

async def adh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aadhar card info command"""
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You are not authorized to use this bot!")
        return
    
    if not context.args:
        await update.message.reply_text("🆔 *Usage:* `/adh XXXXXXXXXXXX`", parse_mode="Markdown")
        return
    
    if not await check_channel(update, context):
        await update.message.reply_text("❌ Please join the channel first! /start")
        return
    
    aadhar = context.args[0]
    msg = await update.message.reply_text("🔄 *Fetching Aadhar information...*", parse_mode="Markdown")
    
    data = await fetch_api(AADHAR_API.format(aadhar))
    await msg.edit_text(f"{data}\n\n━━━━━━━━━━━━━━━━\n⚡ API BY {API_BY}")

async def vec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vehicle RC info command"""
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You are not authorized to use this bot!")
        return
    
    if not context.args:
        await update.message.reply_text("🚗 *Usage:* `/vec WBXX1234567`", parse_mode="Markdown")
        return
    
    if not await check_channel(update, context):
        await update.message.reply_text("❌ Please join the channel first! /start")
        return
    
    rc = context.args[0]
    msg = await update.message.reply_text("🔄 *Fetching vehicle information...*", parse_mode="Markdown")
    
    data = await fetch_api(RC_API.format(rc))
    await msg.edit_text(f"{data}\n\n━━━━━━━━━━━━━━━━\n⚡ API BY {API_BY}")

async def upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """UPI ID info command"""
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You are not authorized to use this bot!")
        return
    
    if not context.args:
        await update.message.reply_text("💳 *Usage:* `/upi name@bank`", parse_mode="Markdown")
        return
    
    if not await check_channel(update, context):
        await update.message.reply_text("❌ Please join the channel first! /start")
        return
    
    upi_id = context.args[0]
    if "@" not in upi_id:
        await update.message.reply_text("❌ *Invalid UPI ID!*\nExample: `name@okhdfcbank`", parse_mode="Markdown")
        return
    
    bank = upi_id.split("@")[1].upper()
    
    result = (
        f"✅ *UPI Information*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📌 *UPI ID:* `{upi_id}`\n"
        f"🏦 *Bank/Provider:* `{bank}`\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚡ API BY {API_BY}"
    )
    
    await update.message.reply_text(result, parse_mode="Markdown")

async def ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """IFSC code info command"""
    # Check authorization
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You are not authorized to use this bot!")
        return
    
    if not context.args:
        await update.message.reply_text("🏦 *Usage:* `/ifsc SBIN0001234`", parse_mode="Markdown")
        return
    
    if not await check_channel(update, context):
        await update.message.reply_text("❌ Please join the channel first! /start")
        return
    
    code = context.args[0]
    url = f"https://ifsc.razorpay.com/{code}"
    msg = await update.message.reply_text("🔄 *Fetching IFSC information...*", parse_mode="Markdown")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    bank_name = data.get('BANK', 'N/A')
                    branch = data.get('BRANCH', 'N/A')
                    address = data.get('ADDRESS', 'N/A')
                    city = data.get('CITY', 'N/A')
                    district = data.get('DISTRICT', 'N/A')
                    state = data.get('STATE', 'N/A')
                    
                    result = (
                        f"✅ *IFSC Information*\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"🏦 *Bank:* `{bank_name}`\n"
                        f"📍 *Branch:* `{branch}`\n"
                        f"🏙️ *City:* `{city}`\n"
                        f"🏛️ *District:* `{district}`\n"
                        f"🌍 *State:* `{state}`\n"
                        f"📮 *Address:* `{address[:100]}...`\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"⚡ API BY {API_BY}"
                    )
                    await msg.edit_text(result, parse_mode="Markdown")
                else:
                    await msg.edit_text("❌ *Invalid IFSC Code!*", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ *Error:* `{str(e)}`", parse_mode="Markdown")

# ================= CALLBACK HANDLER =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard buttons"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚡ Feature coming soon...")

# ================= ERROR HANDLER =================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    print(f"Update {update} caused error {context.error}")

# ================= MAIN =================
def main():
    """Main function to run the bot"""
    print("🚀 Starting Telegram Bot...")
    
    # Start HTTP server for Render
    keep_alive()
    print("✅ HTTP Server active")
    
    # Create bot application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num))
    app.add_handler(CommandHandler("adh", adh))
    app.add_handler(CommandHandler("vec", vec))
    app.add_handler(CommandHandler("upi", upi))
    app.add_handler(CommandHandler("ifsc", ifsc))
    
    # Add authorization commands
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("listusers", listusers))
    
    # Add button handler
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    print("🤖 Bot is polling for updates...")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"📊 Authorized Users: {len(AUTHORIZED_USERS)}")
    print(f"⚡ API BY: {API_BY}")
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()