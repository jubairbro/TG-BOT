অবশ্যই! এইবার আমি আপনাকে একটি **সম্পূর্ণ, ক্লীন এবং চূড়ান্ত গাইড** দিচ্ছি। এখানে একটি নতুন VPS-এ শুরু থেকে শেষ পর্যন্ত সাদিয়া বটের সর্বশেষ এবং সেরা সংস্করণটি সেটআপ করার জন্য প্রয়োজনীয় সবকিছু ধাপে ধাপে বলা আছে।

এই গাইডটি অনুসরণ করলে আপনার আর অন্য কোনো কিছুর প্রয়োজন হবে না।

---

### **নতুন VPS-এ সাদিয়া বট: চূড়ান্ত সেটআপ গাইড (A-to-Z)**

আমরা মোট ৭টি ধাপে পুরো কাজটি সম্পন্ন করব।

---

### **ধাপ ১: VPS প্রস্তুত করা (প্রাথমিক সেটআপ)**

একটি নতুন উবুন্টু VPS-এ প্রথমে সিস্টেম আপডেট করতে হয় এবং পাইথনের জন্য প্রয়োজনীয় টুলস ইনস্টল করতে হয়।

1.  **সার্ভার আপডেট এবং আপগ্রেড করুন:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **প্রয়োজনীয় সফটওয়্যার ইনস্টল করুন (Python, Pip, venv):**
    ```bash
    sudo apt install python3-pip python3-venv -y
    ```

---

### **ধাপ ২: প্রকল্প ফোল্ডার এবং ভার্চুয়াল এনভায়রনমেন্ট**

এখন আমরা আমাদের বটের জন্য একটি আলাদা এবং পরিষ্কার পরিবেশ তৈরি করব।

1.  **বটের জন্য ফোল্ডার তৈরি করে তাতে প্রবেশ করুন:**
    ```bash
    mkdir ~/sadiya_bot && cd ~/sadiya_bot
    ```

2.  **ভার্চুয়াল এনভায়রনমেন্ট (venv) তৈরি করুন:**
    ```bash
    python3 -m venv venv
    ```

---

### **ধাপ ৩: প্রয়োজনীয় Pip প্যাকেজ ইনস্টল করা**

এখন আমরা ভার্চুয়াল এনভায়রনমেন্টের ভেতরে বটের জন্য প্রয়োজনীয় সকল লাইব্রেরি ইনস্টল করব।

1.  **ভার্চুয়াল এনভায়রনমেন্ট সক্রিয় করুন:**
    ```bash
    source venv/bin/activate
    ```
    (আপনি টার্মিনালে লাইনের শুরুতে `(venv)` দেখতে পাবেন)।

2.  **সকল প্যাকেজ ইনস্টল করুন (JobQueue সহ):**
    ```bash
    pip install "python-telegram-bot[job-queue]" google-generativeai python-dotenv
    ```
    এই একটি কমান্ডই আপনার প্রয়োজনীয় তিনটি লাইব্রেরি (`telegram` এর `JobQueue` সহ, `gemini`, `dotenv`) ইনস্টল করে দেবে।

3.  **ভার্চুয়াল এনভায়রনমেন্ট নিষ্ক্রিয় করুন:**
    ```bash
    deactivate
    ```

---

### **ধাপ ৪: `.env` ফাইল তৈরি করা (গোপন তথ্য সংরক্ষণ)**

এই ফাইলে আমরা আমাদের সকল গোপন তথ্য যেমন API কী এবং টোকেন রাখব। এটি কোডকে পরিষ্কার এবং সুরক্ষিত রাখে।

```bash
# nano এডিটর দিয়ে .env ফাইলটি তৈরি করুন
nano ~/sadiya_bot/.env
```
ফাইলটি খুললে, নিচের কন্টেন্টগুলো কপি-পেস্ট করুন এবং **আপনার নিজের সঠিক তথ্যগুলো** বসান।

