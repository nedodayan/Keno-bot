import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(i.strip()) for i in os.getenv("ADMIN_IDS", "123456789").split(",") if i.strip()]

# Economy constants
INITIAL_BONUS = 50.0
WITHDRAWAL_THRESHOLD = 2000.0
MIN_BET = 10.0
MAX_BET = 500.0

# Payment details shown to users
PAYMENT_INSTRUCTIONS = (
    "💳 **Deposit Instructions (Ethiopian Birr)**\n\n"
    "1. **Telebirr**: `0911223344` (Name: Abebe B.)\n"
    "2. **CBE Bank**: `1000123456789` (Name: Abebe B.)\n\n"
    "⚠️ After transferring, click **'Submit Deposit Receipt'** below and enter the amount along with the transaction reference/screenshot to notify admins."
)
