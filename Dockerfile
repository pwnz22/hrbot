FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем необходимые директории
RUN mkdir -p downloads exports logs

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1

# По умолчанию запускаем бот
CMD ["python", "-m", "bot.main"]
