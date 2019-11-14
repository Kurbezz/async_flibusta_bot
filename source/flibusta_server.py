# TODO: refactor all

import io
from typing import List, Optional
from datetime import date

import aiohttp
from aiohttp import ClientTimeout, ServerDisconnectedError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

try:
    import ujson as json
except ImportError:
    import json


from config import Config


class NoContent(Exception):
    pass


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


class AuthorSearchResult:
    authors: List["Author"]

    def __init__(self, obj: dict):
        self.count: int = obj["count"]

        if self.count != 0:
            self.authors = [Author(a) for a in obj["result"]]
        else:
            self.authors = []

    def __bool__(self):
        return bool(self.count)


class BookSearchResult:
    books: List["Book"]

    def __init__(self, obj: dict):
        self.count: int = obj["count"]

        if self.count != 0:
            self.books = [Book(b) for b in obj["result"]]
        else:
            self.books = []

    def __bool__(self):
        return bool(self.count)


class SequenceSearchResult:
    sequences: List['Sequence']

    def __init__(self, obj: dict):
        self.count: int = obj["count"]

        if self.count != 0:
            self.sequences = [Sequence(s) for s in obj["result"]]
        else:
            self.sequences = []

    def __bool__(self):
        return self.count != 0


class Author:
    def __init__(self, obj: dict):
        self.count = obj.get("count", None)

        if obj.get("result", None) is None:
            self.obj = obj
        else:
            self.obj = obj["result"]

    def __del__(self):
        del self.obj

    def __bool__(self):
        return self.count != 0

    @property
    def id(self):
        return self.obj["id"]

    @property
    def first_name(self):
        return self.obj["first_name"]

    @property
    def last_name(self):
        return self.obj["last_name"]

    @property
    def middle_name(self):
        return self.obj["middle_name"]

    @property
    def annotation_exists(self):
        return self.obj["annotation_exists"]

    @property
    def books(self):
        return [Book(x) for x in self.obj["books"]] if self.obj.get("books", None) else []

    @property
    def normal_name(self) -> str:
        temp = ''
        if self.last_name:
            temp = self.last_name
        if self.first_name:
            if temp:
                temp += " "
            temp += self.first_name
        if self.middle_name:
            if temp:
                temp += " "
            temp += self.middle_name
        return temp

    @property
    def short(self) -> str:
        temp = ''
        if self.last_name:
            temp += self.last_name
        if self.first_name:
            if temp:
                temp += " "
            temp += self.first_name[0]
        if self.middle_name:
            if temp:
                temp += " "
            temp += self.middle_name[0]
        return temp

    @property
    def to_send(self) -> str:
        result = f'👤 <b>{self.normal_name}</b>\n/a_{self.id}'
        if self.annotation_exists:
            result += f"\nОб авторе: /a_info_{self.id}"
        return result + "\n\n"

    @staticmethod
    async def by_id(author_id: int, allowed_langs, limit: int, page: int) -> "Author":
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/author/{author_id}/{json.dumps(allowed_langs)}/{limit}/{page}") as response:
            if response.status != 200:
                raise NoContent
            return Author(await response.json())

    @staticmethod
    async def search(query: str, allowed_langs: List[str], limit: int, page: int) -> Optional[AuthorSearchResult]:
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/author/search/{json.dumps(allowed_langs)}/{limit}/{page}/{query}") \
                    as response:
            if response.status != 200:
                return None
            return AuthorSearchResult(await response.json())

    @staticmethod
    async def get_random(allowed_langs: List[str]) -> "Author":
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/author/random/{json.dumps(allowed_langs)}") as response:
            if response.status != 200:
                raise NoContent
            return Author(await response.json())


