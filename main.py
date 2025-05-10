import logging
import requests
import telebot
from telebot import formatting as frmt
frmt = frmt
from models.config import TOKEN
from models.minecraft_server_info import get_mc_server_info, GetServerInfoError
from random import randint
import time
from models.orm import MySession, User
from datetime import datetime

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
    out= ""

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
            # return "Произошла ошибка. Проверьте правильность IP адреса или повторите попытку позже"
    except KeyError as e:
        telebot.logger.error("Missing key in data: %s", str(e))
        return frmt.hbold("⚠️ Ошибка формирования данных")

    except ConnectionError:
        raise GetServerInfoError("Ошибочка APIшки (;")

class Bot():
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.session = MySession()

    def mainloop(self):
        bot = self.bot
        @bot.message_handler(regexp=r"^(?!\/).+$")
        def handle_other_messages(message: telebot.types.Message ) -> None:
            new_user = User(id=message.from_user.id)
            self.session.add_user(new_user)
            on_msg(message)
            if message.text.lower() in {'hello!', 'привет'}:
                bot.reply_to(message, "Привет! 👋")
            else:
                handle_stats(message)

        @bot.message_handler(commands=['start'])
        def handle_start(message: telebot.types.Message) -> None:
            """Команда /start"""
            on_msg(message)
            bot.send_message(message.chat.id, f"Добро пожаловать, {message.from_user.first_name}!\n"
                                              f"\n"
                                              f"Я бот, который позволяет получать различную информацию о Minecraft серверах\n")

        @bot.message_handler(commands=['fav'])
        def handle_start(message: telebot.types.Message) -> None:
            """Команда /fav"""
            on_msg(message)
            ls = message.text.split()
            if len(ls) == 1:
                fav_servers = self.session.get_fav_servers(message.from_user.id)
                bot.send_message(message.chat.id, f"Ваши избранные сервера:\n{print_fav_servers(fav_servers)}")
            elif len(ls) == 3:
                if ls[1] in ["add", "a", "+"]:
                    fav_servers = self.session.get_fav_servers(message.from_user.id)
                    fav_servers[f"{ls[2]}"] = ls[2]
                    self.session.set_fav_servers(message.from_user.id, fav_servers)
                    bot.send_message(message.chat.id, f"Добавили сервер")
                elif ls[1] in ["del", "remove", "-"]:
                    fav_servers = self.session.get_fav_servers(message.from_user.id)
                    del fav_servers[ls[2]]
                    self.session.set_fav_servers(message.from_user.id, fav_servers)
                    bot.send_message(message.chat.id, f"Удалил сервер")
            elif len(ls) == 4:
                if ls[1] in ["add", "a", "+"]:
                    fav_servers = self.session.get_fav_servers(message.from_user.id)
                    fav_servers[f"{ls[2]}"] = ls[3]
                    self.session.set_fav_servers(message.from_user.id, fav_servers)
                    bot.send_message(message.chat.id, f"Добавили сервер \nВаши избранные сервера:\n{print_fav_servers(fav_servers)}\n")


            elif len(ls) == 4:
                fav_servers = self.session.get_fav_servers(message.from_user.id)
                fav_servers[f"{ls[2]}"] = ls[1]
                self.session.set_fav_servers(message.from_user.id, fav_servers)
                bot.send_message(message.chat.id, f"Добавили сервер\nВаши избранные сервера:\n{print_fav_servers(fav_servers)}\n")

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
                error_msg = f"{frmt.hbold("Ошибка:")} Не указан IP-адрес сервера!\nПример: /stats mc.example.com"
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
            send_data(message)




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
                            f"Для получения информации о Minecraft сервере напишите боту {bot.get_me().username} или введите в любом чате:\n`@{f'{bot.get_me().username} <MINECRAFT_SERVER_ADDRESS>`'}", parse_mode="markdownV2")
                    )
                    bot.answer_inline_query(inline_query.id, [r1])
                    return

                ans = generate_server_description(inline_query.query)
                self.session.add_request(inline_query.from_user.id)



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
                    input_message_content=telebot.types.InputTextMessageContent(f"{ex}")
                )
                bot.answer_inline_query(inline_query.id, [r2])
            except Exception as ex:
                print(f"EX: {ex}")

        bot.polling(none_stop=True)

if __name__ == "__main__":
    try:
        b = Bot()
        b.mainloop()
    except requests.exceptions.ConnectionError as ex:
        logging.error(f"ConnectionError: {ex}")
    except Exception as ex:
        print(f"UK ex: {ex}")
