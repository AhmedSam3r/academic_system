# How To Run The Project

1. poetry env use python3.12
2. poetry install
3. poetry run pre-commit install
4. poetry run python manage.py createsuperuser
5. poetry run python manage.py runserver
6. poetry run celery -A config worker -Q main,main-retry -l info
   1. poetry run celery -A config worker -l info
      1. this consumes any queues even dlq, leading to message loss
      2. it also leads to messages being consumed from retry queue immadiately after being 