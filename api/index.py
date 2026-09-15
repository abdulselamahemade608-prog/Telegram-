"""
AREFA FOOD ORDERING BOT - IMPROVED VERSION
A complete Telegram bot for managing food orders with admin controls, delivery tracking, and payment integration
"""

import os
import time
import datetime
import json
from flask import Flask, request
import telebot
from telebot import types

# =========================================================
# 1. CONFIGURATION & CONSTANTS
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [7725001366]
CHANNELS = ["@felafel_arafa"]
CHANNEL_URL = "https://t.me/Felafel_arafa"

# =========================================================
# 2. BOT & APP INITIALIZATION
# =========================================================

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# =========================================================
# 3. DATABASE (MEMORY-BASED WITH OPTIONAL PERSISTENCE)
# =========================================================

class Database:
    """Centralized database management"""
    
    def __init__(self):
        self.prices = {
            "super": 150,
            "special": 100,
            "normal": 50
        }
        
        self.delivery_guys = []
        
        self.bank_accounts = {
            "telebirr": {
                "name": "Telebirr",
                "acc": "0947745262",
                "owner": "Kamil"
            }
        }
        
        self.sales_status = {
            "is_open": True,
            "reason": ""
        }
        
        self.daily_report = {
            "total_sales": 0,
            "orders_count": 0,
            "date": datetime.date.today().isoformat()
        }
        
        self.all_users = set()
        self.orders_db = {}
        self.user_spam = {}
        self.active_delivery_msgs = {}
    
    def reset_daily_report(self):
        """Reset daily report if date changed"""
        today = datetime.date.today().isoformat()
        if self.daily_report.get("date") != today:
            self.daily_report = {
                "total_sales": 0,
                "orders_count": 0,
                "date": today
            }
    
    def add_spam(self, user_id):
        """Track spam attempts"""
        current_time = time.time()
        if user_id not in self.user_spam:
            self.user_spam[user_id] = (1, current_time)
        else:
            count, last_time = self.user_spam[user_id]
            self.user_spam[user_id] = (count + 1, current_time)
    
    def is_spam_blocked(self, user_id):
        """Check if user is spam blocked"""
        if user_id not in self.user_spam:
            return False
        
        count, last_time = self.user_spam[user_id]
        # Block if 5+ attempts in last 48 hours
        if count >= 5 and (time.time() - last_time) < 172800:
            return True
        return False

db = Database()

# =========================================================
# 4. BUTTON LABELS & CONSTANTS
# =========================================================

class Buttons:
    """Centralized button labels"""
    # Order types
    NORMAL = "✅ Normal Ertib"
    SPECIAL = "✅ Special Ertib"
    SUPER = "✅ Super Ertib"
    
    # Service types
    DELIVERY = "✅ Takeaway (Delivery)"
    DINEIN = "✅ Dine-in (At Hotel)"
    
    # Navigation
    DEVELOPER = "ℹ️ Developer"
    JOINED = "✅ Joined"
    BACK = "🔙 Back"
    
    # Status
    AVAILABLE = "✅ Available"
    NOT_AVAILABLE = "❌ Not Available"
    CANCEL = "❌ Cancel"
    REJECT = "❌ Reject"

# =========================================================
# 5. HELPER FUNCTIONS
# =========================================================

def is_subscribed(user_id):
    """Check if user is subscribed to required channel"""
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Error checking subscription: {e}")
            return False
    return True

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def create_success_button(text, callback_data):
    """Create a success-style inline button"""
    return types.InlineKeyboardButton(f"✅ {text}", callback_data=callback_data)

def create_danger_button(text, callback_data):
    """Create a danger-style inline button"""
    return types.InlineKeyboardButton(f"❌ {text}", callback_data=callback_data)

def get_order_summary(order, user_id):
    """Generate order summary text"""
    return (
        f"🔔 <b>New Order!</b>\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"📦 Item: {order['item'].capitalize()} x{order['qty']}\n"
        f"💰 Total: {order['total']} ETB\n"
        f"🍽 Service: {order['usage']}\n"
        f"⏰ Time: {order['time'].strftime('%H:%M')}"
    )

