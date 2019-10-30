# Flibusta Bot

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e457160fdaf545cc8a031bb14146204c)](https://www.codacy.com/manual/Kurbezz/async_flibusta_bot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Kurbezz/async_flibusta_bot&amp;utm_campaign=Badge_Grade)

Этот бот для загрузки книг с сайта Флибуста.

Попробовать можно тут: 

Android: [@flibusta_rebot](https://www.t.me/flibusta_rebot)

IOS: [@flibusta_new_copy_rebot](https://www.t.me/flibusta_new_copy_rebot)

## Возможности
* Поиск книг по авторам
* Поиск авторов
* Показ книг автора
* Загрузка книг в fb2, epub, mobi (иногда pdf, doc, djvu)
* Inline-поиск

## Скриншоты

![](/pics/screenshot_1.jpg) | ![](/pics/screenshot_2.jpg) | ![](/pics/screenshot_3.jpg) |
-|-|-
![](/pics/screenshot_4.jpg) | ![](/pics/screenshot_5.jpg) | ![](/pics/screenshot_6.jpg) |
![](/pics/screenshot_7.jpg) | ![](/pics/screenshot_9.jpg) | ![](/pics/screenshot_10.jpg) |

## Настройка
### 1. Настройка бота
1. Создать бота у [@BotFather](https://www.t.me/BotFather)
2.  Вписать token в BOT_TOKEN
3. Вписать username в BOT_NAME
### 2. Настройка БД
1. Установить и настроить PostgreSQL
2. Вписать имя БД в DB_NAME
3. Вписать имя пользователя от БД в DB_USER
4. Вписать пароль от БД в DB_PASSWORD
5. Вписать адрес БД в DB_HOST
6. Вписать порт БД в DB_PORT
7. Выполнить миграцию с помощью manage.py
### 3. Настроить [flibusta server](https://github.com/Kurbezz/flibusta_server)
### 4. Настройка webhook
1. Вписать порт webhook'a в WEBHOOK_PORT
2. Вписать адрес webhook'a в WEBHOOK_HOST
## 5. Настройка сервера
1. Вписать прослушиваемые адреса в SERVER_HOST
2. Вписать прослушиваемый порт в SERVER_PORT
### 6. Настройка ChatBase 
1. Вписать ChatBase token в CHATBASE_API_TOKEN
### 7. Установка зависимостей
1. Установить зависимости из requirements.txt
## Запуск
Запустить main.py
