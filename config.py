import os
from dotenv import load_dotenv

load_dotenv()

# ==========================
# Telegram
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==========================
# Google
# ==========================
GOOGLE_CREDENTIALS_FILE = "service_account.json"
GOOGLE_SHEET_NAME = "ShiftChange"

# ==========================
# Scheduler
# ==========================
CHECK_INTERVAL_SECONDS = 60

# ==========================
# Time Zone
# ==========================
TIMEZONE = "Asia/Tashkent"

# ==========================
# Google Sheets
# ==========================
SHEET_USERS = "Users"
SHEET_QUESTIONS = "Questions"
SHEET_SCHEDULE = "Schedule"
SHEET_SESSIONS = "Sessions"
SHEET_ANSWERS = "Answers"
SHEET_SETTINGS = "Settings"
SHEET_TEMPLATES = "MessageTemplates"
SHEET_LOG = "Log"
