
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
import datetime
import logging
from bot import config
from bot.spam import check_for_spam
from db import order_operations, questions_operations, user_operations
import ast
from bot.config import YOUR_CHAT_ID, PROVIDER_TOKEN
from bot.utils import load_subscriptions, save_subscriptions
import encrypter

logger = logging.getLogger(__name__)

FAQ_QUESTIONS = {
    "Как сделать заказ?": "Для заказа воспользуйтесь командой /order и опишите ваш запрос.",
    "Какие сроки выполнения заказов?": "Сроки выполнения зависят от сложности заказа, но обычно около недели в загруженные и три дня в менее загруженные.",
    "Как происходит оплата?": "Оплата происходит официально через Click.",
    "Есть ли гарантии?": "Да, мы предоставляем гарантии на выполненные работы, в случае проблем вы можете обратиться к нам в тех. поддержку.",
    "Откуда берется цена?": "Цена вычисляется по формуле: кол-во заказов * время работы * 1000.",
    "Какие технологии вы используете?": "Мы используем различные технологии в зависимости от задачи или определенную по пожеланию.",
    "Могу ли я внести изменения в заказ?": "Да, если конечный результат вам не понравится вы можете внести до 2-х изменений в месяц.",
    "Что делать, если возникли проблемы?": "Свяжитесь с нами, и мы обязательно поможем.",
    "Что нужно в описании заказа?": "Вначале вы должны указать в каком формате вам нужен бот (Код или готовый), определившись вы должны написать следующее для формата готового: |токен бота|, сервер. Если нужно напишите какую дата базу использовать  (По умолчанию: SQLite3). Ну и не забудьте написать главную идею подробно и понятно.",
    "Какую дата базу выбрать?": "Зависит от ваших потребностей, если проект маленький и не требует чего-то очен сложного рекомендуется использовать SQLite3. Если нужно что-то получше рекомендуется MySQL, он быстрый и поддерживает большинство SQL протоколов и SQL форматов. Но если нужны гибкая настройка, высокие требования к целостности данных, сложные аналитические задачи - выбирайте PostgreSQL.",
    "Где получить токен бота?": "Переходите к @BotFather (Просто напишите в поиске), там пишите команду /newbot. Там вас попросят несколько пунктов 1. Имя 2. Имя пользователя (как например \"@BotFather\"). В строке имя пользователя пишите без пробелов и спец символов, место пробелов используйте _ или -, имя должно заканчиваться на \"bot\"",
    "Хочу такого же бота как у вас!": "Наш бот с открытым исходным кодом, вы можете его использовать, в соответствии с условиями лицензии (MIT License). Для удобства вот вам ссылка на репозиторий: https://github.com/NiNi123456789Niki/BotsNiNi"
}

paying = [] # List to store orders that are in the paying process. Each element is a dict with 'ord_id' and 'user_id'.
QUESTIONS_PER_PAGE = 7 # Number of FAQ questions to display per page.
PRICE_WAITING, LINK_WAITING, DESCRIPTION_WAITING, SUPPORT_WAITING, ANSWER_WAITING, CLARIFICATION_REQUEST, CLARIFICATION_RESPONSE, ORDER_INPUT, FEEDBACK_WAITING, TIME_WAITING = range(10) # Define conversation states as integer constants using range for readability and maintainability.


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with options to the user when the /start command is used."""
    keyboard = []
    keyboard.append([KeyboardButton("Заказать бота"), KeyboardButton("Написать в поддержку")])
    keyboard.append([KeyboardButton("Оставить отзыв"), KeyboardButton("FAQ")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True) # Create a custom keyboard for user interaction.
    await update.message.reply_text('Вас приветствует бот NiNi bots, после ознакомления с политикой конфиденциальности выберите опцию. Продолжая пользоваться ботом вы соглашаетесь с политикой конфиденциальности', reply_markup=reply_markup) # Send the welcome message with the keyboard.


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /subscribe command to initiate a subscription payment."""
    user_id = str(update.effective_user.id) # Get the user's ID.
    end_date = datetime.datetime.now() + datetime.timedelta(days=30) # Calculate the subscription end date (30 days from now).

    title = "Подписка на ботдиллер" # Invoice title.
    description = "Получите такие возможности как: 1. Возможность заказать бота безграничное количество раз 2. Возможность изменить заказ сколько душе угодно" # Invoice description.
    payload = f"subscribe_{user_id}" # Custom payload to identify the payment type.
    provider_token = PROVIDER_TOKEN # Get the provider token from config.
    currency = "UZS" # Set currency to UZS.
    prices = [LabeledPrice("Цена", 50000)] # Define the price of the subscription.

    await context.bot.send_invoice( # Send the invoice to the user.
        chat_id=user_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        start_parameter=f"sub_{user_id}", # Start parameter for deep linking.
    )

    subscriptions = load_subscriptions() # Load existing subscriptions from file.
    subscriptions[user_id] = end_date.strftime('%Y-%m-%d') # Store the subscription end date for the user.
    save_subscriptions(subscriptions) # Save updated subscriptions to file.



