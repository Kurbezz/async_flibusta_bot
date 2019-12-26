from typing import Union

from chatbase import Message
from aiogram import types
from aioify import aioify

from config import Config


def _analyze(message: str, intent: str, user_id: Union[int, str]):
    return Message(
        api_key=Config.CHATBASE_API_KEY,
        platform="telegram",
        message=message,
        intent=intent,
        user_id=user_id if isinstance(user_id, str) else str(user_id),
        version="3"
    ).send()


_async_analyze = aioify(_analyze)


class Analyze:
    def __init__(self, intent: str, obj, reply_msg=False):
        self.intent = intent
        self.obj = obj
        self.reply_msg = reply_msg

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if Config.CHATBASE_API_KEY:
            await analyze(self.intent, self.obj, self.reply_msg)


async def analyze(intent, obj, reply_msg=None):
    if isinstance(obj, types.Message):
        if reply_msg:
            await _async_analyze(obj.reply_to_message.text, intent, obj.from_user.id)
        else:
            await _async_analyze(obj.text, intent, obj.from_user.id)
    elif isinstance(obj, types.CallbackQuery):
        await _async_analyze(obj.message.text, intent, obj.from_user.id)
    elif isinstance(obj, types.InlineQuery):
        await _async_analyze(obj.query, intent, obj.from_user.id)
