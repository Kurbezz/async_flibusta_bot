import pathlib
from abc import ABC
from typing import Type, Union, List

import asyncpg
from aiogram.types import User, CallbackQuery

from config import Config


async def prepare_db():
    pool = await asyncpg.create_pool(user=Config.DB_USER, password=Config.DB_PASSWORD,
                                     database=Config.DB_NAME, host=Config.DB_HOST,
                                     port=Config.DB_PORT)

    for _class in [TablesCreator, TelegramUserDB, SettingsDB, PostedBookDB]:  # type: Type[ConfigurableDB]
        _class.configurate(pool)

    await TablesCreator.create_tables()

SQL_FOLDER = pathlib.Path("./sql")


class ConfigurableDB(ABC):
    pool: asyncpg.pool.Pool

    @classmethod
    def configurate(cls, pool: asyncpg.pool.Pool):
        cls.pool = pool


class TablesCreator(ConfigurableDB):
    CREATE_TELEGRAM_USER_TABLE = open(SQL_FOLDER / "create_telegram_user_table.sql").read().format(Config.DB_USER)
    CREATE_SETTINGS_TABLE = open(SQL_FOLDER / "create_settings_table.sql").read().format(Config.DB_USER)
    CREATE_POSTED_BOOK_TABLE = open(SQL_FOLDER / "create_posted_book_table.sql").read().format(Config.DB_USER)

    @classmethod
    async def create_tables(cls):
        await cls.pool.execute(cls.CREATE_TELEGRAM_USER_TABLE)
        await cls.pool.execute(cls.CREATE_SETTINGS_TABLE)
        await cls.pool.execute(cls.CREATE_POSTED_BOOK_TABLE)


class TelegramUserDB(ConfigurableDB):
    CREATE_OR_UPDATE = open(SQL_FOLDER / "telegram_user_create_or_update.sql").read()

    @classmethod
    async def create_or_update(cls, obj: Union[User, CallbackQuery]):
        await cls.pool.execute(cls.CREATE_OR_UPDATE, obj.from_user.id, obj.from_user.first_name, 
                               obj.from_user.last_name, obj.from_user.username)
    
    @classmethod
    async def create_or_update_raw(cls, user_id: int, first_name: str, last_name: str, username: str):
        await cls.pool.execute(cls.CREATE_OR_UPDATE, user_id, first_name, last_name, username)


class Settings:
    def __init__(self, user_id: int, allow_ru: bool, allow_be: bool, allow_uk: bool, beta_testing: bool):
        self.user_id: int = user_id
        self.allow_ru: bool = allow_ru
        self.allow_be: bool = allow_be
        self.allow_uk: bool = allow_uk
        self.beta_testing: bool = beta_testing

    def get(self) -> List[str]:
        result: List[str] = []
        if self.allow_ru:
            result.append("ru")
        if self.allow_be:
            result.append("be")
        if self.allow_uk:
            result.append("uk")
        return result


class SettingsDB(ConfigurableDB):
    GET = open(SQL_FOLDER / "settings_get.sql").read()
    UPDATE = open(SQL_FOLDER / "settings_update.sql").read()

    @classmethod
    async def get(cls, user_id: int) -> Settings:
        result = await cls.pool.fetch(cls.GET, user_id)
        if not result:
            return Settings(user_id, True, False, False, False)
        return Settings(user_id, result[0]["allow_ru"], result[0]["allow_be"], 
                        result[0]["allow_uk"], result[0]["beta_testing"])

    @classmethod
    async def update(cls, settings: Settings):
        await cls.pool.execute(cls.UPDATE, settings.user_id, settings.allow_ru,
                               settings.allow_be, settings.allow_uk, settings.beta_testing)


class PostedBook:
    def __init__(self, book_id: int, file_type: str, file_id: str):
        self.book_id: int = book_id
        self.file_type: str = file_type
        self.file_id: str = file_id


class PostedBookDB(ConfigurableDB):
    GET = open(SQL_FOLDER / "posted_book_get.sql").read()
    CREATE_OR_UPDATE = open(SQL_FOLDER / "posted_book_create_or_update.sql").read()
    DELETE = open(SQL_FOLDER / "posted_book_delete.sql").read()

    @classmethod
    async def get(cls, book_id: int, file_type: str):
        result = await cls.pool.fetch(cls.GET, book_id, file_type)
        if not result:
            return None
        return PostedBook(book_id, file_type, result[0]["file_id"])

    @classmethod
    async def create_or_update(cls, book_id: int, file_type: str, file_id: str):
        await cls.pool.execute(cls.CREATE_OR_UPDATE, book_id, file_type, file_id)

    @classmethod
    async def delete(cls, book_id: int, file_type: str):
        await cls.pool.execute(cls.DELETE, book_id, file_type)