# =========================================================
# 6. MAIN MENU & START COMMAND
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):
    """Handle /start command"""
    user_id = message.from_user.id
    db.all_users.add(user_id)
    
    # Check if user is blocked
    if db.is_spam_blocked(user_id):
        bot.send_message(
            message.chat.id,
            "❌ <b>Blocked: Too many invalid attempts.</b>\n"
            "Try again in 48 hours.",
            parse_mode="HTML"
        )
        return
    
    # Check subscription
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
        markup.add(types.InlineKeyboardButton(Buttons.JOINED, callback_data="check_sub"))
        
        bot.send_message(
            message.chat.id,
            "<b>Welcome! 🎉</b>\n\n"
            "Please join our channel first to use this bot.",
            reply_markup=markup,
            parse_mode="HTML"
        )
        return
    
    # User is subscribed, show main menu
    show_main_menu(message)

def show_main_menu(message):
    """Display main menu"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(Buttons.NORMAL, Buttons.SPECIAL, Buttons.SUPER)
    markup.add(Buttons.DEVELOPER)
    
    bot.send_message(
        message.chat.id,
        "<b>🍽 Welcome! Select Your Order:</b>\n\n"
        "Choose your preferred Ertib type:",
        reply_markup=markup,
        parse_mode="HTML"
    )

# =========================================================
# 7. DEVELOPER INFO
# =========================================================

@bot.message_handler(func=lambda m: m.text == Buttons.DEVELOPER)
def developer_info(message):
    """Send developer information"""
    bot.send_message(
        message.chat.id,
        "<b>👨‍💻 Developer Information</b>\n\n"
        "Bot Developer: ABDU\n"
        "Telegram: @Abdu_your_owner\n\n"
        "<i>For support or inquiries, contact the developer.</i>",
        parse_mode="HTML"
    )

# =========================================================
# 8. ORDER PROCESS
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [Buttons.NORMAL, Buttons.SPECIAL, Buttons.SUPER]
)
def process_order_type(message):
    """Handle order type selection"""
    user_id = message.from_user.id
    
    # Verify subscription
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            "❌ <b>Please join the channel first!</b>\n"
            "Use /start",
            parse_mode="HTML"
        )
        return
    
    # Check shop status
    if not db.sales_status["is_open"]:
        bot.send_message(
            message.chat.id,
            f"⚠️ <b>Shop is Closed</b>\n"
            f"Reason: {db.sales_status['reason']}",
            parse_mode="HTML"
        )
        return
    
    # Determine item type
    if "Super" in message.text:
        item = "super"
    elif "Special" in message.text:
        item = "special"
    else:
        item = "normal"
    
    # Ask for service type
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(Buttons.DELIVERY, Buttons.DINEIN)
    markup.add(Buttons.BACK)
    
    msg = bot.send_message(
        message.chat.id,
        f"<b>📦 {item.capitalize()} Ertib Selected</b>\n"
        f"Price: <b>{db.prices[item]} ETB</b> per unit\n\n"
        "<b>Choose service type:</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )
    
    bot.register_next_step_handler(msg, get_quantity, item)

def get_quantity(message, item):
    """Get order quantity"""
    if message.text == Buttons.BACK:
        return show_main_menu(message)
    
    if message.text == Buttons.DELIVERY:
        usage = "Takeaway"
    elif message.text == Buttons.DINEIN:
        usage = "Dine-in"
    else:
        bot.send_message(
            message.chat.id,
            "❌ Please select a valid service type."
        )
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(Buttons.BACK)
    
    msg = bot.send_message(
        message.chat.id,
        f"<b>How many units?</b>\n"
        f"Price per unit: <b>{db.prices[item]} ETB</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )
    
    bot.register_next_step_handler(msg, get_payment_details, item, usage)

def get_payment_details(message, item, usage):
    """Get payment and location details"""
    if message.text == Buttons.BACK:
        return show_main_menu(message)
    
    try:
        qty = int(message.text)
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        
        total = qty * db.prices[item]
        
        # Prepare payment details
        payment_text = "<b>💳 Payment Details:</b>\n\n"
        for bank_id, bank_info in db.bank_accounts.items():
            payment_text += (
                f"🏦 <b>{bank_info['name']}</b>\n"
                f"👤 Owner: {bank_info['owner']}\n"
                f"🔢 Account: <code>{bank_info['acc']}</code>\n\n"
            )
        
        payment_text += (
            f"<b>💰 Total Amount: {total} ETB</b>\n\n"
            f"<b>📸 Instructions:</b>\n"
            f"1. Send payment screenshot\n"
            f"2. Include your location in photo caption\n"
            f"3. Our admin will confirm your order"
        )
        
        msg = bot.send_message(
            message.chat.id,
            payment_text,
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode="HTML"
        )
        
        bot.register_next_step_handler(
            msg, submit_order, item, qty, total, usage
        )
    
    except (ValueError, TypeError):
        db.add_spam(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "❌ <b>Invalid number!</b>\n"
            "Please enter a positive integer.",
            parse_mode="HTML"
        )

# =========================================================
# 9. FINAL ORDER SUBMISSION
# =========================================================

def submit_order(message, item, qty, total, usage):
    """Submit and process order"""
    if message.content_type != "photo":
        bot.send_message(
            message.chat.id,
            "❌ <b>Please send a payment screenshot.</b>\n"
            "You can include your location in the photo caption."
        )
        return
    
    user_id = message.from_user.id
    now = datetime.datetime.now()
    
    # Store order
    db.orders_db[user_id] = {
        "time": now,
        "total": total,
        "usage": usage,
        "item": item,
        "qty": qty,
        "assigned_to": None,
        "status": "pending",
        "user_name": message.from_user.first_name or "Unknown",
        "location": message.caption or "No location provided"
    }
    
    # Prepare admin notification
    caption = (
        f"🔔 <b>New Order!</b>\n"
        f"👤 {message.from_user.first_name}\n"
        f"🆔 <code>{user_id}</code>\n"
        f"📦 {item.capitalize()} x{qty}\n"
        f"💰 {total} ETB\n"
        f"🍽 {usage}\n"
        f"📍 {message.caption or 'No location provided'}\n"
        f"⏰ {now.strftime('%H:%M')}"
    )
    
    # Send to all admins
    markup = types.InlineKeyboardMarkup()
    markup.row(
        create_success_button("Available", f"y_{user_id}_{total}"),
        create_danger_button("Not Available", f"n_{user_id}")
    )
    
    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(
                admin_id,
                message.photo[-1].file_id,
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Error sending to admin {admin_id}: {e}")
    
    # Confirm to user
    bot.send_message(
        user_id,
        "✅ <b>Order Submitted!</b>\n\n"
        "Your order has been sent to admin for confirmation.\n"
        "We will notify you soon.",
        parse_mode="HTML"
    )

# =========================================================
# 10. ADMIN COMMANDS
# =========================================================

@bot.message_handler(commands=["start_sales"])
def open_shop(message):
    """Admin: Open shop"""
    if not is_admin(message.from_user.id):
        return
    
    db.sales_status["is_open"] = True
    db.sales_status["reason"] = ""
    
    bot.send_message(
        message.chat.id,
        "✅ <b>Sales Started!</b>\n"
        "Shop is now open for orders.",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["stop_sales"])
def close_shop(message):
    """Admin: Close shop with reason"""
    if not is_admin(message.from_user.id):
        return
    
    msg = bot.send_message(
        message.chat.id,
        "<b>Why are you closing the shop?</b>\n"
        "Enter the reason:",
        parse_mode="HTML"
    )
    
    bot.register_next_step_handler(msg, save_close_reason)

def save_close_reason(message):
    """Save shop closure reason"""
    db.sales_status["is_open"] = False
    db.sales_status["reason"] = message.text or "No reason provided"
    
    bot.send_message(
        message.chat.id,
        f"🚫 <b>Shop Closed</b>\n"
        f"Reason: {db.sales_status['reason']}",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["report"])
def get_report(message):
    """Admin: Get daily report"""
    if not is_admin(message.from_user.id):
        return
    
    db.reset_daily_report()
    
    report = (
        "📊 <b>Daily Report</b>\n\n"
        f"💰 Total Sales: <b>{db.daily_report['total_sales']} ETB</b>\n"
        f"📦 Orders Count: <b>{db.daily_report['orders_count']}</b>\n"
        f"📅 Date: {db.daily_report['date']}"
    )
    
    bot.send_message(message.chat.id, report, parse_mode="HTML")

@bot.message_handler(commands=["stats"])
def get_stats(message):
    """Admin: Get detailed statistics"""
    if not is_admin(message.from_user.id):
        return
    
    total_users = len(db.all_users)
    pending_orders = sum(1 for o in db.orders_db.values() if o["status"] == "pending")
    delivered = sum(1 for o in db.orders_db.values() if o["status"] == "finished")
    
    stats = (
        "📈 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"⏳ Pending Orders: <b>{pending_orders}</b>\n"
        f"✅ Delivered Orders: <b>{delivered}</b>\n"
        f"🚚 Delivery Guys: <b>{len(db.delivery_guys)}</b>"
    )
    
    bot.send_message(message.chat.id, stats, parse_mode="HTML")

@bot.message_handler(commands=["to_user"])
def send_private_message(message):
    """Admin: Send message to specific user"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            raise ValueError("Invalid format")
        
        user_id = int(parts[1])
        text = parts[2]
        
        bot.send_message(
            user_id,
            f"✉️ <b>Admin Message:</b>\n\n{text}",
            parse_mode="HTML"
        )
        
        bot.send_message(message.chat.id, "✅ Message sent.", parse_mode="HTML")
    
    except (ValueError, IndexError):
        bot.send_message(
            message.chat.id,
            "❌ <b>Usage:</b>\n/to_user [USER_ID] [MESSAGE]"
        )

