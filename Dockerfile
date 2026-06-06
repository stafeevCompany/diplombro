FROM ubuntu:latest
LABEL authors="Aleksey"
FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /Fitness_club

# Установка зависимостей
COPY requirements.txt /Fitness_club/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копирование проекта
COPY . /Fitness_club/

# Команда запуска (может быть переопределена)
CMD ["gunicorn", "Fitness_club.wsgi:application", "--bind", "0.0.0.0:8000"]