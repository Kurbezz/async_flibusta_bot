from typing import Optional

import fire


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
    def configurate(cls, token: str, bot_name: str,
                    db_password: str,
                    server_port: int,
                    flibusta_server: str,
                    flibusta_server_public: str,
                    server_host: str = "localhost",
                    webhook_port: int = 8443,
                    db_host: str = "localhost", 
                    db_port: int = 5432,
                    chatbase_api_key: Optional[str] = None,
                    flibusta_channel_server: Optional[str] = None):
        cls.BOT_TOKEN = token
        cls.BOT_NAME = bot_name
        
        cls.DB_NAME = cls.DB_USER = bot_name
        cls.DB_PASSWORD = db_password
        cls.DB_HOST = db_host
        cls.DB_PORT = db_port
        cls.DSN = f"postgresql://{cls.DB_HOST}:5432/{cls.DB_USER}"

        cls.FLIBUSTA_SERVER = flibusta_server
        cls.FLIBUSTA_SERVER_PUBLIC = flibusta_server_public

        cls.FLIBUSTA_CHANNEL_SERVER = flibusta_channel_server

        cls.WEBHOOK_PORT = webhook_port
        cls.WEBHOOK_HOST = f"https://kurbezz.ru:{cls.WEBHOOK_PORT}/{cls.BOT_NAME}"

        cls.SERVER_HOST = server_host
        cls.SERVER_PORT = server_port

        cls.CHATBASE_API_KEY = chatbase_api_key


fire.Fire(Config.configurate)
