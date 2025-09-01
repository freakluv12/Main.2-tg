FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для Pillow и других библиотек
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff5-dev \
    libopenjp2-7-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения
COPY . .

# Создаём директорию для загрузок
RUN mkdir -p uploads

# Открываем порт 8000
EXPOSE 8000

# Запускаем приложение с uvicorn
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
