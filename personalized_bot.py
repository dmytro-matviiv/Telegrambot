import asyncio
import logging
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from user_manager import UserManager
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class PersonalizedBot:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.user_manager = UserManager()
        self.application = Application.builder().token(bot_token).build()
        
        # Реєструємо обробники команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Обробник для inline кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє команду /start"""
        user = update.effective_user
        user_id = user.id
        
        # Додаємо користувача до бази
        self.user_manager.add_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name
        )
        
        welcome_text = f"""
🚀 Вітаю, {user.first_name}!

Це бот для отримання персоналізованих повідомлень про:
• 🚨 Повітряні тривоги
• 📰 Останні новини
• 🕯️ Меморіальні повідомлення

За замовчуванням ви підписані на всі типи повідомлень.

📋 Доступні команди:
/start - Почати роботу з ботом
/settings - Налаштувати підписки
/status - Перевірити поточні налаштування
/help - Допомога

Натисніть /settings щоб налаштувати, які повідомлення ви хочете отримувати.
        """
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє команду /help"""
        help_text = """
📚 Довідка по командам:

/start - Почати роботу з ботом
/settings - Налаштувати підписки на повідомлення
/status - Перевірити поточні налаштування
/stats - Статистика (тільки для адміністраторів)
/help - Показати цю довідку

🔧 Налаштування підписок:
Ви можете увімкнути або вимкнути отримання:
• 🚨 Повітряні тривоги
• 📰 Останні новини  
• 🕯️ Меморіальні повідомлення

