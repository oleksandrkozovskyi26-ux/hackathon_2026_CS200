import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

from schemas import Member

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise Exception('BOT_TOKEN is not found')

bot = telebot.TeleBot(BOT_TOKEN)

with open("users.json", "r", encoding='utf-8') as file:
    users = json.load(file)

@bot.message_handler(commands=['start'])
def start_message(message):
    if not users.get(message.from_user.id):
        bot.send_message(message.chat.id,
                         "На жаль, ви не зареєстровані в боті на данний момент. Деталі реєстрації нижче")
        bot.send_message(message.chat.id,
                         "Для реєстрації введіть свої прізвище та ім'я в наступному форматі (без лапок):\n '/register ПРІЗВИЩЕ ІМ'Я' (Приклад, '/register Бачурін Єгор')")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_on_duty = types.InlineKeyboardButton(text="Таблиця Чергування", callback_data="table_on_duty")
    btn_check_my_duty = types.InlineKeyboardButton(text="Перевірити коли моє чергування", callback_data="check_my_duty")
    btn_taxes = types.InlineKeyboardButton(text="Таблиця данини за Колівінг", callback_data="get_taxes")

    markup.add(btn_on_duty, btn_check_my_duty)
    markup.add(btn_taxes)

    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"Вітаємо ({users[user_id]["surname"]} {users[user_id]["name"]}) в боті колівінгу #########.")
    bot.send_message(message.chat.id, "Оберіть що бажаєте зробити:", reply_markup=markup)

@bot.message_handler(commands=['register'])
def start_message(message):
    text = message.text.split()
    user_id = message.from_user.id
    if len(text) != 3 or users.get(user_id):
        bot.send_message(message.chat.id, "Ви або зареєстровані, або ввели некоректні дані.")
    else:
        users[user_id] = {"surname": text[1], "name": text[2]}
        with open("users.json", "w", encoding="utf-8") as file:
            json.dump(users, file)
        bot.send_message(message.chat.id, "Вас успішно зареєстровано.")

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons_on_click(call):
    print("hi")

if __name__ == '__main__':
    bot.infinity_polling()

