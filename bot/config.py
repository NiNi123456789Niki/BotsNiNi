import dotenv, os

dotenv.load_dotenv("D:/projects/bot/.env")

BOT_TOKEN = os.getenv("TOKEN")
YOUR_CHAT_ID = os.getenv("YOUR_CHAT_ID")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
FEEDBACK_CHAT_ID = os.getenv("FEEDBACK_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")