@bot.message_handler(commands=["broadcast"])
def broadcast_message(message):
    """Admin: Broadcast message to all users"""
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/broadcast", "").strip()
    
    if not text:
        bot.send_message(
            message.chat.id,
            "❌ <b>Usage:</b>\n/broadcast [MESSAGE]"
        )
        return
    
    sent_count = 0
    for user_id in db.all_users:
        try:
            bot.send_message(
                user_id,
                f"📢 <b>Announcement:</b>\n\n{text}",
                parse_mode="HTML"
            )
            sent_count += 1
        except Exception as e:
            print(f"Error sending to {user_id}: {e}")
    
    bot.send_message(
        message.chat.id,
        f"✅ Broadcast sent to <b>{sent_count}</b> users.",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["set_price"])
def set_price(message):
    """Admin: Set item price"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            raise ValueError
        
        item = parts[1].lower()
        price = int(parts[2])
        
        if item not in db.prices or price <= 0:
            raise ValueError
        
        db.prices[item] = price
        
        bot.send_message(
            message.chat.id,
            f"✅ <b>{item.capitalize()} price updated to {price} ETB</b>",
            parse_mode="HTML"
        )
    
    except (ValueError, IndexError):
        bot.send_message(
            message.chat.id,
            "❌ <b>Usage:</b>\n/set_price [normal/special/super] [price]"
        )

@bot.message_handler(commands=["add_bank"])
def add_bank_account(message):
    """Admin: Add bank account"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split(" ", 3)
        if len(parts) < 4:
            raise ValueError
        
        name = parts[1]
        acc = parts[2]
        owner = parts[3]
        
        db.bank_accounts[name.lower()] = {
            "name": name,
            "acc": acc,
            "owner": owner
        }
        
        bot.send_message(
            message.chat.id,
            f"✅ <b>Bank '{name}' added successfully.</b>",
            parse_mode="HTML"
        )
    
    except (ValueError, IndexError):
        bot.send_message(
            message.chat.id,
            "❌ <b>Usage:</b>\n/add_bank [NAME] [ACCOUNT] [OWNER]"
        )

