import logging
import requests
import telebot
from telebot import formatting as frmt
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

frmt = frmt
from models.config import TOKEN
import models
from models.minecraft_server_info import get_mc_server_info, GetServerInfoError
from random import randint
import time
from models.orm import MySession, User
from datetime import datetime
import logging
from time import sleep

logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

# Форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Обработчик для файла
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Обработчик для консоли
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)

HELP_TEXT = frmt.hbold("Get Minecraft Servers Information Bot") + "\n\n" + \
            f"""Я бот, который позволяет получать информацию о серверах Minecraft
Просто напиши мне адрес (IP) сервера и я напишу тебе информацию о нём (онлайн, описание, и проч.)
            
Доступные команды:
• /stats ADDRESS - получение информация о сервере с адресом ADDRESS
• /help - получение справка
• /fav - изменение и просмотр избранных серверов:
    • /fav - просмотр ваших избранных серверов
    • {frmt.hcode("/fav add mc.example.com")} - добавить сервер с адресом {frmt.hcode("mc.example.com")} в избранные сервера (имя в избранных совпадает с адресом)
    • {frmt.hcode("/fav add mc.example.com best_server")} - добавить сервер с адресом {frmt.hcode("mc.example.com")} в избранные под именем best_server
    • {frmt.hcode("/fav del mc.example.com")} - удаляет сервер с именем {frmt.hcode("mc.example.com")} из избранного"""


def print_fav_servers(fav_servers: dict):
    out = ""

    for k, v in fav_servers.items():
        out += f"{k} - {v}\n"
    return out


def get_printable_user(from_user):
    usr = from_user
    return f"{usr.first_name}{"" if not usr.last_name else f' {usr.last_name}'} ({f'@{usr.username}, ' if usr.username else ""}{usr.id})"


def get_printable_time():
    return time.strftime("%H:%M.%S %d.%m.%Y", time.localtime())


def write_msg(msg):
    with open("msgs.txt", "a+", encoding="utf-8") as f:
        text = f"[{get_printable_time()}] {msg}\n"
        f.write(text)
        print(text)


def get_rnd_id():
    f"{int(time.time())}_{randint(0, 10000)}"


def on_msg(msg):
    write_msg(f"{get_printable_user(msg.from_user)}: {msg.text}")


write_msg("start")


def generate_server_description(address: str) -> str:
    """Описание сервера"""
    try:
        data = get_mc_server_info(address)
        if data["ping"]:
            if len(data['players_list']) > 0:
                pl_list = f"\n• Список игроков: {(', '.join(frmt.hcode(p['name']) for p in data['players_list']) if data['players_list'] else '-')}"
            else:
                pl_list = ""
            return f"""{frmt.hbold(f'Сервер "{address}"')}

• Запрос: {frmt.hcode(address)}
• Цифровой IP: {frmt.hcode(data['address'])}
• Статус: {'🟢Онлайн' if data['is_online'] else "⚫️Оффлайн"}
• Описание: 
{frmt.hpre('\n'.join(data['motd']), language="motd")}
• Версия: {frmt.hcode(data['version'])}
• Онлайн игроков: {data['players']} / {data['max_players']}{pl_list}
"""
        else:
            raise GetServerInfoError(f'Произошла ошибка. Нет ответа от сервера "{address}"')

    except requests.exceptions.Timeout:
        raise GetServerInfoError(f'Превышено время ожидания ответа от сервера "{address}"')

    except KeyError as e:
        telebot.logger.error("Missing key in data: %s", str(e))
        return frmt.hbold("⚠️ Ошибка формирования данных")

    except ConnectionError:
        raise GetServerInfoError("Ошибка подключения к API")


