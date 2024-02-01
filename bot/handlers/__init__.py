from .start_handler import start_router
from aiogram import Router
main_router = Router()
main_router.include_router(start_router)
