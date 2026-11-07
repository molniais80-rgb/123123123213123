import telebot
from telebot import types
import json, os
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN = "8914754146:AAH3WF5wVgNtvfXpomuVCY1KoZ9VrBcGPcw"
ADMIN_ID = 9158877731
GROUP_ID = -1003935415154
PROFIT_TOPIC_ID = 3 

# Ссылки
OFFER_BOT_USERNAME = "FakeOffer122323Bot"  # Юзернейм твоего оффер-бота
TEAM_LINK = "https://t.me/+JLRzlfSdkM0wYWYx"  # Ссылка на твой Тим

WORKER_PERCENT = 80
STAR_TO_USD = 0.02
OFFER_BOT_ID = 9056825852  # ID Оффер-бота

DB = "team.json"
if not os.path.exists(DB):
    json.dump({"wallets": {}, "names": {}, "paid": []}, open(DB, "w", encoding="utf-8"))
db = json.load(open(DB, encoding="utf-8"))

bot = telebot.TeleBot(TOKEN)

def save():
    json.dump(db, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- КЛАВИАТУРА ГЛАВНОГО МЕНЮ ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Обычные текстовые кнопки (без url)
    btn_profile = types.KeyboardButton("👤 Профиль")
    btn_profits = types.KeyboardButton("💰 Мои профиты")
    btn_wallet = types.KeyboardButton("👛 Кошелёк")
    btn_bots = types.KeyboardButton("🤖 Наши боты")
    btn_team = types.KeyboardButton("👥 Тим")
    
    markup.add(btn_profile, btn_profits)
    markup.add(btn_wallet, btn_bots)
    markup.add(btn_team)
    return markup

# --- /start ---
@bot.message_handler(commands=["start"])
def start(m):
    uid = str(m.from_user.id)
    db["names"][uid] = {
        "username": m.from_user.username or "нет_юзернейма",
        "first_name": m.from_user.first_name or "Воркер"
    }
    save()
    bot.send_message(m.chat.id, "Выбери действие:", reply_markup=main_menu())

# --- ОБРАБОТКА КНОПОК МЕНЮ ---
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def show_profile(m):
    uid = str(m.from_user.id)
    wallet = db["wallets"].get(uid, "не указан")
    name = m.from_user.first_name
    username = f"@{m.from_user.username}" if m.from_user.username else "нет"
    
    text = (f"👤 <b>Твой профиль</b>\n\n"
            f"Имя: {name}\n"
            f"Юзернейм: {username}\n"
            f"ID: <code>{uid}</code>\n"
            f"Кошелёк: <code>{wallet}</code>")
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "💰 Мои профиты")
def show_profits(m):
    uid = str(m.from_user.id)
    my_pays = [p for p in db["paid"] if str(p["uid"]) == uid]
    total = sum(p["sum"] for p in my_pays)
    
    text = (f"💰 <b>Твои профиты</b>\n\n"
            f"Всего профитов: {len(my_pays)}\n"
            f"Заработано: <b>{round(total, 2)}$</b>")
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "👛 Кошелёк")
def ask_wallet(m):
    bot.send_message(m.chat.id, "Отправь свой TON-кошелёк для выплат:")
    bot.register_next_step_handler(m, save_wallet)

def save_wallet(m):
    if m.text in ["👤 Профиль", "💰 Мои профиты", "👛 Кошелёк", "🤖 Наши боты", "👥 Тим"]:
        return 
        
    w = m.text.strip() if m.text else ""
    if not w:
        bot.send_message(m.chat.id, "Это не похоже на кошелёк, попробуй снова /start")
        return
    db["wallets"][str(m.from_user.id)] = w
    save()
    bot.send_message(m.chat.id, f"✅ Кошелёк сохранён:\n<code>{w}</code>", parse_mode="HTML", reply_markup=main_menu())

# --- ОБРАБОТКА ССЫЛОК (Наши боты и Тим) ---
@bot.message_handler(func=lambda message: message.text == "🤖 Наши боты")
def show_bots_link(m):
    # Отправляем Inline-кнопку со ссылкой
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Перейти в Оффер-бот", url=f"https://t.me/{OFFER_BOT_USERNAME}"))
    bot.send_message(m.chat.id, "Нажми на кнопку ниже, чтобы перейти:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "👥 Тим")
def show_team_link(m):
    # Отправляем Inline-кнопку со ссылкой
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Перейти в Тим", url=TEAM_LINK))
    bot.send_message(m.chat.id, "Нажми на кнопку ниже, чтобы перейти:", reply_markup=markup)

# --- ПРИЕМ ПРОФИТА ОТ ОФФЕР-БОТА ---
@bot.message_handler(commands=["add_profit"])
def add_profit(m):
    if m.from_user.id != OFFER_BOT_ID:
        return
        
    args = m.text.split()
    if len(args) < 5:
        return
        
    worker_id = args[1]
    try:
        stars = int(args[2])
    except ValueError:
        stars = 0
        
    base_name = args[3]
    gift_id = args[4]
    
    link = f"https://t.me/nft/{base_name}-{gift_id}"
    usd = round(stars * STAR_TO_USD, 2)
    pay = round(usd * WORKER_PERCENT / 100, 2)
    
    worker_info = db["names"].get(worker_id, {})
    worker_name = worker_info.get("first_name", "Неизвестный")
    worker_username = worker_info.get("username", "нет_юзернейма")
    wallet = db["wallets"].get(worker_id, "не указан")
    
    text = (
        f"📈 <b>НОВЫЙ ПРОФИТ</b>\n\n"
        f"👤 Воркер: <a href='tg://user?id={worker_id}'>{worker_name}</a> (@{worker_username})\n"
        f"🖼 NFT: <a href='{link}'>{base_name} #{gift_id}</a>\n"
        f"⭐ Сумма: {stars} ⭐ (~{usd}$)\n"
        f"💰 Воркеру ({WORKER_PERCENT}%): <b>{pay}$</b>\n"
        f"👛 Кошелек: <code>{wallet}</code>\n"
        f"🕒 {datetime.now().strftime('%d.%m %H:%M')}"
    )

    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("💸 Оплатить", callback_data=f"pay:{worker_id}:{pay}"))
    
    try:
        bot.send_message(GROUP_ID, text, parse_mode="HTML", reply_markup=kb, message_thread_id=PROFIT_TOPIC_ID)
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")

# --- ОПЛАТА ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("pay:"))
def pay(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "Оплачивать может только админ")
        return
        
    _, uid, amount = c.data.split(":")
    db["paid"].append({"uid": uid, "sum": float(amount), "date": datetime.now().strftime("%d.%m %H:%M")})
    save()
    
    new_text = c.message.text + "\n\n✅ <b>ОПЛАЧЕНО</b>"
    try:
        bot.edit_message_text(new_text, GROUP_ID, c.message.message_id, parse_mode="HTML")
    except Exception:
        pass
    bot.answer_callback_query(c.id, "Отмечено как оплачено")

# --- Запуск ---
if __name__ == "__main__":
    print("Трекер-бот запущен...")
    bot.infinity_polling()
