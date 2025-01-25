
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
    "Хочу такого же бота как у вас!": "Наш бот с открытым исходным кодом, вы можете его использовать, в соответствии с условиями лицензии (MIT License). Для удобства вот вам ссылка на репозиторий: https://github.com/NiNi123456789Niki/bot"
}

paying = []
QUESTIONS_PER_PAGE = 7
PRICE_WAITING, LINK_WAITING, DESCRIPTION_WAITING, SUPPORT_WAITING, ANSWER_WAITING, CLARIFICATION_REQUEST, CLARIFICATION_RESPONSE, ORDER_INPUT, FEEDBACK_WAITING, TIME_WAITING = range(10)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    keyboard.append([KeyboardButton("Заказать бота"), KeyboardButton("Написать в поддержку")])
    keyboard.append([KeyboardButton("Оставить отзыв"), KeyboardButton("FAQ")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Вас приветствует бот NiNi bots, после ознакомления с политикой конфиденциальности выберите опцию. Продолжая пользоваться ботом вы соглашаетесь с политикой конфиденциальности', reply_markup=reply_markup)




async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    end_date = datetime.datetime.now() + datetime.timedelta(days=30)

    title = "Подписка на ботдиллер"
    description = "Получите такие возможности как: 1. Возможность заказать бота безграничное количество раз 2. Возможность изменить заказ сколько душе угодно"
    payload = f"subscribe_{user_id}"
    provider_token = PROVIDER_TOKEN 
    currency = "UZS"
    prices = [LabeledPrice("Цена", 50000)]

    await context.bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        start_parameter=f"sub_{user_id}",
    )

    subscriptions = load_subscriptions()
    subscriptions[user_id] = end_date.strftime('%Y-%m-%d')
    save_subscriptions(subscriptions)



async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        logger.warning("Получено пустое сообщение или объект update.message")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
        return ConversationHandler.END
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите описание бота максимально подробно (Советуем почитать /faq).")
    
    return ORDER_INPUT

async def handle_order_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        is_spam = check_for_spam(user_message)
    
    except Exception as e:
        logger.error(f"Ошибка при проверке на спам: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при проверке сообщения.")
        return ConversationHandler.END

    if is_spam:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ваше сообщение было распознано как спам. Попробуйте позже.")
        return ConversationHandler.END

    user = update.effective_user
    user_id = user.id
    username = user.username or "не установлен"
    user_operations.check_for_user(username, user_id)
    block = user_operations.check_for_block(user_id)

    if block:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Вы были забанены модераторами!")
        return ConversationHandler.END
    orders = order_operations.create_order(user_id, user_message)

    if orders is False:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Вы потратили максимальное количество заказов!")
        return ConversationHandler.END

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ваш заказ был отправлен!")
    return ConversationHandler.END


async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = 0
    context.user_data['faq_page'] = page
    context.user_data['faq_message_id'] = None
    await send_faq_page(update, context, page)

async def send_faq_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    questions = list(FAQ_QUESTIONS.keys())
    num_questions = len(questions)
    start_index = page * QUESTIONS_PER_PAGE
    end_index = min(start_index + QUESTIONS_PER_PAGE, num_questions)
    
    keyboard = []
    for i in range(start_index, end_index):
        question = questions[i]
        keyboard.append([InlineKeyboardButton(question, callback_data=f"faq_{i}")])
    
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("Назад", callback_data="prev_page"))
    if end_index < num_questions:
        navigation_buttons.append(InlineKeyboardButton("Дальше", callback_data="next_page"))
    
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    chat_id = update.effective_chat.id
    
    if context.user_data['faq_message_id']:
        message_id = context.user_data['faq_message_id']
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Выберите интересующий вас вопрос:",
                reply_markup=reply_markup
            )
        except Exception as e:
            new_message = await context.bot.send_message(
                chat_id=chat_id,
                text="Выберите интересующий вас вопрос:",
                reply_markup=reply_markup
            )
            context.user_data['faq_message_id'] = new_message.message_id
    else:
        new_message = await context.bot.send_message(
            chat_id=chat_id,
            text="Выберите интересующий вас вопрос:",
            reply_markup=reply_markup
        )
        context.user_data['faq_message_id'] = new_message.message_id

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("faq_"):
        question_index = int(query.data.split('_')[1])
        question = list(FAQ_QUESTIONS.keys())[question_index]
        answer = FAQ_QUESTIONS[question]
        
        keyboard = [
            [InlineKeyboardButton("НАЗАД", callback_data="back_to_faq")]
        ]
        
        await query.edit_message_text(
            text=f"<b><strong>{question}</strong></b>\n{answer}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "back_to_faq":
        page = context.user_data.get('faq_page', 0)
        await send_faq_page(update, context, page)
    
    elif query.data == "next_page":
        page = context.user_data.get('faq_page', 0) + 1
        context.user_data['faq_page'] = page
        await send_faq_page(update, context, page)
    
    elif query.data == "prev_page":
        page = context.user_data.get('faq_page', 0) - 1
        context.user_data['faq_page'] = page
        await send_faq_page(update, context, page)
    elif query.data in ("CHECKING", "MAKING", "PAYING", "COMPLETED"):
        message = ""
        orders_str = order_operations.get_orders(query.data)
        orders_list = ast.literal_eval(orders_str)
        
        keyboard = []

        if orders_list: 
            for order in orders_list:
                user_id = order['userid']
                desc = order['description']
                ord_id = order['order_id'] 
                username = user_operations.get_username(user_id)
                message += f"Заказ {ord_id}: \n Пользователь {username} с id {user_id} заказал бота в описанием \"{desc}\". \n"
                keyboard.append([InlineKeyboardButton(f"{ord_id}", callback_data=f"ord_{ord_id}")]) 
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=message, reply_markup=reply_markup)
        else: 
            await query.edit_message_text(text="Нет заказов с данным статусом.")
    elif query.data.startswith("ord_"):
        data = query.data[4:]
        order = order_operations.get_order(data)
        if order: 
            user_id = order[0]
            desc = order[1]
            status = order[2]
            price = order[3]
            if price is None:
                price = "пока не указана"
            else:
                price = order[3]
            username = user_operations.get_username(user_id)

            keyboard = []
            if status == "CHECKING":
                keyboard.append([InlineKeyboardButton("Попросить уточнение", callback_data=f"cor_{user_id}_{data}")])
                keyboard.append([InlineKeyboardButton("Начать выполнение", callback_data=f"mk_{data}_{user_id}")]) 
            elif status == "MAKING":
                keyboard.append([InlineKeyboardButton("Закончить выполнение", callback_data=f"py_{data}_{user_id}")]) 
            if price == 'None':
                keyboard.append([InlineKeyboardButton("Установить цену", callback_data=f"pr_{data}")])
            keyboard.append([InlineKeyboardButton("Забанить пользователя", callback_data=f"bn_{user_id}")])
            keyboard.append([InlineKeyboardButton("Установить время", callback_data=f"stm_{user_id}")])
            keyboard.append([InlineKeyboardButton("Удалить заказ", callback_data=f"delord_{data}")]) 
            keyboard.append([InlineKeyboardButton("НАЗАД", callback_data=status)])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(text=f"Заказ {data}: \nЗаказал: {username}\nID автора заказа: {user_id}\nОписание(Что нужно сделать): {desc}\nСтатус: {status} \nЦена: {price}.", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=f"Заказ с ID {data} не найден.")
    elif query.data.startswith("stm_"):
        data = query.data[4:]
        await query.edit_message_text("Пожалуйста укажите время...")
        context.user_data['user_id_for_time'] = data
        logging.info(f"Setting user_id_for_time: {data}")
        return TIME_WAITING

    elif query.data.startswith("pr_"):
        data = query.data[3:]
        await query.edit_message_text("Пожалуйста отправьте цену...")
        context.user_data['order_id_for_price'] = data 
        return PRICE_WAITING
    
    elif query.data.startswith("mk_"):
        data = query.data[3:].split("_")
        order_operations.change_status("MAKING", data[0])
        await context.bot.sendMessage(data[1], "Над вашим заказом началась работа ⚙...")
    elif query.data.startswith("bn_"):
        data = query.data[3:]
        user_operations.ban_user(data)
        await query.edit_message_text("Пользователь заблокирован!")

    elif query.data.startswith("delord_"):
        data = query.data[7:]
        order_operations.delete_order(data)
        await query.edit_message_text("Заказ удален!")

    elif query.data.startswith("py_"):
        data = query.data[3:].split("_")
        paying.append({"ord_id": data[0], "user_id": data[1]})
        await query.edit_message_text("Пожалуйста отправьте ссылку на бота для теста пользователя...")
        context.user_data['order_id_for_link'] = data[0] 
        context.user_data['user_id_for_link'] = data[1] 
        return LINK_WAITING  

    elif query.data.startswith("cor_"):
        parts = query.data[4:].split("_")
        user_id = int(parts[0])
        ord_id = parts[1]

        await query.edit_message_text(text=f"Введите уточнение для пользователя с ID: {user_id} по заказу {ord_id}:")
        
        context.user_data['clarification'] = {"target_user_id": user_id, "ord_id": ord_id}
        return CLARIFICATION_REQUEST

    elif query.data == "QUESTIONS":
        try:
            questions = questions_operations.get_questions()
            if not questions:
                await query.edit_message_text(text="Нет вопросов!")
            keyboard = []
            text = ""
            for question in questions:
                text += f"Вопрос {question[0]}: \nПользователь {encrypter.decode(question[1])} с вопросом: {encrypter.decode(question[2])}\n"
                keyboard.append([InlineKeyboardButton(f"{question[0]}", callback_data=f"q_{question[0]}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        except Exception as e:
            await query.edit_message_text(text=f"Ошибка: {str(e)}")
    elif query.data.startswith("q_"):
        data = query.data[2:]
        question = questions_operations.get_question(data)
        keyboard = []
        keyboard.append([InlineKeyboardButton("Ответить", callback_data=f"ans_{question[0]}")])
        keyboard.append([InlineKeyboardButton("НАЗАД", callback_data="QUESTIONS")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"Вопрос {question[0]}: \nПользователь {encrypter.decode(question[1])} \nВопрос: {encrypter.decode(question[2])}", reply_markup=reply_markup)
    elif query.data.startswith("ans_"):
        data = query.data[4:]
        question = questions_operations.get_question(data)
        await query.edit_message_text(text=f"Ответьте на вопрос пользователя {encrypter.decode(question[1])} с вопросом: {encrypter.decode(question[2])}")
        context.user_data['question_id_for_answer'] = data
        return ANSWER_WAITING
    elif query.data == "pys":
        await query.edit_message_text(text="Мы рады что вы доверяете нам ❤")
    elif query.data.startswith("nt_"):
        data = query.data[3:]
        order_operations.change_status("COMPLETED", data)
        await query.edit_message_text(text="Мы приносим извинения что вам не понравилось :(. Вы можете оставить отзыв командой /feedback.")
    else:
        await query.edit_message_text(text="Неизвестный запрос.")


async def handle_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Getting to TIME_WAITING")
    time = update.message.text
    tid = context.user_data.get('user_id_for_time')
    keyboard = []
    order = order_operations.get_order_from_tid(tid) 
    if order:
        order_id = order[0]
        keyboard.append([InlineKeyboardButton("Согласен", callback_data="pys")])
        keyboard.append([InlineKeyboardButton("Не согласен", callback_data=f"nt_{order_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Время установлено.")
        await context.bot.send_message(tid, f"Время на ваш заказ {time}. Пожалуйста если вы не согласны с ценой, нажмите \"Не согласен\".", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Order not found.")
    context.user_data.pop('user_id_for_time', None) 
    return ConversationHandler.END 

async def handle_answer_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    question_id = context.user_data.get('question_id_for_answer')
    question = questions_operations.get_question(question_id)
    await context.bot.send_message(chat_id=encrypter.decode(question[1]), text=f"Ответ на ваш вопрос: {answer}")
    await update.message.reply_text("Ваш ответ отправлен.")
    return ConversationHandler.END

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пожалуйста, введите ваше сообщение для поддержки:")
    return SUPPORT_WAITING



async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    try:
        await update.message.reply_text("Ваше сообщение отправлено в поддержку.")
        questions_operations.add_question(user_id, message)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в поддержку: {e}")
        await update.message.reply_text("Произошла ошибка при отправке сообщения в поддержку. Пожалуйста, попробуйте позже.")
    return ConversationHandler.END


async def handle_price_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_str = update.message.text
    order_id = context.user_data.get('order_id_for_price')

    try:
        price = int(price_str)
        if order_operations.set_price(order_id, price): 
            await update.message.reply_text(f"Цена {price} установлена для заказа {order_id}.")
            tid = order_operations.get_tid(ord_id=order_id)
            order_operations.set_price(order_id, price)
            keyboard = []
            keyboard.append([InlineKeyboardButton("Согласен", callback_data=f"ys")])
            keyboard.append([InlineKeyboardButton("Не согласен", callback_data=f"nt_{order_id}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(tid, f"За ваш заказ назначена цена {price} сум. Пожалуйста если вы не согласны с ценой, нажмите \"Не согласен\".", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Ошибка при обновлении цены в базе данных.")

    except ValueError:
        await update.message.reply_text("Неверный формат цены. Пожалуйста, введите число.")
        return PRICE_WAITING
    return ConversationHandler.END

async def handle_link_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    order_id = context.user_data.get('order_id_for_link')
    user_id = context.user_data.get('user_id_for_link')

    try:
        
        order_operations.change_status("PAYING", order_id)
        await context.bot.send_message(user_id, f"Для теста бота перейдите по {link}! Примечание: Если спустя 96 часов вы не оплатили бот, то бот может использоваться в других проектах! Если вам не понравился бот, то вы можете прописать команду /edit и изменить.")
        await context.bot.send_message(user_id, "После теста, и убеждения что бот вам подходит пожалуйста заплатите командой /pay")
        await update.message.reply_text(f"Ссылка {link} отправлена пользователю {user_id} для заказа {order_id}.")
    except Exception as e:  
        logger.error(f"Error sending link: {e}")
        await update.message.reply_text("Не удалось отправить ссылку.")


    return ConversationHandler.END 

async def handle_clarification_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clarification_data = context.user_data.get('clarification')
    if clarification_data:
        target_user_id = clarification_data["target_user_id"]
        ord_id = clarification_data["ord_id"]
        clarification_request = update.message.text 

        try:
            sent_message = await context.bot.send_message(chat_id=target_user_id, text=f"Уточнение по вашему заказу {ord_id}: {clarification_request}\n\nПожалуйста, ответьте на это сообщение.")
            
            context.user_data['waiting_for_clarification'] = {"ord_id": ord_id, "request_message_id": sent_message.message_id}
            await update.message.reply_text(text=f"Запрос на уточнение отправлен пользователю {target_user_id}.")
        except Exception as e:
            logger.error(f"Error sending clarification request: {e}")
            await update.message.reply_text(text="Не удалось отправить запрос на уточнение.")
        finally:
            del context.user_data['clarification']
        return CLARIFICATION_RESPONSE

    elif update.message.reply_to_message:
        waiting_data = context.user_data.get('waiting_for_clarification')
        if waiting_data and update.message.reply_to_message.message_id == waiting_data["request_message_id"]:
            ord_id = waiting_data["ord_id"]
            clarification_answer = update.message.text
            try:
                order = order_operations.get_order(ord_id)
                if order:
                    order_operations.add_to_desc(ord_id, clarification_answer)
                    await update.message.reply_text("Ваш ответ на уточнение отправлен.")
                else:
                    await update.message.reply_text(f"Заказ с ID {ord_id} не найден.")
            except Exception as e:
                logger.error(f"Error updating description or retrieving request: {e}")
                await update.message.reply_text("Не удалось обновить описание заказа или получить запрос.")
            finally:
                del context.user_data['waiting_for_clarification']
            return ConversationHandler.END

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        logger.warning("Получено пустое сообщение или объект update.message")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
        return
    
    user_id = update.effective_user.id
    if user_id == int(YOUR_CHAT_ID):
        keyboard = []
        keyboard.append([InlineKeyboardButton("НА ПРОВЕРКУ", callback_data="CHECKING")])
        keyboard.append([InlineKeyboardButton("ДЕЛАЮТСЯ", callback_data="MAKING")])
        keyboard.append([InlineKeyboardButton("В ПРОЦЕССЕ ОПЛАТЫ", callback_data="PAYING")])
        keyboard.append([InlineKeyboardButton("ВЫПОЛНЕННЫЕ", callback_data="COMPLETED")])
        keyboard.append([InlineKeyboardButton("ВОПРОСЫ", callback_data="QUESTIONS")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Какие заказы показывать сегодня:", reply_markup=reply_markup)
    else:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update caused error {context.error}")
    if update: 
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла непредвиденная ошибка.")

async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    order = order_operations.get_order_from_tid(chat_id)
    if order == "Empty":
        await context.bot.send_message(chat_id=chat_id, text="У вас нет заказов!")
    elif order[2] == "PAYING":
        title = "Оплата за бота"
        description = order[1]
        payload = f"pay_{order[0]}"
        provider_token = PROVIDER_TOKEN 
        currency = "UZS"
        prices = [LabeledPrice("Цена", order[3] * 100)]

        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            start_parameter=f"pay_{order[0]}",
        )
    else:
        await context.bot.send_message(chat_id=chat_id, text="У вас нет заказов на оплату!")

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.successful_payment.invoice_payload.startswith("pay_"):
        order_id = update.message.successful_payment.invoice_payload[4:]
        user_id = update.effective_user.id
        await context.bot.send_message(chat_id=user_id, text="Спасибо за оплату! Будем благодарны если вы оставите отзыв о нашем боте (/feedback).")
        order_operations.change_status("COMPLETED", order_id)
    elif update.message.successful_payment.invoice_payload.startswith("subscribe_"):
        user_id = update.effective_user.id
        await context.bot.send_message(chat_id=user_id, text="Спасибо за оплату! Теперь вы можете заказывать ботов без ограничений.")
        user_operations.subscribe(user_id)

    else:
        await context.bot.send_message(chat_id=update.effective_user.id, text="Ошибка при обработке оплаты.")

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_operations.edit(user_id) is False:
        await context.bot.send_message(chat_id=user_id, text="У вас закончились попытки изменить заказ!")
    else:
        if order_operations.get_order_from_tid(user_id)[2] == "PAYING":
            await context.bot.send_message(chat_id=user_id, text="Пожалуйста, напишите описание изменений, которые вы хотите внести.")
            return DESCRIPTION_WAITING
        else:
            await context.bot.send_message(chat_id=user_id, text="Вы не можете изменить заказ!")

async def handle_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    order_id = order_operations.get_order_from_tid(user_id)[0]
    new_description = update.message.text
    order_operations.add_to_desc(order_id, new_description)
    user_operations.edit(user_id)
    order_operations.change_status("MAKING", order_id)
    await context.bot.send_message(chat_id=user_id, text="Ваши изменения были успешно добавлены к заказу. Скоро за ваш заказ снова возьмутся разработчики.")
    return ConversationHandler.END

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = order_operations.get_order_from_tid(user_id)[2]
    if status == "COMPLETED":
        await update.message.reply_text("Пожалуйста, напишите ваш отзыв о нашем боте.")
        return FEEDBACK_WAITING
    else:
        await update.message.reply_text("Вы не можете оставить отзыв, пока ваш заказ не будет выполнен.")
        return ConversationHandler.END

async def handle_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feedback = update.message.text
    user_id = update.effective_user.id
    await context.bot.send_message(chat_id=config.FEEDBACK_CHAT_ID, text=f"Отзыв от пользователя {user_id}: {feedback}")
    await update.message.reply_text("Ваш отзыв был успешно добавлен.")
    return ConversationHandler.END

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    keyboard.append([InlineKeyboardButton("Политика конфиденциальности", url="https://t.me/NiNi_bots_bot/privacy_policy")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Откройте политику конфиденциальности через эту кнопку (Или откройте напрямую в браузере: https://nini123456789niki.github.io/bot/):", reply_markup=reply_markup)
