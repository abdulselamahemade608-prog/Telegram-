from flask import Flask, request
import telebot
from telebot import types
import datetime
import time

# --- 1. CONFIGURATION ---
TOKEN = "8934567176:AAGjSUFmzUzsUznep9eynoYkGYsk0GAGj9I"
ADMIN_IDS = [7975950709, 7725001366] 
CHANNELS = ["@Felafel_arafa"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- 2. DATABASE (Memory-based) ---
prices = {"super": 150, "special": 100, "normal": 50}
delivery_guys = [] 
bank_accounts = {
    "telebirr": {"name": "Telebirr", "acc": "0947745262", "owner": "Kamil"}
}
sales_status = {"is_open": True, "reason": ""}
daily_report = {"total_sales": 0, "orders_count": 0}
all_users = set()
orders_db = {} 
user_spam = {} 
active_delivery_msgs = {} 

# --- 3. HELPER FUNCTIONS ---
def is_subscribed(u_id):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, u_id).status
            if status in ['left', 'kicked', 'None']: return False
        except Exception:
            return False
    return True

def is_blocked(u_id):
    if u_id in user_spam:
        count, last_t = user_spam[u_id]
        if count >= 5 and (time.time() - last_t) < 172800:
            return True
    return False

# --- 4. MAIN MENU ---
@bot.message_handler(commands=['start'])
def start(message):
    all_users.add(message.chat.id)
    if is_blocked(message.from_user.id):
        bot.send_message(message.chat.id, "❌ <b>Blocked: Too many invalid attempts. Try again in 48h.</b>", parse_mode="HTML")
        return
    
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Join Channel 📢", url="https://t.me/Felafel_arafa")
        check_btn = types.InlineKeyboardButton("Joined ✅", callback_data="check_sub")
        markup.add(btn1)
        markup.add(check_btn)
        
        photo_url = "https://t.me/ISATBIRR1992/2" 
        try:
            bot.send_photo(message.chat.id, photo_url, caption="<b>Welcome! Please join our channel first to use this bot.</b>", reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(message.chat.id, "<b>Welcome! Please join our channel first:</b>", reply_markup=markup, parse_mode="HTML")
    else:
        main_menu(message)

def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Normal Ertib", "Special Ertib", "Super Ertib")
    markup.add("Developer")
    bot.send_message(message.chat.id, "<b>Welcome! Select your order:</b>", reply_markup=markup, parse_mode="HTML")

# --- 5. ORDER PROCESS ---
@bot.message_handler(func=lambda m: m.text in ["Normal Ertib", "Special Ertib", "Super Ertib"])
def choice_usage(message):
    if not is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "❌ <b>Please join the channel first! /start</b>", parse_mode="HTML")
        return
    if not sales_status["is_open"]:
        bot.send_message(message.chat.id, f"⚠️ <b>Shop is Closed.</b>\nReason: {sales_status['reason']}", parse_mode="HTML")
        return
    
    item = "super" if "Super" in message.text else "special" if "Special" in message.text else "normal"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Takeaway (Delivery)", "Dine-in (At Hotel)")
    markup.add("🔙 Back")
    msg = bot.send_message(message.chat.id, "<b>Choose service type:</b>", reply_markup=markup, parse_mode="HTML")
    bot.register_next_step_handler(msg, get_qty, item)

def get_qty(message, item):
    if message.text == "🔙 Back": return main_menu(message)
    usage = "Takeaway" if "Takeaway" in message.text else "Dine-in"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 Back")
    msg = bot.send_message(message.chat.id, f"<b>How many? (Price: {prices[item]} ETB each):</b>", reply_markup=markup, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_pay, item, usage)