class Bot():
    INVILID_CMD_USE = f"Неверное использование команды\nДля получения справки: /help"
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.session = MySession()

    def get_markup(self, user_id):
        fav_servers = self.session.get_fav_servers(user_id)
        names = fav_servers.keys()
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in names:
            keyboard.add(telebot.types.KeyboardButton(text=f"{i}"))

        return keyboard

    def get_inline_preview(self, inline_query, address, name="name1"):
        try:
            r1 = telebot.types.InlineQueryResultArticle(
                id=f"{address}_{name}_{int(time.time())}_{randint(0, 10000)}",
                title=f"🟢 {address} - {name}",
                description="(клик)",
                input_message_content=telebot.types.InputTextMessageContent(
                    generate_server_description(address).replace("-", r"\-"),
                    parse_mode="HTML"
                )
            )
        except models.minecraft_server_info.GetServerInfoError as ex:
            r1 = telebot.types.InlineQueryResultArticle(
                id=f"{address}_{name}_{int(time.time())}_{randint(0, 10000)}",
                title=f"🔴 {address} - {name} (ошибка)",
                description=f"{ex}",
                input_message_content=telebot.types.InputTextMessageContent(
                    "нет данных",
                    parse_mode="HTML"  # Явно указываем HTML
                )
            )
        return r1
    def add_fav_server(self, msg, address, name):
        fav_servers = self.session.get_fav_servers(msg.from_user.id)
        fav_servers[f"{name}"] = address
        self.session.set_fav_servers(msg.from_user.id, fav_servers)
        self.bot.send_message(msg.chat.id, f"Добавили сервер", reply_to_message_id=msg.id, reply_markup=self.get_markup(msg.from_user.id))

    def mainloop(self):
        bot = self.bot

        @bot.message_handler(regexp=r"^(?!\/).+$")
        def handle_other_messages(message: telebot.types.Message) -> None:
            new_user = User(id=message.from_user.id)
            self.session.add_user(new_user)
            on_msg(message)
            fav_servers = self.session.get_fav_servers(message.from_user.id)
            if message.text in fav_servers.keys():
                try:
                    bot.reply_to(message, generate_server_description(fav_servers[message.text]), parse_mode="HTML", reply_markup=self.get_markup(message.from_user.id))
                except GetServerInfoError:
                    bot.reply_to(message, "Ошибка!", parse_mode="HTML", reply_markup=self.get_markup(message.from_user.id))
            else:
                handle_stats(message)

        @bot.message_handler(commands=['start'])
        def handle_start(message: telebot.types.Message) -> None:
            """Команда /start"""
            new_user = User(id=message.from_user.id)
            self.session.add_user(new_user)
            on_msg(message)
            bot.send_message(message.chat.id, f"Добро пожаловать, {message.from_user.first_name}!\n"
                                              f"\n"
                                              f"Я бот, который позволяет получать различную информацию о Minecraft серверах\n"
                                              f"Для получения справки: /help",
                             reply_markup=self.get_markup(message.from_user.id))

        @bot.message_handler(commands=['fav'])
        def handle_start(message: telebot.types.Message) -> None:
            """Команда /fav"""
            new_user = User(id=message.from_user.id)
            self.session.add_user(new_user)
            on_msg(message)
            ls = message.text.split()
            if len(ls) == 1:
                fav_servers = self.session.get_fav_servers(message.from_user.id)
                bot.send_message(message.chat.id, f"Ваши избранные сервера:\n{print_fav_servers(fav_servers)}", reply_markup=self.get_markup(message.from_user.id))
            elif len(ls) == 3:
                if ls[1] in ["add", "a", "+"]:
                    self.add_fav_server(message, ls[2], ls[2])
                elif ls[1] in ["del", "remove", "-"]:
                    fav_servers = self.session.get_fav_servers(message.from_user.id)
                    try:
                        del fav_servers[ls[2]]
                        self.session.set_fav_servers(message.from_user.id, fav_servers)
                        bot.send_message(message.chat.id, f"Удалил сервер", reply_to_message_id=message.id)
                    except:
                        bot.send_message(message.chat.id, f"Сервер не найден", reply_to_message_id=message.id)
                else:
                    bot.send_message(message.chat.id, self.INVILID_CMD_USE,
                                     reply_to_message_id=message.id)

            elif len(ls) == 4:
                if ls[1] in ["add", "a", "+"]:

                    self.add_fav_server(message, ls[2], ls[3])
                else:
                    bot.send_message(message.chat.id, self.INVILID_CMD_USE,
                                     reply_to_message_id=message.id)

            else:
                bot.send_message(message.chat.id, self.INVILID_CMD_USE, reply_to_message_id=message.id)

        @bot.message_handler(commands=['help'])
        def handle_help(message: telebot.types.Message) -> None:
            """Команда /help"""
            new_user = User(id=message.from_user.id)
            self.session.add_user(new_user)
            on_msg(message)
            bot.send_message(message.chat.id, HELP_TEXT, parse_mode='html', reply_markup=self.get_markup(message.from_user.id))

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
                error_msg = f"{frmt.hbold("Ошибка:")} Не указан IP-адрес сервера!\nПример использования: {frmt.hcode('/stats mc.example.com')}"
                bot.reply_to(message, error_msg, parse_mode='html')
            except GetServerInfoError as ex:
                error_msg = f"{frmt.hbold("Ошибка:")} {ex}"
                bot.reply_to(message, error_msg, parse_mode='html')
            except ConnectionError as e:
                bot.reply_to(message, frmt.hbold(f"⚠️ Ошибка подключения: {str(e)}"), parse_mode='html')

            else:

                bot.send_message(message.chat.id, response, parse_mode='html', reply_to_message_id=message.id)
                self.session.add_request(message.from_user.id)

        @bot.message_handler(commands=['stats', 'info'])
        def handle_stats(message: telebot.types.Message) -> None:
            new_user = User(id=message.from_user.id)
            self.session.add_user(new_user)
            send_data(message)

        @bot.inline_handler(lambda query: True)

        def query_text(inline_query):
            new_user = User(id=inline_query.from_user.id)
            self.session.add_user(new_user)
            try:
                write_msg(f"{get_printable_user(inline_query.from_user)} inline: {inline_query.query}")
                query = inline_query.query.strip()

                if not query:
                    replyes = []
                    # Используем простой текст без форматирования для пустого запроса
                    r1 = telebot.types.InlineQueryResultArticle(
                        id=f"{inline_query.query[:32]}_{int(time.time())}_{randint(0, 10000)}",
                        title="Введите IP-адрес Minecraft сервера",
                        description="Для получения информации о нём",
                        input_message_content=telebot.types.InputTextMessageContent(
                            f"Для получения информации о Minecraft сервере напишите боту "
                            f"{bot.get_me().username} или введите в любом чате:\n"
                            f"@{bot.get_me().username} ADDRESS, где ADDRESS - адрес искомого сервера"
                        )
                    )
                    replyes.append(r1)
                    for k, v in self.session.get_fav_servers(inline_query.from_user.id).items():
                        r = self.get_inline_preview(inline_query, v, k)
                        replyes.append(r)

                    bot.answer_inline_query(inline_query.id, replyes, cache_time=1)
                    return

                try:
                    replyes = []

                    self.session.add_request(inline_query.from_user.id)
                    replyes.append(telebot.types.InlineQueryResultArticle(
                        id=f"{inline_query.query[:32]}_{int(time.time())}_{randint(0, 10000)}",
                        title=f"🟢 {query}",
                        description="Получить описание сервера (клик сюда)",
                        input_message_content=telebot.types.InputTextMessageContent(
                            generate_server_description(query).replace("-", r"\-"),
                            parse_mode="HTML"  # Явно указываем HTML
                        )
                    ))
                    for k, v in self.session.get_fav_servers(inline_query.from_user.id).items():
                        if inline_query.query in k + v:
                            r = self.get_inline_preview(inline_query, v, k)
                            replyes.append(r)

                    bot.answer_inline_query(inline_query.id, replyes, cache_time=1)

                except GetServerInfoError as ex:

                    error_msg = str(ex).replace("-", r"\-")  # Экранируем дефисы
                    r2 = telebot.types.InlineQueryResultArticle(
                        id=f"{inline_query.query[:32]}_{int(time.time())}_{randint(0, 10000)}",
                        title="❌Произошла ошибка",
                        description=str(ex),
                        input_message_content=telebot.types.InputTextMessageContent(
                            error_msg,
                            parse_mode=None
                        )
                    )
                    replyes.append(r2)

                    bot.answer_inline_query(inline_query.id, replyes, cache_time=1)
                    return

                except Exception as ex:
                    logger.error(f"Inline query error: {str(ex)}")
                    r3 = telebot.types.InlineQueryResultArticle(
                        id=str(randint(0, 10000)),
                        title="Ошибка",
                        description="Произошла ошибка при обработке запроса",
                        input_message_content=telebot.types.InputTextMessageContent(
                            "Произошла ошибка при обработке запроса. Попробуйте позже."
                        )
                    )
                    bot.answer_inline_query(inline_query.id, [r3], cache_time=1)
            finally:
                pass
            # except Exception as ex:
            #     logger.error(f"Fatal inline query error: {str(ex)}")

        try:
            bot.polling(none_stop=True)
        except telebot.apihelper.ApiTelegramException:
            print("telebot.apihelper.ApiTelegramException 95747")


if __name__ == "__main__":
    try:
        b = Bot()
        b.mainloop()
    except requests.exceptions.ConnectionError as ex:
        logging.error(f"ConnectionError: {ex}")
