import os
import telebot
import html
from telebot import types
from dotenv import load_dotenv

from service import ColivingBudgetService
from duty_service import ColivingDutyService

budget = ColivingBudgetService()
duty = ColivingDutyService()

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise Exception('BOT_TOKEN is not found')

bot = telebot.TeleBot(BOT_TOKEN)


def build_members_table(members) -> str:
    rows = []
    for member in members:
        # Екрануємо символи HTML, щоб уникнути помилок парсингу Telegram
        full_name = html.escape(f"{member.last_name} {member.first_name}".strip())
        paid_status = "Так" if member.is_paid_current_month else "Ні"
        rows.append((full_name, paid_status))

    h1, h2 = "Колівер", "Заплатив"

    # Автоматична ширина під найдовше ім'я
    w1 = max([len(h1)] + [len(r[0]) for r in rows])
    w2 = max(len(h2), 8)

    top = f"┌{'─' * (w1 + 2)}┬{'─' * (w2 + 2)}┐"
    header = f"│ {h1:<{w1}} │ {h2:^{w2}} │"
    middle = f"├{'─' * (w1 + 2)}┼{'─' * (w2 + 2)}┤"
    bottom = f"└{'─' * (w1 + 2)}┴{'─' * (w2 + 2)}┘"

    lines = [top, header, middle]
    for name, status in rows:
        lines.append(f"│ {name:<{w1}} │ {status:^{w2}} │")
    lines.append(bottom)

    table_text = "\n".join(lines)

    # Обгортаємо в <pre> для збереження моноширинного форматування
    return f"<b>Статус оплат:</b>\n<pre>{table_text}</pre>"

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    member = budget.get_by_telegram_id(user_id)
    if not member:
        bot.send_message(message.chat.id,
                         "На жаль, ви не зареєстровані в боті на данний момент. Деталі реєстрації нижче")
        bot.send_message(message.chat.id,
                         "Для реєстрації введіть свої прізвище та ім'я в наступному форматі (без лапок):\n '/register ПРІЗВИЩЕ ІМ'Я' (Приклад, '/register Бачурін Єгор')")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_coliving_info = types.InlineKeyboardButton(text="Інформація про колівінг", callback_data="coliving_info")
    btn_on_duty = types.InlineKeyboardButton(text="Таблиця Чергування", callback_data="table_on_duty")
    btn_check_my_duty = types.InlineKeyboardButton(text="Перевірити коли моє чергування", callback_data="check_my_duty")
    btn_table_taxes = types.InlineKeyboardButton(text="Таблиця данини за Колівінг (Хто заплатив)", callback_data="get_taxes_table")
    btn_taxes = types.InlineKeyboardButton(text="Чи заплатив я за колівінг?", callback_data="get_my_taxes")

    markup.add(btn_coliving_info, btn_on_duty, btn_check_my_duty, btn_table_taxes, btn_taxes)

    bot.send_message(message.chat.id, f"Вітаємо ({member.last_name} {member.first_name}) в боті колівінгу #########.")
    bot.send_message(message.chat.id, "Оберіть що бажаєте зробити:", reply_markup=markup)


@bot.message_handler(commands=['register'])
def start_message(message):
    text = message.text.split()
    user_id = message.from_user.id
    if len(text) != 3 or budget.get_by_telegram_id(user_id):
        bot.send_message(message.chat.id, "Ви або зареєстровані, або ввели некоректні дані.")
    else:
        budget.register_user(user_id, last_name=text[1], first_name=text[2])
        bot.send_message(message.chat.id, "Вас успішно зареєстровано.")

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons_on_click(call):
    user_id = call.from_user.id
    member = budget.get_by_telegram_id(user_id)
    if call.data == "coliving_info":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Інформація про колівінг"
                         "")
    elif call.data == "get_my_taxes":
        bot.answer_callback_query(call.id)
        if member and member.is_paid_current_month:
            bot.send_message(call.message.chat.id, f"Так, ви заплатили✅")
        else:
            bot.send_message(call.message.chat.id, f"Ні, ви не заплатили. Потрібно заплатити якнайшвидше❌")
    elif call.data == "get_taxes_table":
        members = budget.get_all_members()
        text = build_members_table(members)
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
if __name__ == '__main__':
    bot.infinity_polling()

