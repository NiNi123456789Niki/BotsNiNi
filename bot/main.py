
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, PreCheckoutQueryHandler, ConversationHandler
from bot.config import BOT_TOKEN
from bot.handlers import *
from bot.scheduler import run_scheduled_task
import threading
from .button import button_callback

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to set up and run the Telegram bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build() # Build the application with the bot token

    # Command handlers for different bot commands
    faq_handler = CommandHandler('faq', faq_command) # Handler for /faq command
    admin_handler = CommandHandler('admin', admin_command) # Handler for /admin command
    pay_handler = CommandHandler('pay', pay_command) # Handler for /pay command
    subscribe_handler = CommandHandler('subscribe', subscribe_command) # Handler for /subscribe command
    support_handler = CommandHandler('support', support_command) # Handler for /support command
    precheckout_handler = PreCheckoutQueryHandler(precheckout_callback) # Handler for pre-checkout queries (payment)
    successful_payment_handler = MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback) # Handler for successful payments
    edit_handler = CommandHandler('edit', edit_command) # Handler for /edit command
    privacy_handler = CommandHandler('privacy', privacy_command) # Handler for /privacy command
    start_handler = CommandHandler('start', start) # Handler for /start command

    # Conversation handler to manage multi-turn conversations
    conv_handler = ConversationHandler(
        entry_points=[ # Entry points for the conversation handler
            CallbackQueryHandler(button_callback), # Callback query handler for button clicks
            CommandHandler('support', support_command), # /support command entry point
            CommandHandler('edit', edit_command), # /edit command entry point
            CommandHandler('order', start_order), # /order command entry point
            CommandHandler('feedback', feedback_command), # /feedback command entry point
            MessageHandler(filters.TEXT & filters.Regex('^Заказать бота$'), start_order), # "Order bot" button entry point
            MessageHandler(filters.TEXT & filters.Regex('^Написать в поддержку$'), support_command), # "Contact support" button entry point
            MessageHandler(filters.TEXT & filters.Regex('^Оставить отзыв$'), feedback_command), # "Leave feedback" button entry point
            MessageHandler(filters.TEXT & filters.Regex('^FAQ$'), faq_command) # "FAQ" button entry point
        ],
        states={ # States for the conversation handler, mapping state constants to lists of message handlers
            PRICE_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_message)], # Handle price input from admin
            LINK_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link_message)], # Handle bot link input from admin
            DESCRIPTION_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_description)], # Handle edited description input from user
            ANSWER_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer_message)], # Handle answer input from admin to support questions
            SUPPORT_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message)], # Handle support message input from user
            CLARIFICATION_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clarification_message)], # Handle clarification request input from admin
            CLARIFICATION_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clarification_message)], # Handle clarification response input from user (currently handled by same function)
            ORDER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_input)], # Handle order description input from user
            FEEDBACK_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND,  handle_feedback_message)], # Handle feedback message input from user
            TIME_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND,  handle_time_message)] # Handle time input from admin
        },
        fallbacks=[], # Fallback handlers if no state matches (currently none)
    )

    # Add handlers to the application dispatcher
    application.add_handler(conv_handler) # Add conversation handler
    application.add_handler(support_handler) # Add support command handler
    application.add_handler(admin_handler) # Add admin command handler
    application.add_handler(faq_handler) # Add faq command handler
    application.add_handler(pay_handler) # Add pay command handler
    application.add_handler(precheckout_handler) # Add precheckout query handler
    application.add_handler(successful_payment_handler) # Add successful payment handler
    application.add_handler(edit_handler) # Add edit command handler
    application.add_handler(subscribe_handler) # Add subscribe command handler
    application.add_handler(privacy_handler) # Add privacy command handler
    application.add_handler(start_handler) # Add start command handler
    application.add_error_handler(error_handler) # Add global error handler

    application.run_polling() # Start polling for updates from Telegram

    # Run scheduled tasks in a separate thread
    thread = threading.Thread(target=run_scheduled_task, args=(application,), daemon=True) # Create a thread for running scheduled tasks
    thread.start() # Start the scheduled tasks thread