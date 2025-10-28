import logging
import os

def setup_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("bitrix_hh")
    logger.setLevel(logging.INFO)

    # если логгер уже создан — не добавляем дубликаты
    if logger.handlers:
        return logger

    # === Файл ===
    fh = logging.FileHandler("logs/app.log", encoding="utf-8")
    fh.setLevel(logging.INFO)

    # === Консоль ===
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