Використовуйте /settings для зміни налаштувань.
        """
        
        await update.message.reply_text(help_text)
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє команду /settings"""
        user_id = update.effective_user.id
        self.user_manager.update_user_activity(user_id)
        
        # Отримуємо поточні налаштування
        subscriptions = self.user_manager.get_user_subscriptions(user_id)
        
        # Створюємо inline кнопки
        keyboard = []
        
        # Кнопки для кожного типу підписки
        for sub_type, is_enabled in subscriptions.items():
            status_emoji = "✅" if is_enabled else "❌"
            sub_name = {
                'alerts': '🚨 Тривоги',
                'news': '📰 Новини', 
                'memorial': '🕯️ Меморіальні'
            }.get(sub_type, sub_type)
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_emoji} {sub_name}",
                    callback_data=f"toggle_{sub_type}"
                )
            ])
        
        # Кнопка для збереження
        keyboard.append([
            InlineKeyboardButton("💾 Зберегти", callback_data="save_settings")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = """
⚙️ Налаштування підписок

Оберіть, які повідомлення ви хочете отримувати:

• 🚨 Тривоги - повідомлення про повітряні тривоги
• 📰 Новини - останні новини з українських джерел
• 🕯️ Меморіальні - важливі дати та події

Натисніть на кнопку, щоб змінити налаштування.
        """
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup)
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє команду /subscribe"""
        user_id = update.effective_user.id
        self.user_manager.update_user_activity(user_id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Будь ласка, вкажіть тип підписки:\n"
                "/subscribe alerts - підписатися на тривоги\n"
                "/subscribe news - підписатися на новини\n"
                "/subscribe memorial - підписатися на меморіальні повідомлення\n"
                "/subscribe all - підписатися на все"
            )
            return
        
        subscription_type = context.args[0].lower()
        
        if subscription_type == "all":
            # Підписуємо на все
            for sub_type in ['alerts', 'news', 'memorial']:
                self.user_manager.update_subscription(user_id, sub_type, True)
            await update.message.reply_text("✅ Ви підписані на всі типи повідомлень!")
        
        elif subscription_type in ['alerts', 'news', 'memorial']:
            # Підписуємо на конкретний тип
            self.user_manager.update_subscription(user_id, subscription_type, True)
            sub_name = {
                'alerts': 'тривоги',
                'news': 'новини',
                'memorial': 'меморіальні повідомлення'
            }[subscription_type]
            await update.message.reply_text(f"✅ Ви підписані на {sub_name}!")
        
        else:
            await update.message.reply_text(
                "❌ Невідомий тип підписки. Використовуйте:\n"
                "alerts, news, memorial або all"
            )
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє команду /unsubscribe"""
        user_id = update.effective_user.id
        self.user_manager.update_user_activity(user_id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Будь ласка, вкажіть тип підписки:\n"
                "/unsubscribe alerts - відписатися від тривог\n"
                "/unsubscribe news - відписатися від новин\n"
                "/unsubscribe memorial - відписатися від меморіальних повідомлень\n"
                "/unsubscribe all - відписатися від всього"
            )
            return
        
        subscription_type = context.args[0].lower()
        
        if subscription_type == "all":
            # Відписуємо від всього
            for sub_type in ['alerts', 'news', 'memorial']:
                self.user_manager.update_subscription(user_id, sub_type, False)
            await update.message.reply_text("❌ Ви відписані від всіх типів повідомлень!")
        
        elif subscription_type in ['alerts', 'news', 'memorial']:
            # Відписуємо від конкретного типу
            self.user_manager.update_subscription(user_id, subscription_type, False)
            sub_name = {
                'alerts': 'тривоги',
                'news': 'новини',
                'memorial': 'меморіальні повідомлення'
            }[subscription_type]
            await update.message.reply_text(f"❌ Ви відписані від {sub_name}!")
        
        else:
            await update.message.reply_text(
                "❌ Невідомий тип підписки. Використовуйте:\n"
                "alerts, news, memorial або all"
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє команду /status"""
        user_id = update.effective_user.id
        self.user_manager.update_user_activity(user_id)
        
        subscriptions = self.user_manager.get_user_subscriptions(user_id)
        
        status_text = "📊 Ваші поточні налаштування:\n\n"
        
        for sub_type, is_enabled in subscriptions.items():
            status_emoji = "✅" if is_enabled else "❌"
            sub_name = {
                'alerts': '🚨 Тривоги',
                'news': '📰 Новини',
                'memorial': '🕯️ Меморіальні повідомлення'
            }[sub_type]
            
            status_text += f"{status_emoji} {sub_name}\n"
        
        status_text += "\nВикористовуйте /settings для зміни налаштувань."
        
        await update.message.reply_text(status_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє команду /stats (тільки для адміністраторів)"""
        user_id = update.effective_user.id
        
        # Тут можна додати перевірку на адміністратора
        # Поки що доступно всім
        
        stats = self.user_manager.get_stats()
        
        stats_text = f"""
📈 Статистика бота:

👥 Всього користувачів: {stats.get('total_users', 0)}
🚨 Підписників на тривоги: {stats.get('alerts_subscribers', 0)}
📰 Підписників на новини: {stats.get('news_subscribers', 0)}
🕯️ Підписників на меморіальні: {stats.get('memorial_subscribers', 0)}
        """
        
        await update.message.reply_text(stats_text)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє натискання inline кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        self.user_manager.update_user_activity(user_id)
        
        if query.data.startswith("toggle_"):
            # Перемикаємо підписку
            subscription_type = query.data.replace("toggle_", "")
            
            current_subscriptions = self.user_manager.get_user_subscriptions(user_id)
            current_status = current_subscriptions.get(subscription_type, False)
            
            # Змінюємо статус на протилежний
            new_status = not current_status
            self.user_manager.update_subscription(user_id, subscription_type, new_status)
            
            # Оновлюємо повідомлення
            await self.update_settings_message(query)
        
        elif query.data == "save_settings":
            await query.edit_message_text("✅ Налаштування збережено!")
    
    async def update_settings_message(self, query):
        """Оновлює повідомлення з налаштуваннями"""
        user_id = query.from_user.id
        subscriptions = self.user_manager.get_user_subscriptions(user_id)
        
        # Створюємо оновлені кнопки
        keyboard = []
        
        for sub_type, is_enabled in subscriptions.items():
            status_emoji = "✅" if is_enabled else "❌"
            sub_name = {
                'alerts': '🚨 Тривоги',
                'news': '📰 Новини',
                'memorial': '🕯️ Меморіальні'
            }.get(sub_type, sub_type)
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_emoji} {sub_name}",
                    callback_data=f"toggle_{sub_type}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("💾 Зберегти", callback_data="save_settings")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = """
⚙️ Налаштування підписок

Оберіть, які повідомлення ви хочете отримувати:

• 🚨 Тривоги - повідомлення про повітряні тривоги
• 📰 Новини - останні новини з українських джерел
• 🕯️ Меморіальні - важливі дати та події

Натисніть на кнопку, щоб змінити налаштування.
        """
        
        await query.edit_message_text(settings_text, reply_markup=reply_markup)
    
    async def send_personalized_message(self, user_ids: List[int], message: str, 
                                      subscription_type: str, **kwargs):
        """Надсилає персоналізоване повідомлення користувачам"""
        # Отримуємо користувачів, підписаних на цей тип повідомлень
        subscribers = self.user_manager.get_subscribers(subscription_type)
        
        # Фільтруємо тільки тих, хто в списку user_ids
        target_users = list(set(user_ids) & set(subscribers))
        
        success_count = 0
        error_count = 0
        
        for user_id in target_users:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    **kwargs
                )
                success_count += 1
                logger.info(f"Повідомлення надіслано користувачу {user_id}")
            except Exception as e:
                error_count += 1
                logger.error(f"Помилка надсилання повідомлення користувачу {user_id}: {e}")
        
        logger.info(f"Надіслано {success_count} повідомлень, помилок: {error_count}")
        return success_count, error_count
    
    async def send_news_to_users(self, news_item: Dict, user_ids: List[int]):
        """Надсилає новину користувачам"""
        # Форматуємо новину
        title = news_item.get('title', '')
        description = news_item.get('description', '')
        link = news_item.get('link', '')
        source = news_item.get('source', '')
        
        message = f"📰 <b>{title}</b>\n\n"
        if description:
            message += f"{description}\n\n"
        message += f"📖 <a href='{link}'>Читати далі</a>\n"
        message += f"📰 Джерело: {source}"
        
        return await self.send_personalized_message(
            user_ids=user_ids,
            message=message,
            subscription_type='news',
            parse_mode='HTML',
            disable_web_page_preview=False
        )
    
    async def send_alert_to_users(self, alert_message: str, user_ids: List[int]):
        """Надсилає тривогу користувачам"""
        return await self.send_personalized_message(
            user_ids=user_ids,
            message=alert_message,
            subscription_type='alerts',
            parse_mode='HTML'
        )
    
    async def send_memorial_to_users(self, memorial_message: str, user_ids: List[int]):
        """Надсилає меморіальне повідомлення користувачам"""
        return await self.send_personalized_message(
            user_ids=user_ids,
            message=memorial_message,
            subscription_type='memorial',
            parse_mode='HTML'
        )
    
    async def start(self):
        """Запускає бота"""
        logger.info("🚀 Запускаємо персоналізованого бота...")
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()
    
    async def stop(self):
        """Зупиняє бота"""
        logger.info("🛑 Зупиняємо персоналізованого бота...")
        await self.application.stop()
        await self.application.shutdown()
