import os
import requests
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger()
print("🧩 Импортирован именно этот bitrix_api.py:", __file__)

# === Загружаем переменные окружения (.env) ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "config", "credentials.env"))

if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f"❌ Не найден файл {ENV_PATH}")

load_dotenv(ENV_PATH)

BITRIX_BASE_URL   = os.getenv("BITRIX_BASE_URL")
BITRIX_DEAL_ADD   = os.getenv("BITRIX_DEAL_ADD", "crm.deal.add")
BITRIX_DEAL_UPDATE= os.getenv("BITRIX_DEAL_UPDATE", "crm.deal.update")
BITRIX_FILE_UPLOAD= os.getenv("BITRIX_FILE_UPLOAD", "disk.file.upload")
BITRIX_DEAL_LIST  = os.getenv("BITRIX_DEAL_LIST", "crm.deal.list")

# Выводим базовую информацию для контроля
print("=== Bitrix ENV ===")
print(f"BITRIX_BASE_URL: {BITRIX_BASE_URL}")
print(f"BITRIX_DEAL_ADD: {BITRIX_DEAL_ADD}")
print(f"BITRIX_DEAL_UPDATE: {BITRIX_DEAL_UPDATE}")
print("===================")

if not BITRIX_BASE_URL:
    raise ValueError("❌ Не задан BITRIX_BASE_URL в credentials.env")


# === Универсальный запрос к Bitrix ===
def bitrix_request(method_name: str, params: dict = None):
    """Отправка запроса в Bitrix REST API"""
    if not BITRIX_BASE_URL:
        raise ValueError("❌ BITRIX_BASE_URL не задан")

    if not method_name or method_name.strip().lower() == "none":
        raise ValueError(f"❌ Некорректный метод Bitrix: {method_name}")

    url = BITRIX_BASE_URL.rstrip("/") + "/" + method_name.strip().lstrip("/")

    try:
        response = requests.post(url, json=params or {}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            logger.error(f"❌ Bitrix ошибка: {data}")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка запроса Bitrix ({method_name}): {e}")
        return None


# === Создание сделки ===
def create_deal(data: dict):
    """Создание сделки в Bitrix"""
    logger.info(f"🧾 Создаём сделку: {data.get('TITLE')}")
    res = bitrix_request(BITRIX_DEAL_ADD, {"fields": data})
    if res and res.get("result"):
        deal_id = res["result"]
        logger.info(f"✅ Сделка создана, ID: {deal_id}")
        return deal_id
    logger.error(f"❌ Не удалось создать сделку: {res}")
    return None


# === Обновление сделки ===
def update_deal(deal_id: int, fields: dict) -> bool:
    params = {"id": int(deal_id), "fields": fields}
    res = bitrix_request(BITRIX_DEAL_UPDATE, params)
    if res and res.get("result") is True:
        logger.info(f"♻️ Сделка #{deal_id} обновлена")
        return True
    logger.warning(f"⚠️ Не удалось обновить сделку #{deal_id}: {res}")
    return False


# === Список сделок (с пагинацией) ===
def list_deals(filter_: dict = None, select: list = None, order: dict = None, start: int = 0):
    payload = {
        "filter": filter_ or {},
        "select": select or ["ID", "TITLE", "STAGE_ID"],
        "order": order or {"ID": "DESC"},
        "start": start
    }
    res = bitrix_request(BITRIX_DEAL_LIST, payload)
    if not res:
        return [], None
    return res.get("result", []), res.get("next")


# === Поиск сделки по UF (ID отклика HH) ===
def find_deal_by_hh_id(hh_response_id: str, hh_field_code: str):
    """
    Ищем первую сделку, где пользовательское поле (например UF_CRM_1761217763) = hh_response_id
    """
    if not hh_response_id:
        return None

    start = 0
    while True:
        deals, next_start = list_deals(
            filter_={hh_field_code: hh_response_id},
            select=["ID", "TITLE", "STAGE_ID", hh_field_code],
            start=start
        )
        if deals:
            # Возвращаем первую подходящую
            return deals[0]
        if next_start is None:
            break
        start = next_start
    return None


# === Загрузка файла PDF в сделку ===
def upload_pdf_to_deal(deal_id: int, filepath: str):
    """Загрузка PDF и прикрепление к сделке"""
    if not os.path.exists(filepath):
        logger.warning(f"⚠️ Файл не найден: {filepath}")
        return None

    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            upload_url = BITRIX_BASE_URL.rstrip("/") + "/" + BITRIX_FILE_UPLOAD
            upload_res = requests.post(upload_url, files=files, timeout=60)
            upload_res.raise_for_status()
            file_data = upload_res.json()
            logger.info(f"📎 PDF загружен и прикреплён: {filepath}")
            return file_data
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки файла: {e}")
        return None


# === Добавление комментария в сделку ===
def add_comment(deal_id: int, text: str):
    """Добавление комментария в сделку"""
    params = {"id": int(deal_id), "fields": {"COMMENTS": text}}
    res = bitrix_request(BITRIX_DEAL_UPDATE, params)
    if res and res.get("result"):
        logger.info(f"💬 Комментарий добавлен в сделку {deal_id}")
    else:
        logger.warning(f"⚠️ Не удалось добавить комментарий: {res}")