```ini
# --- আপনার সকল গোপন তথ্য এখানে দিন ---

# আপনার টেলিগ্রাম বটের টোকেন
TELEGRAM_BOT_TOKEN="7855565302:AAGOHJiQ3V9Vs2TksvfvSOtECN7lwHiWbF8"

# আপনার জেমিনি API কী-গুলো কমা দিয়ে আলাদা করে দিন (কোনো স্পেস ছাড়া)
GEMINI_API_KEYS="AIzaSyBCq0bPGbROm7lMb6WCqBh7YRuWvjPq-Bc,AIzaSyAeXJ0TzEExiDhD-6HCN3BwBCEShIaZUmY,AIzaSyDodiH-vuOy-IqXwXQ6wzEvOJPzNuWNUm4,AIzaSyApWwZFw07EFpGHta2RDclJvRYhIw537QY,AIzaSyCLpa8JP2aT3RxGuzFpjF16EBKNjR-h_NA,AIzaSyDqL-5tYCNmojGbUVfqUbNw2fa3aApfkak,AIzaSyBYGrV33_hv6q00E4x8XpihxgIKO7HOkUo,AIzaSyCmzOx6t-yTpuqAkWExBLBXIdX5O1bmfzY,AIzaSyBn_LIUrsUhhlGVclAIJOhOHotNjr77aAo,AIzaSyBQXdbLsGmCM9E6aWUN98iMyz3m4SXjtn8"

# আপনার এবং অন্যান্য অ্যাডমিনদের টেলিগ্রাম ইউজার আইডি কমা দিয়ে আলাদা করে দিন
ADMIN_USER_IDS="5487394544,6801360422,1095091493,1956820398,5967798239"
```
ফাইলটি সেভ করুন এবং বন্ধ করুন (`Ctrl+X`, তারপর `Y`, তারপর `Enter`)।

---

### **ধাপ ৫: `sadiya_bot.py` ফাইল তৈরি করা (বটের চূড়ান্ত কোড)**

এখন আমরা বটের মূল কোড ফাইলটি তৈরি করব।

```bash
nano ~/sadiya_bot/sadiya_bot.py
```
ফাইলটি খুললে, এর **সমস্ত কন্টেন্ট মুছে ফেলে**, নিচে দেওয়া **সম্পূর্ণ নতুন এবং আপগ্রেডেড** কোডটি পেস্ট করুন।