class Book:
    def __init__(self, obj: dict):
        self.obj = obj

    def __del__(self):
        del self.obj

    @property
    def id(self):
        return self.obj["id"]

    @property
    def title(self):
        return self.obj["title"]

    @property
    def lang(self):
        return self.obj["lang"]

    @property
    def file_type(self):
        return self.obj["file_type"]

    @property
    def annotation_exists(self):
        return self.obj["annotation_exists"]

    @property
    def authors(self):
        return [Author(a) for a in self.obj["authors"]] if self.obj.get("authors", None) else None

    @property
    def caption(self) -> str:
        if not self.authors:
            return "📖 " + self.title

        authors_text = '\n'.join(["👤 " + author.normal_name for author in self.authors[:15]])
        if len(self.authors) > 15:
            authors_text += "\n" + "и т.д."
        return "📖 " + self.title + '\n\n' + authors_text

    def download_caption(self, file_type) -> str:
        return self.caption + f'\n\n⬇ <a href="{self.get_public_download_link(file_type)}">Скачать</a>'

    @property
    def short_info(self) -> str:
        return f"{self.title} \n {' '.join([a.short for a in self.authors])}"

    @property
    def share_text(self) -> str:
        basic_url = f"https://www.t.me/{Config.BOT_NAME}?start="
        res = f'*{self.title}* | {self.lang}\n'
        if self.authors:
            for a in self.authors:
                res += f'*{a.normal_name}*\n'
        else:
            res += '\n'
        if self.file_type == 'fb2':
            return res + (f'⬇ [Скачать fb2]({basic_url + "fb2_" + str(self.id)}) \n'
                          f'⬇ [Скачать epub]({basic_url + "epub_" + str(self.id)}) \n'
                          f'⬇ [Скачать mobi]({basic_url + "mobi_" + str(self.id)})')
        else:
            return res + f'⬇ [Скачать {self.file_type}]({basic_url + self.file_type + "_" + str(self.id)})'

    @property
    def share_markup(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Не открывается!", callback_data=f"remove_cache"),
            InlineKeyboardButton("Поделиться", switch_inline_query=f"share_{self.id}")
        )
        return markup

    @property
    def share_markup_without_cache(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Поделиться", switch_inline_query=f"share_{self.id}")
        )
        return markup

    def get_download_markup(self, file_type: str) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Скачать', url=self.get_download_link(file_type)))
        return markup

    @property
    def to_send_book(self) -> str:
        res = f'📖 <b>{self.title}</b> | {self.lang}\n'
        if self.annotation_exists:
            res += f"Аннотация: /b_info_{self.id}\n"
        if self.authors:
            for a in self.authors[:15]:
                res += f'👤 <b>{a.normal_name}</b>\n'
            if len(self.authors) > 15:
                res += "  и другие\n\n"
        else:
            res += '\n'
        if self.file_type == 'fb2':
            return res + f'⬇ fb2: /fb2_{self.id}\n⬇ epub: /epub_{self.id}\n⬇ mobi: /mobi_{self.id}\n\n'
        else:
            return res + f'⬇ {self.file_type}: /{self.file_type}_{self.id}\n\n'

    @property
    def to_send_book_without_author(self) -> str:
        res = f'📖 <b>{self.title}</b> | {self.lang}\n'
        if self.annotation_exists:
            res += f"Аннотация: /b_info_{self.id}\n"
        if self.file_type == 'fb2':
            return res + f'⬇ fb2: /fb2_{self.id}\n⬇ epub: /epub_{self.id}\n⬇ mobi: /mobi_{self.id}\n\n'
        else:
            return res + f'⬇ {self.file_type}: /{self.file_type}_{self.id}\n\n'

    @staticmethod
    async def get_by_id(book_id: int) -> "Book":
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/book/{book_id}") as response:
            if response.status == 204:
                raise NoContent
            return Book(await response.json())

    @staticmethod
    async def search(query: str, allowed_langs: List[str], limit: int, page: int) -> Optional[BookSearchResult]:
        async with aiohttp.request(
            "GET",
                f"{Config.FLIBUSTA_SERVER}/book/search/{json.dumps(allowed_langs)}/{limit}/{page}/{query}"
        ) as response:
            if response.status != 200:
                return None
            return BookSearchResult(await response.json())

    @staticmethod
    async def get_random(allowed_langs: List[str]) -> "Book":
        async with aiohttp.request("GET", 
                                   f"{Config.FLIBUSTA_SERVER}/book/random/{json.dumps(allowed_langs)}") as response:
            if response.status != 200:
                raise NoContent
            return Book(await response.json())

    def get_download_link(self, file_type: str) -> str:
        return f"{Config.FLIBUSTA_SERVER}/book/download/{self.id}/{file_type}"

    def get_public_download_link(self, file_type: str) -> str:
        return f"{Config.FLIBUSTA_SERVER_PUBLIC}/book/download/{self.id}/{file_type}"

    @staticmethod
    async def download(book_id: int, file_type: str) -> Optional[BytesResult]:
        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=600)) as session:
                async with session.get(f"{Config.FLIBUSTA_SERVER}/book/download/{book_id}/{file_type}",
                                       timeout=None) as response:
                    if response.status != 200:
                        return None
                    return BytesResult(await response.content.read())
        except ServerDisconnectedError:
            return None


