from db import SettingsDB

import asyncio
from aiogram import types

from functools import wraps
import io
from typing import List, Union


def ignore(exceptions):
    def ignore(fn):
        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def wrapper(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except exceptions:
                    pass
            return wrapper
        else:
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except exceptions:
                    pass
            return wrapper
    return ignore


async def make_settings_lang_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
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
        
    keyboard.row(types.InlineKeyboardButton("⬅️ Назад", callback_data="settings_main"))

    return keyboard


async def download_by_series_keyboard(series_id: int) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()

    for file_type in ["fb2", "epub", "mobi"]:
        keyboard.row(types.InlineKeyboardButton(file_type, callback_data=f"download_c_{file_type}_{series_id}"))

    return keyboard


async def beta_testing_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    settings = await SettingsDB.get(user_id)

    keyboard = types.InlineKeyboardMarkup()

    if settings.beta_testing:
        keyboard.row(types.InlineKeyboardButton("✅ Участвовать в бета тесте!", callback_data="_"))
    else:
        keyboard.row(types.InlineKeyboardButton("Участвовать в бета тесте!", callback_data="beta_test_on"))

    if not settings.beta_testing:
        keyboard.row(types.InlineKeyboardButton("✅ Не участвовать в бета тесте!", callback_data="_"))
    else:
        keyboard.row(types.InlineKeyboardButton("Не участвовать в бета тесте!", callback_data="beta_test_off"))
        
    keyboard.row(types.InlineKeyboardButton("⬅️ Назад", callback_data="settings_main"))

    return keyboard


async def make_settings_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(types.InlineKeyboardButton("Языки", callback_data="langs_settings"))
    # keyboard.row(types.InlineKeyboardButton("Бета тест", callback_data="beta_testing"))

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


def split_text(text: str) -> List[str]:
    parts = []
    i = 0

    while True:
        if i + 2048 > len(text):
            parts.append(text[i:len(text) + 1])
            break
        else:
            new_i = max(
                text.rfind(".", i, i + 2048),
                text.rfind("!", i, i + 2048),
                text.rfind("?", i, i + 2048),
            )

            if new_i == -1:
                new_i = text.rfind("\n", i, i + 2048)
            
            if new_i == -1:
                new_i = min(i + 2048, len(text))

            if new_i == i or new_i == -1:
                break

            parts.append(text[i:new_i + 1])
            i = new_i

    return parts
