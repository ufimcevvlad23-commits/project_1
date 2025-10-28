import os
import requests
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger()

# === Загружаем .env ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "config", "credentials.env"))

if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f"❌ Не найден файл окружения: {ENV_PATH}")

load_dotenv(ENV_PATH)

BITRIX_BASE_URL = os.getenv("BITRIX_BASE_URL")
BITRIX_CONTACT_ADD = "crm.contact.add"
BITRIX_CONTACT_UPDATE = "crm.contact.update"
BITRIX_CONTACT_LIST = "crm.contact.list"

if not BITRIX_BASE_URL:
    raise ValueError("❌ BITRIX_BASE_URL не найден в credentials.env")


def bitrix_request(method_name: str, params: dict = None):
    """Отправка запроса в Bitrix REST API"""
    url = BITRIX_BASE_URL.rstrip("/") + "/" + method_name
    try:
        r = requests.post(url, json=params or {}, timeout=25)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            logger.error(f"❌ Bitrix ошибка: {data}")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка запроса Bitrix ({method_name}): {e}")
        return None


def find_contact_by_hh_id(hh_id: str):
    """Поиск контакта по UF_CRM_1760959751 (HH_ID отклика)"""
    logger.info(f"🔍 Ищем контакт с HH_ID отклика: {hh_id}")
    params = {
        "filter": {"UF_CRM_1760959751": hh_id},
        "select": ["ID", "NAME", "LAST_NAME", "UF_CRM_1760959751"]
    }
    res = bitrix_request(BITRIX_CONTACT_LIST, params)
    result = res.get("result", []) if res else []
    if result:
        contact = result[0]
        logger.info(f"✅ Найден контакт: {contact}")
        return contact
    logger.info("➖ Контакт не найден")
    return None


def create_contact(contact_data: dict):
    """Создаёт контакт с HH_ полями"""
    logger.info(f"🧾 Создаём контакт: {contact_data.get('NAME')} {contact_data.get('LAST_NAME')}")
    res = bitrix_request(BITRIX_CONTACT_ADD, {"fields": contact_data})
    if res and res.get("result"):
        contact_id = res["result"]
        logger.info(f"✅ Контакт создан, ID: {contact_id}")
        return contact_id
    logger.error(f"❌ Не удалось создать контакт: {res}")
    return None


def update_contact(contact_id: int, contact_data: dict):
    """Обновляет контакт с новыми HH_ данными"""
    logger.info(f"♻️ Обновляем контакт #{contact_id}")
    res = bitrix_request(BITRIX_CONTACT_UPDATE, {"id": contact_id, "fields": contact_data})
    if res and res.get("result"):
        logger.info(f"✅ Контакт #{contact_id} успешно обновлён")
        return True
    logger.warning(f"⚠️ Не удалось обновить контакт #{contact_id}: {res}")
    return False
