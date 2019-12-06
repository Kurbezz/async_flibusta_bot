import typing
from typing import Optional
from functools import wraps
from datetime import date

import transliterate as transliterate
from aiogram import Bot, types, exceptions
from aiogram.bot import api
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, base
from aiogram.utils.payload import prepare_file, prepare_arg, generate_payload
import aiohttp

from config import Config

from notifier import Notifier
from flibusta_server import BookAPI, DownloadAPI, AuthorAPI, SequenceAPI, BookAnnotationAPI, AuthorAnnotationAPI, UpdateLogAPI
from flibusta_server import BookWithAuthor
from db import PostedBook, PostedBookDB, SettingsDB
from utils import split_text

ELEMENTS_ON_PAGE = 7
BOOKS_CHANGER = 5


async def get_keyboard(page: int, pages_count: int, keyboard_type: str, 
                       only_one: bool = False) -> Optional[InlineKeyboardMarkup]:
    if pages_count == 1:
        return None
    keyboard = InlineKeyboardMarkup()

    first_row = []
    second_row = []

    if page > 1:
        prev_page = max(1, page - BOOKS_CHANGER)
        if prev_page != page - 1 and not only_one:
            second_row.append(InlineKeyboardButton(f'<< {prev_page}',
                                                   callback_data=f'{keyboard_type}_{prev_page}'))
        first_row.append(InlineKeyboardButton('<', callback_data=f'{keyboard_type}_{page - 1}'))

    if page != pages_count:
        next_page = min(pages_count, page + BOOKS_CHANGER)
        if next_page != page + 1 and not only_one:
            second_row.append(InlineKeyboardButton(f'>> {next_page}',
                                                   callback_data=f'{keyboard_type}_{next_page}'))
        first_row.append(InlineKeyboardButton('>', callback_data=f'{keyboard_type}_{page + 1}'))

    if first_row:
        keyboard.row(*first_row)
    if second_row:
        keyboard.row(*second_row)

    return keyboard


async def normalize(book: BookWithAuthor, file_type: str) -> str:  # remove chars that don't accept in Telegram Bot API
    filename = '_'.join([a.short for a in book.authors]) + '_-_' if book.authors else ''
    filename += book.title if book.title[-1] != ' ' else book.title[:-1]
    filename = transliterate.translit(filename, 'ru', reversed=True)

    for c in "(),….’!\"?»«':":
        filename = filename.replace(c, '')

    for c, r in (('—', '-'), ('/', '_'), ('№', 'N'), (' ', '_'), ('–', '-'), ('á', 'a'), (' ', '_')):
        filename = filename.replace(c, r)

    return filename + '.' + file_type


