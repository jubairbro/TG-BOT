# /root/.ssbot/bot.py
# ---

import logging
import subprocess
import json
import os
import re
from itertools import count

# Third-party libraries
import psutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# --- Configuration ---
BOT_TOKEN = "bot_token"
ADMIN_FILE = "admins.txt"
OWNER_ID = 5487394544
BOT_FOOTER = "\n© Bot by : @JubairFF"

# --- Channel Join Configuration (for non-authorized users) ---
JOIN_CHANNEL_URL = "https://t.me/+1p9RnexGMP0yOGVl"  # আপনার চ্যানেলের লিঙ্ক দিন
JOIN_CHANNEL_NAME = "Telegram Channel"          # আপনার চ্যানেলের নাম দিন

# --- Setup Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- State definitions ---
states = count()
SELECT_TYPE_CREATE, GET_USERNAME_CREATE, GET_DURATION_CREATE, GET_QUOTA_CREATE, GET_IP_LIMIT_CREATE, GET_PASSWORD_CREATE = [next(states) for _ in range(6)]
GET_ADMIN_ID_ADD, SELECT_ADMIN_TO_REMOVE = [next(states) for _ in range(2)]
SELECT_PROTOCOL_DELETE, SELECT_USER_DELETE, CONFIRM_DELETE = [next(states) for _ in range(3)]
SELECT_PROTOCOL_RENEW, SELECT_USER_RENEW, GET_NEW_DURATION_RENEW, GET_NEW_IP_LIMIT_RENEW = [next(states) for _ in range(4)]

# --- Font Styling ---
def style_text(text):
    """Apply special font styling to specific keywords"""
    font_mapping = {
        # Server/Host related
        'Server Host': '𝚂𝚎𝚛𝚟𝚎𝚛 𝙷𝚘𝚜𝚝',
        'Host Server': '𝙷𝚘𝚜𝚝 𝚂𝚎𝚛𝚟𝚎𝚛',
        'NS Host': '𝙽𝚂 𝙷𝚘𝚜𝚝',
        'Location': '𝙻𝚘𝚌𝚊𝚝𝚒𝚘𝚗',
        'Welcome': '𝚆𝚎𝚕𝚌𝚘𝚖𝚎',
        'Sensi Tunnel': '𝚂𝚎𝚗𝚜𝚒 𝚃𝚞𝚗𝚗𝚎𝚕',
        
        # Account related
        'Username': '𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎',
        'Password': '𝙿𝚊𝚜𝚜𝚠𝚘𝚛𝚍',
        'Description': '𝙳𝚎𝚜𝚌𝚛𝚒𝚙𝚝𝚒𝚘𝚗',
        'Expires': '𝙴𝚡𝚙𝚒𝚛𝚎𝚜',
        'Expires On': '𝙴𝚡𝚙𝚒𝚛𝚎𝚜 𝙾𝚗',
        
        # Technical terms
        'Port TLS': '𝙿𝚘𝚛𝚝 𝚃𝙻𝚂',
        'Port non TLS': '𝙿𝚘𝚛𝚝 𝚗𝚘𝚗 𝚃𝙻𝚂',
        'Port DNS': '𝙿𝚘𝚛𝚝 𝙳𝙽𝚂',
        'Security': '𝚂𝚎𝚌𝚞𝚛𝚒𝚝𝚢',
        'Network': '𝙽𝚎𝚝𝚠𝚘𝚛𝚔',
        'Path': '𝙿𝚊𝚝𝚑',
        'ServiceName': '𝚂𝚎𝚛𝚟𝚒𝚌𝚎𝙽𝚊𝚖𝚎',
        'User ID': '𝚄𝚜𝚎𝚛 𝙸𝙳',
        'Public key': '𝙿𝚞𝚋𝚕𝚒𝚌 𝚔𝚎𝚢',
        
        # Links
        'TLS Link': '𝚃𝙻𝚂 𝙻𝚒𝚗𝚔',
        'NTLS Link': '𝙽𝚃𝙻𝚂 𝙻𝚒𝚗𝚔',
        'GRPC Link': '𝙶𝚁𝙿𝙲 𝙻𝚒𝚗𝚔',
        'Save Link': '𝚂𝚊𝚟𝚎 𝙻𝚒𝚗𝚔',
        
        # Buttons and menus
        'Create Account': '𝙲𝚛𝚎𝚊𝚝𝚎 𝙰𝚌𝚌𝚘𝚞𝚗𝚝',
        'Manage Users': '𝙼𝚊𝚗𝚊𝚐𝚎 𝚄𝚜𝚎𝚛𝚜',
        'VPN Bot Menu': '𝚅𝙿𝙽 𝙱𝚘𝚝 𝙼𝚎𝚗𝚞',
        'User Management': '𝚄𝚜𝚎𝚛 𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝',
        'Server Management': '𝚂𝚎𝚛𝚟𝚎𝚛 𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝',
        'Admin Management': '𝙰𝚍𝚖𝚒𝚗 𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝',
    }
    
    for original, styled in font_mapping.items():
        text = text.replace(original, styled)
    
    return text

# --- Helper Functions ---

def load_admins():
    if not os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "w") as f: f.write(str(OWNER_ID) + "\n")
        return {OWNER_ID}
    with open(ADMIN_FILE, "r") as f:
        admins = {int(line.strip()) for line in f if line.strip()}
    admins.add(OWNER_ID)
    return admins

def save_admins(admins):
    with open(ADMIN_FILE, "w") as f:
        for admin_id in admins: f.write(str(admin_id) + "\n")

def is_admin(update: Update) -> bool:
    return update.effective_user.id in load_admins()

def run_script(command):
    logger.info(f"Executing command: {' '.join(command)}")
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
        return json.loads(process.stdout), None
    except json.JSONDecodeError:
        logger.error(f"JSONDecodeError in script output: {process.stdout}")
        return None, "Error: Script returned invalid JSON."
    except subprocess.CalledProcessError as e:
        logger.error(f"CalledProcessError: {e}. Stderr: {e.stderr}. Stdout: {e.stdout}")
        try:
            error_json = json.loads(e.stdout)
            return None, error_json.get('message', e.stderr)
        except (json.JSONDecodeError, AttributeError):
            return None, f"Error executing script: {e.stderr or e.stdout}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None, f"An unexpected error occurred: {e}"

