#!/usr/bin/env python3
"""Скрипт для створення файлу .env"""

env_content = """BOT_TOKEN=8376156549:AAG7j5ZQJBbU4CdAeyMQP-IIJUO8MXMbGOo
CHANNEL_ID=@newstime20
GROUP_CHAT_ID=@GlobalNOChat
ALERTS_API_TOKEN=ed1f73bbaaecda208a960c2a84e20de7ae241d6fab2203
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ Файл .env створено успішно!")
print("📝 Вміст файлу:")
print(env_content)
