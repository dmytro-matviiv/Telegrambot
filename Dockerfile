# Використовуємо стабільну версію Python
FROM python:3.11-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей
COPY requirements-docker-minimal.txt /app/requirements.txt

# Створюємо віртуальне середовище та встановлюємо залежності
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Встановлюємо pip та залежності з обробкою помилок
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt || \
    (echo "Помилка встановлення залежностей, спробуємо альтернативний підхід" && \
     pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt)

# Копіюємо код додатку
COPY . /app/

# Встановлюємо шлях до віртуального середовища
ENV NIXPACKS_PATH=/opt/venv/bin:$NIXPACKS_PATH

# Встановлюємо змінні середовища
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Запускаємо бота
CMD ["python", "main.py"]
