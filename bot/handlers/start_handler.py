from aiogram import F, Router
from aiogram.types import Message

from footballScrap.bot.db import db
from footballScrap.bot.db.database_controller import UserRow

start_router = Router()


@start_router.message(F.text == '/start')
async def start_message(message: Message):
    db.check_user(UserRow(message.from_user.id, message.from_user.full_name))
    await message.answer(text='Все прогнозы публикуются в канале https://t.me/new_ch123')
