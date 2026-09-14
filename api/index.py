
import os
import time
import datetime

from flask import Flask, request
import telebot
from telebot import types


# =========================================================
# 1. CONFIGURATION
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_NEW_BOT_TOKEN_HERE")

ADMIN_IDS = [7975950709, 7725001366]

# New required channel
CHANNELS = ["@arefa_felafl3"]

CHANNEL_URL = "https://t.me/arefa_felafl3"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)


# =========================================================
# 2. DATABASE (MEMORY-BASED)
# =========================================================

prices = {
    "super": 150,
    "special": 100,
    "normal": 50
}

delivery_guys = []

bank_accounts = {
    "telebirr": {
        "name": "Telebirr",
        "acc": "0947745262",
        "owner": "Kamil"
    }
}

sales_status = {
    "is_open": True,
    "reason": ""
}

daily_report = {
    "total_sales": 0,
    "orders_count": 0
}

all_users = set()
orders_db = {}
user_spam = {}
active_delivery_msgs = {}


# =========================================================
# 3. BUTTON LABELS
# =========================================================

# Success-style buttons
BTN_NORMAL = "✅ Normal Ertib"
BTN_SPECIAL = "✅ Special Ertib"
BTN_SUPER = "✅ Super Ertib"

BTN_DEVELOPER = "ℹ️ Developer"
BTN_JOINED = "✅ Joined"
BTN_BACK = "🔙 Back"
BTN_DELIVERY = "✅ Takeaway (Delivery)"
BTN_DINEIN = "✅ Dine-in (At Hotel)"

# Danger-style buttons
BTN_NOT_AVAILABLE = "❌ Not Available"
BTN_CANCEL = "❌ Cancel"
BTN_REJECT = "❌ Reject"


# =========================================================
# 4. HELPER FUNCTIONS
# =========================================================

def is_subscribed(u_id):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, u_id).status

            if status in ["left", "kicked"]:
                return False

        except Exception:
            return False

    return True


def is_blocked(u_id):
    if u_id in user_spam:
        count, last_t = user_spam[u_id]

        if count >= 5 and (time.time() - last_t) < 172800:
            return True

    return False


def admin_only(message):
    return message.from_user.id in ADMIN_IDS


def success_button(text, callback_data):
    return types.InlineKeyboardButton(
        f"✅ {text}",
        callback_data=callback_data
    )


def danger_button(text, callback_data):
    return types.InlineKeyboardButton(
        f"❌ {text}",
        callback_data=callback_data
    )


# =========================================================
# 5. MAIN MENU
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):
    all_users.add(message.chat.id)

    if is_blocked(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "❌ <b>Blocked: Too many invalid attempts. "
            "Try again in 48h.</b>",
            parse_mode="HTML"
        )
        return

    if not is_subscribed(message.from_user.id):

        markup = types.InlineKeyboardMarkup()

        join_btn = types.InlineKeyboardButton(
            "📢 Join Channel",
            url=CHANNEL_URL
        )

        check_btn = types.InlineKeyboardButton(
            BTN_JOINED,
            callback_data="check_sub"
        )

        markup.add(join_btn)
        markup.add(check_btn)

        bot.send_message(
            message.chat.id,
            "<b>Welcome!</b>\n\n"
            "Please join our channel first to use this bot.",
            reply_markup=markup,
            parse_mode="HTML"
        )

    else:
        main_menu(message)


