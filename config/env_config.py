import os

from dotenv import load_dotenv

load_dotenv()

TWOCAPTCHA_KEY = os.getenv("TWOCAPTCHA_KEY")
