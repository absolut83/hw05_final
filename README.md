# Yatube
### Сайт для публикации дневников на django.

Инструкция для развертывания проекта локально
- Клонируйте репозиторий:
```
git clone https://github.com/absolut83/hw05_final.git
```
- Перейдите в директорию с проектом
- Создайте файл *.env*, в котором укажите переменную окружения *SECRET_KEY*.
- Создайте виртуальное окружение:
```
python -m venv venv
```
- Активируйте виртуальное окружение:

для windows: `source venv/Scripts/activate`

для linux: `source venv/bin/activate`

- Установите зависимости:
```
pip install -r requirements.txt
```
- Выполните миграции:
```
python manage.py migrate
```
- Запустите сервер Django:
```
python manage.py runserver
```

## Об авторе
### Виталий Яремчук

absolut83@mail.ru

Telegram - @kuvalda684

#### Используемые технологии
- Python 3.7.7
- Django 2.2.6
