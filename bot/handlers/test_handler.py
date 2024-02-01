from aiogram import Router, Bot
from aiogram.types import Message

from ..config import config

from bot.my_types import ChannelAnswerType

test_router = Router()
bot = Bot(token=config.tg_bot.token)


async def send_forecast_to_channel(ans: ChannelAnswerType):
    await bot.send_message(config.tg_bot.channel_id, text=f"""
    Страна / {ans.country}\n
    Чемпионат / {ans.champ}\n
    Матч / {ans.match}\n
    Счет-Минута / {ans.score} {ans.match_minute}\n
    Прогноз / {ans.forecast_team} близок к голу
    """)