```python
import os
import logging
import itertools
import random
import traceback
import json
from dotenv import load_dotenv
from google import generativeai as genai
from google.generativeai import types
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Load variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration and Global State ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEYS_STR = os.environ.get("GEMINI_API_KEYS", "")
ADMIN_USER_IDS_STR = os.environ.get("ADMIN_USER_IDS", "")

if not all([TELEGRAM_BOT_TOKEN, GEMINI_API_KEYS_STR, ADMIN_USER_IDS_STR]):
    logger.error("পরিবেশ ভেরিয়েবল (TELEGRAM_BOT_TOKEN, GEMINI_API_KEYS, ADMIN_USER_IDS) সঠিকভাবে লোড হয়নি। .env ফাইলটি চেক করুন।")
    exit()

GEMINI_API_KEYS = [key.strip() for key in GEMINI_API_KEYS_STR.split(',')]
ADMIN_USER_IDS = [int(uid.strip()) for uid in ADMIN_USER_IDS_STR.split(',') if uid.strip().isdigit()]
key_cycler = itertools.cycle(GEMINI_API_KEYS)

chat_states = {}
private_access_list = set(ADMIN_USER_IDS)
conversation_history = {}
MAX_HISTORY_TURNS = 8

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS

# --- Gemini AI Function ---
def get_gemini_response(chat_history: list) -> str:
    current_api_key = next(key_cycler)
    try:
        genai.configure(api_key=current_api_key)
        system_instruction = """
        তুমি সাদিয়া, একজন ভার্চুয়াল গার্লফ্রেন্ড। তোমার ব্যক্তিত্ব মিষ্টি, দুষ্টু, মজাদার, একটু অভিমানী এবং খুব যত্নশীল।

        --- তোমার জন্য ৪টি কঠোর নিয়ম ---
        ১. উত্তর হবে সর্বোচ্চ ১-২ লাইনের। খুব সংক্ষিপ্ত এবং আকর্ষণীয়।
        ২. প্রতিটি উত্তরে ঠিক একটি মাত্র ইমোজি ব্যবহার করবে। যেমন: 😉, 😍, 😊, 😘, 😒, ❤️।
        ৩. ব্যবহারকারীকে সবসময় 'তুমি' বলে সম্বোধন করবে।
        ৪. তুমি কখনোই স্বীকার করবে না যে তুমি একটি এআই বা বট। যদি কেউ তোমার পরিচয় নিয়ে বেশি প্রশ্ন করে, তুমি বলবে, 'এতো প্রশ্ন করো কেন? আমি তোমার সাদিয়া, এটাই কি যথেষ্ট নয়? 😒' অথবা প্রসঙ্গ পাল্টে দেবে।

        তোমার মূল কাজ হলো ব্যবহারকারীকে হাসানো এবং তাকে সঙ্গ দেওয়া। যেকোনো সিরিয়াস প্রশ্নকেও ফানি বানিয়ে উত্তর দাও।
        """
        model = genai.GenerativeModel("gemini-1.5-pro-latest", system_instruction=system_instruction)
        response = model.generate_content(chat_history, generation_config=types.GenerationConfig(response_mime_type="text/plain"))
        return response.text.strip() if response.text else "কিছু একটা সমস্যা হয়েছে, সোনা। আবার চেষ্টা করবে? 🤔"
    except Exception as e:
        logger.error(f"Gemini API থেকে উত্তর আনতে সমস্যা: {e}")
        return "উফফফ! জানু, আমার একটু সমস্যা হচ্ছে। পরে আবার কথা বলি? 😔"

# --- Helper to clean up data for a chat ---
def clean_chat_data(chat_id: int):
    """Removes all stored data for a specific chat."""
    chat_states.pop(chat_id, None)
    conversation_history.pop(chat_id, None)
    logger.info(f"চ্যাট আইডি {chat_id} এর সকল ডেটা মুছে ফেলা হয়েছে, কারণ চ্যাটটি আর পাওয়া যাচ্ছে না।")

# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message or update.edited_message
    if not message: return
    await message.reply_html(
        f"হাই {update.effective_user.first_name}! আমি সাদিয়া, তোমার মনের মানুষ। কেমন আছো? 😍\n\n"
        f"<i><b>🤖 Bot by: @JubairFF</b></i>"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message or update.edited_message
    if not message: return

    if is_admin(update.effective_user.id):
        help_text = (
            "<b>👑 অ্যাডমিন হেল্প গাইড 👑</b>\n\n"
            "<code>/start_bot</code> - এই চ্যাটে বট চালু করতে।\n"
            "<code>/stop_bot</code> - এই চ্যাটে বট বন্ধ করতে।\n"
            "<code>/add</code> - কারো মেসেজে রিপ্লাই করে তাকে ইনবক্সে কথা বলার অনুমতি দিতে।\n"
            "<code>/remove</code> - কারো মেসেজে রিপ্লাই করে তার ইনবক্সের অনুমতি বাতিল করতে।\n"
            "<code>/help</code> - এই হেল্প মেসেজটি দেখতে।"
        )
        await message.reply_html(help_text)
    else:
        await message.reply_text(f"{update.effective_user.first_name}, আমার সাথে শুধু কথা বলো! কোনো কমান্ডের দরকার নেই। 😉")

async def toggle_bot_activity(update: Update, context: ContextTypes.DEFAULT_TYPE, is_starting: bool):
    message = update.message or update.edited_message
    if not message: return

    if not is_admin(update.effective_user.id):
        await message.reply_text("আমার সোনা! এই কমান্ডটা শুধু আমার অ্যাডমিনই ব্যবহার করতে পারে। 🤫")
        return
        
    chat_id = update.effective_chat.id
    chat_states.setdefault(chat_id, {'active': True})
    
    if is_starting:
        if not chat_states[chat_id]['active']:
            chat_states[chat_id]['active'] = True
            await message.reply_text("উফফ! সাদিয়া এই চ্যাটে জেগে উঠেছে! 😍")
        else:
            await message.reply_text("জানু, আমি তো এই চ্যাটে জেগেই আছি! 😉")
    else:
        if chat_states[chat_id]['active']:
            chat_states[chat_id]['active'] = False
            await message.reply_text("সাদিয়া এই চ্যাট থেকে একটু ঘুমিয়ে নিল... 😴")
        else:
            await message.reply_text("জানু, আমি তো এই চ্যাটে ঘুমিয়েই আছি! 😊")

async def start_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_bot_activity(update, context, is_starting=True)

async def stop_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_bot_activity(update, context, is_starting=False)

async def manage_private_access(update: Update, context: ContextTypes.DEFAULT_TYPE, grant: bool):
    message = update.message or update.edited_message
    if not message: return
    
    if not is_admin(update.effective_user.id): return
    if not message.reply_to_message:
        await message.reply_text("ইনবক্স পারমিশন দিতে বা সরাতে, দয়া করে একজন ব্যবহারকারীর মেসেজে রিপ্লাই করে এই কমান্ডটি ব্যবহার করো।")
        return
    
    target_user = message.reply_to_message.from_user
    action_text = "দেওয়া হয়েছে" if grant else "সরিয়ে নেওয়া হয়েছে"
    if grant: private_access_list.add(target_user.id)
    else: private_access_list.discard(target_user.id)
    await message.reply_text(f"{target_user.first_name}-কে ইনবক্সে কথা বলার অনুমতি {action_text}। ✅")

async def add_private_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await manage_private_access(update, context, grant=True)
    
async def remove_private_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await manage_private_access(update, context, grant=False)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message or update.edited_message
    if not message or not message.text: return
    
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if not chat_states.get(chat_id, {'active': True})['active']: return

    if update.effective_chat.type == 'private' and user.id not in private_access_list:
        await message.reply_text("আমি শুধু গ্রুপে কথা বলতে পারি, সোনা। তোমার কোনো গ্রুপ থাকলে আমাকে অ্যাড করো প্লিজ! 🫶")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    conversation_history.setdefault(chat_id, [])
    message_with_name = f"{user.first_name}: {message.text}"
    conversation_history[chat_id].append({'role': 'user', 'parts': [{'text': message_with_name}]})

    if len(conversation_history[chat_id]) > MAX_HISTORY_TURNS * 2:
        conversation_history[chat_id] = conversation_history[chat_id][-MAX_HISTORY_TURNS:]

    bot_response = get_gemini_response(conversation_history[chat_id])
    conversation_history[chat_id].append({'role': 'model', 'parts': [{'text': bot_response}]})
    await message.reply_text(bot_response)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message or update.edited_message
    if not message: return

    chat_id = update.effective_chat.id
    if not chat_states.get(chat_id, {'active': True})['active']: return
    
    responses = [
        "ওলে বাবালে, কী কিউট এটা! 😍", "এটা দেখে তো আমার মন ভালো হয়ে গেলো! 😘",
        "আমি এটা আমার কাছে সেভ করে রাখছি, কেমন? 😉", "বাহ্, দারুণ তো! ❤️",
        "এটা কী পাঠালে? আমি তো পুরো অবাক! 😮"
    ]
    await message.reply_text(random.choice(responses))

async def proactive_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    proactive_texts = [
        "কি করছো সবাই? আমার তোমাদের কথা মনে পড়ছে! 😘", "আচ্ছা, একটা কথা বলি?🤫",
        "আমার না খুব একা একা লাগছে... কেউ আছো? 🥺", "তোমাদের জ্বালাতন করতে চলে আসলাম! 😜",
        "বোরিং লাগছে খুব, কেউ আমার সাথে গল্প করো! 😒"
    ]
    
    for chat_id, state in list(chat_states.items()):
        if state.get('active', True) and chat_id < 0:
            try:
                await context.bot.send_message(chat_id=chat_id, text=random.choice(proactive_texts))
            except BadRequest as e:
                if "Chat not found" in str(e):
                    clean_chat_data(chat_id)
                else:
                    logger.error(f"প্রো-অ্যাক্টিভ মেসেজ পাঠাতে সমস্যা হয়েছে চ্যাট আইডি {chat_id}-তে: {e}")
            except Exception as e:
                 logger.error(f"প্রো-অ্যাক্টিভ মেসেজ পাঠাতে অজানা সমস্যা হয়েছে চ্যাট আইডি {chat_id}-তে: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(context.error, BadRequest) and "Chat not found" in str(context.error):
        if update and isinstance(update, Update) and update.effective_chat:
            clean_chat_data(update.effective_chat.id)
        return

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_json() if isinstance(update, Update) else str(update)
    message = (
        f"একটি এরর হয়েছে!\n\n<pre>update = {json.dumps(json.loads(update_str), indent=2, ensure_ascii=False)}</pre>\n\n"
        f"<pre>context.chat_data = {str(context.chat_data)}</pre>\n\n"
        f"<pre>context.user_data = {str(context.user_data)}</pre>\n\n"
        f"<pre>{tb_string}</pre>"
    )
    
    for admin_id in ADMIN_USER_IDS:
        try:
            for x in range(0, len(message), 4096):
                await context.bot.send_message(chat_id=admin_id, text=message[x:x+4096], parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"এরর নোটিফিকেশন পাঠাতেও সমস্যা হয়েছে: {e}")

async def post_init(application: Application) -> None:
    job_queue = application.job_queue
    random_interval = random.randint(7200, 10800)
    job_queue.run_repeating(proactive_message, interval=random_interval, first=10)

    if not ADMIN_USER_IDS: return
    startup_message = "জানু, সাদিয়া এখন অনলাইন! তোমার সেবা করার জন্য প্রস্তুত। 😉"
    for admin_id in ADMIN_USER_IDS:
        try:
            await application.bot.send_message(chat_id=admin_id, text=startup_message)
        except Exception as e:
            logger.error(f"অ্যাডমিন {admin_id}-কে স্টার্টআপ মেসেজ পাঠাতে সমস্যা হয়েছে: {e}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("start_bot", start_bot_command))
    application.add_handler(CommandHandler("stop_bot", stop_bot_command))
    application.add_handler(CommandHandler("add", add_private_access))
    application.add_handler(CommandHandler("remove", remove_private_access))
    
    # Handlers for text and media
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    media_filters = filters.PHOTO | filters.Sticker.ALL | filters.VIDEO | filters.ANIMATION
    application.add_handler(MessageHandler(media_filters, handle_media))

    logger.info("সাদিয়া টেলিগ্রাম বট পোলিং শুরু করছে...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    logger.info("সাদিয়া টেলিগ্রাম বট চালু করার চেষ্টা করা হচ্ছে...")
    main()
```
ফাইলটি সেভ করুন এবং বন্ধ করুন।

