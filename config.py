from dotenv import load_dotenv
import os

if os.path.exists('configs.env'):
    load_dotenv('configs.env')

class Config:
    API_ID = int(os.getenv('API_ID'))
    API_HASH = os.getenv('API_HASH')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    MONGO_URI = os.getenv('MONGO_URL')
    DEFAULT_VOL = float(os.getenv('DEFAULT_VOL'))
