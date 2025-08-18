# 🐳 Docker налаштування для Українського новинного бота

## Проблема

Якщо виникає помилка `ResolutionImpossible` при збірці Docker, це означає конфлікт залежностей у `requirements.txt`.

## ✅ Рішення

### 1. Використовуйте Docker-оптимізовані залежності

```bash
# Замість requirements.txt використовуйте
requirements-docker.txt
```

### 2. Оновлений Dockerfile

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-docker.txt /app/requirements.txt

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
```

### 3. Запуск через Docker Compose

```bash
# Створіть .env файл
cp env_example.txt .env
# Відредагуйте .env з вашими токенами

# Запустіть бота
docker-compose up --build
```

## 🔧 Альтернативні рішення

### Варіант 1: Локальне встановлення

```bash
# Використовуйте основні requirements.txt
python -m pip install -r requirements.txt
python main.py
```

### Варіант 2: Віртуальне середовище

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# або
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python main.py
```

### Варіант 3: Conda

```bash
conda create -n telegram-bot python=3.11
conda activate telegram-bot
pip install -r requirements.txt
python main.py
```

## 📋 Перевірка залежностей

### Тест сумісності

```bash
# Перевірте, чи можна встановити залежності
python -m pip install -r requirements.txt --dry-run
```

### Якщо є конфлікти

1. **Очистіть кеш pip**:
   ```bash
   pip cache purge
   ```

2. **Видаліть конфліктні пакети**:
   ```bash
   pip uninstall httpx httpcore h11
   pip install -r requirements.txt
   ```

3. **Використовуйте Docker-файл**:
   ```bash
   docker build -t telegram-bot .
   docker run --env-file .env telegram-bot
   ```

## 🚀 Рекомендований підхід

1. **Для розробки**: використовуйте `requirements.txt` з віртуальним середовищем
2. **Для продакшену**: використовуйте `requirements-docker.txt` з Docker
3. **Для тестування**: використовуйте `requirements-docker.txt` для стабільності

## 📝 Структура файлів

```
├── requirements.txt          # Основні залежності (для розробки)
├── requirements-docker.txt   # Docker-оптимізовані залежності
├── Dockerfile               # Docker збірка
├── docker-compose.yml       # Docker Compose
├── .dockerignore            # Docker оптимізація
└── DOCKER_SETUP.md         # Ця інструкція
```

## 🆘 Якщо проблема залишається

1. **Перевірте версію Python**: рекомендується 3.11
2. **Очистіть кеш**: `pip cache purge`
3. **Використовуйте Docker**: `docker-compose up --build`
4. **Перевірте логи**: `docker-compose logs telegram-bot`