def process_pay(message, item, usage):
    if message.text == "🔙 Back": return main_menu(message)
    try:
        qty = int(message.text)
        total = qty * prices[item]
        
        banks_text = "<b>Payment Details:</b>\n\n"
        for b_id, b_info in bank_accounts.items():
            banks_text += f"🏦 {b_info['name']}\n👤 {b_info['owner']}\n🔢 <code>{b_info['acc']}</code> (Tap to copy)\n\n"
        
        banks_text += f"💰 <b>Total: {total} ETB</b>\n\nSend Screenshot + Location."
        bot.send_message(message.chat.id, banks_text, reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
        bot.register_next_step_handler(message, final_submit, item, qty, total, usage)
    except Exception:
        bot.send_message(message.chat.id, "❌ Enter a number!", parse_mode="HTML")

def final_submit(message, item, qty, total, usage):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ Please send a screenshot.", parse_mode="HTML")
        return
    
    u_id = message.from_user.id
    now = datetime.datetime.now()
    orders_db[u_id] = {"time": now, "total": total, "usage": usage, "assigned_to": None}

    caption = f"🔔 <b>New Order!</b>\n👤 {message.from_user.first_name}\n🆔 {u_id}\n📦 {item} x{qty}\n💰 {total} ETB\n🍽 {usage}\n📍 {message.caption}\n⏰ {now.strftime('%H:%M')}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Available ✅", callback_data=f"y_{u_id}_{total}"),
               types.InlineKeyboardButton("Not Available ❌", callback_data=f"n_{u_id}"))
    
    for admin in ADMIN_IDS:
        try: bot.send_photo(admin, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
        except Exception: continue
    bot.send_message(u_id, "✅ <b>Sent! Waiting for admin confirmation...</b>", parse_mode="HTML")

# --- 6. ADMIN COMMANDS ---
@bot.message_handler(commands=['start_sales'])
def open_shop(message):
    if message.from_user.id not in ADMIN_IDS: return
    sales_status["is_open"] = True
    bot.send_message(message.chat.id, "✅ <b>Sales started.</b>", parse_mode="HTML")

@bot.message_handler(commands=['stop_sales'])
def close_shop(message):
    if message.from_user.id not in ADMIN_IDS: return
    msg = bot.send_message(message.chat.id, "<b>Why are you closing? (Reason):</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, save_stop_reason)

def save_stop_reason(message):
    sales_status["is_open"] = False
    sales_status["reason"] = message.text
    bot.send_message(message.chat.id, f"🚫 <b>Closed: {message.text}</b>", parse_mode="HTML")

@bot.message_handler(commands=['report'])
def get_report(message):
    if message.from_user.id not in ADMIN_IDS: return
    rep = f"📊 <b>Report</b>\n\n💰 Sales: {daily_report['total_sales']} ETB\n📦 Orders: {daily_report['orders_count']}"
    bot.send_message(message.chat.id, rep, parse_mode="HTML")

@bot.message_handler(commands=['to_user'])
def send_private(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, t_id, txt = message.text.split(" ", 2)
        bot.send_message(t_id, f"✉️ <b>Admin Message:</b>\n\n{txt}", parse_mode="HTML")
        bot.send_message(message.chat.id, "✅ Sent.", parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, "Use: /to_user [ID] [Msg]", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id not in ADMIN_IDS: return
    txt = message.text.replace("/broadcast", "").strip()
    if not txt: return
    for u in all_users:
        try: bot.send_message(u, f"📢 <b>Announcement:</b>\n\n{txt}", parse_mode="HTML")
        except Exception: continue
    bot.send_message(message.chat.id, "✅ Broadcast done.", parse_mode="HTML")

@bot.message_handler(commands=['set_price'])
def set_price(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, item, price = message.text.split()
        if item.lower() in prices:
            prices[item.lower()] = int(price)
            bot.send_message(message.chat.id, f"✅ {item} price set to {price}", parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, "Use: /set_price [normal/special/super] [price]", parse_mode="HTML")

@bot.message_handler(commands=['add_bank'])
def add_bank(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, name, acc, owner = message.text.split(" ", 3)
        bank_accounts[name.lower()] = {"name": name, "acc": acc, "owner": owner}
        bot.send_message(message.chat.id, f"✅ Bank {name} added.", parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, "Use: /add_bank [Name] [Acc] [Owner]", parse_mode="HTML")

@bot.message_handler(commands=['add_delivery'])
def add_delivery(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        d_id = int(message.text.split()[1])
        delivery_guys.append(d_id)
        bot.send_message(message.chat.id, "✅ Delivery guy added.", parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, "Use: /add_delivery [ID]", parse_mode="HTML")

# --- 7. CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_calls(call):
    data = call.data.split("_")
    now = datetime.datetime.now()

    if data[0] == "check_sub":
        if is_subscribed(call.from_user.id): 
            bot.answer_callback_query(call.id, "✅ Thank you for joining!")
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass
            main_menu(call.message)
        else: 
            bot.answer_callback_query(call.id, "❌ You still haven't joined the channel!", show_alert=True)

    elif data[0] == "y":
        u_id, total = int(data[1]), int(data[2])
        usage = orders_db.get(u_id, {}).get("usage", "Dine-in")
        if usage == "Dine-in":
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Received 👍", callback_data="finish"))
            bot.send_message(u_id, f"🎫 <b>Receipt</b>\n💰 Total: {total} ETB\n⏰ Time: {now.strftime('%H:%M')}\n\nShow this at the hotel.", reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(u_id, "🥳 <b>Ertib is Ready! Finding delivery...</b>", parse_mode="HTML")
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚲 Accept", callback_data=f"t_{u_id}"))
            for d in delivery_guys:
                try: bot.send_message(d, f"🚚 <b>New Delivery!</b>\n{call.message.caption}", reply_markup=markup, parse_mode="HTML")
                except Exception: continue

    elif data[0] == "n":
        u_id = int(data[1])
        bot.send_message(u_id, "❌ <b>Sorry, order rejected or sold out.</b>", parse_mode="HTML")

# --- 8. VERCEL FLASK WEBHOOK ROUTES ---
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def catch_all(path):
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        return 'Invalid content type', 400
    return 'Bot is active and running via Webhook!'
        
