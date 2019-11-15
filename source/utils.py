from db import SettingsDB

import asyncio
from aiogram import types

from functools import wraps
import io


def ignore(exception):
    def ignore(fn):
        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def wrapper(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except exception:
                    pass
            return wrapper
        else:
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except exception:
                    pass
            return wrapper
    return ignore


async def make_settings_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    settings = await SettingsDB.get(user_id)
    keyboard = types.InlineKeyboardMarkup()
    if not settings.allow_ru:
        keyboard.row(types.InlineKeyboardButton("Русский: 🅾 выключен!", callback_data="ru_on"))
    else:
        keyboard.row(types.InlineKeyboardButton("Русский: ✅ включен!", callback_data="ru_off"))
    if not settings.allow_uk:
        keyboard.row(types.InlineKeyboardButton("Украинский: 🅾 выключен!", callback_data="uk_on"))
    else:
        keyboard.row(types.InlineKeyboardButton("Украинский: ✅ включен!", callback_data="uk_off"))
    if not settings.allow_be:
        keyboard.row(types.InlineKeyboardButton("Белорусский: 🅾 выключен!", callback_data="be_on"))
    else:
        keyboard.row(types.InlineKeyboardButton("Белорусский: ✅ включен!", callback_data="be_off"))
    return keyboard


class BytesResult(io.BytesIO):
    def __init__(self, content):
        super().__init__(content)
        self.content = content
        self.size = len(content)
        self._name = None

    def get_copy(self):
        _copy = BytesResult(self.content)
        _copy.name = self.name
        return _copy

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