class Sequence:
    def __init__(self, obj, count=None):
        self.obj = obj
        self.count = count

    def __bool__(self):
        return self.count != 0

    @property
    def id(self):
        return self.obj['id']

    @property
    def name(self):
        return self.obj['name']

    @property
    def books(self) -> List[Book]:
        if not self.obj:
            return []
        return [Book(x) for x in self.obj['books']] if self.obj['books'] else []

    @property
    def authors(self) -> List[Author]:
        return [Author(x) for x in self.obj['authors']] if self.obj['authors'] else []

    @property
    def to_send(self) -> str:
        res = f'📚 <b>{self.name}</b>\n'
        if self.authors:
            for a in self.authors[:5]:
                res += f'👤 <b>{a.normal_name}</b>\n'
            if len(self.authors) > 5:
                res += "<b> и другие</b>\n\n"
        else:
            res += '\n'
        res += f'/s_{self.id}\n\n'
        return res

    @staticmethod
    async def get_by_id(seq_id: int, allowed_langs: List[str], limit: int, page: int) -> 'Sequence':
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/sequence/{seq_id}/{json.dumps(allowed_langs)}/{limit}/{page}") as response:
            if response.status != 200:
                return Sequence(None, 0)
            response_json = await response.json()
            return Sequence(response_json["result"], response_json["count"])

    @staticmethod
    async def search(query: str, allowed_langs: List[str], limit: int, page: int) -> Optional[SequenceSearchResult]:
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/sequence/search/{json.dumps(allowed_langs)}/{limit}/{page}/{query}"
        ) as response:
            if response.status != 200:
                return None
            return SequenceSearchResult(await response.json())

    @staticmethod
    async def get_random(allowed_langs: List[str]) -> "Sequence":
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/sequence/random/{json.dumps(allowed_langs)}"
                                   ) as response:
            if response.status != 200:
                raise NoContent
            return Sequence(await response.json())


class BookAnnotation:
    def __init__(self, obj):
        self.obj = obj

    @property
    def book_id(self):
        return self.obj["book_id"]

    @property
    def title(self):
        return self.obj.get("title", "")

    @property
    def body(self):
        return self.obj.get("body", "").replace('<p class="book">', "").replace('</p>', "").replace(
            "<p class=book>", "").replace("<a>", "").replace("</a>", "").replace("</A>", "").replace(
            "[b]", "").replace("[/b]", "")

    @property
    def photo_link(self):
        if not self.obj.get("file"):
            return None
        return f"https://flibusta.is/ib/{self.obj['file']}"

    @property
    def to_send(self):
        return f"{self.title} {self.body}"

    @staticmethod
    async def get_by_book_id(book_id: int):
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/annotation/book/{book_id}") as response:
            if response.status != 200:
                raise NoContent
            return BookAnnotation(await response.json())


class AuthorAnnotation:
    def __init__(self, obj):
        self.obj = obj

    @property
    def author_id(self):
        return self.obj["author_id"]

    @property
    def title(self):
        return self.obj.get("title", "")

    @property
    def body(self):
        return self.obj.get("body", "").replace('<p class="book">', "").replace('</p>', "").replace(
            "<p class=book>", "").replace("<a>", "").replace("</a>", "").replace("</A>", "").replace(
            "[b]", "").replace("[/b]", "")

    @property
    def photo_link(self):
        if not self.obj.get("file"):
            return None
        return f"https://flibusta.is/ia/{self.obj['file']}"

    @property
    def to_send(self):
        return f"{self.title} {self.body}"

    @staticmethod
    async def get_by_author_id(book_id: int):
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/annotation/author/{book_id}") as response:
            if response.status != 200:
                raise NoContent
            return AuthorAnnotation(await response.json())


class UpdateLog:
    books: List[Book]

    def __init__(self, obj: dict):
        self.count = obj['count']

        if self.count != 0:
            self.books = [Book(b) for b in obj["result"]]
        else:
            self.books = []
    
    def __bool__(self):
        return self.count != 0

    @staticmethod
    async def get_by_day(start_date: date, end_date: date, 
                         allowed_langs: List[str], limit: int, page: int) -> Optional["UpdateLog"]:
        start_date = start_date.isoformat()
        end_date = end_date.isoformat()
        async with aiohttp.request(
            "GET", 
            f"{Config.FLIBUSTA_SERVER}/book/update_log_range/{start_date}/{end_date}/{json.dumps(allowed_langs)}/{limit}/{page}"
                ) as response:
            if response.status != 200:
                return None
            return UpdateLog(await response.json())


class Download:
    @staticmethod
    async def update(book_id: int, user_id: int):
        await aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/download_counter/update/{book_id}/{user_id}")