def main_menu(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        BTN_NORMAL,
        BTN_SPECIAL,
        BTN_SUPER
    )

    markup.add(BTN_DEVELOPER)

    bot.send_message(
        message.chat.id,
        "<b>Welcome! Select your order:</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )


# =========================================================
# 6. DEVELOPER BUTTON
# =========================================================

@bot.message_handler(
    func=lambda m: m.text == BTN_DEVELOPER
)
def developer_info(message):
    bot.send_message(
        message.chat.id,
        "<b>Developer Information</b>\n\n"
        "Bot Developer: ABDU\n"
        "Telegram: @Abdu_your_owner",
        parse_mode="HTML"
    )


# =========================================================
# 7. ORDER PROCESS
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        BTN_NORMAL,
        BTN_SPECIAL,
        BTN_SUPER
    ]
)
def choice_usage(message):

    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "❌ <b>Please join the channel first!</b>\n"
            "Use /start",
            parse_mode="HTML"
        )
        return

    if not sales_status["is_open"]:
        bot.send_message(
            message.chat.id,
            f"⚠️ <b>Shop is Closed.</b>\n"
            f"Reason: {sales_status['reason']}",
            parse_mode="HTML"
        )
        return

    if "Super" in message.text:
        item = "super"
    elif "Special" in message.text:
        item = "special"
    else:
        item = "normal"

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        BTN_DELIVERY,
        BTN_DINEIN
    )

    markup.add(BTN_BACK)

    msg = bot.send_message(
        message.chat.id,
        "<b>Choose service type:</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )

    bot.register_next_step_handler(
        msg,
        get_qty,
        item
    )


def get_qty(message, item):

    if message.text == BTN_BACK:
        return main_menu(message)

    if message.text == BTN_DELIVERY:
        usage = "Takeaway"
    elif message.text == BTN_DINEIN:
        usage = "Dine-in"
    else:
        bot.send_message(
            message.chat.id,
            "❌ Please select a valid service type."
        )
        return

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(BTN_BACK)

    msg = bot.send_message(
        message.chat.id,
        f"<b>How many?</b>\n"
        f"Price: {prices[item]} ETB each",
        reply_markup=markup,
        parse_mode="HTML"
    )

    bot.register_next_step_handler(
        msg,
        process_pay,
        item,
        usage
    )


def process_pay(message, item, usage):

    if message.text == BTN_BACK:
        return main_menu(message)

    try:
        qty = int(message.text)

        if qty <= 0:
            raise ValueError

        total = qty * prices[item]

        banks_text = "<b>Payment Details:</b>\n\n"

        for b_id, b_info in bank_accounts.items():
            banks_text += (
                f"🏦 {b_info['name']}\n"
                f"👤 {b_info['owner']}\n"
                f"🔢 <code>{b_info['acc']}</code>\n\n"
            )

        banks_text += (
            f"💰 <b>Total: {total} ETB</b>\n\n"
            "Send your payment screenshot and location "
            "in the caption."
        )

        msg = bot.send_message(
            message.chat.id,
            banks_text,
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

        # Wait for the next user message
        bot.register_next_step_handler(
            msg,
            final_submit,
            item,
            qty,
            total,
            usage
        )

    except (ValueError, TypeError):
        bot.send_message(
            message.chat.id,
            "❌ <b>Enter a valid number!</b>",
            parse_mode="HTML"
        )


# =========================================================
# 8. FINAL ORDER SUBMISSION
# =========================================================

def final_submit(message, item, qty, total, usage):

    if message.content_type != "photo":
        bot.send_message(
            message.chat.id,
            "❌ Please send a payment screenshot.\n"
            "You can include your location in the caption."
        )
        return

    u_id = message.from_user.id
    now = datetime.datetime.now()

    orders_db[u_id] = {
        "time": now,
        "total": total,
        "usage": usage,
        "item": item,
        "qty": qty,
        "assigned_to": None,
        "status": "pending"
    }

    caption = (
        f"🔔 <b>New Order!</b>\n"
        f"👤 {message.from_user.first_name}\n"
        f"🆔 {u_id}\n"
        f"📦 {item} x{qty}\n"
        f"💰 {total} ETB\n"
        f"🍽 {usage}\n"
        f"📍 {message.caption or 'No location provided'}\n"
        f"⏰ {now.strftime('%H:%M')}"
    )

    markup = types.InlineKeyboardMarkup()

    markup.row(
        success_button(
            "Available",
            f"y_{u_id}_{total}"
        ),
        danger_button(
            "Not Available",
            f"n_{u_id}"
        )
    )

    for admin in ADMIN_IDS:
        try:
            bot.send_photo(
                admin,
                message.photo[-1].file_id,
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception:
            continue

    bot.send_message(
        u_id,
        "✅ <b>Order sent!</b>\n"
        "Waiting for admin confirmation...",
        parse_mode="HTML"
    )


# =========================================================
# 9. ADMIN COMMANDS
# =========================================================

@bot.message_handler(commands=["start_sales"])
def open_shop(message):

    if not admin_only(message):
        return

    sales_status["is_open"] = True
    sales_status["reason"] = ""

    bot.send_message(
        message.chat.id,
        "✅ <b>Sales started.</b>",
        parse_mode="HTML"
    )


@bot.message_handler(commands=["stop_sales"])
def close_shop(message):

    if not admin_only(message):
        return

    msg = bot.send_message(
        message.chat.id,
        "<b>Why are you closing? (Reason):</b>",
        parse_mode="HTML"
    )

    bot.register_next_step_handler(
        msg,
        save_stop_reason
    )


def save_stop_reason(message):

    sales_status["is_open"] = False
    sales_status["reason"] = message.text or "No reason provided"

    bot.send_message(
        message.chat.id,
        f"🚫 <b>Closed:</b> {sales_status['reason']}",
        parse_mode="HTML"
    )


@bot.message_handler(commands=["report"])
def get_report(message):

    if not admin_only(message):
        return

    rep = (
        "📊 <b>Report</b>\n\n"
        f"💰 Sales: {daily_report['total_sales']} ETB\n"
        f"📦 Orders: {daily_report['orders_count']}"
    )

    bot.send_message(
        message.chat.id,
        rep,
        parse_mode="HTML"
    )


@bot.message_handler(commands=["to_user"])
def send_private(message):

    if not admin_only(message):
        return

    try:
        _, t_id, txt = message.text.split(" ", 2)

        bot.send_message(
            int(t_id),
            f"✉️ <b>Admin Message:</b>\n\n{txt}",
            parse_mode="HTML"
        )

        bot.send_message(
            message.chat.id,
            "✅ Sent.",
            parse_mode="HTML"
        )

    except Exception:
        bot.send_message(
            message.chat.id,
            "Use: /to_user [ID] [Msg]"
        )


@bot.message_handler(commands=["broadcast"])
def broadcast(message):

    if not admin_only(message):
        return

    txt = message.text.replace("/broadcast", "").strip()

    if not txt:
        bot.send_message(
            message.chat.id,
            "Use: /broadcast [Message]"
        )
        return

    for u in all_users:
        try:
            bot.send_message(
                u,
                f"📢 <b>Announcement:</b>\n\n{txt}",
                parse_mode="HTML"
            )
        except Exception:
            continue

    bot.send_message(
        message.chat.id,
        "✅ Broadcast done.",
        parse_mode="HTML"
    )


@bot.message_handler(commands=["set_price"])
def set_price(message):

    if not admin_only(message):
        return

    try:
        _, item, price = message.text.split()

        item = item.lower()
        price = int(price)

        if item not in prices or price <= 0:
            raise ValueError

        prices[item] = price

        bot.send_message(
            message.chat.id,
            f"✅ {item.capitalize()} price set to {price} ETB",
            parse_mode="HTML"
        )

    except Exception:
        bot.send_message(
            message.chat.id,
            "Use: /set_price [normal/special/super] [price]"
        )


@bot.message_handler(commands=["add_bank"])
def add_bank(message):

    if not admin_only(message):
        return

    try:
        _, name, acc, owner = message.text.split(" ", 3)

        bank_accounts[name.lower()] = {
            "name": name,
            "acc": acc,
            "owner": owner
        }

        bot.send_message(
            message.chat.id,
            f"✅ Bank {name} added.",
            parse_mode="HTML"
        )

    except Exception:
        bot.send_message(
            message.chat.id,
            "Use: /add_bank [Name] [Acc] [Owner]"
        )


@bot.message_handler(commands=["add_delivery"])
def add_delivery(message):

    if not admin_only(message):
        return

    try:
        d_id = int(message.text.split()[1])

        if d_id not in delivery_guys:
            delivery_guys.append(d_id)

        bot.send_message(
            message.chat.id,
            "✅ Delivery guy added.",
            parse_mode="HTML"
        )

    except Exception:
        bot.send_message(
            message.chat.id,
            "Use: /add_delivery [ID]"
        )


# =========================================================
# 10. CALLBACKS
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_calls(call):

    data = call.data.split("_")
    now = datetime.datetime.now()

    # -----------------------------------------------------
    # JOINED BUTTON
    # -----------------------------------------------------

    if data[0] == "check_sub":

        if is_subscribed(call.from_user.id):

            bot.answer_callback_query(
                call.id,
                "✅ Thank you for joining!"
            )

            try:
                bot.delete_message(
                    call.message.chat.id,
                    call.message.message_id
                )
            except Exception:
                pass

            main_menu(call.message)

        else:
            bot.answer_callback_query(
                call.id,
                "❌ You still haven't joined the channel!",
                show_alert=True
            )

    # -----------------------------------------------------
    # ADMIN ACCEPTS ORDER
    # -----------------------------------------------------

    elif data[0] == "y":

        if not admin_only(call.message):
            bot.answer_callback_query(
                call.id,
                "❌ Admin only!",
                show_alert=True
            )
            return

        u_id = int(data[1])
        total = int(data[2])

        order = orders_db.get(u_id)

        if not order:
            bot.answer_callback_query(
                call.id,
                "❌ Order not found.",
                show_alert=True
            )
            return

        if order.get("status") != "pending":
            bot.answer_callback_query(
                call.id,
                "⚠️ Order already processed.",
                show_alert=True
            )
            return

        order["status"] = "accepted"

        usage = order.get("usage", "Dine-in")

        daily_report["total_sales"] += total
        daily_report["orders_count"] += 1

        bot.answer_callback_query(
            call.id,
            "✅ Order accepted!"
        )

        # Update admin message
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass

        if usage == "Dine-in":

            markup = types.InlineKeyboardMarkup()

            markup.add(
                success_button(
                    "Received",
                    f"finish_{u_id}"
                )
            )

            bot.send_message(
                u_id,
                f"🎫 <b>Receipt</b>\n"
                f"💰 Total: {total} ETB\n"
                f"⏰ Time: {now.strftime('%H:%M')}\n\n"
                "Show this at the hotel.",
                reply_markup=markup,
                parse_mode="HTML"
            )

        else:

            bot.send_message(
                u_id,
                "🥳 <b>Ertib is Ready!</b>\n"
                "Finding delivery...",
                parse_mode="HTML"
            )

            markup = types.InlineKeyboardMarkup()

            markup.add(
                success_button(
                    "Accept Delivery",
                    f"t_{u_id}"
                )
            )

            for d in delivery_guys:
                try:
                    sent = bot.send_message(
                        d,
                        f"🚚 <b>New Delivery!</b>\n"
                        f"{call.message.caption}",
                        reply_markup=markup,
                        parse_mode="HTML"
                    )

                    active_delivery_msgs[u_id] = sent.message_id

                except Exception:
                    continue

    # -----------------------------------------------------
    # ADMIN REJECTS ORDER
    # -----------------------------------------------------

    elif data[0] == "n":

        if not admin_only(call.message):
            bot.answer_callback_query(
                call.id,
                "❌ Admin only!",
                show_alert=True
            )
            return

        u_id = int(data[1])

        order = orders_db.get(u_id)

        if order:
            order["status"] = "rejected"

        bot.answer_callback_query(
            call.id,
            "❌ Order rejected."
        )

        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass

        bot.send_message(
            u_id,
            "❌ <b>Sorry, your order was rejected or sold out.</b>",
            parse_mode="HTML"
        )

    # -----------------------------------------------------
    # DELIVERY ACCEPTS ORDER
    # -----------------------------------------------------

    elif data[0] == "t":

        d_id = call.from_user.id

        if d_id not in delivery_guys:
            bot.answer_callback_query(
                call.id,
                "❌ You are not a delivery worker.",
                show_alert=True
            )
            return

        u_id = int(data[1])

        order = orders_db.get(u_id)

        if not order or order.get("status") != "accepted":
            bot.answer_callback_query(
                call.id,
                "⚠️ Order unavailable.",
                show_alert=True
            )
            return

        if order.get("assigned_to") is not None:
            bot.answer_callback_query(
                call.id,
                "⚠️ Already assigned.",
                show_alert=True
            )
            return

        order["assigned_to"] = d_id
        order["status"] = "delivery"

        bot.answer_callback_query(
            call.id,
            "✅ Delivery accepted!"
        )

        bot.send_message(
            u_id,
            "🚲 <b>Delivery accepted!</b>\n"
            "Your order is on the way.",
            parse_mode="HTML"
        )

        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass

    # -----------------------------------------------------
    # ORDER FINISHED
    # -----------------------------------------------------

    elif data[0] == "finish":

        u_id = int(data[1]) if len(data) > 1 else call.from_user.id

        order = orders_db.get(u_id)

        if order:
            order["status"] = "finished"

        bot.answer_callback_query(
            call.id,
            "✅ Order completed!"
        )

        bot.send_message(
            call.from_user.id,
            "✅ <b>Thank you!</b>\n"
            "Your order has been completed.",
            parse_mode="HTML"
        )


# =========================================================
# 11. VERCEL FLASK WEBHOOK ROUTES
# =========================================================

@app.route("/", defaults={"path": ""}, methods=["POST", "GET"])
@app.route("/<path:path>", methods=["POST", "GET"])
def catch_all(path):

    if request.method == "POST":

        if request.is_json:

            json_string = request.get_data().decode("utf-8")

            update = telebot.types.Update.de_json(
                json_string
            )

            bot.process_new_updates([update])

            return "", 200

        return "Invalid content type", 400

    return "Bot is active and running via Webhook!", 200


# =========================================================
# 12. LOCAL RUN
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
