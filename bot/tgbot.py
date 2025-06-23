# Save this code in your python file: /root/bot/tgbot.py
# The Final, Polished, and Fully-Featured Version

import telebot
import psutil
import subprocess
import os
import time
import sqlite3
import json # Added for JSON parsing in speedtest
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telebot import apihelper # Import for error handling
from functools import wraps

# ============== কনফিগারেশন ==============
BOT_TOKEN = "your_bot_token" # আপনার বটের টোকেন এখানে দিন
BOT_OWNER_IDS = [00001726262,18363637373,52820202373773] # আপনার বা বটের মালিকদের আইডি এখানে দিন (একাধিক হলে কমা দিয়ে)
GROUP_ID = -1002758027133 # ওয়েলকাম মেসেজ, /mentionall এবং বট ব্যবহারের অনুমতির জন্য গ্রুপের আইডি
DB_FILE = "/root/bot/commands.db" # ভিডিও কমান্ড সংরক্ষণের জন্য ডেটাবেস
# =========================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# Store bot's start time for uptime calculation
BOT_START_TIME = time.time()

# ============== ডেটাবেস সেটআপ ==============
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_commands (
            command TEXT PRIMARY KEY,
            file_id TEXT,
            caption TEXT,
            file_type TEXT -- 'video', 'document', 'photo', 'text'
        )
    ''')
    conn.commit()
    conn.close()

def save_command(command, file_id, caption, file_type):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO saved_commands (command, file_id, caption, file_type) VALUES (?, ?, ?, ?)", (command.lower(), file_id, caption, file_type))
    conn.commit()
    conn.close()

def get_command(command):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption, file_type FROM saved_commands WHERE command = ?", (command.lower(),))
    data = cursor.fetchone()
    conn.close()
    return data

def delete_command_from_db(command):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_commands WHERE command = ?", (command.lower(),))
    conn.commit()
    conn.close()

def get_all_commands():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT command FROM saved_commands ORDER BY command ASC")
    commands = cursor.fetchall()
    conn.close()
    return commands

# ============== হেল্পার এবং পারমিশন ফাংশন ==============

def _add_credit_line(text):
    """Adds the bot's credit line to the end of a message."""
    return f"{text}\n\n<b>🤖 Bot by : @JubairFF</b>"

def _get_user_and_chat_id(message_or_call):
    """Helper to extract user_id and chat_id reliably from Message or CallbackQuery."""
    if isinstance(message_or_call, telebot.types.CallbackQuery):
        return message_or_call.from_user.id, message_or_call.message.chat.id
    return message_or_call.from_user.id, message_or_call.chat.id

def _send_permission_denied_message(message_or_call, text):
    """Helper to send permission denied message appropriately."""
    if isinstance(message_or_call, telebot.types.CallbackQuery):
        bot.answer_callback_query(message_or_call.id, text, show_alert=True)
    else:
        bot.reply_to(message_or_call, text)

def _edit_message_safe(chat_id, message_id, text, reply_markup=None, disable_web_page_preview=False):
    """
    Safely edits a message, catching 'message is not modified' errors.
    """
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)
    except apihelper.ApiError as e:
        if e.error_code == 400 and "message is not modified" in str(e):
            # This error means the message content/markup is already what we tried to set.
            # It's not a critical error, so we can just log/pass.
            print(f"DEBUG: Message {message_id} in chat {chat_id} not modified (already same content). Ignoring.")
        else:
            raise # Re-raise other API errors

def check_group_membership_and_admin(user_id):
    """
    Checks if a user is a member of the designated GROUP_ID
    and if they are an admin in that group.
    Returns (is_group_member, is_group_admin)
    """
    is_group_member = False
    is_group_admin = False
    
    try:
        chat_member = bot.get_chat_member(GROUP_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            is_group_member = True
        if chat_member.status in ['administrator', 'creator']:
            is_group_admin = True
    except telebot.apihelper.ApiError as e:
        if "user not found" in str(e).lower() or "user is not a member" in str(e).lower() or "not a member" in str(e).lower():
            is_group_member = False
            is_group_admin = False
        else:
            print(f"Error checking group membership/admin status for user {user_id} in group {GROUP_ID}: {e}")
            # For safety, assume not member/admin if unexpected API error occurs
    
    return is_group_member, is_group_admin


def premium_user_required(func):
    """Decorator to ensure only premium users (or bot owners) can use a command."""
    @wraps(func)
    def wrapper(message_or_call):
        user_id, _ = _get_user_and_chat_id(message_or_call)

        # 1. Check if it's a Bot Owner (highest privilege)
        if user_id in BOT_OWNER_IDS:
            return func(message_or_call)

        # 2. Allow /start and /help for everyone (initial access)
        command_text = message_or_call.text.split()[0].lower() if isinstance(message_or_call, telebot.types.Message) and message_or_call.text else ''
        callback_data = message_or_call.data if isinstance(message_or_call, telebot.types.CallbackQuery) else ''
        
        if command_text in ['/start', '/help'] or callback_data == 'show_help':
            return func(message_or_call)

        # 3. Check group membership for other users
        is_group_member, _ = check_group_membership_and_admin(user_id)

        if not is_group_member:
            _send_permission_denied_message(message_or_call, "❌ আপনি আমাদের প্রিমিয়াম সার্ভার এর ইউজার নন, আপনার জন্য এই বট ব্যাবহারের পারমিশন নেই।")
            return
        
        # If passed all checks, proceed
        return func(message_or_call)
    return wrapper

def admin_required(func):
    """Decorator to ensure only bot owners or group admins can use a command."""
    @wraps(func)
    def wrapper(message_or_call):
        user_id, _ = _get_user_and_chat_id(message_or_call)

        # 1. Check if it's a Bot Owner (highest admin privilege)
        if user_id in BOT_OWNER_IDS:
            return func(message_or_call)

        # 2. Check if user is an admin in the designated GROUP_ID
        _, is_group_admin = check_group_membership_and_admin(user_id)

        if is_group_admin:
            return func(message_or_call)

        # If not bot owner and not group admin
        _send_permission_denied_message(message_or_call, "❌ শুধুমাত্র অ্যাডমিনরা এটি ব্যবহার করতে পারবে।")
        return
    return wrapper

def owner_required(func):
    """Decorator to ensure only bot owners can use a command."""
    @wraps(func)
    def wrapper(message_or_call):
        user_id, _ = _get_user_and_chat_id(message_or_call)
        if user_id in BOT_OWNER_IDS:
            return func(message_or_call)
        _send_permission_denied_message(message_or_call, "❌ এই কমান্ডটি শুধুমাত্র বটের মালিকের জন্য।")
        return
    return wrapper

def get_ip_address():
    try:
        return subprocess.check_output(['curl', '-s', 'ipinfo.io/ip'], text=True, timeout=5).strip()
    except Exception:
        return "N/A"

def get_domain():
    domain_file_path = "/etc/xray/domain"
    if os.path.exists(domain_file_path):
        try:
            with open(domain_file_path, 'r') as f:
                return f.read().strip()
        except Exception:
            return "N/A"
    return "Not Set"

def check_service_status(service_name):
    """Checks service status using systemctl and returns 'GOOD', 'BAD', or 'UNKNOWN'."""
    try:
        actual_service_name = service_name
        # Adjusting Xray service names to match the user's systemctl output (e.g., vmess@config)
        if service_name.startswith("xray_"): 
            actual_service_name = service_name.split("_")[1] + "@config"

        # Special handling for 'ws' if it refers to nginx as the websocket handler
        if service_name == "ws": 
            actual_service_name = "nginx" # Assuming Nginx handles websockets

        result = subprocess.run(['systemctl', 'is-active', '--quiet', actual_service_name], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return "GOOD"
        else:
            return "BAD"
    except FileNotFoundError:
        return "UNKNOWN (systemctl command not found)"
    except subprocess.TimeoutExpired:
        return "TIMEOUT (Service status check timed out)"
    except Exception as e:
        return f"ERROR ({e})"

def get_formatted_service_status():
    """Generates a formatted string of service statuses."""
    services = [
        ("OpenSSH", "ssh"),
        ("Dropbear", "dropbear"),
        ("SSH Websocket", "ws"), 
        ("OpenVPN", "openvpn"),
        ("Nginx", "nginx"),
        ("Haproxy", "haproxy"),
        ("Xray Vmess", "xray_vmess"),
        ("Xray Vless", "xray_vless"),
        ("Xray Trojan", "xray_trojan"),
        ("Xray SSocks", "xray_shadowsocks"),
    ]

    status_lines = []
    for display_name, service_key in services:
        status = check_service_status(service_key)
        status_lines.append(f"│ {display_name:<19} : {status}")

    return "<b>📋 চলমান সার্ভিসসমূহের অবস্থা</b>\n\n<pre>╭─ সার্ভিস স্ট্যাটাস\n" + "\n".join(status_lines) + "\n╰───────────</pre>"

def get_bot_uptime():
    """Calculates bot's uptime."""
    uptime_seconds = time.time() - BOT_START_TIME
    d, rem = divmod(uptime_seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    return f"{int(d)}d {int(h)}h {int(m)}m {int(s)}s"

# ============== কীবোর্ড মার্কআপ (ইনলাইন স্টাইল) ==============
def generate_main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('📊 রিপোর্ট', callback_data='show_report'),
        InlineKeyboardButton('🔋 সার্ভার লোড', callback_data='show_health'),
        InlineKeyboardButton('📋 সার্ভিস স্ট্যাটাস', callback_data='show_status'),
        InlineKeyboardButton('📜 নিয়মাবলী', callback_data='show_rules'),
        InlineKeyboardButton('🔌 পোর্ট ইনফো', callback_data='show_ports'),
        InlineKeyboardButton('⚡ স্পিড টেস্ট', callback_data='run_speedtest'), 
        InlineKeyboardButton('❓ সাহায্য', callback_data='show_help')
    )
    return markup

def confirm_reboot_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ হ্যাঁ, রিবুট করুন", callback_data="confirm_reboot"),
        InlineKeyboardButton("❌ না, বাতিল", callback_data="cancel_action")
    )
    return markup

# ============== সাধারণ কমান্ড ও বাটন হ্যান্ডলার ==============

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in BOT_OWNER_IDS:
        welcome_message = "<b>👋 হ্যালো বস!</b> 👑\nসার্ভার ম্যানেজমেন্ট বট আপনার সেবায় প্রস্তুত।\nকী করতে পারি আপনার জন্য?"
    else:
        welcome_message = f"<b>স্বাগতম, {message.from_user.full_name}!</b>\nআমি আপনাদের সার্ভার ম্যানেজমেন্ট বট। 🤖"
    
    bot.reply_to(message, _add_credit_line(welcome_message), reply_markup=generate_main_keyboard())

@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = message.from_user.id
    is_owner = user_id in BOT_OWNER_IDS
    _, is_group_admin = check_group_membership_and_admin(user_id)

    if is_owner or is_group_admin:
        help_text = """<pre>┌─ 🛠️ অ্যাডমিন হ্যাল্প মেন্যু
│
├─╼ 💾 কনটেন্ট ম্যানেজমেন্ট
│  ├─ /save [নাম] (রিপ্লাই দিয়ে)
│  │  └─ ভিডিও/ফাইল/টেক্সট সেভ করে।
│  ├─ /listcmd
│  │  └─ সকল সেভ করা কমান্ডের তালিকা।
│  └─ /delcmd [নাম]
│     └─ সেভ করা কমান্ড মুছে ফেলে।
│
└─╼ ⚙️ সার্ভার ও গ্রুপ টুলস
   ├─ /reboot  : সার্ভার রিবুট করে।
   ├─ /mentionall [বার্তা]
   │  └─ গ্রুপে সবাইকে ঘোষণা দেয়।
   ├─ /run [cmd] : টার্মিনাল কমান্ড চালায়। (বট মালিকের জন্য)
   └─ /speedtest : সার্ভারের ইন্টারনেট স্পিড টেস্ট করে।

┌─ 🤖 সাধারণ ইউজার হ্যাল্প মেন্যু ──╼
│
├─╼ ⚙️ সার্ভার তথ্য
│  ├─ /report : সার্ভারের বিস্তারিত রিপোর্ট।
│  ├─ /health : সার্ভারের স্বাস্থ্য পরীক্ষা।
│  ├─ /status : চলমান সার্ভিসগুলোর অবস্থা।
│  ├─ /ports  : পোর্ট তালিকা।
│  ├─ /rules  : নিয়মাবলী।
│  └─ /speedtest : সার্ভারের ইন্টারনেট স্পিড টেস্ট করে।
│
└─╼ </pre>"""
        bot.reply_to(message, _add_credit_line(help_text))
    else:
        user_help_text = """<pre>┌─ 🤖 সাধারণ হ্যাল্প মেন্যু
│
├─╼ ⚙️ সার্ভার তথ্য
│  ├─ /report : সার্ভারের বিস্তারিত রিপোর্ট।
│  ├─ /health : সার্ভারের স্বাস্থ্য পরীক্ষা।
│  ├─ /status : চলমান সার্ভিসগুলোর অবস্থা।
│  ├─ /ports  : পোর্ট তালিকা।
│  ├─ /rules  : নিয়মাবলী।
│  └─ /speedtest : সার্ভারের ইন্টারনেট স্পিড টেস্ট করে।
│
└─╼ </pre>"""
        bot.reply_to(message, _add_credit_line(user_help_text))

# Handlers for general direct commands (non-admin actions)
@bot.message_handler(commands=['report', 'health', 'status', 'ports', 'rules'])
@premium_user_required
def handle_general_direct_commands(message):
    command_name = message.text.split()[0]
    sent_message = bot.send_message(message.chat.id, "তথ্য লোড হচ্ছে...", reply_markup=None) 

    if command_name == '/report':
        send_report_action(sent_message.chat.id, sent_message.message_id)
    elif command_name == '/health':
        server_health_action(sent_message.chat.id, sent_message.message_id)
    elif command_name == '/status':
        show_service_status_action(sent_message.chat.id, sent_message.message_id)
    elif command_name == '/rules':
        send_rules_action(sent_message.chat.id, sent_message.message_id)
    elif command_name == '/ports':
        send_ports_info_action(sent_message.chat.id, sent_message.message_id)

# Handler specifically for /speedtest (admin only)
@bot.message_handler(commands=['speedtest'])
@premium_user_required
@admin_required
def handle_speedtest_command(message):
    # This will send a new "loading" message and then edit it
    run_speedtest_action(message.chat.id, None) 


# Handlers for inline keyboard callbacks
@bot.callback_query_handler(func=lambda call: call.data in ['show_report', 'show_health', 'show_status', 'show_rules', 'show_ports', 'show_help'])
@premium_user_required
def handle_general_menu_callbacks(call):
    msg_chat_id = call.message.chat.id
    msg_message_id = call.message.message_id
    
    # Show typing action immediately for responsiveness
    bot.send_chat_action(msg_chat_id, 'typing')

    try:
        if call.data == 'show_report':
            send_report_action(msg_chat_id, msg_message_id)
        elif call.data == 'show_health':
            server_health_action(msg_chat_id, msg_message_id)
        elif call.data == 'show_status':
            show_service_status_action(msg_chat_id, msg_message_id)
        elif call.data == 'show_rules':
            send_rules_action(msg_chat_id, msg_message_id)
        elif call.data == 'show_ports':
            send_ports_info_action(msg_chat_id, msg_message_id)
        elif call.data == 'show_help':
            user_id = call.from_user.id
            is_owner = user_id in BOT_OWNER_IDS
            _, is_group_admin = check_group_membership_and_admin(user_id)

            if is_owner or is_group_admin:
                help_text = """<pre>┌─ 🛠️ অ্যাডমিন হ্যাল্প মেন্যু
│
├─╼ 💾 কনটেন্ট ম্যানেজমেন্ট
│  ├─ /save [নাম] (রিপ্লাই দিয়ে)
│  │  └─ ভিডিও/ফাইল/টেক্সট সেভ করে।
│  ├─ /listcmd
│  │  └─ সকল সেভ করা কমান্ডের তালিকা।
│  └─ /delcmd [নাম]
│     └─ সেভ করা কমান্ড মুছে ফেলে।
│
└─╼ ⚙️ সার্ভার ও গ্রুপ টুলস
   ├─ /reboot  : সার্ভার রিবুট করে।
   ├─ /mentionall [বার্তা]
   │  └─ গ্রুপে সবাইকে ঘোষণা দেয়।
   ├─ /run [cmd] : টার্মিনাল কমান্ড চালায়। (বট মালিকের জন্য)
   └─ /speedtest : সার্ভারের ইন্টারনেট স্পিড টেস্ট করে।

┌─ 🤖 সাধারণ ইউজার হ্যাল্প মেন্যু ──╼
│
├─╼ ⚙️ সার্ভার তথ্য
│  ├─ /report : সার্ভারের বিস্তারিত রিপোর্ট।
│  ├─ /health : সার্ভারের স্বাস্থ্য পরীক্ষা।
│  ├─ /status : চলমান সার্ভিসগুলোর অবস্থা।
│  ├─ /ports  : পোর্ট তালিকা।
│  ├─ /rules  : নিয়মাবলী।
│  └─ /speedtest : সার্ভারের ইন্টারনেট স্পিড টেস্ট করে।
│
└─╼ </pre>"""
            else:
                help_text = """<pre>┌─ 🤖 সাধারণ হ্যাল্প মেন্যু
│
├─╼ ⚙️ সার্ভার তথ্য
│  ├─ /report : সার্ভারের বিস্তারিত রিপোর্ট।
│  ├─ /health : সার্ভারের স্বাস্থ্য পরীক্ষা।
│  ├─ /status : চলমান সার্ভিসগুলোর অবস্থা।
│  ├─ /ports  : পোর্ট তালিকা।
│  ├─ /rules  : নিয়মাবলী।
│  └─ /speedtest : সার্ভারের ইন্টারনেট স্পিড টেস্ট করে।
│
└─╼ </pre>"""
            _edit_message_safe(msg_chat_id, msg_message_id, _add_credit_line(help_text), reply_markup=generate_main_keyboard())

    except Exception as e:
        _edit_message_safe(msg_chat_id, msg_message_id, f"❌ কার্যক্রমে সমস্যা হয়েছে: <code>{e}</code>", reply_markup=generate_main_keyboard())
    bot.answer_callback_query(call.id)

# Handler specifically for speedtest callback (admin only)
@bot.callback_query_handler(func=lambda call: call.data == 'run_speedtest')
@premium_user_required
@admin_required
def handle_speedtest_callback(call):
    # This will edit the existing message
    run_speedtest_action(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

# Helper functions for sending info (now take chat_id and message_id for editing)
def send_report_action(chat_id, message_id):
    bot.send_chat_action(chat_id, 'typing') # Show typing action
    try:
        cpu_usage, cpu_cores = psutil.cpu_percent(interval=1), psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        total_ram_gb, used_ram_gb, ram_percent = mem.total / (1024**3), mem.used / (1024**3), mem.percent
        uptime_seconds = time.time() - psutil.boot_time()
        d, rem = divmod(uptime_seconds, 86400); h, rem = divmod(rem, 3600); m, _ = divmod(rem, 60)
        system_uptime = f"{int(d)} দিন,{int(h)} ঘণ্টা,{int(m)} মিনিট"
        ip_address, domain = get_ip_address(), get_domain()

        disk_usage = psutil.disk_usage('/')
        total_disk_gb = disk_usage.total / (1024**3)
        used_disk_gb = disk_usage.used / (1024**3)
        free_disk_gb = disk_usage.free / (1024**3)
        disk_percent = disk_usage.percent

        swap_mem = psutil.swap_memory()
        total_swap_gb = swap_mem.total / (1024**3)
        used_swap_gb = swap_mem.used / (1024**3)
        free_swap_gb = swap_mem.free / (1024**3)
        swap_percent = swap_mem.percent

        # Disk I/O counters
        disk_io = psutil.disk_io_counters()
        total_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0
        total_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0
        
        # Bot Uptime
        bot_uptime = get_bot_uptime()

        report_text = f"""📊 <b>বর্তমান সার্ভার স্ট্যাটাস রিপোর্ট</b> 📊

<pre>╭─BOT STATISTICS :
│  Bot Uptime : {bot_uptime}
╰───────────</pre>
<pre>╭─CPU Information
│  Cores: {cpu_cores}
│  Usage: {cpu_usage:.1f}%
╰───────────</pre>
<pre>╭─RAM ( MEMORY ) :
│  Total: {total_ram_gb:.2f} GB
│  Used: {used_ram_gb:.2f} GB ({ram_percent:.1f}%)
╰───────────</pre>
<pre>╭─SWAP MEMORY :
│  Total: {total_swap_gb:.2f} GB
│  Used: {used_swap_gb:.2f} GB ({swap_percent:.1f}%)
╰───────────</pre>
<pre>╭─DISK :
│  Total: {total_disk_gb:.2f} GB
│  Used: {used_disk_gb:.2f} GB ({disk_percent:.1f}%)
│  Total Disk Read : {total_read_mb:.2f} MB
│  Total Disk Write : {total_write_mb:.2f} MB
╰───────────</pre>
<pre>╭─Network & System
│  System Uptime:{system_uptime}
│  IP Address:{ip_address}
│  Domain:{domain}
╰───────────</pre>

✅ সার্ভার স্ট্যাবল এবং সক্রিয় আছে।"""
        _edit_message_safe(chat_id, message_id, _add_credit_line(report_text), reply_markup=generate_main_keyboard())
    except Exception as e:
        _edit_message_safe(chat_id, message_id, f"❌ রিপোর্ট তৈরি করতে সমস্যা হয়েছে: <code>{e}</code>", reply_markup=generate_main_keyboard())

def server_health_action(chat_id, message_id):
    bot.send_chat_action(chat_id, 'typing') # Show typing action
    try:
        cpu, ram = psutil.cpu_percent(interval=1), psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/')
        disk_percent = disk_usage.percent
        swap_mem = psutil.swap_memory()
        swap_percent = swap_mem.percent

        def create_bar(p, l=12): return f"[{'█' * int(l * p / 100)}{'░' * (l - int(l * p / 100))}] {p:.1f}%"

        health_report = f"""🩺 <b>সার্ভার এর স্বাস্থ্য চেকআপ 🫦</b>

<pre>╭─ আমার নাঁড়ি-ভুঁড়ির ব্যবহার
│  CPU : {create_bar(cpu)}
│  RAM : {create_bar(ram)}
│  Disk: {create_bar(disk_percent)}
│  Swap: {create_bar(swap_percent)}
╰───────────</pre>"""
        _edit_message_safe(chat_id, message_id, _add_credit_line(health_report), reply_markup=generate_main_keyboard())
    except Exception as e:
        _edit_message_safe(chat_id, message_id, f"❌ সার্ভার হেল্থ চেক করতে সমস্যা হয়েছে: <code>{e}</code>", reply_markup=generate_main_keyboard())


def show_service_status_action(chat_id, message_id):
    bot.send_chat_action(chat_id, 'typing') # Show typing action
    status_report = get_formatted_service_status()
    _edit_message_safe(chat_id, message_id, _add_credit_line(status_report), reply_markup=generate_main_keyboard())

def send_rules_action(chat_id, message_id):
    bot.send_chat_action(chat_id, 'typing') # Show typing action
    rules_text = """📜 <b>সার্ভার ব্যবহারের নিয়মাবলী</b>

<pre>╭─ General Rules
│  1. টরেন্ট বা অতিরিক্ত ডাউনলোড নিষিদ্ধ,
│     কম কম ডাউনলোড দেওয়ার চেষ্টা
│     করবেন সবাই।
│  2. এক একাউন্ট একাধিক ডিভাইসে,
│     ব্যবহার করলে একাউন্ট ব্যান করা হবে।
│
│  3. কোনো ধরনের অবৈধ ১৮+ সাইট এবং
│     ডার্ক ওয়েব ভিজিট নিষিদ্ধ এগুলার জন্য,
│     VPS ব্যান হতে পারে ।
╰───────────</pre>"""
    _edit_message_safe(chat_id, message_id, _add_credit_line(rules_text), reply_markup=generate_main_keyboard())

def send_ports_info_action(chat_id, message_id):
    bot.send_chat_action(chat_id, 'typing') # Show typing action
    ports_text = """🔌 <b>PORT INFORMATION</b>

<pre>╭─ Connection Ports
│ • SSH        : 22, 443, 80
│ • Dropbear   : 443, 109, 143
│ • Websocket  : 80, 443
│ • OpenVPN    : 443, 1194, 2200
╰───────────</pre>
<pre>╭─ Core Service Ports
│ • Nginx      : 80, 81, 443
│ • Haproxy    : 80, 443
│ • DNS        : 53, 443
╰───────────</pre>
<pre>╭─ XRAY Protocol Ports
│ • Vmess      : 80, 443
│ • Vless      : 80, 443
│ • Trojan     : 443
│ • Shadowsocks: 443
╰───────────</pre>"""
    _edit_message_safe(chat_id, message_id, _add_credit_line(ports_text), reply_markup=generate_main_keyboard())

def run_speedtest_action(chat_id, message_id_to_edit=None): 
    # Determine which message to edit or if a new one needs to be sent
    if message_id_to_edit:
        # Edit existing message (from callback)
        _edit_message_safe(chat_id, message_id_to_edit, "⏳ স্পিড টেস্ট চলছে... এতে কিছুক্ষণ সময় লাগতে পারে।", reply_markup=None)
        msg_id_for_final_edit = message_id_to_edit
    else:
        # Send a new temporary message (from direct command)
        temp_msg = bot.send_message(chat_id, "⏳ স্পিড টেস্ট চলছে... এতে কিছুক্ষণ সময় লাগতে পারে।", reply_markup=None)
        msg_id_for_final_edit = temp_msg.message_id

    bot.send_chat_action(chat_id, 'typing') # Show typing action

    try:
        # Changed to use --format=json and --share for Ookla speedtest CLI
        result = subprocess.run(['speedtest', '--format=json', '--share'], capture_output=True, text=True, timeout=300)
        output_json = result.stdout.strip()

        if result.returncode == 0 and output_json:
            data = json.loads(output_json)
            
            # Extracting data based on Ookla Speedtest CLI JSON format
            ip_address = data.get('interface', {}).get('externalIp', 'N/A')
            isp = data.get('isp', 'N/A')
            ping_ms = data.get('ping', {}).get('latency', 'N/A')
            isp_rating = data.get('ispRating', 'N/A') 
            sponsor = data.get('server', {}).get('sponsor', 'N/A')

            # Download/Upload in bytes, convert to Mbps
            download_bps = data.get('download', {}).get('bandwidth', 0)
            upload_bps = data.get('upload', {}).get('bandwidth', 0)
            download_mbps = f"{(download_bps * 8 / (10**6)):.2f} Mbps" if download_bps else 'N/A'
            upload_mbps = f"{(upload_bps * 8 / (10**6)):.2f} Mbps" if upload_bps else 'N/A'

            server_name = data.get('server', {}).get('name', 'N/A')
            country = data.get('server', {}).get('country', 'N/A')
            lat_lon = f"{data.get('server', {}).get('lat', 'N/A')}, {data.get('server', {}).get('lon', 'N/A')}"
            
            # Get share URL
            share_url = data.get('share', {}).get('url', 'N/A')

            speed_text = f"""⚡ <b>স্পিড টেস্ট রেজাল্ট</b> ⚡

🌐 <b><u>ইন্টারফেস তথ্য:</u></b>
  ‣  <b>IP:</b> <a href='https://ipinfo.io/{ip_address}'>{ip_address}</a>
  ‣  <b>ISP:</b> <i>{isp}</i>
  ‣  <b>ISP রেটিং:</b> <i>{isp_rating}</i>

📡 <b><u>সার্ভার তথ্য:</u></b>
  ‣  <b>সার্ভার:</b> <i>{server_name}, {country}</i>
  ‣  <b>স্পন্সর:</b> <i>{sponsor}</i>
  ‣  <b>ল্যাট/লং:</b> <i>{lat_lon}</i>

📊 <b><u>পারফরম্যান্স:</u></b>
  ‣  <b>পিং:</b> <code>{ping_ms:.0f} ms</code>
  ‣  <b>ডাউনলোড:</b> <code>{download_mbps}</code>
  ‣  <b>আপলোড:</b> <code>{upload_mbps}</code>

🔗 <b><u>শেয়ার লিংক:</u></b>
  ‣  <a href='{share_url}'>Speedtest.net Result</a>

✅ আপনার সার্ভারের ইন্টারনেট স্পিড টেস্ট সফলভাবে সম্পন্ন হয়েছে!"""
            _edit_message_safe(chat_id, msg_id_for_final_edit, _add_credit_line(speed_text), reply_markup=generate_main_keyboard(), disable_web_page_preview=False)
        else:
            error_output = result.stderr.strip() if result.stderr else "কোনো আউটপুট নেই।"
            _edit_message_safe(chat_id, msg_id_for_final_edit, f"❌ স্পিড টেস্ট ব্যর্থ হয়েছে। অনুগ্রহ করে পরে আবার চেষ্টা করুন।\nবিস্তারিত:\n<pre>{error_output}</pre>", reply_markup=generate_main_keyboard())
    except FileNotFoundError:
        _edit_message_safe(chat_id, msg_id_for_final_edit, "❌ `speedtest` কমান্ডটি খুঁজে পাওয়া যায়নি। সার্ভারে `Ookla Speedtest CLI` ইন্সটল করা আছে কিনা নিশ্চিত করুন। যদি না থাকে, তাদের অফিসিয়াল ওয়েবসাইট থেকে এটি ইন্সটল করতে পারেন।", reply_markup=generate_main_keyboard())
    except subprocess.TimeoutExpired:
        _edit_message_safe(chat_id, msg_id_for_final_edit, "❌ স্পিড টেস্ট সময়সীমা অতিক্রম করেছে।", reply_markup=generate_main_keyboard())
    except json.JSONDecodeError:
        _edit_message_safe(chat_id, msg_id_for_final_edit, f"❌ স্পিড টেস্ট থেকে অবৈধ আউটপুট পাওয়া গেছে। `speedtest` কমান্ডটি ঠিকভাবে কাজ করছে না।\nআউটপুট:\n<pre>{output_json}</pre>", reply_markup=generate_main_keyboard())
    except Exception as e:
        _edit_message_safe(chat_id, msg_id_for_final_edit, f"❌ স্পিড টেস্ট চলাকালীন অপ্রত্যাশিত ত্রুটি: <code>{e}</code>", reply_markup=generate_main_keyboard())


# ============== গ্রুপ ম্যানেজমেন্ট হ্যান্ডলার ==============
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    if message.chat.id == GROUP_ID:
        for user in message.new_chat_members:
            bot.send_message(GROUP_ID, _add_credit_line(f"<b>🖤 স্বাগতম,</b><i> {user.full_name}!</i>🥰\nআমাদের প্রিমিয়াম সার্ভিস এ জয়েন করার জন্য আপনাকে ধন্যবাদ 💚 \nআপনার জন্য উপযোগী কমান্ড \nদেখতে <code>/help</code> কামন্ড দিন 🧯\n সার্ভার রুলস দেখতে <code>/rules</code> কমান্ড দিন 🧊।"))

# ============== অ্যাডমিন কমান্ড হ্যান্ডলার ==============

@bot.message_handler(commands=['save'])
@premium_user_required 
@admin_required 
def handle_save_command(message):
    command_name_args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    command_name = command_name_args.split()[0] if command_name_args else ""

    if not message.reply_to_message:
        return bot.reply_to(message, "❌ একটি ফাইলে বা টেক্সটে রিপ্লাই করে কমান্ডটি ব্যবহার করুন।")
    if not command_name:
        return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/save [নাম]</code>")

    reply = message.reply_to_message
    file_id = None
    caption = reply.caption or ""
    file_type = None

    # Prioritize media types, then fall back to text
    if reply.video:
        file_id = reply.video.file_id
        file_type = 'video'
    elif reply.document:
        file_id = reply.document.file_id
        file_type = 'document'
    elif reply.photo:
        file_id = reply.photo[-1].file_id # Get the largest photo
        file_type = 'photo'
    elif reply.text: # Handle saving text content
        file_id = reply.text # The text itself is stored as file_id
        file_type = 'text'
        caption = "" # For text content, caption is usually not needed/relevant

    if not file_id:
        return bot.reply_to(message, "❌ শুধুমাত্র ভিডিও, ডকুমেন্ট, ফটো বা টেক্সট সেভ করা যাবে।")

    save_command(command_name, file_id, caption, file_type)
    bot.reply_to(message, f"✅ `/{command_name}` কমান্ডটি সফলভাবে সেভ করা হয়েছে।")

@bot.message_handler(commands=['listcmd'])
@premium_user_required
@admin_required
def handle_listcmd_command(message):
    commands = get_all_commands()
    if not commands:
        return bot.reply_to(message, "📂 কোনো কমান্ড সেভ করা হয়নি।")
    cmd_list = "<b>📂 সংরক্ষিত কমান্ড:</b>\n\n" + "\n".join([f"• `/{cmd[0]}`" for cmd in commands])
    bot.reply_to(message, cmd_list)

@bot.message_handler(commands=['delcmd'])
@premium_user_required
@admin_required
def handle_delcmd_command(message):
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not args:
        return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/delcmd [নাম]</code>")
    command_name = args.split()[0]
    if get_command(command_name):
        delete_command_from_db(command_name)
        bot.reply_to(message, f"✅ `/{command_name}` কমান্ডটি মুছে ফেলা হয়েছে।")
    else:
        bot.reply_to(message, "❌ আপাতত এই নামে কোনো কমান্ড নেই।")

@bot.message_handler(commands=['reboot'])
@premium_user_required
@admin_required
def handle_reboot_command(message):
    bot.reply_to(message, "🤔 আপনি কি সত্যিই সার্ভারটি রিবুট করতে চান?", reply_markup=confirm_reboot_keyboard())

@bot.message_handler(commands=['mentionall'])
@premium_user_required
@admin_required
def handle_mentionall_command(message):
    if message.chat.id != GROUP_ID:
        return bot.reply_to(message, "এই কমান্ডটি শুধুমাত্র নির্ধারিত গ্রুপে কাজ করবে।")
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not args:
        return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/mentionall [বার্তা]</code>")
    
    bot.send_message(GROUP_ID, f"📣 <b><u>সকলের জন্য বিজ্ঞপ্তি!</u></b> 📣\n\n{args}")

@bot.message_handler(commands=['run'])
@premium_user_required 
@owner_required 
def handle_run_command(message):
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not args:
        return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/run [কমান্ড]</code>")
    msg = bot.reply_to(message, f"⏳ কমান্ড চলছে...\n<pre>{args}</pre>")
    bot.send_chat_action(message.chat.id, 'typing') # Show typing action
    try:
        res = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=120)
        output = (res.stdout + res.stderr).strip()
        if not output:
            output = "✅ সফল, কোনো আউটপুট নেই।"
        
        if len(output) > 4096:
            with open("output.txt", "w", encoding='utf-8') as f: f.write(output)
            with open("output.txt", "rb") as f: bot.send_document(message.chat.id, f, caption="কমান্ড আউটপুট")
            os.remove("output.txt"); bot.delete_message(msg.chat.id, msg.message_id)
        else:
            _edit_message_safe(msg.chat.id, msg.message_id, f"<b>আপনার কমান্ড এর ফলাফল 🤟:</b>\n<pre>{output}</pre>")
    except Exception as e:
        _edit_message_safe(msg.chat.id, msg.message_id, f"❌ কমান্ড ব্যর্থ: <code>{e}</code>")


# ============== কলব্যাক হ্যান্ডলার (রিবুট কনফার্মেশনের জন্য) ==============
@bot.callback_query_handler(func=lambda call: call.data in ["confirm_reboot", "cancel_action"])
@premium_user_required
@admin_required
def handle_reboot_callback_query(call):
    action = call.data
    msg = call.message

    if action == "confirm_reboot":
        try:
            _edit_message_safe(msg.chat.id, msg.message_id, "✅ রিবুট কমান্ড পাঠানো হয়েছে। \n⚠️ সার্ভার কিছুক্ষণের জন্য অফলাইন হয়ে যাবে।", reply_markup=None)
            subprocess.run(['sudo', 'reboot'], check=True)
        except Exception as e:
            _edit_message_safe(msg.chat.id, msg.message_id, f"❌ রিবুট ব্যর্থ হয়েছে: <code>{e}</code>")

    elif action == "cancel_action":
        _edit_message_safe(msg.chat.id, msg.message_id, "👍 কাজটি বাতিল করা হয়েছে।", reply_markup=None)

    bot.answer_callback_query(call.id)


# ============== কাস্টম কমান্ড হ্যান্ডলার (ডাইনামিক) ==============
@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
@premium_user_required
def handle_custom_commands(message):
    command_name = message.text[1:].lower().split()[0]
    command_data = get_command(command_name)

    if command_data:
        file_id, caption, file_type = command_data
        try:
            if file_type == 'text':
                bot.send_message(message.chat.id, file_id) # file_id holds the text content
            else:
                sender_map = {'video': bot.send_video, 'document': bot.send_document, 'photo': bot.send_photo}
                bot.send_chat_action(message.chat.id, file_type) # Show "sending video/photo/document" status
                sender_map[file_type](message.chat.id, file_id, caption=caption)
        except Exception as e:
            bot.reply_to(message, f"❌ ফাইল পাঠাতে সমস্যা: <code>{e}</code>")
    # If it's not a saved custom command, and wasn't caught by other handlers,
    # it will simply be ignored.

# ============== স্টার্টআপ ==============
if __name__ == '__main__':
    print("বট চালু হচ্ছে...")
    init_db()
    for owner_id in BOT_OWNER_IDS:
        try:
            # Send silent startup message to owners
            bot.send_message(owner_id, "✅ বট সফলভাবে চালু হয়েছে।", disable_notification=True)
        except Exception as e:
            print(f"মালিক {owner_id} কে বার্তা পাঠাতে ব্যর্থ: {e}")
    print("Bot is running...")
    
    bot.infinity_polling(timeout=90, long_polling_timeout=60, allowed_updates=['message', 'callback_query', 'new_chat_members'])
