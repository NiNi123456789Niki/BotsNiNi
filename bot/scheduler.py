
import schedule
import time
import datetime
from db import user_operations
from bot.utils import load_subscriptions, save_subscriptions

def check_subscriptions(context):
    """Checks for expired subscriptions and updates user status."""
    now = datetime.datetime.now() # Get current datetime
    subscriptions = load_subscriptions() # Load subscriptions from file

    for user_id, end_date_str in list(subscriptions.items()): # Iterate through subscriptions
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d') # Convert end date string to datetime object
        if now >= end_date: # Check if current time is past the subscription end date
            context.bot.send_message(chat_id=int(user_id), text="Ваша подписка закончилась. Пожалуйста, продлите её.") # Send message to user about subscription expiration
            user_operations.unsubscribe(user_id) # Unsubscribe the user in the database
            user_operations.reset_user(user_id) # Reset user's order count to default
            del subscriptions[user_id] # Remove user from active subscriptions

    save_subscriptions(subscriptions) # Save updated subscriptions to file

def run_scheduled_task(application):
    """Runs scheduled tasks for subscription checks and monthly user resets."""
    schedule.every().day.at("00:00").do(check_subscriptions, context=application.bot) # Schedule daily subscription check at midnight
    schedule.every().month.at("00:00").do(user_operations.reset) # Schedule monthly user reset at midnight on the first of each month

    while True: # Run scheduler continuously
        schedule.run_pending() # Run any pending scheduled tasks
        time.sleep(60) # Wait for 60 seconds before checking for pending tasks again