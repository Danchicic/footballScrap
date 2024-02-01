from dataclasses import dataclass

from environs import Env


@dataclass
class TgBot:
    token: str
    chat_id: str
    channel_id: str


@dataclass
class Config:
    tg_bot: TgBot


env = Env()
env.read_env()
config = Config(
    tg_bot=TgBot(token=env('BOT_TOKEN'),
                 chat_id=env('CHAT_ID'),
                 channel_id=env('CHANNEL_ID')
                 ),

)
