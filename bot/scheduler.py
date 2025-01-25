import schedule
import time
import datetime
from db import user_operations
from bot.utils import load_subscriptions, save_subscriptions

def check_subscriptions(context):
    now = datetime.datetime.now()
    subscriptions = load_subscriptions()
    
    for user_id, end_date_str in list(subscriptions.items()):
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        if now >= end_date:
            context.bot.send_message(chat_id=int(user_id), text="Ваша подписка закончилась. Пожалуйста, продлите её.")
            user_operations.unsubscribe(user_id)
            user_operations.reset_user(user_id)
            del subscriptions[user_id]
    
    save_subscriptions(subscriptions)

def run_scheduled_task(application):
    schedule.every().day.at("00:00").do(check_subscriptions, context=application.bot)
    schedule.every().month.at("00:00").do(user_operations.reset)

    while True:
        schedule.run_pending()
        time.sleep(60)