def format_v2ray_output(data, account_type):
    d = data.get('data', {})
    save_link = f"https://{d.get('domain', 'your.domain.com')}:81/{account_type.lower()}-{d.get('username', 'user')}.txt"
    message = f"""
───────────────────────────
    Xray/{account_type.capitalize()} Account
───────────────────────────
**𝙳𝚎𝚜𝚌𝚛𝚒𝚙𝚝𝚒𝚘𝚗**  : `{d.get('username', 'N/A')}`
**𝙷𝚘𝚜𝚝 𝚂𝚎𝚛𝚟𝚎𝚛**  : `{d.get('domain', 'N/A')}`
**𝙽𝚂 𝙷𝚘𝚜𝚝**   : `{d.get('ns_domain', 'N/A')}`
**𝙻𝚘𝚌𝚊𝚝𝚒𝚘𝚗**     : `{d.get('city', 'N/A')}`
**𝙿𝚘𝚛𝚝 𝚃𝙻𝚂**     : `443`
**𝙿𝚘𝚛𝚝 𝚗𝚘𝚗 𝚃𝙻𝚂** : `80`, `8080`
**𝙿𝚘𝚛𝚝 𝙳𝙽𝚂**     : `53`, `443`
**𝚂𝚎𝚌𝚞𝚛𝚒𝚝𝚢**     : `auto`
**𝙽𝚎𝚝𝚠𝚘𝚛𝚔**      : `WS or gRPC`
**𝙿𝚊𝚝𝚑**         : `/whatever/{account_type.lower()}`
**𝚂𝚎𝚛𝚟𝚒𝚌𝚎𝙽𝚊𝚖𝚎**  : `{account_type.lower()}-grpc`
**𝚄𝚜𝚎𝚛 𝙸𝙳**      : `{d.get('uuid', 'N/A')}`
**𝙿𝚞𝚋𝚕𝚒𝚌 𝚔𝚎𝚢**  : `{d.get('pubkey', 'N/A')}`
───────────────────────────
**𝚃𝙻𝚂 𝙻𝚒𝚗𝚔**    : `{d.get(f'{account_type.lower()}_tls_link', 'N/A')}`
───────────────────────────
"""
    if d.get(f'{account_type.lower()}_nontls_link'):
        message += f"**𝙽𝚃𝙻𝚂 𝙻𝚒𝚗𝚔**   : `{d.get(f'{account_type.lower()}_nontls_link', 'N/A')}`\n───────────────────────────\n"
    if d.get(f'{account_type.lower()}_grpc_link'):
        message += f"**𝙶𝚁𝙿𝙲 𝙻𝚒𝚗𝚔**   : `{d.get(f'{account_type.lower()}_grpc_link', 'N/A')}`\n───────────────────────────\n"
    message += f"""
**𝚂𝚊𝚟𝚎 𝙻𝚒𝚗𝚔**   : {save_link}
───────────────────────────
**𝙴𝚡𝚙𝚒𝚛𝚎𝚜 𝙾𝚗**  : `{d.get('expired', 'N/A')}`
"""
    return style_text(message)

def format_ssh_output(data):
    d = data.get('data', {})
    save_link = f"https://{d.get('domain', 'your.domain.com')}:81/ssh-{d.get('username', 'user')}.txt"
    return style_text(f"""
───────────────────────────
    SSH / OVPN Account Created
───────────────────────────
**𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎**   : `{d.get('username', 'N/A')}`
**𝙿𝚊𝚜𝚜𝚠𝚘𝚛𝚍**   : `{d.get('password', 'N/A')}`
**𝙷𝚘𝚜𝚝**       : `{d.get('domain', 'N/A')}`
**𝙽𝚂 𝙷𝚘𝚜𝚝**   : `{d.get('ns_domain', 'N-A')}`
**𝙻𝚘𝚌𝚊𝚝𝚒𝚘𝚗**   : `{d.get('city', 'N/A')}`
**𝙿𝚞𝚋𝚕𝚒𝚌 𝚔𝚎𝚢**  : `{d.get('pubkey', 'N/A')}`
**𝙴𝚡𝚙𝚒𝚛𝚎𝚜**    : `{d.get('expired', 'N/A')}`
───────────────────────────
── **Ports** ──
**OpenSSH**   : `443`, `80`, `22`
**UDP SSH**   : `1-65535`
**DNS**       : `443`, `53`, `22`
**Dropbear**  : `443`, `109`
**SSH WS**    : `80`
**SSH SSLWS** : `443`
**SSL/TLS**   : `443`
**OVPN SSL**  : `443`
**OVPN TCP**  : `1194`
**OVPN UDP**  : `2200`
**BadVPN UDP**: `7100`, `7300`
───────────────────────────
── **configuration** ──
**Port 80 config :**
`{d.get('domain', 'N/A')}:80@{d.get('username', 'N/A')}:{d.get('password', 'N/A')}`
**port 443 config :**
`{d.get('domain', 'N/A')}:443@{d.get('username', 'N/A')}:{d.get('password', 'N/A')}`
**UPD Custom Config** : 
`{d.get('domain', 'N/A')}:1-65535@{d.get('username', 'N/A')}:{d.get('password', 'N/A')}`
───────────────────────────
**𝚂𝚊𝚟𝚎 𝙻𝚒𝚗𝚔**  : {save_link}
───────────────────────────
""")

async def get_users_for_protocol(protocol):
    data, error = run_script(['/usr/bin/apidelete', protocol])
    if error or data.get('status') != 'success':
        return [], error or data.get('message', 'Failed to fetch user list.')
    return data.get('users', []), None

async def delete_previous_messages(context: ContextTypes.DEFAULT_TYPE, update: Update):
    """Deletes the bot's last prompt and the user's reply."""
    chat_id = update.effective_chat.id
    user_message_id = update.message.message_id
    prompt_message_id = context.user_data.pop('prompt_message_id', None)
    
    try:
        if prompt_message_id:
            await context.bot.delete_message(chat_id=chat_id, message_id=prompt_message_id)
        if user_message_id:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_message_id)
    except Exception as e:
        logger.warning(f"Could not delete message: {e}")

