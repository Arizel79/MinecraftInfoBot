import logging

import telebot
from telebot import formatting
from models.config import TOKEN
from models.minecraft_server_info import get_mc_server_info, GetServerInfoError
from random import randint
import time

HELP_TEXT = formatting.hbold("Get Minecraft Servers Information Bot") + "\n\n" + \
            """Я бот, который позволяет получать информацию о серверах Minecraft
            
            Доступные команды:
            /stats IP  информация о сервере
            /help  справка"""


def get_printable_user(from_user):
    usr = from_user
    return f"{usr.first_name}{"" if not usr.last_name else f' {usr.last_name}'} ({f'@{usr.username}, ' if usr.username else ""}{usr.id})"


def get_printable_time():
    return time.strftime("%H:%M.%S %d.%m.%Y", time.localtime())


def write_msg(msg):
    with open("msgs.txt", "a+", encoding="utf-8") as f:
        text = f"[{get_printable_time()}] {msg}"
        f.write(text)
        print(text)


def on_msg(msg):
    write_msg(f"{get_printable_user(msg.from_user)}: {msg.text}")


write_msg("start")


def generate_server_description(address: str) -> str:
    """Описание сервера"""
    try:
        data = get_mc_server_info(address)
        if data["ping"]:
            if len(data['players_list']) > 0:
                pl_list = f"\n• Список игроков: {(', '.join(formatting.hcode(p['name']) for p in data['players_list']) if data['players_list'] else '-')}"
            else:
                pl_list = ""
            return f"""{formatting.hbold(f'Сервер "{address}"')}

• Запрос: {formatting.hcode(address)}
• Цифровой IP: {formatting.hcode(data['address'])}
• Статус: {'🟢Онлайн' if data['is_online'] else "⚫️Оффлайн"}
• Описание: 
{formatting.hpre('\n'.join(data['motd']), language="motd")}
• Версия: {formatting.hcode(data['version'])}
• Онлайн игроков: {data['players']} / {data['max_players']}{pl_list}
"""
        else:
            raise GetServerInfoError(f'Произошла ошибка. Нет ответа от сервера "{address}"')
            # return "Произошла ошибка. Проверьте правильность IP адреса или повторите попытку позже"
    except KeyError as e:
        telebot.logger.error("Missing key in data: %s", str(e))
        return formatting.hbold("⚠️ Ошибка формирования данных")

    except ConnectionError:
        raise GetServerInfoError("Ошибочка APIшки (;")


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message: telebot.types.Message) -> None:
    """Команда /start"""
    on_msg(message)
    bot.send_message(message.chat.id, "Бот запущен! 🚀")


@bot.message_handler(commands=['help'])
def handle_help(message: telebot.types.Message) -> None:
    """Команда /help"""
    on_msg(message)
    bot.send_message(message.chat.id, HELP_TEXT, parse_mode='html')


def send_data(message):
    """Запрос информации о сервере"""
    try:
        args = message.text.split()
        if message.text[0] == "/":
            if len(args) < 2:
                raise ValueError

            ip = args[1]
        else:
            ip = args[0]

        response = generate_server_description(ip)
    except ValueError:
        error_msg = f"{formatting.hbold("Ошибка:")} Не указан IP-адрес сервера!\nПример: /stats mc.example.com"
        bot.reply_to(message, error_msg, parse_mode='html')
    except GetServerInfoError as ex:
        error_msg = f"{formatting.hbold("Ошибка:")} {ex}"
        bot.reply_to(message, error_msg, parse_mode='html')
    except ConnectionError as e:
        bot.reply_to(message, formatting.hbold(f"⚠️ Ошибка подключения: {str(e)}"), parse_mode='html')

    else:
        bot.send_message(message.chat.id, response, parse_mode='html', reply_to_message_id=message.id)


@bot.message_handler(commands=['stats', 'info'])
def handle_stats(message: telebot.types.Message) -> None:
    send_data(message)


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message: telebot.types.Message) -> None:
    on_msg(message)
    if message.text.lower() in {'hello!', 'привет'}:
        bot.reply_to(message, "Привет! 👋")
    else:
        handle_stats(message)


# Обработчик inline-запросов
@bot.inline_handler(lambda query: True)
def query_text(inline_query):
    try:
        write_msg(f"{get_printable_user(inline_query.from_user)} inline: {inline_query.query}")
        query = inline_query.query.rstrip()

        if query == "":
            r1 = telebot.types.InlineQueryResultArticle(
                id=str(randint(0, 10000)),
                title=f"Введите IP Minecraft сервера",
                description="Для получения информации о нём",
                input_message_content=telebot.types.InputTextMessageContent(
                    f"Используйте:\n{'@GetMinecraftInfoBot SERVER-IP'}", parse_mode="html")
            )
            bot.answer_inline_query(inline_query.id, [r1])
            return
        ans = generate_server_description(inline_query.query)
        # Создаем результаты для inline-ответа
        r1 = telebot.types.InlineQueryResultArticle(
            id=str(randint(0, 10000)),
            title=f"Сервер {inline_query.query}",
            description="Получить описание сервера",
            input_message_content=telebot.types.InputTextMessageContent(ans, parse_mode="html")
        )
        bot.answer_inline_query(inline_query.id, [r1])

    except GetServerInfoError as ex:
        # print(f"INLINE EX: {ex}")
        r2 = telebot.types.InlineQueryResultArticle(
            id=str(randint(0, 10000)),
            title=f"Произошла ошибка: ",
            description=f"{ex}",
            input_message_content=telebot.types.InputTextMessageContent(f"{ex}", parse_mode="html")
        )
        bot.answer_inline_query(inline_query.id, [r2])
    except Exception as ex:
        print(f"EX: {ex}")


if __name__ == "__main__":
    try:
        bot.infinity_polling()
    except ConnectionError as ex:
        logging.error(f"ConnectionError: {ex}")
