# Сокращение ссылок, подсчет кликов, проверка на сокращенную ссылку - с помощью api.vk


### Как установить

Для начала Вам нужно зарегистрироваться в социальной сети [vk.com](https://vk.com/). Затем необходимо получить [сервисный ключ доступа (токен)](https://id.vk.com/about/business/go/docs/ru/vkid/latest/vk-id/connection/tokens/service-token), его можно получить после создания [приложения](https://id.vk.com/about/business/go/docs/ru/vkid/latest/vk-id/connection/create-application). Далее необходимо создать файл `.env` в директории программы и записать в первую строку `API_VK_TOKEN = ваш токен`.

Python3 должен быть уже установлен. Для запуска необходима версия [Python 3.9.*](https://www.python.org/downloads/)
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```
Рекомендуется использовать [virtualenv/venv](https://docs.python.org/3/library/venv.html) для изоляции проекта.

### Как использовать

1. Скрипт `shorten_link.py` сокращает url c помощью api vk.
Функция принимает две переменные `api_vk_token, url`.
Возвращает готовую к использованию сокращенную ссылку.

2. Скрипт `count_clicks.py` считает количестко переходов(кликов) по сокращенной с помощью api vk ссылке.
Функция принимает две переменные `api_vk_token, short_vk_url`.
Возвращает количество кликов в `int`.

3. Скрипт `is_shorten_link.py` проверяет с помощью api vk является ли введенная сылка сокращенной.
Функция принимает две переменные `api_vk_token, url`.
Возвращает `True` если ссылка коректная и `False` если с ошибкой.
