FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p static

ENV PYTHONPATH=/app:/app/MATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
