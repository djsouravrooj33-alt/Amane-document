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
RC_API = "https://org.proportalxc.workers.dev/?rc={}"  # ✅ নতুন পাওয়ারফুল API

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
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can use this command!")
        return
    
    if not context.args:
        await update.message.reply_text("📝 *Usage:* `/adduser 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        AUTHORIZED_USERS.add(user_id)
        save_authorized_users(AUTHORIZED_USERS)
        
        await update.message.reply_text(
            f"✅ *User Authorized Successfully!*\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"📊 Total Authorized: `{len(AUTHORIZED_USERS)}`",
            parse_mode="Markdown"
        )
        
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
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can use this command!")
        return
    
    if not context.args:
        await update.message.reply_text("📝 *Usage:* `/removeuser 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        
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
        "🚗 `/vec UP78FU3511` - Vehicle RC info (NEW API!)\n"
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
    """Vehicle RC info command - NEW POWERFUL API"""
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You are not authorized to use this bot!")
        return
    
    if not context.args:
        await update.message.reply_text("🚗 *Usage:* `/vec UP78FU3511`", parse_mode="Markdown")
        return
    
    if not await check_channel(update, context):
        await update.message.reply_text("❌ Please join the channel first! /start")
        return
    
    rc = context.args[0].upper()
    msg = await update.message.reply_text("🔄 *Fetching vehicle information from Proportalxc API...*", parse_mode="Markdown")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(RC_API.format(rc), timeout=20) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract data from the new API structure
                    reg_data = data.get('data', {}).get('registration_identity_matrix', {})
                    owner_data = data.get('data', {}).get('ownership_profile_analytics', {})
                    tech_data = data.get('data', {}).get('technical_structural_blueprint', {})
                    insurance_data = data.get('data', {}).get('insurance_security_audit_report', {})
                    financial_data = data.get('data', {}).get('financial_legal_encumbrance_vault', {})
                    timeline_data = data.get('data', {}).get('lifecycle_compliance_timeline', {})
                    rto_data = data.get('data', {}).get('regional_transport_intelligence_grid', {})
                    
                    # Format the response
                    result = (
                        f"🚗 *VEHICLE RC DETAILS*\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"📌 *Registration No:* `{reg_data.get('official_registration_id', rc)}`\n"
                        f"👤 *Owner Name:* `{owner_data.get('legal_asset_holder', 'N/A')}`\n"
                        f"📍 *Address:* `{owner_data.get('physical_location_address', 'N/A')[:100]}...`\n"
                        f"🏭 *Vehicle Model:* `{tech_data.get('manufacturer_origin', 'N/A')}`\n"
                        f"🔧 *Engine:* `{tech_data.get('engine_id_mask', 'N/A')}`\n"
                        f"🔩 *Chassis:* `{tech_data.get('chassis_id_mask', 'N/A')}`\n"
                        f"⛽ *Fuel:* `{tech_data.get('propulsion_energy_source', 'N/A')}`\n"
                        f"📅 *Registration Date:* `{timeline_data.get('inception_registration_date', 'N/A')}`\n"
                        f"📊 *Vehicle Age:* `{timeline_data.get('chronological_asset_age', 'N/A')}`\n"
                        f"🏛️ *RTO Office:* `{rto_data.get('zonal_transport_office', 'N/A')}`\n"
                        f"🏙️ *City:* `{owner_data.get('geo_administrative_city', 'N/A')}`\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"🛡️ *Insurance:* `{insurance_data.get('underwriting_organization', 'N/A')}`\n"
                        f"📅 *Insurance Expiry:* `{insurance_data.get('protection_validity_limit', 'N/A')}`\n"
                        f"💰 *Loan/Lien:* `{financial_data.get('hypothecation_lien_status', 'N/A')}`\n"
                        f"🏦 *Lien Holder:* `{financial_data.get('lien_holder_institution', 'N/A')}`\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"⚡ API Developer: @Proportalxc\n"
                        f"⚡ Powered by: {API_BY}"
                    )
                    await msg.edit_text(result, parse_mode="Markdown")
                else:
                    await msg.edit_text("❌ *API Error! Please try again later.*", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ *Error:* `{str(e)}`", parse_mode="Markdown")

async def upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """UPI ID info command - IMPROVED"""
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
    
    psp = upi_id.split("@")[1].upper()
    
    # Full PSP/Bank mapping
    psp_names = {
        "OKHDFCBANK": "HDFC Bank",
        "OKSBI": "State Bank of India", 
        "OKICICI": "ICICI Bank",
        "OKAXIS": "Axis Bank",
        "OKKOTAK": "Kotak Mahindra Bank",
        "OKYESBANK": "Yes Bank",
        "PAYTM": "Paytm Payments Bank",
        "PHONEPE": "PhonePe",
        "YBL": "Yes Bank",
        "SBIN": "SBI",
        "HDFCBANK": "HDFC Bank",
        "ICICI": "ICICI Bank",
        "AXIS": "Axis Bank",
        "KOTAK": "Kotak Bank",
        "INDUS": "IndusInd Bank",
        "FED": "Federal Bank",
        "CANARA": "Canara Bank",
        "BOB": "Bank of Baroda",
        "PNB": "Punjab National Bank",
        "UNION": "Union Bank of India",
        "BANKOFBARODA": "Bank of Baroda",
        "IDBI": "IDBI Bank",
        "YESBANK": "Yes Bank",
        "RBL": "RBL Bank",
        "AU": "AU Small Finance Bank",
        "FINO": "FINO Payments Bank",
        "AIRTEL": "Airtel Payments Bank",
        "AMAZONPAY": "Amazon Pay",
        "GOOGLEPAY": "Google Pay",
        "BHIM": "BHIM UPI"
    }
    
    bank_name = psp_names.get(psp, psp)
    
    result = (
        f"✅ *UPI INFORMATION*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📌 *UPI ID:* `{upi_id}`\n"
        f"🏦 *Bank/Provider:* `{bank_name}`\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚡ *Note:* Owner name is not publicly available due to NPCI restrictions\n"
        f"⚡ API BY {API_BY}"
    )
    
    await update.message.reply_text(result, parse_mode="Markdown")

async def ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """IFSC code info command - DUAL API"""
    if not await is_authorized(update, context):
        await update.message.reply_text("❌ You are not authorized to use this bot!")
        return
    
    if not context.args:
        await update.message.reply_text("🏦 *Usage:* `/ifsc SBIN0001234`", parse_mode="Markdown")
        return
    
    if not await check_channel(update, context):
        await update.message.reply_text("❌ Please join the channel first! /start")
        return
    
    code = context.args[0].upper()
    msg = await update.message.reply_text("🔄 *Fetching IFSC information...*", parse_mode="Markdown")
    
    try:
        # Try first API
        url = f"https://ifsc.datayuge.com/?code={code}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') and data.get('data'):
                        bank_data = data['data']
                        result = (
                            f"✅ *IFSC INFORMATION*\n"
                            f"━━━━━━━━━━━━━━━━\n"
                            f"🏦 *Bank:* `{bank_data.get('bank', 'N/A')}`\n"
                            f"📍 *Branch:* `{bank_data.get('branch', 'N/A')}`\n"
                            f"🏙️ *City:* `{bank_data.get('city', 'N/A')}`\n"
                            f"🏛️ *District:* `{bank_data.get('district', 'N/A')}`\n"
                            f"🌍 *State:* `{bank_data.get('state', 'N/A')}`\n"
                            f"📮 *Address:* `{bank_data.get('address', 'N/A')[:100]}...`\n"
                            f"━━━━━━━━━━━━━━━━\n"
                            f"⚡ API BY {API_BY}"
                        )
                        await msg.edit_text(result, parse_mode="Markdown")
                    else:
                        # Try backup API
                        backup_url = f"https://ifsc.razorpay.com/{code}"
                        async with session.get(backup_url, timeout=10) as backup_res:
                            if backup_res.status == 200:
                                data = await backup_res.json()
                                result = (
                                    f"✅ *IFSC INFORMATION*\n"
                                    f"━━━━━━━━━━━━━━━━\n"
                                    f"🏦 *Bank:* `{data.get('BANK', 'N/A')}`\n"
                                    f"📍 *Branch:* `{data.get('BRANCH', 'N/A')}`\n"
                                    f"🏙️ *City:* `{data.get('CITY', 'N/A')}`\n"
                                    f"🏛️ *District:* `{data.get('DISTRICT', 'N/A')}`\n"
                                    f"🌍 *State:* `{data.get('STATE', 'N/A')}`\n"
                                    f"📮 *Address:* `{data.get('ADDRESS', 'N/A')[:100]}...`\n"
                                    f"━━━━━━━━━━━━━━━━\n"
                                    f"⚡ API BY {API_BY}"
                                )
                                await msg.edit_text(result, parse_mode="Markdown")
                            else:
                                await msg.edit_text("❌ *Invalid IFSC Code!*", parse_mode="Markdown")
                else:
                    await msg.edit_text("❌ *API Error! Try again later.*", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ *Error:* `{str(e)}`", parse_mode="Markdown")

# ================= CALLBACK HANDLER ================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):