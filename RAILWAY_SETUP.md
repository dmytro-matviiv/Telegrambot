# 🚂 Railway налаштування для Українського новинного бота

## Проблема

Бот не запускається в Railway хостингу.

## ✅ Рішення

### 1. Створено спеціальні файли для Railway

- **`railway.json`** - налаштування Railway
- **`requirements-railway.txt`** - стабільні залежності
- **`Dockerfile`** - оптимізований для Railway
- **`healthcheck.py`** - перевірка здоров'я додатку

### 2. Налаштування Railway

#### Крок 1: Підключення репозиторію
1. Зайдіть на [Railway.app](https://railway.app)
2. Створіть новий проект
3. Підключіть GitHub репозиторій
4. Виберіть гілку `feature/alerts-grouping-and-docker`

#### Крок 2: Налаштування змінних середовища
Додайте наступні змінні в Railway:

```env
BOT_TOKEN=ваш_токен_бота
CHANNEL_ID=@ваш_канал
ALERTS_API_TOKEN=токен_api_тривог
```

#### Крок 3: Налаштування збірки
- **Builder**: Dockerfile
- **Dockerfile Path**: Dockerfile
- **Start Command**: `python main.py`

### 3. Перевірка логів

Якщо бот не запускається, перевірте логи в Railway:

1. Зайдіть у ваш проект
2. Виберіть сервіс
3. Перейдіть на вкладку "Deployments"
4. Натисніть на останній deployment
5. Перегляньте логи

### 4. Типові проблеми та рішення

#### Проблема: "Module not found"
**Рішення**: Перевірте `requirements-railway.txt` та `Dockerfile`

#### Проблема: "Environment variables not set"
**Рішення**: Додайте всі необхідні змінні в Railway

#### Проблема: "Port already in use"
**Рішення**: Railway автоматично призначає порт

#### Проблема: "Build failed"
**Рішення**: Перевірте логи збірки та `Dockerfile`

### 5. Тестування локально

```bash
# Тест health check
python healthcheck.py

# Тест Docker збірки
docker build -t railway-test .
docker run --env-file .env railway-test
```

### 6. Структура файлів для Railway

```
├── railway.json                    # Налаштування Railway
├── requirements-railway.txt        # Залежності для Railway
├── Dockerfile                     # Docker збірка
├── healthcheck.py                 # Health check
├── main.py                        # Основний файл
├── config.py                      # Конфігурація
├── air_alerts_monitor.py          # Монітор тривог
├── news_collector.py              # Збір новин
└── telegram_publisher.py          # Публікація в Telegram
```

### 7. Команди для оновлення

```bash
# Оновлення коду
git add .
git commit -m "Fix Railway deployment"
git push origin feature/alerts-grouping-and-docker

# Railway автоматично перезбирає та перезапускає
```

### 8. Моніторинг

- **Health Check**: `/health` endpoint
- **Логи**: Railway Dashboard
- **Метрики**: CPU, Memory, Network
- **Перезапуск**: Автоматичний при помилках

### 9. Якщо проблема залишається

1. **Перевірте логи Railway**
2. **Перевірте змінні середовища**
3. **Перевірте Docker збірку локально**
4. **Зв'яжіться з підтримкою Railway**

## 🎯 Результат

Після налаштування бот повинен:
- ✅ Успішно збиратися в Railway
- ✅ Запускатися без помилок
- ✅ Працювати з групуванням тривог
- ✅ Публікувати новини з різних джерел
- ✅ Моніторити повітряні тривоги