# --- UI Menus ---
async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return
        
    welcome_message = style_text(f"""╭─────────────────────────╮
│ </> **𝚅𝙿𝙽 𝙱𝚘𝚝 𝙼𝚎𝚗𝚞** >          │
╭─────────────────────────╯
**𝚆𝚎𝚕𝚌𝚘𝚖𝚎**, {user.first_name}!
**𝙸 𝚊𝚖** your VPN Account
**𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝 𝙱𝚘𝚝.**
╰─────────────────────────╯""")
    
    keyboard = [
        [InlineKeyboardButton("➕ 𝙲𝚛𝚎𝚊𝚝𝚎 𝙰𝚌𝚌𝚘𝚞𝚗𝚝", callback_data="create_account_start")],
        [InlineKeyboardButton("👥 𝙼𝚊𝚗𝚊𝚐𝚎 𝚄𝚜𝚎𝚛𝚜", callback_data="manage_users_menu")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    if is_admin(update):
        keyboard.append([InlineKeyboardButton("🖥️ Server", callback_data="server_menu")])
        keyboard.append([InlineKeyboardButton("🔒 Admin", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.delete()
        await context.bot.send_message(update.effective_chat.id, welcome_message + BOT_FOOTER, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(welcome_message + BOT_FOOTER, reply_markup=reply_markup, parse_mode='Markdown')

def create_protocol_menu(callback_prefix, back_target="back_to_main"):
    keyboard = [
        [InlineKeyboardButton("Vmess", callback_data=f"{callback_prefix}_vmess"), InlineKeyboardButton("Vless", callback_data=f"{callback_prefix}_vless")],
        [InlineKeyboardButton("Trojan", callback_data=f"{callback_prefix}_trojan"), InlineKeyboardButton("SSH", callback_data=f"{callback_prefix}_ssh")],
        [InlineKeyboardButton("« Back", callback_data=back_target)],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_button_menu(back_target="back_to_main"):
    keyboard = [
        [InlineKeyboardButton("« Back", callback_data=back_target)],
    ]
    return InlineKeyboardMarkup(keyboard)
    
def create_cancel_menu():
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]]
    return InlineKeyboardMarkup(keyboard)

# --- Command & Fallback Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        keyboard = [[InlineKeyboardButton(f"📢 Join {JOIN_CHANNEL_NAME}", url=JOIN_CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⛔️ You are not authorized to use this bot." + BOT_FOOTER, reply_markup=reply_markup)
        return
    
    await send_main_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = style_text("""╭─────────────────────────╮
│ </> **Bot Help** >              │
╭─────────────────────────╯
**𝚃𝚑𝚒𝚜 𝚋𝚘𝚝** helps you manage
**𝚅𝙿𝙽 𝚊𝚌𝚌𝚘𝚞𝚗𝚝𝚜**. The interface is
**𝚏𝚞𝚕𝚕𝚢 𝚋𝚞𝚝𝚝𝚘𝚗-𝚍𝚛𝚒𝚟𝚎𝚗.**
│
**𝚄𝚜𝚎** /cancel or the Cancel button
**𝚝𝚘 𝚜𝚝𝚘𝚙 𝚊𝚗𝚢 𝚘𝚗𝚐𝚘𝚒𝚗𝚐 𝚙𝚛𝚘𝚌𝚎𝚜𝚜.**
╰─────────────────────────╯""")
    
    keyboard = [[InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")]]
    await update.callback_query.edit_message_text(help_text + BOT_FOOTER, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current operation and returns to the main menu."""
    if update.callback_query:
        await update.callback_query.answer("Operation cancelled.")
    
    prompt_message_id = context.user_data.pop('prompt_message_id', None)
    if prompt_message_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_message_id)
        except Exception:
            pass

    context.user_data.clear()
    await send_main_menu(update, context)
    return ConversationHandler.END

# --- Bot Restart Command ---
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the bot service"""
    if not is_admin(update):
        await update.message.reply_text("⛔️ You are not authorized to use this command." + BOT_FOOTER)
        return
    
    await update.message.reply_text("🔄 𝚁𝚎𝚜𝚝𝚊𝚛𝚝𝚒𝚗𝚐 𝚋𝚘𝚝 𝚜𝚎𝚛𝚟𝚒𝚌𝚎..." + BOT_FOOTER)
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'bot.service'], check=True)
        await update.message.reply_text("✅ 𝙱𝚘𝚝 𝚜𝚎𝚛𝚟𝚒𝚌𝚎 𝚛𝚎𝚜𝚝𝚊𝚛𝚝𝚎𝚍 𝚜𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕𝚢!" + BOT_FOOTER)
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ 𝙵𝚊𝚒𝚕𝚎𝚍 𝚝𝚘 𝚛𝚎𝚜𝚝𝚊𝚛𝚝 𝚋𝚘𝚝 𝚜𝚎𝚛𝚟𝚒𝚌𝚎: {e}" + BOT_FOOTER)
    except Exception as e:
        await update.message.reply_text(f"❌ 𝙴𝚛𝚛𝚘𝚛: {e}" + BOT_FOOTER)

# --- Account Creation Conversation ---
async def create_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = style_text("""╭─────────────────────────╮
│ </> **𝙲𝚛𝚎𝚊𝚝𝚎 𝙰𝚌𝚌𝚘𝚞𝚗𝚝** >        │
╭─────────────────────────╯
**𝙿𝚕𝚎𝚊𝚜𝚎 𝚌𝚑𝚘𝚘𝚜𝚎** the account
**𝚝𝚢𝚙𝚎** to create.
╰─────────────────────────╯""")
    await update.callback_query.edit_message_text(text, reply_markup=create_protocol_menu("create_proto", "back_to_main"), parse_mode='Markdown')
    return SELECT_TYPE_CREATE

async def select_type_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    account_type = query.data.split('_')[2]
    context.user_data['account_type'] = account_type
    
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙲𝚛𝚎𝚊𝚝𝚎 {account_type.capitalize()}** >      │
╭─────────────────────────╯
**𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** a username.
╰─────────────────────────╯""")
    
    await query.message.delete()
    prompt_message = await query.message.reply_text(text, reply_markup=create_cancel_menu(), parse_mode='Markdown')
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return GET_USERNAME_CREATE

async def get_username_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    username = update.message.text
    
    if not re.match("^[a-zA-Z0-9_-]+$", username):
        error_message = await update.message.reply_text("Invalid username. Use only letters, numbers, `_`, `-`. Try again.", reply_markup=create_cancel_menu())
        context.user_data['prompt_message_id'] = error_message.message_id
        return GET_USERNAME_CREATE
    
    context.user_data['username'] = username
    
    summary = f"**𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎**: `{username}`"
    text_prompt = "**𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** the duration in days (e.g., 30)."
    next_state = GET_DURATION_CREATE
    
    if context.user_data['account_type'] == 'ssh':
        text_prompt = "**𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** a password for the SSH account."
        next_state = GET_PASSWORD_CREATE
        
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙴𝚗𝚝𝚎𝚛 𝙳𝚎𝚝𝚊𝚒𝚕𝚜** >         │
╭─────────────────────────╯
{summary}
│
│ {text_prompt}
╰─────────────────────────╯""")
    prompt_message = await update.message.reply_text(text, parse_mode='Markdown', reply_markup=create_cancel_menu())
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return next_state

async def get_password_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    context.user_data['password'] = update.message.text
    ud = context.user_data
    
    summary = f"**𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎**: `{ud['username']}`\n**𝙿𝚊𝚜𝚜𝚠𝚘𝚛𝚍**: `{'*' * len(ud['password'])}`"
    
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙴𝚗𝚝𝚎𝚛 𝙳𝚎𝚝𝚊𝚒𝚕𝚜** >         │
╭─────────────────────────╯
{summary}
│
│ **𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** the duration
│ **𝚒𝚗 𝚍𝚊𝚢𝚜** (e.g., 30).
╰─────────────────────────╯""")
    prompt_message = await update.message.reply_text(text, parse_mode='Markdown', reply_markup=create_cancel_menu())
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return GET_DURATION_CREATE

async def get_duration_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    duration = update.message.text
    
    if not duration.isdigit() or int(duration) <= 0:
        error_message = await update.message.reply_text("Invalid duration. Please enter a positive number. Try again.", reply_markup=create_cancel_menu())
        context.user_data['prompt_message_id'] = error_message.message_id
        return GET_DURATION_CREATE
    
    context.user_data['duration'] = duration
    ud = context.user_data

    summary = f"**𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎**: `{ud['username']}`\n"
    if 'password' in ud:
        summary += f"**𝙿𝚊𝚜𝚜𝚠𝚘𝚛𝚍**: `{'*' * len(ud['password'])}`\n"
    summary += f"**𝙳𝚞𝚛𝚊𝚝𝚒𝚘𝚗**: `{ud['duration']}` days"
    
    if context.user_data['account_type'] == 'ssh':
        text_prompt = "**𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** the IP limit (e.g., 1. Use 0 for unlimited)."
        next_state = GET_IP_LIMIT_CREATE
    else:
        text_prompt = "**𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** the data quota in GB (e.g., 10. Use 0 for unlimited)."
        next_state = GET_QUOTA_CREATE

    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙴𝚗𝚝𝚎𝚛 𝙳𝚎𝚝𝚊𝚒𝚕𝚜** >         │
╭─────────────────────────╯
{summary}
│
│ {text_prompt}
╰─────────────────────────╯""")
    prompt_message = await update.message.reply_text(text, parse_mode='Markdown', reply_markup=create_cancel_menu())
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return next_state

async def get_quota_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    quota = update.message.text
    
    if not quota.isdigit() or int(quota) < 0:
        error_message = await update.message.reply_text("Invalid quota. Please enter a number (0 or more). Try again.", reply_markup=create_cancel_menu())
        context.user_data['prompt_message_id'] = error_message.message_id
        return GET_QUOTA_CREATE
    
    context.user_data['quota'] = quota
    ud = context.user_data
    
    summary = f"**𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎**: `{ud['username']}`\n**𝙳𝚞𝚛𝚊𝚝𝚒𝚘𝚗**: `{ud['duration']}` days\n**𝚀𝚞𝚘𝚝𝚊**: `{ud['quota']}` GB"

    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙴𝚗𝚝𝚎𝚛 𝙳𝚎𝚝𝚊𝚒𝚕𝚜** >         │
╭─────────────────────────╯
{summary}
│
│ **𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** the IP limit
│ **(𝚎.𝚐.,** 1. Use 0 for unlimited).
╰─────────────────────────╯""")
    prompt_message = await update.message.reply_text(text, parse_mode='Markdown', reply_markup=create_cancel_menu())
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return GET_IP_LIMIT_CREATE

async def get_ip_limit_and_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    ip_limit = update.message.text
    
    if not ip_limit.isdigit() or int(ip_limit) < 0:
        error_message = await update.message.reply_text("Invalid IP limit. Please enter a number (0 or more). Try again.", reply_markup=create_cancel_menu())
        context.user_data['prompt_message_id'] = error_message.message_id
        return GET_IP_LIMIT_CREATE
    
    context.user_data['ip_limit'] = ip_limit
    
    processing_message = await update.message.reply_text("𝙲𝚛𝚎𝚊𝚝𝚒𝚗𝚐 𝚊𝚌𝚌𝚘𝚞𝚗𝚝, 𝚙𝚕𝚎𝚊𝚜𝚎 𝚠𝚊𝚒𝚝...")
    
    ud = context.user_data
    account_type = ud['account_type']
    command = ['/usr/bin/apicreate', account_type, ud['username']]
    if account_type == 'ssh':
        command.extend([ud['password'], ud['duration'], ud['ip_limit']])
    else:
        command.extend([ud['duration'], ud['quota'], ud['ip_limit']])
    
    data, error = run_script(command)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)
    
    if error or (data and data.get('status') != 'success'):
        message_text = f"❌ **𝙵𝚊𝚒𝚕𝚎𝚍 𝚝𝚘 𝚌𝚛𝚎𝚊𝚝𝚎 𝚊𝚌𝚌𝚘𝚞𝚗𝚝.**\n**𝚁𝚎𝚊𝚜𝚘𝚗:** {error or data.get('message', 'Unknown error')}"
        await update.message.reply_text(message_text + BOT_FOOTER, parse_mode='Markdown', reply_markup=create_back_button_menu("back_to_main"))
    else:
        if account_type == 'ssh':
            message_text = format_ssh_output(data)
        else:
            message_text = format_v2ray_output(data, account_type)
        await update.message.reply_text(message_text + BOT_FOOTER, parse_mode='Markdown', reply_markup=create_back_button_menu("back_to_main"))
    
    context.user_data.clear()
    return ConversationHandler.END

# --- User Management Menu & Functions ---
async def manage_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = style_text("""╭─────────────────────────╮
│ </> **𝚄𝚜𝚎𝚛 𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝** >       │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** a user management
**𝚘𝚙𝚝𝚒𝚘𝚗** from below.
╰─────────────────────────╯""")
    keyboard = [
        [InlineKeyboardButton("📋 List Users", callback_data="list_user_start")],
        [InlineKeyboardButton("➖ Delete User", callback_data="delete_user_start")],
        [InlineKeyboardButton("🔄 Renew User", callback_data="renew_user_start")],
        [InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def list_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = style_text("""╭─────────────────────────╮
│ </> **𝙻𝚒𝚜𝚝 𝚄𝚜𝚎𝚛𝚜** >            │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** a service to list
**𝚞𝚜𝚎𝚛𝚜** from.
╰─────────────────────────╯""")
    await update.callback_query.edit_message_text(text, reply_markup=create_protocol_menu("list_proto", "manage_users_menu"), parse_mode='Markdown')

async def list_user_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    protocol = query.data.split('_')[2]
    await query.edit_message_text(f"𝙵𝚎𝚝𝚌𝚑𝚒𝚗𝚐 𝚞𝚜𝚎𝚛 𝚕𝚒𝚜𝚝 𝚏𝚘𝚛 {protocol.capitalize()}...")
    users, error = await get_users_for_protocol(protocol)
    
    title = f"**{protocol.capitalize()} Users**"
    if error:
        body = f"│ **𝙴𝚛𝚛𝚘𝚛:** {error}"
    elif not users:
        body = f"│ **𝙽𝚘 𝚞𝚜𝚎𝚛𝚜 𝚏𝚘𝚞𝚗𝚍** for {protocol.capitalize()}."
    else:
        user_list = "\n".join([f"│ • `{user}`" for user in users])
        if len(user_list) > 3800: body = "│ 𝚄𝚜𝚎𝚛 𝚕𝚒𝚜𝚝 𝚒𝚜 𝚝𝚘𝚘 𝚕𝚘𝚗𝚐 𝚝𝚘 𝚍𝚒𝚜𝚙𝚕𝚊𝚢."
        else: body = user_list

    message_text = style_text(f"""╭─────────────────────────╮
│ </> {title}
╭─────────────────────────╯
{body}
╰─────────────────────────╯""")

    await query.edit_message_text(
        message_text + BOT_FOOTER, 
        parse_mode='Markdown', 
        reply_markup=create_back_button_menu("manage_users_menu")
    )

# --- Delete User Conversation ---
async def delete_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = style_text("""╭─────────────────────────╮
│ </> **𝙳𝚎𝚕𝚎𝚝𝚎 𝚄𝚜𝚎𝚛** >           │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** a service to delete
**𝚊 𝚞𝚜𝚎𝚛** from.
╰─────────────────────────╯""")
    await update.callback_query.edit_message_text(text, reply_markup=create_protocol_menu("delete_proto", "manage_users_menu"), parse_mode='Markdown')
    return SELECT_PROTOCOL_DELETE

async def delete_user_select_protocol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    protocol = query.data.split('_')[2]
    context.user_data['protocol'] = protocol
    await query.edit_message_text(f"𝙵𝚎𝚝𝚌𝚑𝚒𝚗𝚐 𝚞𝚜𝚎𝚛𝚜 𝚏𝚘𝚛 {protocol.capitalize()}...")
    users, error = await get_users_for_protocol(protocol)
    if error or not users:
        await query.edit_message_text(f"**𝙴𝚛𝚛𝚘𝚛:** {error or 'No users found.'}" + BOT_FOOTER, reply_markup=create_back_button_menu("manage_users_menu"))
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(user, callback_data=f"delete_user_{user}")] for user in users]
    keyboard.append([InlineKeyboardButton("« Back", callback_data="manage_users_menu")])
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙳𝚎𝚕𝚎𝚝𝚎 {protocol.capitalize()} 𝚄𝚜𝚎𝚛** >   │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** a user to delete.
╰─────────────────────────╯""")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return SELECT_USER_DELETE

async def delete_user_confirm_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    username = query.data.split('_')[2]
    context.user_data['username'] = username
    keyboard = [
        [InlineKeyboardButton("❗️ Yes, Delete", callback_data="confirm_delete_yes")],
        [InlineKeyboardButton("« No, Back", callback_data="manage_users_menu")]
    ]
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙲𝚘𝚗𝚏𝚒𝚛𝚖 𝙳𝚎𝚕𝚎𝚝𝚒𝚘𝚗** >      │
╭─────────────────────────╯
**𝙰𝚛𝚎 𝚢𝚘𝚞 𝚜𝚞𝚛𝚎** you want to
**𝚍𝚎𝚕𝚎𝚝𝚎** `{username}`?
╰─────────────────────────╯""")
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_DELETE

async def delete_user_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    protocol, username = context.user_data['protocol'], context.user_data['username']
    await query.edit_message_text(f"𝙳𝚎𝚕𝚎𝚝𝚒𝚗𝚐 `{username}`...", parse_mode='Markdown')
    data, error = run_script(['/usr/bin/apidelete', protocol, username])
    if error or (data and data.get('status') != 'success'):
        body = f"│ ❌ **𝙵𝚊𝚒𝚕𝚎𝚍 𝚝𝚘 𝚍𝚎𝚕𝚎𝚝𝚎 𝚞𝚜𝚎𝚛.**\n│ **𝚁𝚎𝚊𝚜𝚘𝚗:** {error or data.get('message', 'Unknown error')}"
    else:
        body = f"│ ✅ **𝚄𝚜𝚎𝚛** `{username}` **𝚑𝚊𝚜 𝚋𝚎𝚎𝚗**\n│ **𝚜𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕𝚢 𝚍𝚎𝚕𝚎𝚝𝚎𝚍.**"
        
    message_text = style_text(f"""╭─────────────────────────╮
│ </> **𝙳𝚎𝚕𝚎𝚝𝚒𝚘𝚗 𝚂𝚝𝚊𝚝𝚞𝚜** >       │
╭─────────────────────────╯
{body}
╰─────────────────────────╯""")
    await query.edit_message_text(message_text + BOT_FOOTER, parse_mode='Markdown', reply_markup=create_back_button_menu("manage_users_menu"))
    context.user_data.clear()
    return ConversationHandler.END

# --- Renew User Conversation ---
async def renew_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = style_text("""╭─────────────────────────╮
│ </> **𝚁𝚎𝚗𝚎𝚠 𝚄𝚜𝚎𝚛** >            │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** a service to renew
**𝚊 𝚞𝚜𝚎𝚛** from.
╰─────────────────────────╯""")
    await update.callback_query.edit_message_text(text, reply_markup=create_protocol_menu("renew_proto", "manage_users_menu"), parse_mode='Markdown')
    return SELECT_PROTOCOL_RENEW

async def renew_user_select_protocol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    protocol = query.data.split('_')[2]
    context.user_data['protocol'] = protocol
    await query.edit_message_text(f"𝙵𝚎𝚝𝚌𝚑𝚒𝚗𝚐 𝚞𝚜𝚎𝚛𝚜 𝚏𝚘𝚛 {protocol.capitalize()}...")
    users, error = await get_users_for_protocol(protocol)
    if error or not users:
        await query.edit_message_text(f"**𝙴𝚛𝚛𝚘𝚛:** {error or 'No users found.'}" + BOT_FOOTER, reply_markup=create_back_button_menu("manage_users_menu"))
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(user, callback_data=f"renew_user_{user}")] for user in users]
    keyboard.append([InlineKeyboardButton("« Back", callback_data="manage_users_menu")])
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝚁𝚎𝚗𝚎𝚠 {protocol.capitalize()} 𝚄𝚜𝚎𝚛** >    │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** a user to renew.
╰─────────────────────────╯""")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return SELECT_USER_RENEW

async def renew_user_get_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    username = query.data.split('_')[2]
    context.user_data['username'] = username
    
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝚁𝚎𝚗𝚎𝚠 𝚄𝚜𝚎𝚛** >            │
╭─────────────────────────╯
**𝚄𝚜𝚎𝚛:** `{username}`
│
│ **𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** the new duration
│ **𝚒𝚗 𝚍𝚊𝚢𝚜** (e.g., 30).
╰─────────────────────────╯""")

    await query.message.delete()
    prompt_message = await query.message.reply_text(text, parse_mode='Markdown', reply_markup=create_cancel_menu())
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return GET_NEW_DURATION_RENEW

async def renew_user_get_ip_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    duration = update.message.text
    
    if not duration.isdigit() or int(duration) <= 0:
        error_message = await update.message.reply_text("Invalid duration. Please enter a positive number.", reply_markup=create_cancel_menu())
        context.user_data['prompt_message_id'] = error_message.message_id
        return GET_NEW_DURATION_RENEW
    
    context.user_data['duration'] = duration
    ud = context.user_data
    
    summary = f"**𝚄𝚜𝚎𝚛**: `{ud['username']}`\n**𝙽𝚎𝚠 𝙳𝚞𝚛𝚊𝚝𝚒𝚘𝚗**: `{ud['duration']}` days"
    
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝚁𝚎𝚗𝚎𝚠 𝚄𝚜𝚎𝚛** >            │
╭─────────────────────────╯
{summary}
│
│ **𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛** the new IP limit
│ **(𝚎.𝚐.,** 2. Use 0 for unlimited).
╰─────────────────────────╯""")
    prompt_message = await update.message.reply_text(text, parse_mode='Markdown', reply_markup=create_cancel_menu())
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return GET_NEW_IP_LIMIT_RENEW

async def renew_user_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    ip_limit = update.message.text
    
    if not ip_limit.isdigit() or int(ip_limit) < 0:
        error_message = await update.message.reply_text("Invalid IP limit. Please enter a number (0 or more).", reply_markup=create_cancel_menu())
        context.user_data['prompt_message_id'] = error_message.message_id
        return GET_NEW_IP_LIMIT_RENEW
    
    ud = context.user_data
    processing_message = await update.message.reply_text(f"𝚁𝚎𝚗𝚎𝚠𝚒𝚗𝚐 `{ud['username']}`...")

    data, error = run_script(['/usr/bin/apirenew', ud['protocol'], ud['username'], ud['duration'], ip_limit])
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)

    if error or (data and data.get('status') != 'success'):
        body = f"│ ❌ **𝙵𝚊𝚒𝚕𝚎𝚍 𝚝𝚘 𝚛𝚎𝚗𝚎𝚠 𝚞𝚜𝚎𝚛.**\n│ **𝚁𝚎𝚊𝚜𝚘𝚗:** {error or data.get('message', 'Unknown error')}"
    else:
        d = data.get('data', {})
        body = f"""│ ✅ **𝚄𝚜𝚎𝚛** `{d.get('username')}` **𝚛𝚎𝚗𝚎𝚠𝚎𝚍!**
│
│ **𝙽𝚎𝚠 𝙴𝚡𝚙𝚒𝚛𝚢:** `{d.get('exp')}`
│ **𝙽𝚎𝚠 𝙸𝙿 𝙻𝚒𝚖𝚒𝚝:** `{d.get('limitip')}`"""

    message_text = style_text(f"""╭─────────────────────────╮
│ </> **𝚁𝚎𝚗𝚎𝚠𝚊𝚕 𝚂𝚝𝚊𝚝𝚞𝚜** >        │
╭─────────────────────────╯
{body}
╰─────────────────────────╯""")
    await update.message.reply_text(message_text + BOT_FOOTER, parse_mode='Markdown', reply_markup=create_back_button_menu("manage_users_menu"))
    
    context.user_data.clear()
    return ConversationHandler.END

