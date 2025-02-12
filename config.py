import  os
import dotenv

dotenv.load_dotenv()



CASCADE_USER = os.getenv('CASCADE_USER')
CASCADE_PASSWORD = os.getenv('CASCADE_PASSWORD')
CASCADE_USERS_URL = os.getenv('CASCADE_USERS_URL')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
