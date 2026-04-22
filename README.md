# API для платформы художников и иллюстраторов - "Нить".


## Функционал

- Регистрация и аутентификация
- Профили, настройка информации профиля, настройка публичности профиля
- Система подписок на пользователей
- Поиск по пользователям
- Публикация постов с изображением
- Поддержка системы тегов, поиск по тегам, популярные
- Взаимодействие с постами, комментарии, лайки, добавление в избранное
- Управление пользователями, постами, комментариями, тегами через админ-интерфейс

## Структура проекта


├── app/
│   ├── routes/          # эндпоинты
│   │   ├── auth.py      # аутентификация
│   │   ├── users.py     # работа с пользователями
│   │   ├── posts.py     # посты
│   │   ├── comments.py  # комментарии
│   │   └── tags.py      # теги
│   ├── admin.py         # админка
│   ├── config.py        # конфигурация .env
│   ├── database.py      # подключение к бд
│   ├── models.py        # модели
│   ├── schemas.py       # схемы
│   └── main.py          # точка входа
├── uploads/             # изображения
│   ├── avatars/         
│   ├── headers/         
│   └── *.jpg            
├── .env.example         # пример переменных окружения
├── .gitignore
├── requirements.txt
├── nit.db               
└── README.md

## Стек
Веб - FastAPI
ORM - SQLAlchemy
База данных - SQLite
Аутентификация - JWT (python-jose)
Пароли - Bcrypt (passlib)
Валидация данных - Pydantic
Админ-интерфейс - SQLAdmin

## Установка

Клонировать репозиторий
```bash
git clone https://github.com/polosatikkk/kartinki-backend.git
cd nit-backend
```
Создать виртуальное окружение
```python
python -m venv venv
```
Активация окружения
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

Зависимости
```python
pip install -r requirements.txt
```
.env файл с ключами
cp .env.example .env

```python
uvicorn app.main:app --reload  
```