# --- Server Management ---
async def server_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = style_text("""╭─────────────────────────╮
│ </> **𝚂𝚎𝚛𝚟𝚎𝚛 𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝** >     │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** a server management
**𝚘𝚙𝚝𝚒𝚘𝚗** below.
╰─────────────────────────╯""")
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="server_stats")],
        [InlineKeyboardButton("🚀 Speedtest", callback_data="server_speedtest")],
        [InlineKeyboardButton("🔄 Reboot", callback_data="server_reboot_prompt")],
        [InlineKeyboardButton("« Back", callback_data="back_to_main")],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def server_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("𝙵𝚎𝚝𝚌𝚑𝚒𝚗𝚐 𝚜𝚎𝚛𝚟𝚎𝚛 𝚜𝚝𝚊𝚝𝚜...")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    body = f"""│ • **𝙲𝙿𝚄** : {cpu}%
│ • **𝚁𝙰𝙼** : {ram.percent}% ({ram.used/10**9:.2f} GB)
│ • **𝙳𝚒𝚜𝚔**: {disk.percent}% ({disk.used/10**9:.2f} GB)"""

    stats = style_text(f"""╭─────────────────────────╮
│ </> **𝚂𝚎𝚛𝚟𝚎𝚛 𝚂𝚝𝚊𝚝𝚜** >          │
╭─────────────────────────╯
{body}
╰─────────────────────────╯""")
    await query.edit_message_text(stats + BOT_FOOTER, parse_mode='Markdown', reply_markup=create_back_button_menu("server_menu"))

