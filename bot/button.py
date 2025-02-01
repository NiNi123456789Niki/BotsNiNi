
import ast
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import logging
from telegram.ext import ContextTypes, ConversationHandler
from .config import YOUR_CHAT_ID
from .handlers import ANSWER_WAITING, CLARIFICATION_REQUEST, FAQ_QUESTIONS, LINK_WAITING, PRICE_WAITING, TIME_WAITING, send_faq_page
from db import order_operations, questions_operations, user_operations
import encrypter
from .handlers import paying

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks from inline keyboards."""
    query = update.callback_query # Get the callback query object
    await query.answer() # Acknowledge the callback query to prevent the button from spinning

    if query.data.startswith("faq_"):
        """Handles clicks on FAQ question buttons."""
        question_index = int(query.data.split('_')[1]) # Extract the question index from the callback data
        question = list(FAQ_QUESTIONS.keys())[question_index] # Get the question text from FAQ_QUESTIONS dictionary keys
        answer = FAQ_QUESTIONS[question] # Get the answer text from FAQ_QUESTIONS dictionary

        keyboard = [
            [InlineKeyboardButton("НАЗАД", callback_data="back_to_faq")] # Button to go back to FAQ page list
        ]

        await query.edit_message_text( # Edit the message to show the question and answer
            text=f"<b><strong>{question}</strong></b>\n{answer}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard) # Inline keyboard with "BACK" button
        )

    elif query.data == "back_to_faq":
        """Handles clicks on "BACK" button in FAQ question view."""
        page = context.user_data.get('faq_page', 0) # Get the current FAQ page number from user_data, default to 0
        await send_faq_page(update, context, page) # Send the FAQ page list again

    elif query.data == "next_page":
        """Handles clicks on "NEXT PAGE" button in FAQ page list."""
        page = context.user_data.get('faq_page', 0) + 1 # Increment the FAQ page number
        context.user_data['faq_page'] = page # Update the FAQ page number in user_data
        await send_faq_page(update, context, page) # Send the next FAQ page list

    elif query.data == "prev_page":
        """Handles clicks on "PREVIOUS PAGE" button in FAQ page list."""
        page = context.user_data.get('faq_page', 0) - 1 # Decrement the FAQ page number
        context.user_data['faq_page'] = page # Update the FAQ page number in user_data
        await send_faq_page(update, context, page) # Send the previous FAQ page list
    elif query.data in ("CHECKING", "MAKING", "PAYING", "COMPLETED"):
        """Handles clicks on order status filter buttons in admin panel."""
        message = ""
        orders_str = order_operations.get_orders(query.data) # Get orders from the database based on the selected status
        orders_list = ast.literal_eval(orders_str) # Convert the string representation of list of orders to a Python list

        keyboard = []

        if orders_list:
            for order in orders_list: # Iterate through the list of orders
                user_id = order['userid'] # Get user ID from order data
                desc = order['description'] # Get order description from order data
                ord_id = order['order_id'] # Get order ID from order data
                username = user_operations.get_username(user_id) # Get username from user ID
                message += f"Заказ {ord_id}: \n Пользователь {username} с id {user_id} заказал бота в описанием \"{desc}\". \n" # Construct message text for each order
                keyboard.append([InlineKeyboardButton(f"{ord_id}", callback_data=f"ord_{ord_id}")]) # Create a button for each order ID
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with order ID buttons
            await query.edit_message_text(text=message, reply_markup=reply_markup) # Edit the message to display the list of orders with buttons
        else:
            await query.edit_message_text(text="Нет заказов с данным статусом.") # If no orders found for the selected status, display this message
    elif query.data.startswith("ord_"):
        """Handles clicks on order ID buttons in admin panel to view order details."""
        data = query.data[4:] # Extract order ID from callback data
        order = order_operations.get_order(data) # Get order details from the database using order ID
        if order:
            user_id = order[0] # Get user ID from order details
            desc = order[1] # Get order description from order details
            status = order[2] # Get order status from order details
            price = order[3] # Get order price from order details
            if price is None:
                price = "пока не указана" # If price is None, set it to "not set yet"
            else:
                price = order[3] # Otherwise, use the price from the database
            username = user_operations.get_username(user_id) # Get username from user ID

            keyboard = []
            if status == "CHECKING":
                keyboard.append([InlineKeyboardButton("Попросить уточнение", callback_data=f"cor_{user_id}_{data}")]) # Button to request clarification
                keyboard.append([InlineKeyboardButton("Начать выполнение", callback_data=f"mk_{data}_{user_id}")]) # Button to start making the order
            elif status == "MAKING":
                keyboard.append([InlineKeyboardButton("Закончить выполнение", callback_data=f"py_{data}_{user_id}")]) # Button to finish making the order (move to paying stage)
            if price == 'None':
                keyboard.append([InlineKeyboardButton("Установить цену", callback_data=f"pr_{data}")]) # Button to set the price if not already set
            keyboard.append([InlineKeyboardButton("Забанить пользователя", callback_data=f"bn_{user_id}")]) # Button to ban the user
            keyboard.append([InlineKeyboardButton("Установить время", callback_data=f"stm_{user_id}")]) # Button to set the time for the order
            keyboard.append([InlineKeyboardButton("Удалить заказ", callback_data=f"delord_{data}")]) # Button to delete the order
            keyboard.append([InlineKeyboardButton("НАЗАД", callback_data=status)]) # Button to go back to the order status list
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with order action buttons

            await query.edit_message_text(text=f"Заказ {data}: \nЗаказал: {username}\nID автора заказа: {user_id}\nОписание(Что нужно сделать): {desc}\nСтатус: {status} \nЦена: {price}.", reply_markup=reply_markup) # Edit message to show order details and action buttons
        else:
            await query.edit_message_text(text=f"Заказ с ID {data} не найден.") # If order not found, display this message
    elif query.data.startswith("stm_"):
        """Handles clicks on "Set Time" button to enter TIME_WAITING state."""
        data = query.data[4:] # Extract user ID from callback data
        await query.edit_message_text("Пожалуйста укажите время...") # Ask admin to input the time
        context.user_data['user_id_for_time'] = data # Store user ID in user_data to use in TIME_WAITING state
        logging.info(f"Setting user_id_for_time: {data}")
        return TIME_WAITING # Return TIME_WAITING state for conversation handler

    elif query.data.startswith("pr_"):
        """Handles clicks on "Set Price" button to enter PRICE_WAITING state."""
        data = query.data[3:] # Extract order ID from callback data
        await query.edit_message_text("Пожалуйста отправьте цену...") # Ask admin to input the price
        context.user_data['order_id_for_price'] = data # Store order ID in user_data to use in PRICE_WAITING state
        return PRICE_WAITING # Return PRICE_WAITING state for conversation handler

    elif query.data.startswith("mk_"):
        """Handles clicks on "Start Making" button to change order status to MAKING."""
        data = query.data[3:].split("_") # Extract order ID and user ID from callback data
        order_operations.change_status("MAKING", data[0]) # Change order status in the database
        await context.bot.sendMessage(data[1], "Над вашим заказом началась работа ⚙...") # Send message to the user that work has started

    elif query.data.startswith("bn_"):
        """Handles clicks on "Ban User" button to ban the user."""
        data = query.data[3:] # Extract user ID from callback data
        user_operations.ban_user(data) # Ban the user in the database
        await query.edit_message_text("Пользователь заблокирован!") # Inform admin that user is banned

    elif query.data.startswith("delord_"):
        """Handles clicks on "Delete Order" button to delete the order."""
        data = query.data[7:] # Extract order ID from callback data
        order_operations.delete_order(data) # Delete the order from the database
        await query.edit_message_text("Заказ удален!") # Inform admin that order is deleted

    elif query.data.startswith("py_"):
        """Handles clicks on "Finish Making" button to move order to PAYING state and ask for bot link."""
        data = query.data[3:].split("_") # Extract order ID and user ID from callback data
        paying.append({"ord_id": data[0], "user_id": data[1]}) # Add order to the paying list (in-memory list, might need persistence if bot restarts)
        await query.edit_message_text("Пожалуйста отправьте ссылку на бота для теста пользователя...") # Ask admin to input the bot link for testing
        context.user_data['order_id_for_link'] = data[0] # Store order ID in user_data to use in LINK_WAITING state
        context.user_data['user_id_for_link'] = data[1] # Store user ID in user_data to use in LINK_WAITING state
        return LINK_WAITING # Return LINK_WAITING state for conversation handler

    elif query.data.startswith("cor_"):
        """Handles clicks on "Request Clarification" button to enter CLARIFICATION_REQUEST state."""
        parts = query.data[4:].split("_") # Extract user ID and order ID from callback data
        user_id = int(parts[0]) # Convert user ID to integer
        ord_id = parts[1] # Get order ID

        await query.edit_message_text(text=f"Введите уточнение для пользователя с ID: {user_id} по заказу {ord_id}:") # Ask admin to input clarification text

        context.user_data['clarification'] = {"target_user_id": user_id, "ord_id": ord_id} # Store user ID and order ID in user_data for CLARIFICATION_REQUEST state
        return CLARIFICATION_REQUEST # Return CLARIFICATION_REQUEST state for conversation handler

    elif query.data == "QUESTIONS":
        """Handles clicks on "QUESTIONS" button to view support questions."""
        try:
            questions = questions_operations.get_questions() # Get all questions from the database
            if not questions:
                await query.edit_message_text(text="Нет вопросов!") # If no questions found, display this message
            keyboard = []
            text = ""
            for question in questions: # Iterate through the questions
                text += f"Вопрос {question[0]}: \nПользователь {encrypter.decode(question[1])} с вопросом: {encrypter.decode(question[2])}\n" # Construct message text for each question, decoding user ID and question text
                keyboard.append([InlineKeyboardButton(f"{question[0]}", callback_data=f"q_{question[0]}")]) # Create button for each question ID
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with question ID buttons
            await query.edit_message_text(text=text, reply_markup=reply_markup) # Edit message to show the list of questions with buttons
        except Exception as e:
            await query.edit_message_text(text=f"Ошибка: {str(e)}") # If error occurs, display error message

    elif query.data.startswith("q_"):
        """Handles clicks on question ID buttons to view question details and actions."""
        data = query.data[2:] # Extract question ID from callback data
        question = questions_operations.get_question(data) # Get question details from the database using question ID
        keyboard = []
        keyboard.append([InlineKeyboardButton("Ответить", callback_data=f"ans_{question[0]}")]) # Button to answer the question
        keyboard.append([InlineKeyboardButton("Удалить вопрос", callback_data=f"delq_{encrypter.decode(question[1])}")]) # Button to delete the question (using user ID as callback data, might be incorrect, should be question ID)
        keyboard.append([InlineKeyboardButton("Заблокировать пользователя", callback_data=f"bn_{encrypter.decode(question[1])}")]) # Button to ban the user who asked the question
        keyboard.append([InlineKeyboardButton("НАЗАД", callback_data="QUESTIONS")]) # Button to go back to the questions list
        reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with question action buttons
        await query.edit_message_text(text=f"Вопрос {question[0]}: \nПользователь {encrypter.decode(question[1])} \nВопрос: {encrypter.decode(question[2])}", reply_markup=reply_markup) # Edit message to show question details and action buttons

    elif query.data.startswith("delq_"):
        """Handles clicks on "Delete Question" button to delete the question and notify the user."""
        data = query.data[5:] # Extract user ID from callback data (again, might be question ID instead)
        await context.bot.send_message(data, "Ваш вопрос был удален!") # Send message to the user (using user ID, should be question ID to identify the question for admin purposes)
        questions_operations.delete_question_with_tid(data) # Delete the question from the database using user ID (should be question ID)

    elif query.data == "back_to_admin":
        """Handles clicks on "BACK TO ADMIN PANEL" button (if implemented). Currently triggered by /admin command."""

        user_id = update.effective_user.id # Get user ID
        if user_id == int(YOUR_CHAT_ID): # Check if user is admin
            keyboard = []
            keyboard.append([InlineKeyboardButton("НА ПРОВЕРКУ", callback_data="CHECKING")]) # Button to view orders in CHECKING status
            keyboard.append([InlineKeyboardButton("ДЕЛАЮТСЯ", callback_data="MAKING")]) # Button to view orders in MAKING status
            keyboard.append([InlineKeyboardButton("В ПРОЦЕССЕ ОПЛАТЫ", callback_data="PAYING")]) # Button to view orders in PAYING status
            keyboard.append([InlineKeyboardButton("ВЫПОЛНЕННЫЕ", callback_data="COMPLETED")]) # Button to view orders in COMPLETED status
            keyboard.append([InlineKeyboardButton("ВОПРОСЫ", callback_data="QUESTIONS")]) # Button to view questions
            reply_markup = InlineKeyboardMarkup(keyboard) # Create inline keyboard with admin panel options

            await update.message.reply_text("Какие заказы показывать сегодня:", reply_markup=reply_markup) # Send admin panel options message
        else:
            await update.message.reply_text('У вас нет прав для выполнения этой команды.') # Inform user about lack of admin rights

    elif query.data.startswith("ans_"):
        """Handles clicks on "Answer" button to enter ANSWER_WAITING state."""
        data = query.data[4:] # Extract question ID from callback data
        question = questions_operations.get_question(data) # Get question details from the database using question ID
        await query.edit_message_text(text=f"Ответьте на вопрос пользователя {encrypter.decode(question[1])} с вопросом: {encrypter.decode(question[2])}") # Ask admin to input answer to the question, decoding user ID and question text
        context.user_data['question_id_for_answer'] = data # Store question ID in user_data to use in ANSWER_WAITING state
        return ANSWER_WAITING # Return ANSWER_WAITING state for conversation handler
    elif query.data == "pys":
        """Handles clicks on "Agree with Time" button (positive response to time set by admin)."""
        await query.edit_message_text(text="Мы рады что вы доверяете нам ❤") # Positive feedback message
    elif query.data.startswith("nt_"):
        """Handles clicks on "Disagree with Time/Price" button (negative response to time/price set by admin)."""
        data = query.data[3:] # Extract order ID from callback data
        order_operations.change_status("COMPLETED", data) # Change order status to COMPLETED (assuming negative response means order cancellation or disagreement)
        await query.edit_message_text(text="Мы приносим извинения что вам не понравилось :(. Вы можете оставить отзыв командой /feedback.") # Apology message and suggestion to leave feedback
    else:
        await query.edit_message_text(text="Неизвестный запрос.") # For unknown callback data, display this message