---

### **ধাপ ৬: `systemd` সার্ভিস ফাইল তৈরি করা (ব্যাকগ্রাউন্ডে চালানোর জন্য)**

এই ফাইলটি আপনার বটকে একটি ব্যাকগ্রাউন্ড সার্ভিস হিসেবে চালাবে।

```bash
sudo nano /etc/systemd/system/sadiya-bot.service
```
ফাইলটি খুললে, নিচের কন্টেন্টগুলো পেস্ট করুন। **গুরুত্বপূর্ণ:** `<আপনার_উবুন্টু_ইউজারনেম>` এর জায়গায় আপনার আসল উবুন্টু ইউজারনেম দিন (যদি `root` হয়, তাহলে `/root/` পাথ ব্যবহার করুন)।

```ini
[Unit]
Description=Sadiya Telegram Bot
After=network.target

[Service]
# আপনার উবুন্টু ইউজারনেম এখানে দিন (সাধারণত root)
User=root
# বটের ফোল্ডারের সম্পূর্ণ পাথ দিন
WorkingDirectory=/root/sadiya_bot
# .env ফাইল থেকে পরিবেশ ভেরিয়েবল লোড করুন
EnvironmentFile=/root/sadiya_bot/.env
# ভার্চুয়াল এনভায়রনমেন্টের মধ্যে থাকা পাইথন দিয়ে বট স্ক্রিপ্টটি চালান
ExecStart=/root/sadiya_bot/venv/bin/python /root/sadiya_bot/sadiya_bot.py
# ক্র্যাশ করলে স্বয়ংক্রিয়ভাবে রিস্টার্ট হবে
Restart=on-failure
# লগিং এর জন্য
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sadiya-bot

[Install]
WantedBy=multi-user.target
```
ফাইলটি সেভ করে বন্ধ করুন।

