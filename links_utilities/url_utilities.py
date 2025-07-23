import requests
from urllib.parse import urlparse


def shorten_link(api_vk_token, url):
    url_vk = 'https://api.vk.ru/method/utils.getShortLink'
    payload = {
        'access_token': api_vk_token,
        'url': url,
        'v': 5.199
    }
    response = requests.get(url_vk, params=payload)
    response.raise_for_status()
    short_link = response.json()
    return short_link['response']['short_url']


def count_clicks(api_vk_token, short_vk_url):
    url_vk = 'https://api.vk.ru/method/utils.getLinkStats'
    parsed_url = urlparse(short_vk_url)
    key = parsed_url.path.lstrip('/')
    payload = {
        'access_token': api_vk_token,
        'key': key,
        'interval': 'forever',
        'v': 5.199
    }
    response = requests.get(url_vk, params=payload)
    response.raise_for_status()
    counted_clicks = response.json()
    return counted_clicks['response']['stats'][0]['views']


def is_shorten_link(api_vk_token, url):
    url_vk = 'https://api.vk.ru/method/utils.getLinkStats'
    parsed_url = urlparse(url)
    key = parsed_url.path.lstrip('/')
    payload = {
        'access_token': api_vk_token,
        'key': key,
        'interval': 'forever',
        'v': 5.199
    }
    response = requests.get(url_vk, params=payload)
    response.raise_for_status()
    link_stats = response.json()
    return 'error' not in link_stats
