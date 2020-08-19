from typing import Optional
import os


class Config:
    BOT_TOKEN: str

    BOT_NAME: str

    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int

    FLIBUSTA_SERVER: str
    FLIBUSTA_SERVER_PUBLIC: str

    FLIBUSTA_CHANNEL_SERVER: Optional[str]

    WEBHOOK_PORT: int
    WEBHOOK_HOST: str

    SERVER_HOST: str
    SERVER_PORT: int

    REDIS_HOST: str
    REDIS_PASSWORD: str

    CHATBASE_API_KEY: Optional[str]

    DSN: str

    @classmethod
    def configurate(cls):
        cls.BOT_TOKEN = os.environ['BOT_TOKEN']
        cls.BOT_NAME = os.environ['BOT_NAME']
        
        cls.DB_NAME = os.environ.get('DB_NAME', cls.BOT_NAME)
        cls.DB_USER = os.environ.get('DB_USER', cls.BOT_NAME)
        cls.DB_PASSWORD = os.environ['DB_PASSWORD']
        cls.DB_HOST = os.environ.get('DB_HOST', 'localhost')
        cls.DB_PORT = os.environ.get('DB_PORT', 5432)

        cls.DSN = f"postgresql://{cls.DB_HOST}:5432/{cls.DB_USER}"

        cls.FLIBUSTA_SERVER = os.environ['FLIBUSTA_SERVER']
        cls.FLIBUSTA_SERVER_PUBLIC = os.environ['FLIBUSTA_SERVER_PUBLIC']

        cls.FLIBUSTA_CHANNEL_SERVER = os.environ.get('FLIBUSTA_CHANNEL_SERVER', None)

        cls.WEBHOOK_PORT = os.environ['WEBHOOK_PORT']
        cls.WEBHOOK_HOST = os.environ['WEBHOOK_HOST'] # f"https://kurbezz.ru:{cls.WEBHOOK_PORT}/{cls.BOT_NAME}"

        cls.SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
        cls.SERVER_PORT = os.environ['SERVER_PORT']

        cls.CHATBASE_API_KEY = os.environ.get('CHATBASE_API_KEY', None)


Config.configurate()
