import os
import sys
import json
import requests
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger()

# === Добавляем путь до проекта ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# === Путь к .env ===
ENV_PATH = os.path.join(PROJECT_ROOT, "bitrix_hh_integration", "config", "credentials.env")
if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f"❌ Не найден файл окружения: {ENV_PATH}")

load_dotenv(ENV_PATH)

BITRIX_BASE_URL = os.getenv("BITRIX_BASE_URL")
if not BITRIX_BASE_URL:
    raise ValueError("❌ BITRIX_BASE_URL не задан в credentials.env")

BITRIX_CONTACT_FIELDS = "crm.contact.fields"


def get_contact_fields():
    """Получает все поля контакта из Bitrix"""
    url = f"{BITRIX_BASE_URL}/{BITRIX_CONTACT_FIELDS}"
    logger.info(f"📡 Запрашиваем поля контактов: {url}")

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        if "error" in data:
            logger.error(f"❌ Ошибка Bitrix: {data}")
            return None

        fields = data.get("result", {})
        logger.info(f"✅ Получено {len(fields)} полей контакта")
        return fields

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при запросе полей: {e}")
        return None


def save_fields_to_file(fields):
    """Сохраняет список полей в файл"""
    os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)
    file_path = os.path.join(PROJECT_ROOT, "data", "contact_fields.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(fields, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Поля сохранены в {file_path}")


if __name__ == "__main__":
    logger.info("🚀 Получаем список полей контакта Bitrix24...")
    fields = get_contact_fields()
    if fields:
        save_fields_to_file(fields)
    else:
        logger.warning("⚠️ Не удалось получить список полей контакта.")
