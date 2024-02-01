import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot import *

token = config.tg_bot.token

# logger initializing
logger = logging.getLogger(__name__)


# configuration and turn on bot
async def main():
    # configurate logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Инициализируем бот и диспетчер

    dp: Dispatcher = Dispatcher()
    dp.include_router(handlers.main_router)
    bot: Bot = Bot(token=token,
                   parse_mode='HTML'
                   )
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
    # with open('./bot/db/12.txt') as f:
    #     f.read()
