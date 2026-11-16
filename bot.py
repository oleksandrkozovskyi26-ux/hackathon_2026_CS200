import os
import telebot
import html
from telebot import types
from dotenv import load_dotenv
from datetime import date, timedelta

from service import ColivingBudgetService
from duty_service import ColivingDutyService
from schemas import *

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

def format_duty_dates(dates: list[date]) -> list[str]:
    """Сортує дати та об'єднує послідовні дні в діапазони (наприклад, 01-03.09)."""
    if not dates:
        return []

    sorted_dates = sorted(set(dates))  # прибираємо дублікати та сортуємо
    ranges = []
    start = end = sorted_dates[0]

    for current in sorted_dates[1:]:
        if current == end + timedelta(days=1):
            end = current
        else:
            ranges.append((start, end))
            start = end = current
    ranges.append((start, end))

    formatted = []
    for s, e in ranges:
        if s == e:
            formatted.append(s.strftime("%d.%m"))
        elif s.month == e.month:
            formatted.append(f"{s.strftime('%d')}-{e.strftime('%d.%m')}")
        else:
            formatted.append(f"{s.strftime('%d.%m')}-{e.strftime('%d.%m')}")

    return formatted

def build_duties_table(members, today_duty=None) -> str:
    rows = []

    for member in members:
        initial = f"{member.first_name[0]}." if member.first_name else ""
        short_name = f"{member.last_name} {initial}".strip()

        prefix = "*" if (today_duty and member == today_duty) else " "
        display_name = html.escape(f"{prefix}{short_name}")

        date_chunks = format_duty_dates(member.duty_dates)
        dates_str = ", ".join(date_chunks) if date_chunks else "—"

        rows.append((display_name, dates_str))

    # Автоматична ширина під найдовше прізвище (макс. 16 символів)
    w_name = min(16, max((len(r[0]) for r in rows), default=10))

    lines = []
    for name, dates_str in rows:
        clean_name = name[:w_name]
        lines.append(f"{clean_name:<{w_name}} │ {dates_str}")

    table_text = "\n".join(lines)

    header_info = "<b>Графік чергувань:</b>\n"
    if today_duty:
        t_first = today_duty.first_name or ""
        t_name = html.escape(f"{today_duty.last_name} {t_first}".strip())
        header_info += f"Сьогодні (*): <b>{t_name}</b>\n"

    return f"{header_info}<pre>{table_text}</pre>"

import html
from schemas import ColivingInfo, SotnykContact, WifiAccessPoint


def format_coliving_info(info: ColivingInfo) -> str:
    """Форматує довідкову інформацію про колівінг для виводу в Telegram (HTML)."""
    blocks: list[str] = []

    # 1. Заголовок
    blocks.append(f"🏠 <b>{html.escape(info.coliving_name)}</b>")

    # 2. Компактна таблиця основних параметрів
    meta_rows = [
        ("Внесок", f"{info.monthly_fee_uah} грн/міс"),
        ("Дедлайн", f"до {info.payment_deadline_day}-го числа"),
        ("Сотник", _format_sotnyk(info.sotnyk)),
    ]
    if info.sotnyk.phone:
        meta_rows.append(("Телефон", info.sotnyk.phone))

    w_key = max(len(r[0]) for r in meta_rows)
    table_lines = [f"{k:<{w_key}} │ {v}" for k, v in meta_rows]
    blocks.append(f"<pre>{html.escape(chr(10).join(table_lines))}</pre>")

    # 3. Посилання на банку
    if info.jar_url:
        safe_url = html.escape(info.jar_url, quote=True)
        blocks.append(f'💳 <b>Банка для оплати:</b> <a href="{safe_url}">Поповнити</a>')

    # 4. Точки Wi-Fi (з урахуванням location та копіюванням пароля в 1 тап)
    if info.wifi_points:
        wifi_lines = ["📶 <b>Wi-Fi:</b>"]
        for wp in info.wifi_points:
            wifi_lines.append(_format_wifi_point(wp))
        blocks.append("\n".join(wifi_lines))

    # 5. Чекліст чергового
    if info.duty_checklist:
        duty_lines = ["🧹 <b>Чекліст чергового:</b>"]
        for item in info.duty_checklist:
            duty_lines.append(f"• {html.escape(item)}")
        blocks.append("\n".join(duty_lines))

    # 6. Правила колівінгу
    if info.house_rules:
        rules_lines = ["📜 <b>Правила колівінгу:</b>"]
        for idx, rule in enumerate(info.house_rules, start=1):
            rules_lines.append(f"{idx}. {html.escape(rule)}")
        blocks.append("\n".join(rules_lines))

    return "\n\n".join(blocks)


def _format_sotnyk(sotnyk: SotnykContact) -> str:
    if sotnyk.telegram_username:
        username = sotnyk.telegram_username.lstrip("@")
        return f"{sotnyk.full_name} (@{username})"
    return sotnyk.full_name


def _format_wifi_point(wp: WifiAccessPoint) -> str:
    ssid = html.escape(wp.ssid)
    password = html.escape(wp.password)
    if wp.location:
        location = html.escape(wp.location)
        return f"• <b>{location}</b> ({ssid}): <code>{password}</code>"
    return f"• {ssid}: <code>{password}</code>"


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
    btn_table_taxes = types.InlineKeyboardButton(text="Таблиця данини за Колівінг (Хто заплатив)", callback_data="get_taxes_table")
    btn_taxes = types.InlineKeyboardButton(text="Чи заплатив я за колівінг?", callback_data="get_my_taxes")

    markup.add(btn_coliving_info, btn_on_duty, btn_table_taxes, btn_taxes)

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
        bot.send_message(call.message.chat.id, "Сунична 136"
                         "")
    elif call.data == "get_my_taxes":
        if member and member.is_paid_current_month:
            bot.send_message(call.message.chat.id, f"Так, ви заплатили✅")
        else:
            bot.send_message(call.message.chat.id, f"Ні, ви не заплатили. Потрібно заплатити якнайшвидше❌")
    elif call.data == "get_taxes_table":
        members = budget.get_all_members()
        text = build_members_table(members)
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    elif call.data == "table_on_duty":
        members = duty.get_all_members_with_duties()
        today_duty = duty.get_today_duty_member()

        if not members:
            bot.send_message(call.message.chat.id, "Список чергувань порожній.")
            return

        text = build_duties_table(members, today_duty)
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")

if __name__ == '__main__':
    bot.infinity_polling()

