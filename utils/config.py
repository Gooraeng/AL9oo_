from dotenv import load_dotenv

import os, sys


sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

load_dotenv()

discord_api_token = os.getenv('discord_api_token')
feedback_log_channel = os.getenv('feedback_log_channel')
refer_db = os.getenv('refer_db')
carhunt_db = os.getenv('carhunt_db')
clash_db = os.getenv('clash_db')
elite_db = os.getenv('elite_db')
weekly_db = os.getenv('weekly_db')
db_webhook = os.getenv('db_webhook')

vaild_formats = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
]