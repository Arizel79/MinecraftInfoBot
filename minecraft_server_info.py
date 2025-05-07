import json
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_mc_server_info(address: str) -> Dict[str, Any]:
    """
    Получает информацию о Minecraft-сервере через API mcsrvstat.us.

    Args:
        address (str): IP или домен сервера (с портом, если не стандартный).

    Returns:
        Dict[str, Any]: Словарь с данными сервера.

    Raises:
        ConnectionError: Ошибка сети или API.
        ValueError: Некорректные данные в ответе.
    """
    try:
        response = requests.get(
            f"https://api.mcsrvstat.us/3/{address}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

    except requests.exceptions.RequestException as exc:
        logger.error("API request error: %s", str(exc))
        raise ConnectionError(f"Ошибка API: {str(exc)}") from exc
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON response")
        raise ValueError("Некорректный ответ API") from exc

    players_data = data.get("players", {})

    return {
        "ping": data["debug"]["ping"],
        "motd": data.get("motd", {}).get("clean", ["Нет описания"]),
        "version": data.get("version", "Неизвестно"),
        "players": players_data.get("online", 0),
        "max_players": players_data.get("max", 0),
        "is_online": data.get("online", False),
        "address": f"{data.get('ip', '')}:{data.get('port', '')}",
        "players_list": players_data.get("list", [])
    }


if __name__ == "__main__":
    from pprint import pprint
    test_address = "185.9.145.219:25809"
    try:
        server_data = get_mc_server_info(test_address)
        pprint(server_data)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
