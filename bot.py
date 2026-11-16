import os
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise Exception('BOT_TOKEN is not found')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_on_duty = types.InlineKeyboardButton(text="Таблиця Чергування", callback_data="table_on_duty")
    btn_check_my_duty = types.InlineKeyboardButton(text="Перевірити коли моє чергування", callback_data="check_my_duty")
    btn_taxes = types.InlineKeyboardButton(text="Таблиця данини за Колівінг", callback_data="get_taxes")
    btn_admin_panel = types.InlineKeyboardButton(text="Відкрити адмін панель", callback_data="admin_panel")

    markup.add(btn_on_duty, btn_check_my_duty)
    markup.add(btn_taxes, btn_admin_panel)
    bot.send_message(message.chat.id, "Вітаємо в боті колівінгу ######### (Назва колівінгу прихована до презентації).")
    bot.send_message(message.chat.id, "Оберіть що бажаєте зробити:", reply_markup=markup)

if __name__ == '__main__':
    bot.infinity_polling()

