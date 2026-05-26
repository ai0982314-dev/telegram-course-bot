import logging
import asyncio
import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =========================================
# CONFIG (এখানে আপনার তথ্য বসান)
# =========================================
BOT_TOKEN = "YOUR_BOT_TOKEN"  # @BotFather থেকে পাওয়া টোকেন
ADMIN_ID = 123456789         # আপনার টেলিগ্রাম আইডি (যেমন: 56849302)
FIREBASE_URL = "https://courseify-bot-default-rtdb.asia-southeast1.firebasedatabase.app"
CHANNEL_LINK = "https://t.me/YOUR_CHANNEL"

# =========================================
# LOGGING
# =========================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# =========================================
# FIREBASE FUNCTIONS
# =========================================
def save_user(user_id, name):
    data = {"name": name}
    requests.put(f"{FIREBASE_URL}/users/{user_id}.json", json=data)

def save_payment(user_id, data):
    requests.put(f"{FIREBASE_URL}/payments/{user_id}.json", json=data)

def get_users():
    users = requests.get(f"{FIREBASE_URL}/users.json").json()
    return users

# =========================================
# STATES
# =========================================
broadcast_mode = {}

# =========================================
# COMMAND HANDLERS
# =========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.first_name)

    keyboard = [["📚 Buy Course"], ["💳 Payment"], ["📞 Support"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = """
🎓 Welcome To HSC Learning Bot!

✅ Buy HSC Courses
✅ Get PDFs & Notes
✅ Premium Channel Access
✅ Contact Support Easily

🚀 Start Learning Today
"""
    await update.message.reply_text(text, reply_markup=reply_markup)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You Are Not Admin")
        return

    keyboard = [
        ["📊 Dashboard"],
        ["💰 Payments", "👥 Users"],
        ["📢 Broadcast"],
        ["📚 Subjects", "🔄 Cycles"],
        ["📖 Chapters", "📺 Channels"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("⚙️ ADMIN PANEL", reply_markup=reply_markup)

# =========================================
# MESSAGE HANDLER
# =========================================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text == "📊 Dashboard":
        users = get_users()
        total_users = len(users) if users else 0
        msg = f"📊 DASHBOARD\n\n👥 Users: {total_users}\n\n🔥 Bot Status: ONLINE\n\n✅ Firebase Connected"
        await update.message.reply_text(msg)

    elif text == "📚 Buy Course":
        await update.message.reply_text("📚 Available Courses\n\n1️⃣ Physics\n2️⃣ Chemistry\n3️⃣ Math\n4️⃣ Biology\n\n💳 Send Payment Screenshot After Payment")

    elif text == "💳 Payment":
        await update.message.reply_text("💰 Send Payment Screenshot\n\n📝 Also Send Transaction ID")

    elif text == "📞 Support":
        await update.message.reply_text("📞 Contact Admin")

    elif text == "👥 Users":
        users = get_users()
        total = len(users) if users else 0
        await update.message.reply_text(f"👥 Total Users: {total}")

    elif text == "💰 Payments":
        await update.message.reply_text("💰 PAYMENT PANEL\n\n✅ Screenshot Receive Active\n✅ Payment Save Active")

    elif text == "📚 Subjects":
        await update.message.reply_text("📚 SUBJECT MANAGEMENT\n\n✅ Add Subject\n✅ Edit Subject\n✅ Delete Subject")

    elif text == "🔄 Cycles":
        await update.message.reply_text("🔄 CYCLE MANAGEMENT\n\n✅ Add Cycle\n✅ Edit Cycle\n✅ Delete Cycle")

    elif text == "📖 Chapters":
        await update.message.reply_text("📖 CHAPTER MANAGEMENT\n\n✅ Add Chapter\n✅ Edit Chapter\n✅ Delete Chapter")

    elif text == "📺 Channels":
        await update.message.reply_text("📺 CHANNEL MANAGEMENT\n\n✅ Add Channel\n✅ Delete Channel")

    elif text == "📢 Broadcast":
        if user.id != ADMIN_ID:
            return
        broadcast_mode[user.id] = True
        await update.message.reply_text("📢 Send Broadcast Message")

    elif user.id in broadcast_mode:
        users = get_users()
        success = 0
        if users:
            for uid in users:
                try:
                    await context.bot.send_message(chat_id=int(uid), text=text)
                    success += 1
                except:
                    pass
        await update.message.reply_text(f"✅ Broadcast Sent To {success} Users")
        del broadcast_mode[user.id]

    else:
        data = {"name": user.first_name, "message": text}
        save_payment(user.id, data)

# =========================================
# PHOTO HANDLER
# =========================================
async def photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1].file_id

    caption = f"💰 NEW PAYMENT\n\n👤 Name: {user.first_name}\n🆔 ID: {user.id}\n\n✅ Screenshot Received"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption)

    save_payment(user.id, {"name": user.first_name, "photo": photo})
    await update.message.reply_text(f"✅ Payment Submitted\n\n⏳ Wait For Admin Approval\n\n🔗 Channel Access After Approval:\n{CHANNEL_LINK}")

# =========================================
# APPROVE / REJECT
# =========================================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(chat_id=user_id, text=f"✅ Payment Approved\n\n🎉 Welcome To Premium Access\n\n🔗 Join Channel:\n{CHANNEL_LINK}")
        await update.message.reply_text("✅ User Approved")
    except:
        await update.message.reply_text("❌ Usage: /approve USER_ID")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(chat_id=user_id, text="❌ Payment Rejected\n\n📞 Contact Admin")
        await update.message.reply_text("❌ User Rejected")
    except:
        await update.message.reply_text("❌ Usage: /reject USER_ID")

# =========================================
# MAIN
# =========================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    app.add_handler(MessageHandler(filters.PHOTO, photos))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("🔥 BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
