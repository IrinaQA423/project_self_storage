import os

from dotenv import load_dotenv

def load_config():
    load_dotenv()
    tg_token = os.getenv('TG_TOKEN')
    if not tg_token:
        raise ValueError("Токен Telegram не найден в переменных окружения")
    return tg_token 