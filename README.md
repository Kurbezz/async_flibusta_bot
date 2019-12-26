# Flibusta Bot

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e457160fdaf545cc8a031bb14146204c)](https://www.codacy.com/manual/Kurbezz/async_flibusta_bot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Kurbezz/async_flibusta_bot&amp;utm_campaign=Badge_Grade)

Этот бот для загрузки книг с сайта Флибуста.

Попробовать можно тут: 

Android: [@flibusta_rebot](https://www.t.me/flibusta_rebot)

IOS: [@flibusta_new_copy_rebot](https://www.t.me/flibusta_new_copy_rebot)

## Возможности
* Поиск книг/авторов/серий
* Показ книг автора
* Показ книг серии
* Загрузка книг в fb2, epub, mobi (иногда pdf, doc, djvu)
* Inline-поиск

## Скриншоты

![](/pics/screenshot_1.jpg) | ![](/pics/screenshot_2.jpg) | ![](/pics/screenshot_3.jpg) |
-|-|-
![](/pics/screenshot_4.jpg) | ![](/pics/screenshot_5.jpg) | ![](/pics/screenshot_6.jpg) |
![](/pics/screenshot_7.jpg) | ![](/pics/screenshot_9.jpg) | ![](/pics/screenshot_10.jpg) |

## Настройка
### 1. Настройка бота
1.1 Создать бота у [@BotFather](https://www.t.me/BotFather)
1.2 Получить токен
### 2. Настройка БД
2.1 Установить и настроить PostgreSQL
2.2 Создать пользователя и бд в соотвествии с username бота
### 3. Установить и настроить [flibusta server](https://github.com/Kurbezz/flibusta_server)
### 4. Установка зависимостей
4.1 Установить зависимости из requirements.txt
4.2 (Опционально, для большей производительности) Установить зависимости из optional-requirements.txt
### 5. Настроить Nginx
5.1 Установить Nginx
5.2 Настроить по [шаблону](https://github.com/Kurbezz/nginx_config_examples/blob/master/examples/bot.conf)
## 5. Запуск
5.1 Запустить main.py передавая конфигурацию в аргументах
