import asyncio
from aiogram import Bot


class Notifier:
    def __init__(self, bot: Bot, chat_id: int, notification_type: str):
        self.bot = bot
        self.chat_id = chat_id
        self.notification_type = notification_type

        self.run = True
        self.task = None

    async def run_notify_loop(self):
        while self.run:
            await self.bot.send_chat_action(self.chat_id, self.notification_type)
            await asyncio.sleep(1)

    async def __aenter__(self):
        self.task = asyncio.create_task(self.run_notify_loop())

    async def __aexit__(self, exc_type, exc_val, ext_tb):
        self.run = False
        await self.task