async def server_speedtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("𝚁𝚞𝚗𝚗𝚒𝚗𝚐 𝚜𝚙𝚎𝚎𝚍𝚝𝚎𝚜𝚝... 𝚃𝚑𝚒𝚜 𝚖𝚊𝚢 𝚝𝚊𝚔𝚎 𝚊 𝚖𝚒𝚗𝚞𝚝𝚎." + BOT_FOOTER, parse_mode='Markdown')
    try:
        result = subprocess.run(['speedtest-cli', '--json'], capture_output=True, text=True, check=True, timeout=120)
        data = json.loads(result.stdout)
        body = f"""│ • **𝙿𝚒𝚗𝚐**    : {data['ping']:.2f} ms
│ • **𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍**: {data['download']/10**6:.2f} Mbps
│ • **𝚄𝚙𝚕𝚘𝚊𝚍**  : {data['upload']/10**6:.2f} Mbps"""
        speed = style_text(f"""╭─────────────────────────╮
│ </> **𝚂𝚙𝚎𝚎𝚍𝚝𝚎𝚜𝚝 𝚁𝚎𝚜𝚞𝚕𝚝𝚜** >     │
╭─────────────────────────╯
{body}
╰─────────────────────────╯""")
        await query.edit_message_text(speed + BOT_FOOTER, parse_mode='Markdown', reply_markup=create_back_button_menu("server_menu"))
    except Exception as e:
        await query.edit_message_text(f"**𝚂𝚙𝚎𝚎𝚍𝚝𝚎𝚜𝚝 𝚏𝚊𝚒𝚕𝚎𝚍:** {e}" + BOT_FOOTER, reply_markup=create_back_button_menu("server_menu"))