async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the order conversation flow when the /order command is used."""
    if not update.message or not update.message.text: # Check if the update contains a message and text.
        logger.warning("Получено пустое сообщение или объект update.message") # Log a warning if message is empty.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.") # Inform user about error.
        return ConversationHandler.END # End the conversation.
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите описание бота максимально подробно (Советуем почитать /faq).") # Ask user for order description.

    return ORDER_INPUT # Move to the ORDER_INPUT state in the conversation.

async def handle_order_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's order description input in the ORDER_INPUT state."""
    user_message = update.message.text # Get the user's message (order description).

    try:
        is_spam = check_for_spam(user_message) # Check if the message is spam using the spam checker function.

    except Exception as e: # Catch any exceptions during spam check.
        logger.error(f"Ошибка при проверке на спам: {e}") # Log the error.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при проверке сообщения.") # Inform user about error.
        return ConversationHandler.END # End the conversation.

    if is_spam: # If the message is identified as spam.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ваше сообщение было распознано как спам. Попробуйте позже.") # Inform user about spam detection.
        return ConversationHandler.END # End the conversation.

    user = update.effective_user # Get the user object.
    user_id = user.id # Get the user ID.
    username = user.username or "не установлен" # Get username, or "не установлен" if none.
    user_operations.check_for_user(username, user_id) # Check if user exists in database, create if not.
    block = user_operations.check_for_block(user_id) # Check if user is blocked.

    if block: # If user is blocked.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Вы были забанены модераторами!") # Inform user about ban.
        return ConversationHandler.END # End the conversation.
    orders = order_operations.create_order(user_id, user_message) # Create a new order in the database.

    if orders is False: # If user has reached maximum order limit.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Вы потратили максимальное количество заказов!") # Inform user about order limit.
        return ConversationHandler.END # End the conversation.

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ваш заказ был отправлен!") # Confirm order submission to user.
    return ConversationHandler.END # End the conversation.


