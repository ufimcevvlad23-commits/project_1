import os
import json
import requests
from utils.logger import setup_logger
from services.auth import get_valid_token

logger = setup_logger()

HH_API_BASE = "https://api.hh.ru"


def get_headers():
    """Формируем заголовки с токеном"""
    try:
        token = get_valid_token()
    except Exception as e:
        logger.error(f"❌ Ошибка получения токена: {e}")
        token = os.getenv("HH_ACCESS_TOKEN")

    if not token:
        raise RuntimeError("❌ Не найден access_token hh.ru")

    return {
        "User-Agent": "Bitrix-HH-Integration/1.0",
        "Authorization": f"Bearer {token}"
    }


def get_active_vacancies(employer_id="2688361", all_accessible=True):
    """Получаем список активных вакансий компании"""
    url = f"{HH_API_BASE}/employers/{employer_id}/vacancies/active"
    params = {"all_accessible": str(all_accessible).lower()}
    r = requests.get(url, headers=get_headers(), params=params, timeout=20)

    if r.status_code == 403:
        logger.error("🚫 Доступ запрещён. Проверь права API и токен hh.ru")
        r.raise_for_status()

    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    logger.info(f"📄 Получено {len(items)} активных вакансий")
    return items


def get_collections(vacancy_id):
    """Список коллекций (этапов откликов) по вакансии"""
    url = f"{HH_API_BASE}/negotiations"
    params = {"vacancy_id": vacancy_id}
    r = requests.get(url, headers=get_headers(), params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    collections = data.get("collections", [])
    logger.info(f"📚 Для вакансии {vacancy_id} найдено {len(collections)} коллекций")
    return collections


def get_negotiations_in_collection(collection_id, vacancy_id):
    """Отклики в конкретной коллекции (response, phone_interview и т.п.)"""
    url = f"{HH_API_BASE}/negotiations/{collection_id}"
    params = {"vacancy_id": vacancy_id}
    r = requests.get(url, headers=get_headers(), params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    logger.info(f"💬 В коллекции {collection_id} — {len(items)} откликов")
    return items


def get_resume_pdf(resume_id, filename):
    """Пробует скачать PDF-резюме"""
    if not resume_id:
        logger.warning("⚠️ Нет resume_id — пропускаем загрузку PDF")
        return False

    url = f"{HH_API_BASE}/resumes/{resume_id}/download"
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 404:
            logger.warning(f"⚠️ Резюме {resume_id} недоступно для скачивания (404)")
            return False
        r.raise_for_status()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(r.content)
        logger.info(f"📄 Резюме сохранено: {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания резюме {resume_id}: {e}")
        return False
