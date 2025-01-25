import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, PreCheckoutQueryHandler, ConversationHandler
from bot.config import BOT_TOKEN
from bot.handlers import *
from bot.scheduler import run_scheduled_task
import threading

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()


    faq_handler = CommandHandler('faq', faq_command)
    admin_handler = CommandHandler('admin', admin_command)
    pay_handler = CommandHandler('pay', pay_command)
    subscribe_handler = CommandHandler('subscribe', subscribe_command)
    support_handler = CommandHandler('support', support_command)
    precheckout_handler = PreCheckoutQueryHandler(precheckout_callback)
    successful_payment_handler = MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    edit_handler = CommandHandler('edit', edit_command)
    privacy_handler = CommandHandler('privacy', privacy_command)
    start_handler = CommandHandler('start', start)

    conv_handler = ConversationHandler(
        entry_points=[ 
            CallbackQueryHandler(button_callback),
            CommandHandler('support', support_command),
            CommandHandler('edit', edit_command),
            CommandHandler('order', start_order),
            CommandHandler('feedback', feedback_command),
            MessageHandler(filters.TEXT & filters.Regex('^Заказать бота$'), start_order),
            MessageHandler(filters.TEXT & filters.Regex('^Написать в поддержку$'), support_command),
            MessageHandler(filters.TEXT & filters.Regex('^Оставить отзыв$'), feedback_command),
            MessageHandler(filters.TEXT & filters.Regex('^FAQ$'), faq_command)
        ],
        states={
            PRICE_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_message)],
            LINK_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link_message)],
            DESCRIPTION_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_description)],
            ANSWER_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer_message)],
            SUPPORT_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message)],
            CLARIFICATION_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clarification_message)],
            CLARIFICATION_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clarification_message)],
            ORDER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_input)],
            FEEDBACK_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND,  handle_feedback_message)],
            TIME_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND,  handle_time_message)]
        },
        fallbacks=[], 
    )


    application.add_handler(conv_handler)
    application.add_handler(support_handler)
    application.add_handler(admin_handler)
    application.add_handler(faq_handler)
    application.add_handler(pay_handler)
    application.add_handler(precheckout_handler)
    application.add_handler(successful_payment_handler)
    application.add_handler(edit_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(privacy_handler)
    application.add_handler(start_handler)
    application.add_error_handler(error_handler)

    application.run_polling()
    thread = threading.Thread(target=run_scheduled_task, args=(application,), daemon=True)
    thread.start()

