import telebot
from telebot import types
import json, os
from datetime import datetime

# --- НАСТРОЙКИ ТРЕКЕР-БОТА ---
TOKEN = "8914754146:AAH3WF5wVgNtvfXpomuVCY1KoZ9VrBcGPcw"
ADMIN_ID = 9158877731  # Твой ID (кто может нажимать «Оплатить»)
GROUP_ID = -1003935415154  # ID группы, куда летят профиты
PROFIT_TOPIC_ID = 3  # ID ТОПИКА (вкладки) в группе

WORKER_PERCENT = 80      # Процент воркера
STAR_TO_USD = 0.02       # Курс звезды в долларах

# ID твоего Оффер-бота (aiogram), чтобы Трекер слушал только его
OFFER_BOT_ID = 9056825852  # ЗАМЕНИ НА ID ОФФЕР-БОТА

DB = "team.json"

# Создаем базу, если ее нет
if not os.path.exists(DB):
    json.dump({"wallets": {}, "names": {}, "paid": []}, open(DB, "w", encoding="utf-8"))

db = json.load(open(DB, encoding="utf-8"))
bot = telebot.TeleBot(TOKEN)

def save():
    json.dump(db, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- /start: Сохранение кошелька и данных воркера ---
@bot.message_handler(commands=["start"])
def start(m):
    uid = str(m.from_user.id)
    
    # Сохраняем имя и юзернейм воркера для дальнейших отчетов
    db["names"][uid] = {
        "username": m.from_user.username or "нет_юзернейма",
        "first_name": m.from_user.first_name or "Воркер"
    }
    save()

    if uid in db["wallets"]:
        bot.send_message(
            m.chat.id, 
            f"👛 Твой кошелёк уже сохранён:\n{db['wallets'][uid]}\n\nОтправь новый, чтобы заменить:"
        )
        msg = bot.send_message(m.chat.id, "...")
        bot.register_next_step_handler(msg, lambda mm: save_wallet(mm, True))
    else:
        msg = bot.send_message(m.chat.id, "Отправь свой TON-кошелёк для выплат:")
        bot.register_next_step_handler(msg, save_wallet)

def save_wallet(m, replace=False):
    w = m.text.strip() if m.text else ""
    if not w or w.startswith("/"):
        bot.send_message(m.chat.id, "Это не похоже на кошелёк, отправь ещё раз /start")
        return
    db["wallets"][str(m.from_user.id)] = w
    save()
    bot.send_message(m.chat.id, f"✅ Кошелёк сохранён:\n{w}")

# --- ПРИЕМ ПРОФИТА ОТ ОФФЕР-БОТА ---
@bot.message_handler(commands=["add_profit"])
def add_profit(m):
    # Проверяем, что команду прислал именно Оффер-бот
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
    
    # Формируем ссылку на NFT
    link = f"https://t.me/nft/{base_name}-{gift_id}"
    usd = round(stars * STAR_TO_USD, 2)
    pay = round(usd * WORKER_PERCENT / 100, 2)
    
    # Получаем данные воркера из базы
    worker_info = db["names"].get(worker_id, {})
    worker_name = worker_info.get("first_name", "Неизвестный")
    worker_username = worker_info.get("username", "нет_юзернейма")
    wallet = db["wallets"].get(worker_id, "не указан (пусть напишет /start)")
    
    # Формируем красивый отчет
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
    
    # Отправляем в указанный топик группы
    try:
        bot.send_message(
            GROUP_ID, 
            text, 
            parse_mode="HTML", 
            reply_markup=kb, 
            message_thread_id=PROFIT_TOPIC_ID
        )
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")

# --- КНОПКА «ОПЛАТИТЬ» ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("pay:"))
def pay(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "Оплачивать может только админ")
        return
        
    _, uid, amount = c.data.split(":")
    
    # Записываем выплату в базу
    db["paid"].append({
        "uid": uid, 
        "sum": float(amount),
        "date": datetime.now().strftime("%d.%m %H:%M")
    })
    save()
    
    # Меняем текст сообщения, добавляя плашку ОПЛАЧЕНО
    new_text = c.message.text + "\n\n✅ <b>ОПЛАЧЕНО</b>"
    try:
        bot.edit_message_text(
            new_text,
            GROUP_ID, 
            c.message.message_id, 
            parse_mode="HTML"
        )
    except Exception:
        pass # Если текст не изменился, игнорируем ошибку
    bot.answer_callback_query(c.id, "Отмечено как оплачено")

# --- Запуск ---
if __name__ == "__main__":
    print("Трекер-бот запущен и ожидает данные от Оффер-бота...")
    bot.infinity_polling()
