# Русский

### Установка на Windows

1. Убедитесь, что у вас установлен Python.
2. Создайте свою логику шифрования в файле `encrypter.py`.
3. Создайте файл `.env` и заполните следующим образом: TOKEN=YOUR_BOT_TOKEN, ADMIN_ID=YOUR_ADMIN_ID, PROVIDER_TOKEN=YOUR_PROVIDER_TOKEN, FEEDBACK_CHAT_ID=YOUR_FEEDBACK_CHAT_ID, DATABASE_URL=DATABASE_URL.
4. Запустите скрипт `install.bat` для установки всех необходимых пакетов и библиотек.
5. Для запуска бота используйте скрипт `run.bat`.

### Установка на Linux/Mac

1. Убедитесь, что у вас установлен Python.
2. Создайте свою логику шифрования в файле `encrypter.py`.
3. Создайте файл `.env` и заполните следующим образом: TOKEN=YOUR_BOT_TOKEN, ADMIN_ID=YOUR_ADMIN_ID, PROVIDER_TOKEN=YOUR_PROVIDER_TOKEN, FEEDBACK_CHAT_ID=YOUR_FEEDBACK_CHAT_ID, DATABASE_URL=DATABASE_URL.
4. Сделайте скрипты исполняемыми:
   ```bash
   chmod +x install.sh run.sh
   ```
5. Запустите скрипт `install.sh` для установки всех необходимых пакетов и библиотек.
6. Для запуска бота используйте скрипт `run.sh`.

**ВАЖНО**: У вас должен быть установлен Python и PostgreSQL.

Этот бот разработан с использованием библиотек [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot), [schedule](https://github.com/dbader/schedule), [python-dotenv](https://github.com/theskumar/python-dotenv) и [psycopg2][https://github.com/psycopg/psycopg2].

---

# English

### Installation on Windows

1. Ensure that Python is installed.
2. Create a file `encrypter.py` and fill it with your encryption logic.
3. Create a file `.env` and fill it with the following values: TOKEN=YOUR_BOT_TOKEN, ADMIN_ID=YOUR_ADMIN_ID, PROVIDER_TOKEN=YOUR_PROVIDER_TOKEN, FEEDBACK_CHAT_ID=YOUR_FEEDBACK_CHAT_ID, DATABASE_URL=DATABASE_URL.
4. Run the `install.bat` script to install all necessary packages and libraries.
5. Use the `run.bat` script to start the bot.

### Installation on Linux/Mac

1. Ensure that Python is installed.
2. Create a file `encrypter.py` and fill it with your encryption logic.
3. Create a file `.env` and fill it with the following values: TOKEN=YOUR_BOT_TOKEN, ADMIN_ID=YOUR_ADMIN_ID, PROVIDER_TOKEN=YOUR_PROVIDER_TOKEN, FEEDBACK_CHAT_ID=YOUR_FEEDBACK_CHAT_ID, DATABASE_URL=DATABASE_URL.
4. Make the scripts executable:
   ```bash
   chmod +x install.sh run.sh
   ```
5. Run the `install.sh` script to install all necessary packages and libraries.
6. Use the `run.sh` script to start the bot.

**Important**: You must have Python and PostgreSQL installed.

This bot is developed using the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot), [schedule](https://github.com/dbader/schedule), [python-dotenv](https://github.com/theskumar/python-dotenv) and [psycopg2][https://github.com/psycopg/psycopg2] libraries .
