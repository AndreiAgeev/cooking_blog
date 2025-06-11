# Cooking blog
## Описание:
Проект блога для рецептов.
Проект представляет собой платформу, где пользователи могут создавать и делиться своими рецептами блюд, а также подписываться друг на друга. Обеспечен различный доступ для обычных пользователей, зарегестрированных пользователей и администраторов. Проект написан на React + DRF + PostgreSQL Nginx (в рамках курса для проекта был написан именно backend на DRF). Проект запускается с помощью Docker.

## Документация для backend
Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost/api/docs/ будет доступна спецификация API.

## Как запустить проект на локальной машине
Скопировать репозиторий и перейти в него. В папке backend cоздать и активировать вирутальное окружение:
```
python3 -m venv venv
```
```
source env/bin/activate # для Linux
source env/Scripts/activate # для Windows
```
Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Из папки foodgram выполнить команду docker compose up и подождать, пока проект соберётся. Далее необходимо будет выполнить несколько команд в контейнере backend:
```
docker compose exec backend python manage.py migrate - применяет миграции в БД
docker compose backend python manage.py loadjson - загружает в БД ингредиенты из файлов в папке data
docker compose exec backend python manage.py collectstatic - собирает статику бэкенда
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/ - копирует собранную статистку в выделенную папку, связанную с volume static в Docker
docker compose exec backend python manage.py createsuperuser - необходимо будет создать суперюзера
```
Проект будет доступен по ссылке http://localhost/. После запуска необходимо будет по ссылке http://localhost/admin/ войти в админку с теми данными, по которым был создан суперюзер, и создать несколько тегов.