@bot.message_handler(commands=["add_delivery"])
def add_delivery_guy(message):
    """Admin: Add delivery person"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        delivery_id = int(message.text.split()[1])
        
        if delivery_id not in db.delivery_guys:
            db.delivery_guys.append(delivery_id)
        
        bot.send_message(
            message.chat.id,
            f"✅ <b>Delivery person (ID: {delivery_id}) added.</b>",
            parse_mode="HTML"
        )
    
    except (ValueError, IndexError):
        bot.send_message(
            message.chat.id,
            "❌ <b>Usage:</b>\n/add_delivery [USER_ID]"
        )

@bot.message_handler(commands=["list_delivery"])
def list_delivery_guys(message):
    """Admin: List all delivery persons"""
    if not is_admin(message.from_user.id):
        return
    
    if not db.delivery_guys:
        bot.send_message(message.chat.id, "No delivery persons added yet.")
        return
    
    text = "<b>🚚 Delivery Persons:</b>\n\n"
    for idx, d_id in enumerate(db.delivery_guys, 1):
        text += f"{idx}. ID: <code>{d_id}</code>\n"
    
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# =========================================================
# 11. CALLBACK HANDLERS
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    """Handle subscription check button"""
    user_id = call.from_user.id
    
    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ Thank you for joining!")
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        
        show_main_menu(call.message)
    
    else:
        bot.answer_callback_query(
            call.id,
            "❌ You still haven't joined the channel!",
            show_alert=True
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("y_"))
def admin_accept_order(call):
    """Handle admin accepting order"""
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "❌ Admin only!",
            show_alert=True
        )
        return
    
    try:
        data = call.data.split("_")
        user_id = int(data[1])
        total = int(data[2])
        
        order = db.orders_db.get(user_id)
        
        if not order:
            bot.answer_callback_query(call.id, "❌ Order not found.", show_alert=True)
            return
        
        if order["status"] != "pending":
            bot.answer_callback_query(
                call.id,
                "⚠️ Order already processed.",
                show_alert=True
            )
            return
        
        order["status"] = "accepted"
        db.daily_report["total_sales"] += total
        db.daily_report["orders_count"] += 1
        
        bot.answer_callback_query(call.id, "✅ Order accepted!")
        
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass
        
        # Handle based on service type
        if order["usage"] == "Dine-in":
            markup = types.InlineKeyboardMarkup()
            markup.add(create_success_button("Received", f"finish_{user_id}"))
            
            bot.send_message(
                user_id,
                f"🎫 <b>Receipt</b>\n"
                f"💰 Total: {total} ETB\n"
                f"⏰ Time: {datetime.datetime.now().strftime('%H:%M')}\n\n"
                "Show this receipt at the hotel counter.",
                reply_markup=markup,
                parse_mode="HTML"
            )
        
        else:  # Takeaway - find delivery
            bot.send_message(
                user_id,
                "🥳 <b>Your Order is Ready!</b>\n"
                "🚲 Finding delivery driver...",
                parse_mode="HTML"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(create_success_button("Accept Delivery", f"t_{user_id}"))
            
            for delivery_id in db.delivery_guys:
                try:
                    sent = bot.send_message(
                        delivery_id,
                        f"🚚 <b>New Delivery Order!</b>\n\n"
                        f"📦 Item: {order['item'].capitalize()} x{order['qty']}\n"
                        f"💰 Amount: {total} ETB\n"
                        f"📍 Location: {order['location']}\n"
                        f"👤 User: @{call.from_user.username or 'User'}",
                        reply_markup=markup,
                        parse_mode="HTML"
                    )
                    db.active_delivery_msgs[user_id] = sent.message_id
                
                except Exception as e:
                    print(f"Error notifying delivery {delivery_id}: {e}")
    
    except (ValueError, IndexError) as e:
        print(f"Error in admin_accept_order: {e}")
        bot.answer_callback_query(call.id, "❌ Error processing order.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("n_"))
def admin_reject_order(call):
    """Handle admin rejecting order"""
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "❌ Admin only!",
            show_alert=True
        )
        return
    
    try:
        user_id = int(call.data.split("_")[1])
        
        order = db.orders_db.get(user_id)
        if order:
            order["status"] = "rejected"
        
        bot.answer_callback_query(call.id, "❌ Order rejected.")
        
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass
        
        bot.send_message(
            user_id,
            "❌ <b>Your order was rejected or sold out.</b>\n\n"
            "Please try again later or contact admin.",
            parse_mode="HTML"
        )
    
    except (ValueError, IndexError):
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("t_"))
def delivery_accept_order(call):
    """Handle delivery person accepting order"""
    delivery_id = call.from_user.id
    
    if delivery_id not in db.delivery_guys:
        bot.answer_callback_query(
            call.id,
            "❌ You are not registered as delivery person.",
            show_alert=True
        )
        return
    
    try:
        user_id = int(call.data.split("_")[1])
        order = db.orders_db.get(user_id)
        
        if not order or order["status"] != "accepted":
            bot.answer_callback_query(
                call.id,
                "⚠️ Order unavailable.",
                show_alert=True
            )
            return
        
        if order["assigned_to"] is not None:
            bot.answer_callback_query(
                call.id,
                "⚠️ Order already assigned to another driver.",
                show_alert=True
            )
            return
        
        order["assigned_to"] = delivery_id
        order["status"] = "delivery"
        
        bot.answer_callback_query(call.id, "✅ Delivery accepted!")
        
        bot.send_message(
            user_id,
            "🚲 <b>Delivery Accepted!</b>\n"
            "Your order is on the way. 🛵",
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
    
    except (ValueError, IndexError):
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("finish"))
def mark_order_finished(call):
    """Handle marking order as finished"""
    try:
        data = call.data.split("_")
        if len(data) > 1:
            user_id = int(data[1])
        else:
            user_id = call.from_user.id
        
        order = db.orders_db.get(user_id)
        if order:
            order["status"] = "finished"
        
        bot.answer_callback_query(call.id, "✅ Order completed!")
        
        bot.send_message(
            call.from_user.id,
            "✅ <b>Thank You!</b>\n\n"
            "Your order has been completed successfully.\n"
            "We appreciate your business! 🙏",
            parse_mode="HTML"
        )
    
    except (ValueError, IndexError):
        pass

# =========================================================
# 12. FLASK WEBHOOK ROUTES
# =========================================================

@app.route("/", defaults={"path": ""}, methods=["POST", "GET"])
@app.route("/<path:path>", methods=["POST", "GET"])
def webhook(path):
    """Handle Telegram webhook"""
    if request.method == "POST":
        if request.is_json:
            try:
                json_data = request.get_data().decode("utf-8")
                update = telebot.types.Update.de_json(json_data)
                bot.process_new_updates([update])
                return "", 200
            except Exception as e:
                print(f"Webhook error: {e}")
                return "Error processing update", 400
        
        return "Invalid content type", 400
    
    return "🤖 Arefa Bot is active and running!", 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "bot_name": "Arefa Food Bot",
        "users": len(db.all_users),
        "orders": len(db.orders_db)
    }, 200

# =========================================================
# 13. ERROR HANDLERS
# =========================================================

@bot.message_handler(func=lambda m: True)
def handle_unknown(message):
    """Handle unknown messages"""
    if message.text and not message.text.startswith("/"):
        bot.send_message(
            message.chat.id,
            "❌ <b>Command not recognized.</b>\n\n"
            "Please use the main menu or /start to begin.",
            parse_mode="HTML"
        )

# =========================================================
# 14. MAIN EXECUTION
# =========================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting bot on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