def need_one_or_more_langs(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        for a in args:
            if isinstance(a, Message):
                allowed_langs = (await SettingsDB.get(a.chat.id)).get()
                if not allowed_langs:
                    return await Sender.try_reply_or_send_message(a.chat.id, "Нужно выбрать хотя бы один язык! /settings",
                                                                  reply_to_message_id=a.message_id)
                return await fn(*args, **kwargs)
            elif isinstance(a, types.CallbackQuery):
                allowed_langs = (await SettingsDB.get(a.from_user.id)).get()
                if not allowed_langs:
                    return await Sender.try_reply_or_send_message(a.from_user.id, "Нужно выбрать хотя бы один язык! /settings",
                                                                  reply_to_message_id=a.message_id)
                return await fn(*args, **kwargs)
    return wrapper


async def get_book_from_channel(book_id: int, file_type: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{Config.FLIBUSTA_CHANNEL_SERVER}/get_message_id/{book_id}/{file_type}") as response:
            return await response.json()


class Sender:
    bot: Bot

    @classmethod
    def configure(cls, bot: Bot):
        cls.bot = bot

    @classmethod
    async def send_document(cls, chat_id: typing.Union[base.Integer, base.String],
                            document: typing.Union[base.InputFile, base.String],
                            filename: str = 'document',
                            thumb: typing.Union[base.InputFile, base.String, None] = None,
                            caption: typing.Union[base.String, None] = None,
                            parse_mode: typing.Union[base.String, None] = None,
                            disable_notification: typing.Union[base.Boolean, None] = None,
                            reply_to_message_id: typing.Union[base.Integer, None] = None,
                            reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                       types.ReplyKeyboardMarkup,
                                                       types.ReplyKeyboardRemove,
                                                       types.ForceReply, None] = None) -> types.Message:
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=[filename])
        if cls.bot.parse_mode:
            payload.setdefault('parse_mode', cls.bot.parse_mode)

        files = {filename: document}
        prepare_file(payload, files, filename, document)

        result = await cls.bot.request(api.Methods.SEND_DOCUMENT, payload, files)
        return types.Message(**result)
    
    @classmethod
    async def try_reply_or_send_message(cls, *args, **kwargs):
        try:
            return await cls.bot.send_message(*args, **kwargs)
        except exceptions.BadRequest:
            kwargs.pop('reply_to_message_id')
            return await cls.bot.send_message(*args, **kwargs)

    @classmethod
    async def try_reply_or_send_photo(cls, *args, **kwargs):
        try:
            return await cls.bot.send_photo(*args, **kwargs)
        except exceptions.BadRequest:
            kwargs.pop('reply_to_message_id')
            return await cls.bot.send_photo(*args, **kwargs)

    @staticmethod
    async def remove_cache(type_: str, id_: int):
        await PostedBookDB.delete(id_, type_)

    @classmethod
    async def send_book(cls, msg: Message, book_id: int, file_type: str):
        async with Notifier(cls.bot, msg.chat.id, "upload_document"):
            book = await BookAPI.get_by_id(book_id)

            if book is None:
                await msg.reply("Книга не найдена!")
                return
            
            pb = await PostedBookDB.get(book_id, file_type)
            if pb:
                try:
                    await cls.bot.send_document(msg.chat.id, pb.file_id, reply_to_message_id=msg.message_id,
                                                 caption=book.caption, reply_markup=book.share_markup)
                except exceptions.BadRequest:
                    await cls.bot.send_document(msg.chat.id, pb.file_id,
                                                 caption=book.caption, reply_markup=book.share_markup)
            else:
                book_on_channel = await get_book_from_channel(book_id, file_type)

                if book_on_channel is not None:
                    try:
                        send_response = await cls.bot.forward_message(msg.chat.id, book_on_channel["channel_id"], 
                                                                      book_on_channel["message_id"])
                        await DownloadAPI.update(book_id, msg.chat.id)
                        return
                    except exceptions.MessageToForwardNotFound:
                        pass

                book_bytes = await BookAPI.download(book_id, file_type)
                if not book_bytes:
                    await cls.try_reply_or_send_message(msg.chat.id, 
                                                               "Ошибка! Попробуйте позже :(",
                                                               reply_to_message_id=msg.message_id)
                    await DownloadAPI.update(book_id, msg.chat.id)
                    return
                if book_bytes.size > 50_000_000:
                    await cls.try_reply_or_send_message(
                        msg.chat.id, 
                        book.download_caption(file_type), parse_mode="HTML",
                        reply_to_message_id=msg.message_id
                    )
                    await DownloadAPI.update(book_id, msg.chat.id)
                    return
                book_bytes.name = await normalize(book, file_type)
                try:
                    send_response = await cls.bot.send_document(msg.chat.id, book_bytes,
                                                                reply_to_message_id=msg.message_id,
                                                                caption=book.caption, reply_markup=book.share_markup)
                except exceptions.BadRequest:
                    book_bytes = book_bytes.get_copy()
                    send_response = await cls.bot.send_document(msg.chat.id, book_bytes,
                                                                caption=book.caption, reply_markup=book.share_markup)
                await PostedBookDB.create_or_update(book_id, file_type, send_response.document.file_id)
                await DownloadAPI.update(book_id, msg.chat.id)

    @classmethod
    @need_one_or_more_langs
    async def search_books(cls, msg: Message, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        search_result = await BookAPI.search(msg.reply_to_message.text,
                                          (await SettingsDB.get(msg.chat.id)).get(), 
                                          ELEMENTS_ON_PAGE, page)

        if search_result is None:
            await cls.bot.edit_message_text('Произошла ошибка :( Попробуйте позже', 
                                            chat_id=msg.chat.id, message_id=msg.message_id)
            return

        if not search_result:
            await cls.bot.edit_message_text('Книги не найдены!', chat_id=msg.chat.id, message_id=msg.message_id)
            return

        page_count = search_result.count // ELEMENTS_ON_PAGE + (1 if search_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = '\n\n\n'.join(book.to_send_book for book in search_result.books) \
                   + f'\n\n<code>Страница {page}/{page_count}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                         reply_markup=await get_keyboard(page, page_count, 'b'))

    @classmethod
    @need_one_or_more_langs
    async def search_authors(cls, msg: Message, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        search_result = await AuthorAPI.search(msg.reply_to_message.text, 
                                            (await SettingsDB.get(msg.chat.id)).get(), 
                                            ELEMENTS_ON_PAGE, page)

        if search_result is None:
            await cls.bot.edit_message_text('Произошла ошибка :( Попробуйте позже', 
                                            chat_id=msg.chat.id, message_id=msg.message_id)
            return

        if not search_result:
            await cls.bot.edit_message_text('Автор не найден!', chat_id=msg.chat.id, message_id=msg.message_id)
            return

        page_max = search_result.count // ELEMENTS_ON_PAGE + (1 if search_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = ''.join(author.to_send for author in search_result.authors) \
                   + f'<code>Страница {page}/{page_max}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                        reply_markup=await get_keyboard(page, page_max, 'a'))

    @classmethod
    @need_one_or_more_langs
    async def search_books_by_author(cls, msg: Message, author_id: int, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        author = await AuthorAPI.by_id(author_id, (await SettingsDB.get(msg.chat.id)).get(), ELEMENTS_ON_PAGE, page)

        if author is None:
            await msg.reply("Автор не найден!")
            return
    
        books = author.books
        if not books:
            await msg.reply('Ошибка! Книги не найдены!')
            return
        page_max = author.count // ELEMENTS_ON_PAGE + (1 if author.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = f"<b>{author.normal_name}:</b>"
        if author.annotation_exists:
            msg_text += f"\nОб авторе: /a_info_{author.id}\n\n"
        else:
            msg_text += "\n\n"
        msg_text += ''.join([book.to_send_book_without_author for book in books]) + \
            f'<code>Страница {page}/{page_max}</code>'                   
        if not msg.reply_to_message:
            await cls.try_reply_or_send_message(msg.chat.id, msg_text, parse_mode='HTML', 
                                                reply_markup=await get_keyboard(1, page_max, 'ba'),
                                                reply_to_message_id=msg.message_id
            )
        else:
            await cls.bot.edit_message_text(msg_text, msg.chat.id, msg.message_id, parse_mode='HTML',
                                             reply_markup=await get_keyboard(page, page_max, 'ba'))

    @classmethod
    @need_one_or_more_langs
    async def search_series(cls, msg: Message, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')
        sequences_result = await SequenceAPI.search(msg.reply_to_message.text, 
                                                 (await SettingsDB.get(msg.chat.id)).get(), 
                                                 ELEMENTS_ON_PAGE, page)

        if sequences_result is None:
            await cls.bot.edit_message_text('Произошла ошибка :( Попробуйте позже', 
                                            chat_id=msg.chat.id, message_id=msg.message_id)
            return

        if not sequences_result:
            return await cls.try_reply_or_send_message(msg.chat.id, 'Ошибка! Серии не найдены!',
                                                       reply_to_message_id=msg.message_id)
        page_max = sequences_result.count // ELEMENTS_ON_PAGE + (
            1 if sequences_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = ''.join([sequence.to_send for sequence in sequences_result.sequences[:5]]) \
                   + f'<code>Страница {page}/{page_max}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                         reply_markup=await get_keyboard(page, page_max, 's'))

    @classmethod
    @need_one_or_more_langs
    async def search_books_by_series(cls, msg: Message, series_id: int, page: int, after_download: bool = False):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        settings = await SettingsDB.get(msg.chat.id)

        search_result = await SequenceAPI.get_by_id(series_id, settings.get(), ELEMENTS_ON_PAGE, page)

        if search_result is None:
            await cls.bot.edit_message_text('Произошла ошибка :( Попробуйте позже', 
                                            chat_id=msg.chat.id, message_id=msg.message_id)
            return

        books = search_result.books
        if not books:
            return await cls.try_reply_or_send_message(msg.chat.id, 'Ошибка! Книги в серии не найдены!',
                                                       reply_to_message_id=msg.message_id)
        page_max = search_result.count // ELEMENTS_ON_PAGE + (1 if search_result.count % ELEMENTS_ON_PAGE != 0 else 0)
        msg_text = f"<b>{search_result.name}:</b>\n\n" + \
                   '\n\n\n'.join([book.to_send_book for book in books]
                           ) + f'\n\n<code>Страница {page}/{page_max}</code>'

        if not msg.reply_to_message:
            keyboard = await get_keyboard(1, page_max, 'bs') 
        else:
            keyboard = await get_keyboard(page, page_max, 'bs')

        if keyboard is None:
            keyboard = types.InlineKeyboardMarkup()
        
        if not after_download:
            keyboard.row(types.InlineKeyboardButton("⬇️ Скачать серию", callback_data=f"download_c_{series_id}"))
        else:
            keyboard.row(types.InlineKeyboardButton("✅ Книги отправляются!", 
                                                    callback_data=f"download_c_{series_id}"))

        if not msg.reply_to_message:
            await cls.try_reply_or_send_message(msg.chat.id, msg_text, parse_mode='HTML', 
                                                reply_markup=keyboard,
                                                reply_to_message_id=msg.message_id)
        else:
            await cls.bot.edit_message_text(msg_text, msg.chat.id, msg.message_id, parse_mode='HTML',
                                            reply_markup=keyboard)

    @classmethod
    @need_one_or_more_langs
    async def send_books_by_series(cls, query: types.CallbackQuery, series_id: int, file_type: str):
        await cls.search_books_by_series(query.message, series_id, 1, after_download=True)

        await cls.bot.send_chat_action(query.from_user.id, 'typing')
        search_result = await SequenceAPI.get_by_id(series_id, (await SettingsDB.get(query.from_user.id)).get(), 
                                                    1_000_000, 1)

        if search_result is None or not search_result.books:
            return

        for book in search_result.books:
            if book.file_type == "fb2":
                await cls.send_book(query.message, book.id, file_type)
            else:
                await cls.send_book(query.message, book.id, book.file_type)

    @classmethod
    @need_one_or_more_langs
    async def get_random_book(cls, msg: Message):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        book = await BookAPI.get_random((await SettingsDB.get(msg.chat.id)).get())
        if book is None:
            await cls.try_reply_or_send_message(msg.chat.id, "Пока бот не может это сделать, но скоро это исправят!")
            return

        await cls.try_reply_or_send_message(msg.chat.id, book.to_send_book, parse_mode='HTML',
                                            reply_to_message_id=msg.message_id)

    @classmethod
    @need_one_or_more_langs
    async def get_random_author(cls, msg: Message):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        author = await AuthorAPI.get_random((await SettingsDB.get(msg.chat.id)).get())
        if author is None:
            await cls.try_reply_or_send_message(msg.chat.id, "Пока бот не может это сделать, но скоро это исправят!")
            return

        await cls.try_reply_or_send_message(msg.chat.id, author.to_send, parse_mode='HTML',
                                            reply_to_message_id=msg.message_id)
            

    @classmethod
    @need_one_or_more_langs
    async def get_random_sequence(cls, msg: Message):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        sequence = await SequenceAPI.get_random((await SettingsDB.get(msg.chat.id)).get())
        if sequence is None:
            await cls.try_reply_or_send_message(msg.chat.id, "Пока бот не может это сделать, но скоро это исправят!")
            return

        await cls.try_reply_or_send_message(msg.chat.id, sequence.to_send, parse_mode="HTML",
                                            reply_to_message_id=msg.message_id)

    @classmethod
    async def send_book_detail(cls, msg: Message, book_id: int):
        book = await BookAPI.get_by_id(book_id)

        if book is None:
            await msg.reply("Книга не найдена!")
            return

        keyboard = None
        if book.annotation_exists:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("Посмотреть аннотацию", callback_data=f"b_ann_{book_id}_1")
            )

        await cls.try_reply_or_send_message(msg.chat.id, book.to_send_book_detail, parse_mode="HTML",
                                            reply_to_message_id=msg.message_id, reply_markup=keyboard)

    @classmethod
    @need_one_or_more_langs
    async def send_book_annotation(cls, msg: Message, book_id: int, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        annotation = await BookAnnotationAPI.get_by_book_id(book_id)

        if annotation is None:
            await cls.try_reply_or_send_message(msg.chat.id, "Нет аннотации для этой книги!",
                                                reply_to_message_id=msg.message_id)
            return

        msg_parts = split_text(annotation.body)

        text = msg_parts[page-1] + f'\n<code>Страница {page}/{len(msg_parts)}</code>'

        keyboard = await get_keyboard(page, len(msg_parts), f"b_ann_{book_id}", only_one=True)
        if keyboard is None:
            keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("Назад", callback_data=f"book_detail_{book_id}")
        )

        await cls.bot.edit_message_text(text, chat_id=msg.chat.id, message_id=msg.message_id,
                                        parse_mode="HTML", reply_markup=keyboard)

    @classmethod
    async def send_book_detail_edit(cls, msg: Message, book_id: int):
        book = await BookAPI.get_by_id(book_id)

        if book is None:
            await msg.reply("Книга не найдена!")
            return

        keyboard = None
        if book.annotation_exists:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("Посмотреть аннотацию", callback_data=f"b_ann_{book_id}_1")
            )

        await cls.bot.edit_message_text(book.to_send_book_detail, chat_id=msg.chat.id, 
                                        message_id=msg.message_id, parse_mode="HTML",
                                        reply_markup=keyboard)

    @classmethod
    async def send_author_annotation(cls, msg: Message, author_id: int):
        page = 1

        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        annotation = await AuthorAnnotationAPI.get_by_author_id(author_id)
        if annotation is None:
            await cls.try_reply_or_send_message(msg.chat.id, "Нет информации для этого автора!",
                                                reply_to_message_id=msg.message_id)
            return

        msg_parts = split_text(annotation.body)

        text = msg_parts[page-1] + f'\n\n<code>Страница {page}/{len(msg_parts)}</code>'

        keyboard = await get_keyboard(page, len(msg_parts), f"a_ann_{author_id}", only_one=True)

        await cls.try_reply_or_send_message(msg.chat.id, text,
                                            reply_to_message_id=msg.message_id, parse_mode="HTML", reply_markup=keyboard)

    @classmethod
    async def send_author_annotation_edit(cls, msg: Message, author_id: int, page: int):
        await cls.bot.send_chat_action(msg.chat.id, 'typing')

        annotation = await AuthorAnnotationAPI.get_by_author_id(author_id)
        if annotation is None:
            await cls.try_reply_or_send_message(msg.chat.id, "Нет информации для этого автора!",
                                                reply_to_message_id=msg.message_id)
            return

        msg_parts = split_text(annotation.body)

        text = msg_parts[page-1] + f'\n\n<code>Страница {page}/{len(msg_parts)}</code>'

        keyboard = await get_keyboard(page, len(msg_parts), f"a_ann_{author_id}", only_one=True)

        await cls.bot.edit_message_text(text, chat_id=msg.chat.id, message_id=msg.message_id,
                                        parse_mode="HTML", reply_markup=keyboard)

    @classmethod
    @need_one_or_more_langs
    async def send_update_log(cls, msg: types.Message, start_date: date, end_date: date, page: int, type_: str):
        update_log = await UpdateLogAPI.get_by_day(start_date, end_date, (await SettingsDB.get(msg.chat.id)).get(), 7, page)
        if not update_log:
            await cls.bot.edit_message_text('Обновления не найдены!', chat_id=msg.chat.id, message_id=msg.message_id)
            return
        page_count = update_log.count // ELEMENTS_ON_PAGE + (1 if update_log.count % ELEMENTS_ON_PAGE != 0 else 0)
        if start_date == end_date:
            msg_text = f'Обновления за {start_date.isoformat()}\n\n'
        else:
            msg_text = f'Обновления за {start_date.isoformat()} - {end_date.isoformat()}\n\n'
        msg_text += '\n\n\n'.join(book.to_send_book for book in update_log.books) \
                   + f'\n\n<code>Страница {page}/{page_count}</code>'
        await cls.bot.edit_message_text(msg_text, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='HTML',
                                        reply_markup=await get_keyboard(page, page_count, 
                                        f'ul_{type_}_{start_date.isoformat()}_{end_date.isoformat()}'))
