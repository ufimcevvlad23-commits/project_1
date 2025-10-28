import os
import sys
import json
import requests
from dotenv import load_dotenv

# === Добавляем корень проекта в sys.path ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))  # на 2 уровня вверх
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from bitrix_hh_integration.utils.logger import setup_logger  # ✅ теперь путь точный

logger = setup_logger()

# === Путь к .env ===
ENV_PATH = os.path.join(PROJECT_ROOT, "bitrix_hh_integration", "config", "credentials.env")
if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f"❌ Не найден файл окружения: {ENV_PATH}")

load_dotenv(ENV_PATH)

BITRIX_BASE_URL = os.getenv("BITRIX_BASE_URL")
BITRIX_DEAL_FIELDS = os.getenv("BITRIX_DEAL_FIELDS", "crm.deal.fields")

if not BITRIX_BASE_URL:
    raise ValueError("❌ BITRIX_BASE_URL не задан в credentials.env")


def get_deal_fields():
    """Получает список всех полей сделок из Bitrix"""
    url = f"{BITRIX_BASE_URL}/{BITRIX_DEAL_FIELDS}"
    logger.info(f"📡 Запрашиваем поля сделок: {url}")

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        if "error" in data:
            logger.error(f"❌ Ошибка Bitrix: {data}")
            return None

        fields = data.get("result", {})
        logger.info(f"✅ Получено {len(fields)} полей сделки из Bitrix")
        return fields

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при запросе полей: {e}")
        return None


def save_fields_to_file(fields):
    """Сохраняет поля в файл JSON"""
    data_dir = os.path.join(PROJECT_ROOT, "bitrix_hh_integration", "data")
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, "deal_fields.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(fields, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Список полей сохранён в {file_path}")


if __name__ == "__main__":
    logger.info("🚀 Получаем список полей сделок Bitrix24...")
    fields = get_deal_fields()
    if fields:
        save_fields_to_file(fields)
    else:
        logger.warning("⚠️ Не удалось получить список полей.")