async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /faq command to display FAQ questions in pages."""
    page = 0 # Initialize page number to 0.
    context.user_data['faq_page'] = page # Store current page in user data.
    context.user_data['faq_message_id'] = None # Initialize message ID for editing FAQ message later.
    await send_faq_page(update, context, page) # Send the first page of FAQ questions.

async def send_faq_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Sends a specific page of FAQ questions with navigation buttons."""
    questions = list(FAQ_QUESTIONS.keys()) # Get list of FAQ questions.
    num_questions = len(questions) # Get total number of questions.
    start_index = page * QUESTIONS_PER_PAGE # Calculate starting index for current page.
    end_index = min(start_index + QUESTIONS_PER_PAGE, num_questions) # Calculate ending index for current page.

    keyboard = []
    for i in range(start_index, end_index): # Iterate through questions for the current page.
        question = questions[i] # Get question text.
        keyboard.append([InlineKeyboardButton(question, callback_data=f"faq_{i}")]) # Add button for each question.

    navigation_buttons = []
    if page > 0: # Add "Назад" button if not on the first page.
        navigation_buttons.append(InlineKeyboardButton("Назад", callback_data="prev_page"))
    if end_index < num_questions: # Add "Дальше" button if there are more questions.
        navigation_buttons.append(InlineKeyboardButton("Дальше", callback_data="next_page"))

    if navigation_buttons: # Add navigation buttons row to keyboard if any.
        keyboard.append(navigation_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard.

    chat_id = update.effective_chat.id # Get chat ID.

    if context.user_data['faq_message_id']: # If a FAQ message ID exists in user data (for editing).
        message_id = context.user_data['faq_message_id'] # Get the message ID.
        try:
            await context.bot.edit_message_text( # Try to edit the existing message.
                chat_id=chat_id,
                message_id=message_id,
                text="Выберите интересующий вас вопрос:",
                reply_markup=reply_markup
            )
        except Exception as e: # If editing fails (e.g., message not found).
            new_message = await context.bot.send_message( # Send a new message instead.
                chat_id=chat_id,
                text="Выберите интересующий вас вопрос:",
                reply_markup=reply_markup
            )
            context.user_data['faq_message_id'] = new_message.message_id # Update message ID in user data.
    else: # If no FAQ message ID exists (first time sending).
        new_message = await context.bot.send_message( # Send a new message.
            chat_id=chat_id,
            text="Выберите интересующий вас вопрос:",
            reply_markup=reply_markup
        )
        context.user_data['faq_message_id'] = new_message.message_id # Store the new message ID.

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button callbacks."""
    query = update.callback_query # Get the callback query.
    await query.answer() # Acknowledge the callback query to prevent button from spinning.

    if query.data.startswith("faq_"): # If the callback is for a specific FAQ question.
        question_index = int(query.data.split('_')[1]) # Extract question index from callback data.
        question = list(FAQ_QUESTIONS.keys())[question_index] # Get question text from index.
        answer = FAQ_QUESTIONS[question] # Get answer text for the question.

        keyboard = [
            [InlineKeyboardButton("НАЗАД", callback_data="back_to_faq")] # Button to go back to FAQ question list.
        ]

        await query.edit_message_text( # Edit the message to display the question and answer.
            text=f"<b><strong>{question}</strong></b>\n{answer}",
            parse_mode="HTML", # Enable HTML parsing for bold text.
            reply_markup=InlineKeyboardMarkup(keyboard) # Add "НАЗАД" button.
        )

    elif query.data == "back_to_faq": # If callback is to go back to FAQ question list.
        page = context.user_data.get('faq_page', 0) # Get current FAQ page from user data.
        await send_faq_page(update, context, page) # Resend the FAQ page.

    elif query.data == "next_page": # If callback is to go to the next FAQ page.
        page = context.user_data.get('faq_page', 0) + 1 # Increment page number.
        context.user_data['faq_page'] = page # Update page number in user data.
        await send_faq_page(update, context, page) # Resend the FAQ page.

    elif query.data == "prev_page": # If callback is to go to the previous FAQ page.
        page = context.user_data.get('faq_page', 0) - 1 # Decrement page number.
        context.user_data['faq_page'] = page # Update page number in user data.
        await send_faq_page(update, context, page) # Resend the FAQ page.
    elif query.data in ("CHECKING", "MAKING", "PAYING", "COMPLETED"): # If callback is for order status filtering (admin panel).
        message = ""
        orders_str = order_operations.get_orders(query.data) # Get orders with the selected status from the database.
        orders_list = ast.literal_eval(orders_str) # Convert the string representation of list of dicts to actual list of dicts.

        keyboard = []

        if orders_list: # If there are orders with the selected status.
            for order in orders_list: # Iterate through each order.
                user_id = order['userid'] # Get user ID from order data.
                desc = order['description'] # Get order description.
                ord_id = order['order_id'] # Get order ID.
                username = user_operations.get_username(user_id) # Get username from user ID.
                message += f"Заказ {ord_id}: \n Пользователь {username} с id {user_id} заказал бота в описанием \"{desc}\". \n" # Build message string with order details.
                keyboard.append([InlineKeyboardButton(f"{ord_id}", callback_data=f"ord_{ord_id}")]) # Add button for each order ID.
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with order ID buttons.
            await query.edit_message_text(text=message, reply_markup=reply_markup) # Edit message to display order list with buttons.
        else: # If no orders found with the selected status.
            await query.edit_message_text(text="Нет заказов с данным статусом.") # Inform admin that no orders found.
    elif query.data.startswith("ord_"): # If callback is for a specific order (admin panel).
        data = query.data[4:] # Extract order ID from callback data.
        order = order_operations.get_order(data) # Get order details from database using order ID.
        if order: # If order is found.
            user_id = order[0] # Get user ID from order data.
            desc = order[1] # Get order description.
            status = order[2] # Get order status.
            price = order[3] # Get order price.
            if price is None: # If price is not set yet.
                price = "пока не указана" # Display "пока не указана".
            else:
                price = order[3] # Otherwise, display the actual price.
            username = user_operations.get_username(user_id) # Get username from user ID.

            keyboard = []
            if status == "CHECKING": # If order status is "CHECKING".
                keyboard.append([InlineKeyboardButton("Попросить уточнение", callback_data=f"cor_{user_id}_{data}")]) # Add button to request clarification.
                keyboard.append([InlineKeyboardButton("Начать выполнение", callback_data=f"mk_{data}_{user_id}")]) # Add button to start making the bot.
            elif status == "MAKING": # If order status is "MAKING".
                keyboard.append([InlineKeyboardButton("Закончить выполнение", callback_data=f"py_{data}_{user_id}")]) # Add button to mark order as ready for payment.
            if price == 'None': # If price is not set.
                keyboard.append([InlineKeyboardButton("Установить цену", callback_data=f"pr_{data}")]) # Add button to set price.
            keyboard.append([InlineKeyboardButton("Забанить пользователя", callback_data=f"bn_{user_id}")]) # Add button to ban user.
            keyboard.append([InlineKeyboardButton("Установить время", callback_data=f"stm_{user_id}")]) # Add button to set time for order completion.
            keyboard.append([InlineKeyboardButton("Удалить заказ", callback_data=f"delord_{data}")]) # Add button to delete order.
            keyboard.append([InlineKeyboardButton("НАЗАД", callback_data=status)]) # Button to go back to status order list.
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with order actions.

            await query.edit_message_text(text=f"Заказ {data}: \nЗаказал: {username}\nID автора заказа: {user_id}\nОписание(Что нужно сделать): {desc}\nСтатус: {status} \nЦена: {price}.", reply_markup=reply_markup) # Edit message to display order details and action buttons.
        else: # If order is not found.
            await query.edit_message_text(text=f"Заказ с ID {data} не найден.") # Inform admin that order not found.
    elif query.data.startswith("stm_"): # If callback is to set time for order completion (admin panel).
        data = query.data[4:] # Extract user ID from callback data.
        await query.edit_message_text("Пожалуйста укажите время...") # Ask admin to input time.
        context.user_data['user_id_for_time'] = data # Store user ID in user data to use in next message handler.
        logging.info(f"Setting user_id_for_time: {data}") # Log user ID for time setting.
        return TIME_WAITING # Move to TIME_WAITING state.

    elif query.data.startswith("pr_"): # If callback is to set price for order (admin panel).
        data = query.data[3:] # Extract order ID from callback data.
        await query.edit_message_text("Пожалуйста отправьте цену...") # Ask admin to input price.
        context.user_data['order_id_for_price'] = data # Store order ID in user data to use in next message handler.
        return PRICE_WAITING # Move to PRICE_WAITING state.

    elif query.data.startswith("mk_"): # If callback is to mark order as "MAKING" (admin panel).
        data = query.data[3:].split("_") # Extract order ID and user ID from callback data.
        order_operations.change_status("MAKING", data[0]) # Update order status in database to "MAKING".
        await context.bot.sendMessage(data[1], "Над вашим заказом началась работа ⚙...") # Send message to user informing that work has started.
    elif query.data.startswith("bn_"): # If callback is to ban user (admin panel).
        data = query.data[3:] # Extract user ID from callback data.
        user_operations.ban_user(data) # Ban the user in the database.
        await query.edit_message_text("Пользователь заблокирован!") # Inform admin that user is banned.

    elif query.data.startswith("delord_"): # If callback is to delete order (admin panel).
        data = query.data[7:] # Extract order ID from callback data.
        order_operations.delete_order(data) # Delete order from database.
        await query.edit_message_text("Заказ удален!") # Inform admin that order is deleted.

    elif query.data.startswith("py_"): # If callback is to mark order as "PAYING" (admin panel).
        data = query.data[3:].split("_") # Extract order ID and user ID from callback data.
        paying.append({"ord_id": data[0], "user_id": data[1]}) # Add order to paying list.
        await query.edit_message_text("Пожалуйста отправьте ссылку на бота для теста пользователя...") # Ask admin to send bot link for user testing.
        context.user_data['order_id_for_link'] = data[0] # Store order ID in user data for next message handler.
        context.user_data['user_id_for_link'] = data[1] # Store user ID in user data for next message handler.
        return LINK_WAITING # Move to LINK_WAITING state.

    elif query.data.startswith("cor_"): # If callback is to request clarification from user (admin panel).
        parts = query.data[4:].split("_") # Extract user ID and order ID from callback data.
        user_id = int(parts[0]) # Get user ID.
        ord_id = parts[1] # Get order ID.

        await query.edit_message_text(text=f"Введите уточнение для пользователя с ID: {user_id} по заказу {ord_id}:") # Ask admin to input clarification message.

        context.user_data['clarification'] = {"target_user_id": user_id, "ord_id": ord_id} # Store clarification data in user data.
        return CLARIFICATION_REQUEST # Move to CLARIFICATION_REQUEST state.

    elif query.data == "QUESTIONS": # If callback is to view support questions (admin panel).
        try:
            questions = questions_operations.get_questions() # Get all support questions from database.
            if not questions: # If no questions found.
                await query.edit_message_text(text="Нет вопросов!") # Inform admin that no questions found.
            keyboard = []
            text = ""
            for question in questions: # Iterate through each question.
                text += f"Вопрос {question[0]}: \nПользователь {encrypter.decode(question[1])} с вопросом: {encrypter.decode(question[2])}\n" # Build message text with question details (decode encrypted data).
                keyboard.append([InlineKeyboardButton(f"{question[0]}", callback_data=f"q_{question[0]}")]) # Add button for each question ID.
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with question ID buttons.
            await query.edit_message_text(text=text, reply_markup=reply_markup) # Edit message to display question list with buttons.
        except Exception as e: # Catch any errors during question retrieval.
            await query.edit_message_text(text=f"Ошибка: {str(e)}") # Inform admin about error.
    elif query.data.startswith("q_"): # If callback is to view a specific question (admin panel).
        data = query.data[2:] # Extract question ID from callback data.
        question = questions_operations.get_question(data) # Get question details from database using question ID.
        keyboard = []
        keyboard.append([InlineKeyboardButton("Ответить", callback_data=f"ans_{question[0]}")]) # Add button to answer the question.
        keyboard.append([InlineKeyboardButton("НАЗАД", callback_data="QUESTIONS")]) # Button to go back to question list.
        reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with answer and back buttons.
        await query.edit_message_text(text=f"Вопрос {question[0]}: \nПользователь {encrypter.decode(question[1])} \nВопрос: {encrypter.decode(question[2])}", reply_markup=reply_markup) # Edit message to display question details and action buttons (decode encrypted data).
    elif query.data.startswith("ans_"): # If callback is to answer a question (admin panel).
        data = query.data[4:] # Extract question ID from callback data.
        question = questions_operations.get_question(data) # Get question details from database using question ID.
        await query.edit_message_text(text=f"Ответьте на вопрос пользователя {encrypter.decode(question[1])} с вопросом: {encrypter.decode(question[2])}") # Ask admin to input answer (decode encrypted data).
        context.user_data['question_id_for_answer'] = data # Store question ID in user data for next message handler.
        return ANSWER_WAITING # Move to ANSWER_WAITING state.
    elif query.data == "pys": # If callback is for user agreeing to the time (user response).
        await query.edit_message_text(text="Мы рады что вы доверяете нам ❤") # Positive feedback to user.
    elif query.data.startswith("nt_"): # If callback is for user disagreeing to time/price (user response).
        data = query.data[3:] # Extract order ID from callback data.
        order_operations.change_status("COMPLETED", data) # Change order status to "COMPLETED" (implicitly meaning cancelled/rejected).
        await query.edit_message_text(text="Мы приносим извинения что вам не понравилось :(. Вы можете оставить отзыв командой /feedback.") # Apology and suggestion to leave feedback.
    else: # If unknown callback data received.
        await query.edit_message_text(text="Неизвестный запрос.") # Inform admin about unknown request.


async def handle_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the time input message from admin in TIME_WAITING state."""
    logger.debug("Getting to TIME_WAITING") # Debug log.
    time = update.message.text # Get the time message from admin.
    tid = context.user_data.get('user_id_for_time') # Get user ID from user data.
    keyboard = []
    order = order_operations.get_order_from_tid(tid) # Get order details using user ID (tid).
    if order: # If order is found.
        order_id = order[0] # Get order ID.
        keyboard.append([InlineKeyboardButton("Согласен", callback_data="pys")]) # Button for user to agree.
        keyboard.append([InlineKeyboardButton("Не согласен", callback_data=f"nt_{order_id}")]) # Button for user to disagree.
        reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with agreement options.
        await update.message.reply_text("Время установлено.") # Inform admin that time is set.
        await context.bot.send_message(tid, f"Время на ваш заказ {time}. Пожалуйста если вы не согласны с ценой, нажмите \"Не согласен\".", reply_markup=reply_markup) # Send time information and agreement options to user.
    else: # If order not found.
        await update.message.reply_text("Order not found.") # Inform admin that order not found.
    context.user_data.pop('user_id_for_time', None) # Clear user_id_for_time from user data.
    return ConversationHandler.END # End the conversation.

async def handle_answer_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the answer input message from admin in ANSWER_WAITING state."""
    answer = update.message.text # Get the answer message from admin.
    question_id = context.user_data.get('question_id_for_answer') # Get question ID from user data.
    question = questions_operations.get_question(question_id) # Get question details using question ID.
    await context.bot.send_message(chat_id=encrypter.decode(question[1]), text=f"Ответ на ваш вопрос: {answer}") # Send the answer to the user who asked the question (decode user ID).
    await update.message.reply_text("Ваш ответ отправлен.") # Inform admin that answer is sent.
    return ConversationHandler.END # End the conversation.

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /support command to start support message input."""
    await update.message.reply_text("Пожалуйста, введите ваше сообщение для поддержки:") # Ask user to input support message.
    return SUPPORT_WAITING # Move to SUPPORT_WAITING state.



async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the support message input from user in SUPPORT_WAITING state."""
    user_id = update.effective_user.id # Get user ID.
    message = update.message.text # Get support message from user.
    try:
        await update.message.reply_text("Ваше сообщение отправлено в поддержку.") # Confirm message sent to user.
        questions_operations.add_question(user_id, message) # Add the question to the database.
    except Exception as e: # Catch any errors during question saving.
        logger.error(f"Ошибка при отправке сообщения в поддержку: {e}") # Log the error.
        await update.message.reply_text("Произошла ошибка при отправке сообщения в поддержку. Пожалуйста, попробуйте позже.") # Inform user about error.
    return ConversationHandler.END # End the conversation.


async def handle_price_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the price input message from admin in PRICE_WAITING state."""
    price_str = update.message.text # Get price message from admin.
    order_id = context.user_data.get('order_id_for_price') # Get order ID from user data.

    try:
        price = int(price_str) # Try to convert price to integer.
        if order_operations.set_price(order_id, price): # Set the price in the database.
            await update.message.reply_text(f"Цена {price} установлена для заказа {order_id}.") # Inform admin about price set.
            tid = order_operations.get_tid(ord_id=order_id) # Get user ID (tid) associated with the order.
            order_operations.set_price(order_id, price) # Redundant, already set above, maybe for error handling/consistency.
            keyboard = []
            keyboard.append([InlineKeyboardButton("Согласен", callback_data=f"ys")]) # Button for user to agree.
            keyboard.append([InlineKeyboardButton("Не согласен", callback_data=f"nt_{order_id}")]) # Button for user to disagree.
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with agreement options.
            await context.bot.send_message(tid, f"За ваш заказ назначена цена {price} сум. Пожалуйста если вы не согласны с ценой, нажмите \"Не согласен\".", reply_markup=reply_markup) # Send price information and agreement options to user.
        else: # If price update in database fails.
            await update.message.reply_text("Ошибка при обновлении цены в базе данных.") # Inform admin about database error.

    except ValueError: # If price input is not a valid integer.
        await update.message.reply_text("Неверный формат цены. Пожалуйста, введите число.") # Inform admin about invalid price format.
        return PRICE_WAITING # Stay in PRICE_WAITING state to re-enter price.
    return ConversationHandler.END # End the conversation.

async def handle_link_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the bot link input message from admin in LINK_WAITING state."""
    link = update.message.text # Get bot link from admin.
    order_id = context.user_data.get('order_id_for_link') # Get order ID from user data.
    user_id = context.user_data.get('user_id_for_link') # Get user ID from user data.

    try:

        order_operations.change_status("PAYING", order_id) # Change order status to "PAYING" in database.
        await context.bot.send_message(user_id, f"Для теста бота перейдите по {link}! Примечание: Если спустя 96 часов вы не оплатили бот, то бот может использоваться в других проектах! Если вам не понравился бот, то вы можете прописать команду /edit и изменить.") # Send bot link and payment instructions to user.
        await context.bot.send_message(user_id, "После теста, и убеждения что бот вам подходит пожалуйста заплатите командой /pay") # Further payment instructions to user.
        await update.message.reply_text(f"Ссылка {link} отправлена пользователю {user_id} для заказа {order_id}.") # Inform admin that link is sent.
    except Exception as e:
        logger.error(f"Error sending link: {e}") # Log error if sending link fails.
        await update.message.reply_text("Не удалось отправить ссылку.") # Inform admin about link sending failure.


    return ConversationHandler.END # End the conversation.

async def handle_clarification_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles clarification request messages from admin and clarification response messages from user."""
    clarification_data = context.user_data.get('clarification') # Get clarification request data from user data.
    if clarification_data: # If it's a clarification request from admin.
        target_user_id = clarification_data["target_user_id"] # Get target user ID.
        ord_id = clarification_data["ord_id"] # Get order ID.
        clarification_request = update.message.text # Get clarification request message from admin.

        try:
            sent_message = await context.bot.send_message(chat_id=target_user_id, text=f"Уточнение по вашему заказу {ord_id}: {clarification_request}\n\nПожалуйста, ответьте на это сообщение.") # Send clarification request to user.

            context.user_data['waiting_for_clarification'] = {"ord_id": ord_id, "request_message_id": sent_message.message_id} # Store waiting for clarification data in user data.
            await update.message.reply_text(text=f"Запрос на уточнение отправлен пользователю {target_user_id}.") # Inform admin that request is sent.
        except Exception as e: # Catch errors during sending clarification request.
            logger.error(f"Error sending clarification request: {e}") # Log error.
            await update.message.reply_text(text="Не удалось отправить запрос на уточнение.") # Inform admin about sending failure.
        finally:
            del context.user_data['clarification'] # Clear clarification request data from user data.
        return CLARIFICATION_RESPONSE # Move to CLARIFICATION_RESPONSE state (though not strictly used in this function, could be for future expansion).

    elif update.message.reply_to_message: # If it's a clarification response from user (replying to clarification request).
        waiting_data = context.user_data.get('waiting_for_clarification') # Get waiting for clarification data from user data.
        if waiting_data and update.message.reply_to_message.message_id == waiting_data["request_message_id"]: # Check if reply is to the correct clarification request message.
            ord_id = waiting_data["ord_id"] # Get order ID.
            clarification_answer = update.message.text # Get clarification answer from user.
            try:
                order = order_operations.get_order(ord_id) # Get order details.
                if order: # If order is found.
                    order_operations.add_to_desc(ord_id, clarification_answer) # Append clarification answer to order description in database.
                    await update.message.reply_text("Ваш ответ на уточнение отправлен.") # Inform user that answer is sent.
                else: # If order is not found.
                    await update.message.reply_text(f"Заказ с ID {ord_id} не найден.") # Inform user that order not found.
            except Exception as e: # Catch errors during description update or order retrieval.
                logger.error(f"Error updating description or retrieving request: {e}") # Log error.
                await update.message.reply_text("Не удалось обновить описание заказа или получить запрос.") # Inform user about update/retrieval failure.
            finally:
                del context.user_data['waiting_for_clarification'] # Clear waiting for clarification data from user data.
            return ConversationHandler.END # End the conversation.

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /admin command to display admin panel options."""
    if not update.message or not update.message.text: # Check if update contains message and text.
        logger.warning("Получено пустое сообщение или объект update.message") # Log warning if message is empty.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.") # Inform admin about error.
        return # No ConversationHandler.END here as it's not part of a conversation flow.

    user_id = update.effective_user.id # Get user ID.
    if user_id == int(YOUR_CHAT_ID): # Check if user ID matches admin's chat ID from config.
        keyboard = []
        keyboard.append([InlineKeyboardButton("НА ПРОВЕРКУ", callback_data="CHECKING")]) # Button to view orders in "CHECKING" status.
        keyboard.append([InlineKeyboardButton("ДЕЛАЮТСЯ", callback_data="MAKING")]) # Button to view orders in "MAKING" status.
        keyboard.append([InlineKeyboardButton("В ПРОЦЕССЕ ОПЛАТЫ", callback_data="PAYING")]) # Button to view orders in "PAYING" status.
        keyboard.append([InlineKeyboardButton("ВЫПОЛНЕННЫЕ", callback_data="COMPLETED")]) # Button to view orders in "COMPLETED" status.
        keyboard.append([InlineKeyboardButton("ВОПРОСЫ", callback_data="QUESTIONS")]) # Button to view support questions.
        reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with admin options.

        await update.message.reply_text("Какие заказы показывать сегодня:", reply_markup=reply_markup) # Send admin panel options.
    else: # If user is not admin.
        await update.message.reply_text('У вас нет прав для выполнения этой команды.') # Inform user about lack of admin rights.

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler to log errors and inform the user."""
    logger.error(f"Update caused error {context.error}") # Log the error.
    if update: # If update object is available.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла непредвиденная ошибка.") # Inform user about error.

async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /pay command to initiate payment for an order."""
    chat_id = update.effective_chat.id # Get chat ID.
    order = order_operations.get_order_from_tid(chat_id) # Get order details using user ID (chat ID).
    if order == "Empty": # If no order found for the user.
        await context.bot.send_message(chat_id=chat_id, text="У вас нет заказов!") # Inform user about no orders.
    elif order[2] == "PAYING": # If order status is "PAYING".
        title = "Оплата за бота" # Invoice title.
        description = order[1] # Invoice description (order description).
        payload = f"pay_{order[0]}" # Custom payload to identify the payment type and order ID.
        provider_token = PROVIDER_TOKEN # Get provider token from config.
        currency = "UZS" # Set currency to UZS.
        prices = [LabeledPrice("Цена", order[3] * 100)] # Define price based on order price from database (multiplied by 100 for cents/tiyin).

        await context.bot.send_invoice( # Send the invoice to the user.
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            start_parameter=f"pay_{order[0]}", # Start parameter for deep linking.
        )
    else: # If order status is not "PAYING".
        await context.bot.send_message(chat_id=chat_id, text="У вас нет заказов на оплату!") # Inform user that there are no orders ready for payment.

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles pre-checkout queries for payments."""
    query = update.pre_checkout_query # Get pre-checkout query.
    await query.answer(ok=True) # Answer the pre-checkout query to proceed with payment.

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles successful payment callbacks."""
    if update.message.successful_payment.invoice_payload.startswith("pay_"): # If payment is for an order.
        order_id = update.message.successful_payment.invoice_payload[4:] # Extract order ID from payload.
        user_id = update.effective_user.id # Get user ID.
        await context.bot.send_message(chat_id=user_id, text="Спасибо за оплату! Будем благодарны если вы оставите отзыв о нашем боте (/feedback).") # Thank user for payment and suggest leaving feedback.
        order_operations.change_status("COMPLETED", order_id) # Change order status to "COMPLETED" in database.
    elif update.message.successful_payment.invoice_payload.startswith("subscribe_"): # If payment is for subscription.
        user_id = update.effective_user.id # Get user ID.
        await context.bot.send_message(chat_id=user_id, text="Спасибо за оплату! Теперь вы можете заказывать ботов без ограничений.") # Thank user for subscription payment.
        user_operations.subscribe(user_id) # Update user subscription status in database.

    else: # If unknown payment payload.
        await context.bot.send_message(chat_id=update.effective_user.id, text="Ошибка при обработке оплаты.") # Inform user about payment processing error.

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /edit command to allow users to edit their order description."""
    user_id = update.effective_user.id # Get user ID.
    if user_operations.edit(user_id) is False: # Check if user has edit attempts remaining.
        await context.bot.send_message(chat_id=user_id, text="У вас закончились попытки изменить заказ!") # Inform user about no edit attempts left.
    else: # If user has edit attempts.
        order = order_operations.get_order_from_tid(user_id)
        if order and order[2] == "PAYING": # Check if order status is "PAYING" (only editable at this stage).
            await context.bot.send_message(chat_id=user_id, text="Пожалуйста, напишите описание изменений, которые вы хотите внести.") # Ask user to input edit description.
            return DESCRIPTION_WAITING # Move to DESCRIPTION_WAITING state.
        else: # If order is not in "PAYING" status or no order found.
            await context.bot.send_message(chat_id=user_id, text="Вы не можете изменить заказ!") # Inform user that order cannot be edited.

async def handle_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the edited description input from user in DESCRIPTION_WAITING state."""
    user_id = update.effective_user.id # Get user ID.
    order_id = order_operations.get_order_from_tid(user_id)[0] # Get order ID using user ID.
    new_description = update.message.text # Get new description from user.
    order_operations.add_to_desc(order_id, new_description) # Add new description to order description in database.
    user_operations.edit(user_id) # Decrement user's edit attempts count.
    order_operations.change_status("MAKING", order_id) # Change order status back to "MAKING" to restart development.
    await context.bot.send_message(chat_id=user_id, text="Ваши изменения были успешно добавлены к заказу. Скоро за ваш заказ снова возьмутся разработчики.") # Inform user about successful edit and restart of development.
    return ConversationHandler.END # End the conversation.

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /feedback command to start feedback input."""
    user_id = update.effective_user.id # Get user ID.
    order = order_operations.get_order_from_tid(user_id)
    if order and order[2] == "COMPLETED": # Check if order status is "COMPLETED" (only allow feedback after completion).
        await update.message.reply_text("Пожалуйста, напишите ваш отзыв о нашем боте.") # Ask user to input feedback.
        return FEEDBACK_WAITING # Move to FEEDBACK_WAITING state.
    else: # If order is not "COMPLETED" or no order found.
        await update.message.reply_text("Вы не можете оставить отзыв, пока ваш заказ не будет выполнен.") # Inform user that feedback can only be left after order completion.
        return ConversationHandler.END # End the conversation. # Although it's already ending by not returning FEEDBACK_WAITING, explicit return for clarity.

async def handle_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the feedback message input from user in FEEDBACK_WAITING state."""
    feedback = update.message.text # Get feedback message from user.
    user_id = update.effective_user.id # Get user ID.
    await context.bot.send_message(chat_id=config.FEEDBACK_CHAT_ID, text=f"Отзыв от пользователя {user_id}: {feedback}") # Send feedback to feedback channel (using chat ID from config).
    await update.message.reply_text("Ваш отзыв был успешно добавлен.") # Confirm feedback submission to user.
    return ConversationHandler.END # End the conversation.

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /privacy command to display privacy policy information."""
    keyboard = []
    keyboard.append([InlineKeyboardButton("Политика конфиденциальности", url="https://t.me/NiNi_bots_bot/privacy_policy")]) # Button linking to privacy policy.
    reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with privacy policy button.
    await update.message.reply_text("Откройте политику конфиденциальности через эту кнопку (Или откройте напрямую в браузере: https://nini123456789niki.github.io/BotsNiNi/):", reply_markup=reply_markup) # Send privacy policy message with button and direct link.

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    keyboard.append([InlineKeyboardButton("Политика конфиденциальности", url="https://t.me/NiNi_bots_bot/privacy_policy")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Откройте политику конфиденциальности через эту кнопку (Или откройте напрямую в браузере: https://nini123456789niki.github.io/BotsNiNi/):", reply_markup=reply_markup)
