import io
from typing import List, Optional
from datetime import date

import aiohttp
from aiohttp import ClientTimeout, ServerDisconnectedError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import BytesResult

try:
    import ujson as json
except ImportError:
    import json


from config import Config


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
    def to_send_book_without_author(self) -> str:
        res = f'📖 <b>{self.title}</b> | {self.lang}\n'
        if self.annotation_exists:
            res += f"Аннотация: /b_info_{self.id}\n"
        if self.file_type == 'fb2':
            return res + f'⬇ fb2: /fb2_{self.id}\n⬇ epub: /epub_{self.id}\n⬇ mobi: /mobi_{self.id}\n\n'
        else:
            return res + f'⬇ {self.file_type}: /{self.file_type}_{self.id}\n\n'

    def get_download_link(self, file_type: str) -> str:
        return f"{Config.FLIBUSTA_SERVER}/book/download/{self.id}/{file_type}"

    def get_public_download_link(self, file_type: str) -> str:
        return f"{Config.FLIBUSTA_SERVER_PUBLIC}/book/download/{self.id}/{file_type}"


class BookWithAuthor(Book):
    def __init__(self, obj: dict):
        Book.__init__(self, obj)

    @property
    def authors(self):
        return [Author(a) for a in self.obj["authors"]] if self.obj.get("authors", None) else []

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


class BookSearchResult:
    books: List[BookWithAuthor]

    def __init__(self, obj: dict):
        self.count: int = obj["count"]

        if self.count != 0:
            self.books = [BookWithAuthor(b) for b in obj["result"]]
        else:
            self.books = []

    def __bool__(self):
        return bool(self.count)


class BookAPI:
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
    
    @staticmethod
    async def get_by_id(book_id: int) -> Optional[BookWithAuthor]:
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/book/{book_id}") as response:
            if response.status != 200:
                return None
            return BookWithAuthor(await response.json())

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
    async def get_random(allowed_langs: List[str]) -> Optional[BookWithAuthor]:
        async with aiohttp.request("GET", 
                                   f"{Config.FLIBUSTA_SERVER}/book/random/{json.dumps(allowed_langs)}") as response:
            if response.status != 200:
                return None
            return BookWithAuthor(await response.json())


class Author:
    def __init__(self, obj: dict):
        self.obj = obj

    def __del__(self):
        del self.obj

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


class AuthorWithBooks(Author):
    def __init__(self, obj: dict):
        Author.__init__(self, obj["result"])

        self.count = obj.get("count", None)
    
    def __bool__(self):
        return self.count != 0

    @property
    def books(self):
        return [Book(x) for x in self.obj["books"]] if self.obj.get("books", None) else []


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


class AuthorAPI:
    @staticmethod
    async def by_id(author_id: int, allowed_langs, limit: int, page: int) -> Optional[AuthorWithBooks]:
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/author/{author_id}/{json.dumps(allowed_langs)}/{limit}/{page}") as response:
            if response.status != 200:
                return None
            return AuthorWithBooks(await response.json())

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
    async def get_random(allowed_langs: List[str]) -> Optional[Author]:
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/author/random/{json.dumps(allowed_langs)}") as response:
            if response.status != 200:
                return None
            return Author(await response.json())


class Sequence:
    def __init__(self, obj):
        self.obj = obj

    @property
    def id(self):
        return self.obj['id']

    @property
    def name(self):
        return self.obj['name']


class SequenceWithBooks(Sequence):
    def __init__(self, obj: dict):
        Sequence.__init__(self, obj["result"])

        self.count = obj["count"]

    def __bool__(self):
        return self.count != 0

    @property
    def books(self) -> List[BookWithAuthor]:
        if not self.obj:
            return []
        return [BookWithAuthor(x) for x in self.obj['books']] if self.obj['books'] else []


class SequenceWithAuthors(Sequence):
    def __init__(self, obj: dict):
        Sequence.__init__(self, obj)
    
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
                res += "<b> и другие</b>\n"
        else:
            res += '\n'
        res += f'/s_{self.id}\n\n'
        return res


class SequenceSearchResult:
    sequences: List[SequenceWithAuthors]

    def __init__(self, obj: dict):
        self.count: int = obj["count"]

        if self.count != 0:
            self.sequences = [SequenceWithAuthors(s) for s in obj["result"]]
        else:
            self.sequences = []

    def __bool__(self):
        return self.count != 0


class SequenceAPI:
    @staticmethod
    async def get_by_id(seq_id: int, allowed_langs: List[str], limit: int, page: int) -> Optional[SequenceWithBooks]:
        async with aiohttp.request(
                "GET",
                f"{Config.FLIBUSTA_SERVER}/sequence/{seq_id}/{json.dumps(allowed_langs)}/{limit}/{page}") as response:
            if response.status != 200:
                return None
            response_json = await response.json()
            return SequenceWithBooks(response_json)

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
    async def get_random(allowed_langs: List[str]) -> Optional[SequenceWithAuthors]:
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/sequence/random/{json.dumps(allowed_langs)}"
                                   ) as response:
            if response.status != 200:
                return None
            return SequenceWithAuthors(await response.json())


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


class BookAnnotationAPI:
    @staticmethod
    async def get_by_book_id(book_id: int) -> Optional[BookAnnotation]:
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/annotation/book/{book_id}") as response:
            if response.status != 200:
                return None
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


class AuthorAnnotationAPI:
    @staticmethod
    async def get_by_author_id(book_id: int) -> Optional[AuthorAnnotation]:
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/annotation/author/{book_id}") as response:
            if response.status != 200:
                return None
            return AuthorAnnotation(await response.json())


class UpdateLog:
    books: List[BookWithAuthor]

    def __init__(self, obj: dict):
        self.count = obj['count']

        if self.count != 0:
            self.books = [BookWithAuthor(b) for b in obj["result"]]
        else:
            self.books = []
    
    def __bool__(self):
        return self.count != 0


class UpdateLogAPI:
    @staticmethod
    async def get_by_day(start_date: date, end_date: date, 
                         allowed_langs: List[str], limit: int, page: int) -> Optional[UpdateLog]:
        start_date_d = start_date.isoformat()
        end_date_d = end_date.isoformat()
        async with aiohttp.request(
            "GET", 
            f"{Config.FLIBUSTA_SERVER}/book/update_log_range/{start_date_d}/{end_date_d}/{json.dumps(allowed_langs)}/{limit}/{page}"
                ) as response:
            if response.status != 200:
                return None
            return UpdateLog(await response.json())


class DownloadAPI:
    @staticmethod
    async def update(book_id: int, user_id: int):
        async with aiohttp.request("GET", f"{Config.FLIBUSTA_SERVER}/download_counter/update/{book_id}/{user_id}") as resp:
            pass
