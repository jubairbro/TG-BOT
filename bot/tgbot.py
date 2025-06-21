# Save this code in your python file: /root/bot/tgbot.py
# The Final, Polished, and Fully-Featured Version

import telebot
import psutil
import subprocess
import os
import time
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from functools import wraps

# ============== কনফিগারেশন ==============
BOT_TOKEN = "8002173814:AAHMo01WzE37PVSM1YYnocYnxiV0V8jK7Wk"
ADMIN_IDS = [5487394544,6801360422,1956820398] # প্রধান অ্যাডমিনদের আইডি
GROUP_ID = -1002758027133 # ওয়েলকাম মেসেজ এবং /mentionall এর জন্য গ্রুপের আইডি
DB_FILE = "/root/bot/commands.db" # ভিডিও কমান্ড সংরক্ষণের জন্য ডেটাবেস
# =========================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ============== ডেটাবেস সেটআপ ==============
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_commands (
            command TEXT PRIMARY KEY,
            file_id TEXT,
            caption TEXT,
            file_type TEXT
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
def admin_required(func):
    @wraps(func)
    def wrapper(message_or_call):
        user_id = message_or_call.from_user.id
        # কলব্যাক কোয়েরি বা মেসেজ থেকে চ্যাট আইডি বের করা
        chat_id = message_or_call.message.chat.id if isinstance(message_or_call, telebot.types.CallbackQuery) else message_or_call.chat.id

        # প্রধান অ্যাডমিনদের জন্য সরাসরি অনুমতি
        if user_id in ADMIN_IDS:
            return func(message_or_call)

        # গ্রুপে অ্যাডমিন স্ট্যাটাস চেক করা
        if chat_id < 0: # গ্রুপ বা সুপারগ্রুপ
            try:
                chat_member = bot.get_chat_member(chat_id, user_id)
                if chat_member.status in ['administrator', 'creator']:
                    return func(message_or_call)
            except Exception as e:
                print(f"অ্যাডমিন চেক করতে সমস্যা: {e}")

        # যদি কোনো শর্তই পূরণ না হয়
        if isinstance(message_or_call, telebot.types.CallbackQuery):
            bot.answer_callback_query(message_or_call.id, "❌ শুধুমাত্র অ্যাডমিনরা এটি ব্যবহার করতে পারবে।", show_alert=True)
        else:
            bot.reply_to(message_or_call, "❌ এই কমান্ডটি শুধুমাত্র অ্যাডমিনদের জন্য।")
        return
    return wrapper

def get_ip_address():
    try:
        return subprocess.check_output(['curl', '-s', 'ipinfo.io/ip'], text=True).strip()
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

# ============== কীবোর্ড মার্কআপ ==============
def generate_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton('📊 রিপোর্ট'), KeyboardButton('🔋 সার্ভার লোড '),
        KeyboardButton('📋 সার্ভিস স্ট্যাটাস'), KeyboardButton('📜 নিয়মাবলী'),
        KeyboardButton('🔌 পোর্ট ইনফো '), KeyboardButton('❓ সাহায্য')
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
    bot.reply_to(message, f"<b>স্বাগতম, {message.from_user.full_name}!</b>\nআমি আপনাদের সার্ভার ম্যানেজমেন্ট বট। 🤖", reply_markup=generate_main_keyboard())

@bot.message_handler(commands=['help'])
def send_help(message):
    is_admin = False
    try:
        is_admin = message.from_user.id in ADMIN_IDS or (message.chat.id < 0 and bot.get_chat_member(message.chat.id, message.from_user.id).status in ['administrator', 'creator'])
    except:
        is_admin = message.from_user.id in ADMIN_IDS

    if is_admin:
        admin_help_text = """<pre>┌─ 🛠️ অ্যাডমিন হ্যাল্প মেন্যু
│
├─╼ 💾 কনটেন্ট ম্যানেজমেন্ট
│  ├─ /save [নাম] (রিপ্লাই দিয়ে)
│  │  └─ ভিডিও/ফাইল সেভ করে।
│  ├─ /listcmd
│  │  └─ সকল সেভ করা কমান্ডের তালিকা।
│  └─ /delcmd [নাম]
│     └─ সেভ করা কমান্ড মুছে ফেলে।
│
└─╼ ⚙️ সার্ভার ও গ্রুপ টুলস
   ├─ /reboot  : সার্ভার রিবুট করে।
   ├─ /mentionall [বার্তা]
   │  └─ গ্রুপে সবাইকে ঘোষণা দেয়।
   └─ /run [cmd] : টার্মিনাল কমান্ড চালায়।

┌─ 🤖 সাধারণ ইউজার হ্যাল্প মেন্যু ──╼
│
├─╼ ⚙️ সার্ভার তথ্য
│  ├─ /report : সার্ভারের বিস্তারিত রিপোর্ট।
│  ├─ /health : সার্ভারের স্বাস্থ্য পরীক্ষা।
│  ├─ /status : চলমান সার্ভিসগুলোর অবস্থা।
│  ├─ /ports  : পোর্ট তালিকা।
│  └─ /rules  : নিয়মাবলী।
│
└─╼ </pre>"""
        bot.reply_to(message, admin_help_text)
    else:
        user_help_text = """<pre>┌─ 🤖 সাধারণ হ্যাল্প মেন্যু
│
├─╼ ⚙️ সার্ভার তথ্য
│  ├─ /report : সার্ভারের বিস্তারিত রিপোর্ট।
│  ├─ /health : সার্ভারের স্বাস্থ্য পরীক্ষা।
│  ├─ /status : চলমান সার্ভিসগুলোর অবস্থা।
│  ├─ /ports  : পোর্ট তালিকা।
│  └─ /rules  : নিয়মাবলী।
│
└─╼ </pre>"""
        bot.reply_to(message, user_help_text)

@bot.message_handler(regexp="^(❓ সাহায্য)$")
def send_help_from_keyboard(message):
    send_help(message)

@bot.message_handler(regexp="^(📊 রিপোর্ট|/report)$")
def send_report(message):
    try:
        cpu_usage, cpu_cores = psutil.cpu_percent(interval=1), psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        total_ram_gb, used_ram_gb, ram_percent = mem.total / (1024**3), mem.used / (1024**3), mem.percent
        uptime_seconds = time.time() - psutil.boot_time()
        d, rem = divmod(uptime_seconds, 86400); h, rem = divmod(rem, 3600); m, _ = divmod(rem, 60)
        uptime = f"{int(d)} দিন,{int(h)} ঘণ্টা,{int(m)} মিনিট"
        ip_address, domain = get_ip_address(), get_domain()

        report_text = f"""📊 <b>বর্তমান সার্ভার স্ট্যাটাস রিপোর্ট</b> 📊

<pre>╭─CPU Information
│  Cores: {cpu_cores}
│  Usage: {cpu_usage:.1f}%
╰───────────</pre>
<pre>╭─RAM Information
│  Total: {total_ram_gb:.2f} GB
│  Used: {used_ram_gb:.2f} GB ({ram_percent:.1f}%)
╰───────────</pre>
<pre>╭─Network & System
│  System Uptime: {uptime}
│  IP Address: {ip_address}
│  Domain: {domain}
╰───────────</pre>

✅ সার্ভার স্ট্যাবল এবং সক্রিয় আছে।"""
        bot.reply_to(message, report_text)
    except Exception as e:
        bot.reply_to(message, f"❌ রিপোর্ট তৈরি করতে সমস্যা হয়েছে: <code>{e}</code>")

@bot.message_handler(regexp="^(🔋 সার্ভার লোড|/health)$")
def server_health(message):
    cpu, ram, disk = psutil.cpu_percent(interval=1), psutil.virtual_memory().percent, psutil.disk_usage('/').percent
    def create_bar(p, l=12): return f"[{'█' * int(l * p / 100)}{'░' * (l - int(l * p / 100))}] {p:.1f}%"
    health_report = f"""🩺 <b>সার্ভার হেলথ্ চেক</b>

<pre>╭─ আমার নাঁড়ি-ভুঁড়ির ব্যবহার
│  CPU : {create_bar(cpu)}
│  RAM : {create_bar(ram)}
│  Disk: {create_bar(disk)}
╰───────────</pre>"""
    bot.reply_to(message, health_report)

@bot.message_handler(regexp="^(📋 সার্ভিস স্ট্যাটাস|/status)$")
def show_service_status(message):
    services = ["ssh", "dropbear", "nginx", "xray", "openvpn", "stunnel4", "trojan-go"]
    status_report = "<b>📋 চলমান সার্ভিসসমূহের অবস্থা</b>\n\n<pre>╭─ সার্ভিস স্ট্যাটাস"
    for service in services:
        try:
            is_active = subprocess.run(['systemctl', 'is-active', '--quiet', service]).returncode == 0
            status_icon = "✅" if is_active else "❌"
            status_report += f"\n│  {status_icon} {service:<12}"
        except FileNotFoundError:
             status_report += f"\n│  ❓ {service:<12}"
    status_report += "\n╰───────────</pre>"
    bot.reply_to(message, status_report)

@bot.message_handler(regexp="^(📜 নিয়মাবলী|/rules)$")
def send_rules(message):
    rules_text = """📜 <b>সার্ভার ব্যবহারের নিয়মাবলী</b>

<pre>╭─ General Rules
│  1. টরেন্ট বা অতিরিক্ত ডাউনলোড নিষিদ্ধ,
│কম কম ডাউনলোড দেওয়ার চেষ্টা করবেন সবাই।
│
│  2. এক একাউন্ট একাধিক ডিভাইসে,
│ব্যবহার করলে একাউন্ট ব্যান করা হবে।
│
│  3. কোনো ধরনের অবৈধ ১৮+ সাইট এবং
│ডার্ক ওয়েব ভিজিট নিষিদ্ধ এগুলার জন্য,
│VPS ব্যান হতে পারে ।
╰───────────</pre>"""
    bot.reply_to(message, rules_text)

@bot.message_handler(regexp="^(🔌 পোর্টস|/ports)$")
def send_ports_info(message):
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
    bot.reply_to(message, ports_text)

# ============== গ্রুপ ম্যানেজমেন্ট হ্যান্ডলার ==============
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    if message.chat.id == GROUP_ID:
        for user in message.new_chat_members:
            bot.send_message(GROUP_ID, f"<b>🖤 স্বাগতম,</b><i> {user.full_name}!</i>🥰\nআমাদের প্রিমিয়াম সার্ভিস এ জয়েন করার জন্য আপনাকে ধন্যবাদ 💚 \nআপনার জন্য উপযোগী কমান্ড \nদেখতে <code>/help</code> কামন্ড দিন 🧯\n সার্ভার রুলস দেখতে <code>/rules</code> কমান্ড দিন 🧊।")

# ============== অ্যাডমিন কমান্ড হ্যান্ডলার ==============
@bot.message_handler(commands=['save', 'listcmd', 'delcmd', 'reboot', 'run', 'mentionall'])
@admin_required
def handle_admin_commands(message):
    command, *args_list = message.text.split(maxsplit=1)
    args = args_list[0] if args_list else ""

    # কনটেন্ট ম্যানেজমেন্ট
    if command == '/save':
        if not message.reply_to_message:
            return bot.reply_to(message, "❌ একটি ফাইলে রিপ্লাই করে কমান্ডটি ব্যবহার করুন।")
        command_name = args.split()[0] if args else ""
        if not command_name: return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/save [নাম]</code>")

        reply = message.reply_to_message
        file_id, file_type = (reply.video.file_id, 'video') if reply.video else \
                             (reply.document.file_id, 'document') if reply.document else \
                             (reply.photo[-1].file_id, 'photo') if reply.photo else (None, None)

        if not file_id: return bot.reply_to(message, "❌ শুধুমাত্র ভিডিও, ডকুমেন্ট বা ফটো সেভ করা যাবে।")

        save_command(command_name, file_id, reply.caption or "", file_type)
        bot.reply_to(message, f"✅ `/{command_name}` কমান্ডটি সফলভাবে সেভ করা হয়েছে।")

    elif command == '/listcmd':
        commands = get_all_commands()
        if not commands: return bot.reply_to(message, "📂 কোনো কমান্ড সেভ করা হয়নি।")
        cmd_list = "<b>📂 সংরক্ষিত কমান্ড:</b>\n\n" + "\n".join([f"• `/{cmd[0]}`" for cmd in commands])
        bot.reply_to(message, cmd_list)

    elif command == '/delcmd':
        if not args: return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/delcmd [নাম]</code>")
        command_name = args.split()[0]
        if get_command(command_name):
            delete_command_from_db(command_name)
            bot.reply_to(message, f"✅ `/{command_name}` কমান্ডটি মুছে ফেলা হয়েছে।")
        else: bot.reply_to(message, "❌ আপাতত এই নামে কোনো কমান্ড নেই।")

    # সার্ভার ও গ্রুপ টুলস
    elif command == '/reboot':
        bot.reply_to(message, "🤔 আপনি কি সত্যিই সার্ভারটি রিবুট করতে চান?", reply_markup=confirm_reboot_keyboard())

    elif command == '/mentionall':
        if message.chat.id != GROUP_ID: return bot.reply_to(message, "এই কমান্ডটি শুধুমাত্র নির্ধারিত গ্রুপে কাজ করবে।")
        if not args: return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/mentionall [বার্তা]</code>")
        bot.send_message(GROUP_ID, f"📣 <b><u>সকলের জন্য বিজ্ঞপ্তি!</u></b> 📣\n\n{args}")

    elif command == '/run':
        if not args: return bot.reply_to(message, "<b>ব্যবহার:</b> <code>/run [কমান্ড]</code>")
        msg = bot.reply_to(message, f"⏳ কমান্ড চলছে...\n<pre>{args}</pre>")
        try:
            res = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=120)
            output = (res.stdout + res.stderr).strip() or "✅ সফল, কোনো আউটপুট নেই।"
            if len(output) > 4096:
                with open("output.txt", "w") as f: f.write(output)
                with open("output.txt", "rb") as f: bot.send_document(message.chat.id, f, caption="কমান্ড আউটপুট")
                os.remove("output.txt"); bot.delete_message(msg.chat.id, msg.message_id)
            else: bot.edit_message_text(f"<b>আপনার কমান্ড এর ফলাফল 🤟:</b>\n<pre>{output}</pre>", msg.chat.id, msg.message_id)
        except Exception as e: bot.edit_message_text(f"❌ কমান্ড ব্যর্থ: {e}", msg.chat.id, msg.message_id)

