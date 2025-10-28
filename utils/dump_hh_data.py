import os
import sys
import json
from datetime import datetime

# === Автоматически добавляем путь до проекта ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from services.hh_api import (
    get_active_vacancies,
    get_collections,
    get_negotiations_in_collection
)
from utils.logger import setup_logger

logger = setup_logger()


def dump_hh_data():
    """Диагностическая функция: получает все вакансии, коллекции и отклики"""
    logger.info("🔍 Начинаем сбор данных с hh.ru для отладки...")

    dump = {
        "timestamp": datetime.now().isoformat(),
        "vacancies": []
    }

    vacancies = get_active_vacancies()
    if not vacancies:
        logger.warning("⚠️ Вакансии не найдены. Проверь токен hh.ru.")
        return

    for vacancy in vacancies:
        vacancy_id = vacancy.get("id")
        vacancy_name = vacancy.get("name")

        logger.info(f"📄 Вакансия: {vacancy_name} ({vacancy_id})")
        vac_info = {"id": vacancy_id, "name": vacancy_name, "collections": []}

        collections = get_collections(vacancy_id)
        for coll in collections:
            coll_id = coll.get("id")
            coll_name = coll.get("name")
            logger.info(f"📚 Коллекция: {coll_name} ({coll_id})")

            negotiations = get_negotiations_in_collection(coll_id, vacancy_id)
            coll_info = {
                "id": coll_id,
                "name": coll_name,
                "negotiations": negotiations
            }
            vac_info["collections"].append(coll_info)

        dump["vacancies"].append(vac_info)

    # === Сохраняем результат ===
    os.makedirs("logs", exist_ok=True)
    output_file = os.path.join("logs", "hh_data_dump.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dump, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Данные сохранены в {output_file}")


if __name__ == "__main__":
    dump_hh_data()
