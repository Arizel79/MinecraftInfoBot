# MinecraftInfoBot
Telegram бот для получения информации о серверах Minecraft 
## Установка
```
pip install pyTelegramBotApi
pip install requests
pip install sqlalchemy
```
Откройте файл `config.py` и измените значение переменной `TOKEN` на ваш токен телеграм бота

# Запуск
```python main.py```

# Использование
### Команды бота:
* /stats ADDRESS - получение информация о сервере с адресом ADDRESS
* /help - получение справка
* /fav - изменение и просмотр избранных серверов:
    * /fav - просмотр ваших избранных серверов
    * /fav add 2b2t.org - добавить сервер с адресом 2b2t.org в избранные сервера (имя в избранных совпадает с адресом)
    * /fav add 2b2t.org bestServer - добавить сервер с адресом 2b2t.org в избранные под именем bestServer
    * /fav del 2b2t.org - удаляет сервер с именем 2b2t.org из избранного

