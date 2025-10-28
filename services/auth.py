import os
import json
import time
import requests
from dotenv import load_dotenv
from utils.logger import setup_logger

# Загружаем переменные окружения
load_dotenv("config/credentials.env")
logger = setup_logger()

# === Базовые константы ===
CLIENT_ID = "NGSSI44TJVJD491CUPI2EHDNISAMBFVIDF7U2V3JOVLJ70QABPKTR1HD6C5PSOAJ"
CLIENT_SECRET = "L649P2DAEJ2HKP8OB4P4A3CPU07ATKNG7J4VLDJJA5K2OFG02Q1S2KEVR6Q4FAC6"
REDIRECT_URI = "http://localhost:8000/hh_auth"


# === Абсолютный путь к файлу токенов ===
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # .../bitrix_hh_integration/
TOKENS_PATH = os.path.join(BASE_DIR, "data", "tokens.json")


# === Вспомогательные функции ===
def save_tokens(tokens: dict):
    """Сохраняем токены hh.ru в файл"""
    os.makedirs(os.path.dirname(TOKENS_PATH), exist_ok=True)
    with open(TOKENS_PATH, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Токены hh.ru сохранены: {TOKENS_PATH}")


def load_tokens() -> dict | None:
    """Загружаем токены из файла"""
    if os.path.exists(TOKENS_PATH):
        with open(TOKENS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("⚠️ Файл токенов hh.ru не найден.")
    return None


def get_new_tokens(auth_code: str) -> dict:
    """Получаем новые токены по authorization_code"""
    url = "https://hh.ru/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code,
    }

    r = requests.post(url, data=data)
    if r.status_code != 200:
        logger.error(f"❌ Ошибка получения токенов hh.ru: {r.status_code} {r.text}")
        r.raise_for_status()

    tokens = r.json()
    tokens["created_at"] = int(time.time())
    save_tokens(tokens)
    return tokens


def refresh_tokens(tokens: dict) -> dict:
    """Обновляем токены hh.ru по refresh_token"""
    url = "https://hh.ru/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": tokens["refresh_token"],
    }

    r = requests.post(url, data=data)
    if r.status_code != 200:
        logger.error(f"❌ Ошибка обновления токенов hh.ru: {r.status_code} {r.text}")
        r.raise_for_status()

    new_tokens = r.json()
    new_tokens["created_at"] = int(time.time())
    save_tokens(new_tokens)
    logger.info("🔁 Токены hh.ru обновлены.")
    return new_tokens


def get_valid_token() -> str:
    """Возвращает действительный access_token (автообновление при необходимости)"""
    tokens = load_tokens()
    if not tokens:
        raise Exception("❌ Нет сохранённых токенов hh.ru. Сначала вызови get_new_tokens().")

    expires_in = tokens.get("expires_in", 0)
    created_at = tokens.get("created_at", 0)
    lifetime = time.time() - created_at

    # Если токен просрочен или скоро истечёт — обновляем
    if lifetime > expires_in - 60:
        logger.info("♻️ Токен hh.ru истёк — обновляем...")
        tokens = refresh_tokens(tokens)

    return tokens["access_token"]
