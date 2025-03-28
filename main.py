import telebot
from telebot import formatting
from config import TOKEN
from minecraft_server_info import get_mc_server_info


HELP_TEXT = formatting.mbold("Get Minecraft Information Bot") + "\n\n" + \
            """Я бот, который позволяет получать информацию о серверах Minecraft
            
            Доступные команды:
            /stats IP  информация о сервере
            /help  справка"""


def generate_server_description(address: str, data: dict) -> str:
    """Описание сервера"""
    try:
        return formatting.munderline("Информация о сервере Minecraft") + f"""

• Запрос: {formatting.mcode(address)}
• Цифровой IP: {formatting.mcode(data['address'])}
• Описание: 
{formatting.mcode('\n'.join(data['motd']))}
• Онлайн игроков: {data['players']}/{data['max_players']}
• Список игроков: {', '.join(formatting.mcode(p['name']) for p in data['players_list'])}
• Версия: {formatting.mcode(data['version'])}
"""
    except KeyError as e:
        telebot.logger.error("Missing key in data: %s", str(e))
        return formatting.mbold("⚠️ Ошибка формирования данных")


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message: telebot.types.Message) -> None:
    """Команда /start"""
    bot.send_message(message.chat.id, "Бот запущен! 🚀")


@bot.message_handler(commands=['help'])
def handle_help(message: telebot.types.Message) -> None:
    """Команда /help"""
    bot.send_message(message.chat.id, HELP_TEXT, parse_mode='MarkdownV2')


@bot.message_handler(commands=['stats', 'info'])
def handle_stats(message: telebot.types.Message) -> None:
    """Запрос информации о сервере"""
    try:
        args = message.text.split()
        if len(args) < 2:
            raise ValueError

        ip = args[1]
        server_data = get_mc_server_info(ip)
        response = generate_server_description(ip, server_data)
    except ValueError:
        error_msg = formatting.mbold("Ошибка:") + "\nНе указан IP-адрес сервера!\nПример: /stats mc.example.com"
        bot.reply_to(message, error_msg, parse_mode='MarkdownV2')
    except ConnectionError as e:
        bot.reply_to(message, formatting.mbold(f"⚠️ Ошибка подключения: {str(e)}"), parse_mode='MarkdownV2')
    except Exception as e:
        telebot.logger.error("Unexpected error: %s", str(e))
        bot.reply_to(message, formatting.mbold("⚠️ Произошла непредвиденная ошибка"), parse_mode='MarkdownV2')
    else:
        bot.send_message(message.chat.id, response, parse_mode='MarkdownV2')


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message: telebot.types.Message) -> None:
    if message.text.lower() in {'hello!', 'привет'}:
        bot.reply_to(message, "Привет! 👋")
    else:
        bot.reply_to(message, "🚫 Команда не распознана. Введите /help")


if __name__ == "__main__":
    bot.infinity_polling()