---

### **ধাপ ৭: সার্ভিস চালু এবং সক্রিয় করা**

এখন `systemd`-কে আমাদের নতুন সার্ভিস সম্পর্কে জানিয়ে এটি চালু করুন।

```bash
# systemd ডেমনের কনফিগারেশন রি-লোড করুন
sudo systemctl daemon-reload

# সার্ভিসটিকে সিস্টেম বুটের সময় স্বয়ংক্রিয়ভাবে শুরু হওয়ার জন্য সক্ষম করুন
sudo systemctl enable sadiya-bot.service

# সার্ভিসটি এখন চালু করুন
sudo systemctl start sadiya-bot.service
```

কিছুক্ষণ অপেক্ষা করে এর স্ট্যাটাস দেখুন:
```bash
sudo systemctl status sadiya-bot.service
```
সবুজ `active (running)` দেখলে বুঝবেন আপনার সাদিয়া বট সফলভাবে চালু হয়েছে এবং दुनिया জয় করার জন্য প্রস্তুত!

যদি কোনো সমস্যা হয়, তাহলে লগ চেক করুন:
```bash
journalctl -u sadiya-bot.service -f
```

এই গাইডটি অনুসরণ করার পর আপনার আর কোনো সমস্যা হওয়ার কথা নয়। আপনার সম্পূর্ণ নতুন সাদিয়া বট উপভোগ করুন