# ============== কলব্যাক হ্যান্ডলার (রিবুট কনফার্মেশনের জন্য) ==============
@bot.callback_query_handler(func=lambda call: True)
@admin_required
def handle_callback_query(call):
    action = call.data
    msg = call.message

    if action == "confirm_reboot":
        try:
            bot.edit_message_text("✅ রিবুট কমান্ড পাঠানো হয়েছে। \n⚠️ সার্ভার কিছুক্ষণের জন্য অফলাইন হয়ে যাবে।", msg.chat.id, msg.message_id, reply_markup=None)
            subprocess.run(['sudo', 'reboot'], check=True)
        except Exception as e:
            bot.edit_message_text(f"❌ রিবুট ব্যর্থ হয়েছে: <code>{e}</code>", msg.chat.id, msg.message_id)

    elif action == "cancel_action":
        bot.edit_message_text("👍 কাজটি বাতিল করা হয়েছে।", msg.chat.id, msg.message_id, reply_markup=None)

    bot.answer_callback_query(call.id)


# ============== কাস্টম কমান্ড হ্যান্ডলার (ডাইনামিক) ==============
@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
def handle_custom_commands(message):
    command_name = message.text[1:].lower().split()[0]
    command_data = get_command(command_name)

    if command_data:
        file_id, caption, file_type = command_data
        try:
            sender_map = {'video': bot.send_video, 'document': bot.send_document, 'photo': bot.send_photo}
            sender_map[file_type](message.chat.id, file_id, caption=caption)
        except Exception as e:
            bot.reply_to(message, f"❌ ফাইল পাঠাতে সমস্যা: <code>{e}</code>")

# ============== স্টার্টআপ ==============
if __name__ == '__main__':
    print("বট চালু হচ্ছে...")
    init_db()
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, "✅ বট সফলভাবে চালু হয়েছে।", disable_notification=True)
        except Exception as e:
            print(f"অ্যাডমিন {admin_id} কে বার্তা পাঠাতে ব্যর্থ: {e}")
    print("Bot is running...")
    bot.infinity_polling(timeout=90, long_polling_timeout=60, allowed_updates=['message', 'callback_query', 'new_chat_members'])
