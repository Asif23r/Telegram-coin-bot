import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

BOT_TOKEN = "your bot token"
OWNER_ID = your telegram chatid # Replace with your numeric Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)

user_balances = {}
user_claims = set()
coin_requests = {}  # user_id: chat_id

# Utils
def add_vartul(user_id, amount):
    user_balances[user_id] = user_balances.get(user_id, 0) + amount

def get_balance(user_id):
    return user_balances.get(user_id, 0)

def transfer_vartul(from_id, to_id, amount):
    if get_balance(from_id) < amount:
        return False
    add_vartul(from_id, -amount)
    add_vartul(to_id, amount)
    return True

# Bot Joined in Group
@bot.my_chat_member_handler()
def when_added(event):
    if event.new_chat_member.user.id == bot.get_me().id:
        user_id = event.from_user.id
        if user_id not in user_claims:
            user_claims.add(user_id)
            add_vartul(user_id, 100)
            bot.send_message(user_id, "🎉 You've received 100 🪙 for adding me to a group!")

# Reply with "thank you" earns coins
@bot.message_handler(func=lambda m: m.reply_to_message and 'thank' in m.text.lower())
def thank_you_handler(message):
    user_id = message.from_user.id
    add_vartul(user_id, 2)
    bot.reply_to(message, "💖 Thanks for being kind! You received 2 🪙")

# Handle when coinless user replies
@bot.message_handler(func=lambda m: m.reply_to_message and 'thank' in m.text.lower())
def thank_you_zero_handler(message):
    user_id = message.from_user.id
    if get_balance(user_id) == 0:
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🎁 Request Coins", callback_data=f"req:{user_id}"),
            InlineKeyboardButton("➕ Add Me to Group", url="https://t.me/@raazx_1bot?startgroup=true")
        )
        bot.reply_to(message, "⚠️ You don't have coins. Choose an option:", reply_markup=markup)

# Handle coin request button
@bot.callback_query_handler(func=lambda call: call.data.startswith("req:"))
def handle_coin_request(call):
    uid = call.from_user.id
    if uid in coin_requests:
        bot.answer_callback_query(call.id, "Already requested.")
        return

    coin_requests[uid] = call.message.chat.id
    bot.send_message(OWNER_ID, f"🟡 {call.from_user.first_name} (@{call.from_user.username or 'no_username'}) is requesting 20 coins.",
                     reply_markup=InlineKeyboardMarkup().row(
                         InlineKeyboardButton("✅ Approve", callback_data=f"approve:{uid}")
                     ))
    bot.answer_callback_query(call.id, "Request sent to owner!")

# Owner approves request
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve:"))
def approve_request(call):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "Not authorized.")
        return

    uid = int(call.data.split(":")[1])
    add_vartul(uid, 20)
    chat_id = coin_requests.pop(uid, None)
    if chat_id:
        bot.send_message(chat_id, "✅ You received 20 🪙 from the owner!")
    bot.answer_callback_query(call.id, "Coins sent.")

# /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"""👋 Hello {message.from_user.first_name}!

I am *RaazXBot* – your smart group assistant powered by coins 🪙

Features:
• 100 🪙 when you add me to a group
• Earn 2 🪙 when you say "thank you" in replies
• Gift coins to others
• Request coins from owner

Type /help to see all commands.
""", parse_mode="Markdown")

# /help
@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, """
📜 *Commands:*
/wallet – Show your balance
/gift <amount> – Gift coins (reply to user)
/addmoney <uid> <amt> – Add coins (owner)
/top – Show top 5 users
""", parse_mode="Markdown")

# /wallet
@bot.message_handler(commands=["wallet"])
def wallet(message):
    bal = get_balance(message.from_user.id)
    bot.reply_to(message, f"💰 You have {bal} 🪙")

# /gift
@bot.message_handler(commands=["gift"])
def gift(message):
    if not message.reply_to_message or len(message.text.split()) != 2:
        bot.reply_to(message, "⚠️ Reply to someone with /gift <amount>")
        return
    try:
        amount = int(message.text.split()[1])
        if amount <= 0:
            raise ValueError
        from_id = message.from_user.id
        to_id = message.reply_to_message.from_user.id
        if from_id == to_id:
            bot.reply_to(message, "❌ You can't gift yourself.")
            return
        if transfer_vartul(from_id, to_id, amount):
            bot.reply_to(message, f"🎁 Gifted {amount} 🪙")
        else:
            bot.reply_to(message, "❌ Not enough balance.")
    except:
        bot.reply_to(message, "❌ Invalid amount.")

# /addmoney
@bot.message_handler(commands=["addmoney"])
def addmoney(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Owner only.")
        return
    try:
        _, uid, amt = message.text.split()
        add_vartul(int(uid), int(amt))
        bot.reply_to(message, "✅ Coins added.")
    except:
        bot.reply_to(message, "⚠️ Usage: /addmoney <user_id> <amount>")

# /top
@bot.message_handler(commands=["top"])
def top(message):
    if not user_balances:
        bot.reply_to(message, "No data.")
        return
    top_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)[:5]
    msg = "🏆 *Top Coin Holders:*\n\n"
    for i, (uid, bal) in enumerate(top_users, 1):
        msg += f"{i}. ID `{uid}` — {bal} 🪙\n"
    bot.reply_to(message, msg, parse_mode="Markdown")

# --- Run ---
print("Bot is running...")
bot.infinity_polling()