async def server_reboot_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = style_text("""╭─────────────────────────╮
│ </> **𝙲𝚘𝚗𝚏𝚒𝚛𝚖 𝚁𝚎𝚋𝚘𝚘𝚝** >        │
╭─────────────────────────╯
│ ⚠️ **𝙰𝚁𝙴 𝚈𝙾𝚄 𝚂𝚄𝚁𝙴?** This will
│ **𝚍𝚒𝚜𝚌𝚘𝚗𝚗𝚎𝚌𝚝** the bot briefly.
╰─────────────────────────╯""")
    keyboard = [[InlineKeyboardButton("❗️ 𝚈𝙴𝚂, 𝚁𝙴𝙱𝙾𝙾𝚃 𝙽𝙾𝚆 ❗️", callback_data="server_reboot_confirm")], [InlineKeyboardButton("« Cancel", callback_data="server_menu")]]
    await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def server_reboot_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("**𝚁𝚎𝚋𝚘𝚘𝚝 𝚌𝚘𝚖𝚖𝚊𝚗𝚍 𝚒𝚜𝚜𝚞𝚎𝚍.** 𝙱𝚘𝚝 𝚠𝚒𝚕𝚕 𝚋𝚎 𝚘𝚏𝚏𝚕𝚒𝚗𝚎 𝚋𝚛𝚒𝚎𝚏𝚕𝚢." + BOT_FOOTER)
    subprocess.run(['sudo', 'reboot'])

