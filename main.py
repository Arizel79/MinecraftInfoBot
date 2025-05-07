import telebot
from telebot import formatting
from config import TOKEN
from minecraft_server_info import get_mc_server_info


HELP_TEXT = formatting.hbold("Get Minecraft Servers Information Bot") + "\n\n" + \
"""Я бот, который позволяет получать информацию о серверах Minecraft

Доступные команды:
/stats IP  информация о сервере
/help  справка"""


def generate_server_description(address: str) -> str:
    data = get_mc_server_info(address)
    """Описание сервера"""
    try:
        if data["ping"]:
            if len(data['players_list']) > 0:
                pl_list = f"\n• Список игроков: {(', '.join(formatting.hcode(p['name']) for p in data['players_list']) if data['players_list'] else '-')}"
            else:
                pl_list = ""
            return f"""{formatting.hbold(f'Сервер "{address}"')}
• Ping: {data["ping"]}
• Запрос: {formatting.hcode(address)}
• Цифровой IP: {formatting.hcode(data['address'])}
• Статус: {'🟢Онлайн' if data['is_online'] else "⚫️Оффлайн"}
• Описание: 
{formatting.hpre('\n'.join(data['motd']), language="motd")}
• Версия: {formatting.hcode(data['version'])}
• Онлайн игроков: {data['players']} / {data['max_players']}{pl_list}
"""
        else:
            return "Произошла ошибка. Проверьте правильность IP адреса или повторите попытку позже"
    except KeyError as e:
        telebot.logger.error("Missing key in data: %s", str(e))
        return formatting.hbold("⚠️ Ошибка формирования данных")


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message: telebot.types.Message) -> None:
    """Команда /start"""
    bot.send_message(message.chat.id, "Бот запущен! 🚀")


@bot.message_handler(commands=['help'])
def handle_help(message: telebot.types.Message) -> None:
    """Команда /help"""
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
        server_data = get_mc_server_info(ip)
        response = generate_server_description(ip)
    except ValueError:
        error_msg = formatting.hbold("Ошибка:") + "\nНе указан IP-адрес сервера!\nПример: /stats mc.example.com"
        bot.reply_to(message, error_msg, parse_mode='html')
    except ConnectionError as e:
        bot.reply_to(message, formatting.hbold(f"⚠️ Ошибка подключения: {str(e)}"), parse_mode='html')
    #except Exception as e:
    #    telebot.logger.error("Unexpected error: %s", str(e))
    #    bot.reply_to(message, formatting.hbold("⚠️ Произошла непредвиденная ошибка"), parse_mode='html')
    else:
        bot.send_message(message.chat.id, response, parse_mode='html', reply_to_message_id=message.id)


@bot.message_handler(commands=['stats', 'info'])
def handle_stats(message: telebot.types.Message) -> None:
    send_data(message)

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message: telebot.types.Message) -> None:
    if message.text.lower() in {'hello!', 'привет'}:
        bot.reply_to(message, "Привет! 👋")
    else:
        handle_stats(message)

if __name__ == "__main__":
    bot.infinity_polling()
