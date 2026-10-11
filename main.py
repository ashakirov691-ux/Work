import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, DB_PATH, MSK, WORK_START_HOUR, WORK_END_HOUR
from database import init_db, is_auto_mode, is_service_open, set_setting
from handlers import user_router, admin_router
from helpers import BanMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def schedule_loop():
    """Фоновая проверка рабочего времени для авто-режима (07:00–23:00 МСК)."""
    while True:
        try:
            if is_auto_mode():
                now            = datetime.now(MSK)
                should_be_open = WORK_START_HOUR <= now.hour < WORK_END_HOUR
                if should_be_open != is_service_open():
                    set_setting("service_open", "1" if should_be_open else "0")
                    logging.info("Авто-режим: приём сервисов переключен на -> %s", "ОТКРЫТ" if should_be_open else "ЗАКРЫТ")
        except Exception as e:
            logging.warning(f"Ошибка в schedule_loop: {e}")
        await asyncio.sleep(60)

async def main():
    init_db()
    logging.info("База данных успешно инициализирована: %s", DB_PATH)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Мидлварь блокировки (блокирует любые сообщения и колбэки забаненных пользователей)
    dp.message.outer_middleware(BanMiddleware())
    dp.callback_query.outer_middleware(BanMiddleware())

    # Регистрация модульных роутеров
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Фоновые сервисы
    asyncio.create_task(schedule_loop())

    logging.info("Бот успешно запущен и ожидает событий...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