# --- Admin Management ---
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = style_text("""╭─────────────────────────╮
│ </> **𝙰𝚍𝚖𝚒𝚗 𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝** >      │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** an admin management
**𝚘𝚙𝚝𝚒𝚘𝚗** from below.
╰─────────────────────────╯""")
    keyboard = [
        [InlineKeyboardButton("➕ Add Admin", callback_data="admin_add_start")],
        [InlineKeyboardButton("➖ Remove Admin", callback_data="admin_remove_start")],
        [InlineKeyboardButton("📋 List Admins", callback_data="admin_list")],
        [InlineKeyboardButton("« Back", callback_data="back_to_main")],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = "\n".join([f"│ • `{admin_id}`" for admin_id in load_admins()])
    text = style_text(f"""╭─────────────────────────╮
│ </> **𝙲𝚞𝚛𝚛𝚎𝚗𝚝 𝙰𝚍𝚖𝚒𝚗𝚜** >        │
╭─────────────────────────╯
{admins}
╰─────────────────────────╯""")
    await update.callback_query.edit_message_text(text + BOT_FOOTER, parse_mode='Markdown', reply_markup=create_back_button_menu("admin_menu"))

async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = style_text("""╭─────────────────────────╮
│ </> **𝙰𝚍𝚍 𝙰𝚍𝚖𝚒𝚗** >             │
╭─────────────────────────╯
**𝙿𝚕𝚎𝚊𝚜𝚎 𝚜𝚎𝚗𝚍** the Telegram User
**𝙸𝙳** of the new admin.
╰─────────────────────────╯""")
    await update.callback_query.message.delete()
    prompt_message = await update.callback_query.message.reply_text(text, parse_mode='Markdown', reply_markup=create_cancel_menu())
    context.user_data['prompt_message_id'] = prompt_message.message_id
    return GET_ADMIN_ID_ADD

async def get_admin_id_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_previous_messages(context, update)
    try:
        new_admin_id = int(update.message.text)
        admins = load_admins()
        if new_admin_id in admins:
            await update.message.reply_text(f"**𝚄𝚜𝚎𝚛** `{new_admin_id}` **𝚒𝚜 𝚊𝚕𝚛𝚎𝚊𝚍𝚢 𝚊𝚗 𝚊𝚍𝚖𝚒𝚗.**", parse_mode='Markdown', reply_markup=create_back_button_menu("admin_menu"))
        else:
            admins.add(new_admin_id)
            save_admins(admins)
            await update.message.reply_text(f"✅ **𝚂𝚞𝚌𝚌𝚎𝚜𝚜! 𝚄𝚜𝚎𝚛** `{new_admin_id}` **𝚒𝚜 𝚗𝚘𝚠 𝚊𝚗 𝚊𝚍𝚖𝚒𝚗.**", parse_mode='Markdown', reply_markup=create_back_button_menu("admin_menu"))
    except ValueError:
        error_message = await update.message.reply_text("**𝙸𝚗𝚟𝚊𝚕𝚒𝚍 𝙸𝙳.** 𝙿𝚕𝚎𝚊𝚜𝚎 𝚜𝚎𝚗𝚍 𝚊 𝚗𝚞𝚖𝚎𝚛𝚒𝚌 𝚄𝚜𝚎𝚛 𝙸𝙳.", reply_markup=create_cancel_menu())
        context.user_data['prompt_message_id'] = error_message.message_id
        return GET_ADMIN_ID_ADD
    
    context.user_data.clear()
    return ConversationHandler.END

async def admin_remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admins = [admin for admin in load_admins() if admin != OWNER_ID]
    if not admins:
        await update.callback_query.edit_message_text("**𝙽𝚘 𝚘𝚝𝚑𝚎𝚛 𝚊𝚍𝚖𝚒𝚗𝚜 𝚝𝚘 𝚛𝚎𝚖𝚘𝚟𝚎.**"+ BOT_FOOTER, reply_markup=create_back_button_menu("admin_menu"))
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(f"ID: {admin_id}", callback_data=f"admin_remove_{admin_id}")] for admin_id in admins]
    keyboard.append([InlineKeyboardButton("« Cancel", callback_data="admin_menu")])
    text = style_text("""╭─────────────────────────╮
│ </> **𝚁𝚎𝚖𝚘𝚟𝚎 𝙰𝚍𝚖𝚒𝚗** >          │
╭─────────────────────────╯
**𝚂𝚎𝚕𝚎𝚌𝚝** an admin to remove:
╰─────────────────────────╯""")
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return SELECT_ADMIN_TO_REMOVE

