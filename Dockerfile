# syntax=docker/dockerfile:1


ARG PYTHON_VERSION=3.11.8
FROM python:${PYTHON_VERSION}-alpine as base

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1 
WORKDIR /app


COPY . .
RUN pip install -r requirements.txt

EXPOSE 8001

CMD uvicorn main:wdm --host 0.0.0.0 --port 8001