async def select_admin_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    admin_id = int(query.data.split('_')[2])
    admins = load_admins()
    admins.remove(admin_id)
    save_admins(admins)
    await query.edit_message_text(f"✅ **𝚂𝚞𝚌𝚌𝚎𝚜𝚜! 𝙰𝚍𝚖𝚒𝚗** `{admin_id}` **𝚑𝚊𝚜 𝚋𝚎𝚎𝚗 𝚛𝚎𝚖𝚘𝚟𝚎𝚍.**", parse_mode='Markdown', reply_markup=create_back_button_menu("admin_menu"))
    return ConversationHandler.END

# --- General Button Router ---
async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    route = query.data
    
    if route == "back_to_main": 
        await send_main_menu(update, context)
    elif route == "help": 
        await help_command(update, context)
    elif route == "manage_users_menu": 
        await manage_users_menu(update, context)
    elif route == "server_menu": 
        await server_menu(update, context)
    elif route == "admin_menu": 
        await admin_menu(update, context)
    elif route == "list_user_start": 
        await list_user_start(update, context)
    elif route.startswith("list_proto_"): 
        await list_user_execute(update, context)
    elif route == "server_stats": 
        await server_stats(update, context)
    elif route == "server_speedtest": 
        await server_speedtest(update, context)
    elif route == "server_reboot_prompt": 
        await server_reboot_prompt(update, context)
    elif route == "server_reboot_confirm": 
        await server_reboot_confirm(update, context)
    elif route == "admin_list": 
        await admin_list(update, context)

# --- Main Function ---
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    universal_fallbacks = [
        CommandHandler('cancel', cancel_conversation),
        CallbackQueryHandler(cancel_conversation, pattern='^cancel_operation$'),
    ]

    conv_handlers = {
        "create": ConversationHandler(
            entry_points=[CallbackQueryHandler(create_account_start, pattern='^create_account_start$')],
            states={
                SELECT_TYPE_CREATE: [CallbackQueryHandler(select_type_create, pattern=r'^create_proto_')],
                GET_USERNAME_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username_create)],
                GET_PASSWORD_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password_create)],
                GET_DURATION_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration_create)],
                GET_QUOTA_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quota_create)],
                GET_IP_LIMIT_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ip_limit_and_create)],
            },
            fallbacks=universal_fallbacks + [CallbackQueryHandler(send_main_menu, pattern='^back_to_main$')]
        ),
        "delete": ConversationHandler(
            entry_points=[CallbackQueryHandler(delete_user_start, pattern='^delete_user_start$')],
            states={
                SELECT_PROTOCOL_DELETE: [CallbackQueryHandler(delete_user_select_protocol, pattern=r'^delete_proto_')],
                SELECT_USER_DELETE: [CallbackQueryHandler(delete_user_confirm_prompt, pattern=r'^delete_user_')],
                CONFIRM_DELETE: [CallbackQueryHandler(delete_user_execute, pattern='^confirm_delete_yes$')],
            },
            fallbacks=universal_fallbacks + [CallbackQueryHandler(manage_users_menu, pattern='^manage_users_menu$')]
        ),
        "renew": ConversationHandler(
            entry_points=[CallbackQueryHandler(renew_user_start, pattern='^renew_user_start$')],
            states={
                SELECT_PROTOCOL_RENEW: [CallbackQueryHandler(renew_user_select_protocol, pattern=r'^renew_proto_')],
                SELECT_USER_RENEW: [CallbackQueryHandler(renew_user_get_duration, pattern=r'^renew_user_')],
                GET_NEW_DURATION_RENEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, renew_user_get_ip_limit)],
                GET_NEW_IP_LIMIT_RENEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, renew_user_execute)],
            },
            fallbacks=universal_fallbacks + [CallbackQueryHandler(manage_users_menu, pattern='^manage_users_menu$')]
        ),
        "admin_add": ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_add_start, pattern='^admin_add_start$')],
            states={GET_ADMIN_ID_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_admin_id_add)]},
            fallbacks=universal_fallbacks
        ),
        "admin_remove": ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_remove_start, pattern='^admin_remove_start$')],
            states={SELECT_ADMIN_TO_REMOVE: [CallbackQueryHandler(select_admin_to_remove, pattern=r'^admin_remove_\d+$')]},
            fallbacks=universal_fallbacks + [CallbackQueryHandler(admin_menu, pattern='^admin_menu$')]
        ),
    }

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart_bot))  # Added restart command
    for handler in conv_handlers.values():
        application.add_handler(handler)
    application.add_handler(CallbackQueryHandler(button_router))

    application.run_polling()

if __name__ == "__main__":
    main()
