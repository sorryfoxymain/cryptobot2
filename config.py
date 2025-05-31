import os
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables from .env file
load_dotenv()

# Logging settings
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# Database settings
DB_PATH = "wallet_monitor.db"

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')

# Moralis settings
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjFlMGMzN2FkLTBlZDgtNGVhZi1iYzJkLWJkY2M5NDQyN2ZlYiIsIm9yZ0lkIjoiNDUwMjIwIiwidXNlcklkIjoiNDYzMjM2IiwidHlwZUlkIjoiY2Q3YjY4ZmMtNDRjOS00YzQzLWE1MDgtYzRhMzA3Y2I5NDQxIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDg2OTcxMDIsImV4cCI6NDkwNDQ1NzEwMn0.RjZdniJOuhYP74C2YsiVgqDEqMcdOW_6aYmYq0Hv7gw"

# Monitoring settings
POLLING_INTERVAL = 60  # seconds
SIGNIFICANT_CHANGE_THRESHOLD = 0.05  # 5%

# Monitoring Settings
MONITORING_INTERVAL = 300  # seconds (5 minutes)
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds

# Analysis Settings
MIN_TRANSACTION_VALUE_USD = 100  # Minimum USD value to consider a transaction significant

# Notification Settings
ENABLE_NOTIFICATIONS = True
NOTIFICATION_CHANNELS = {
    "telegram": {
        "enabled": True,
        "bot_token": "7823259809:AAH7L9uBIVNfW_9hV6E393D8RL6FUKiCrEQ",
        "chat_id": None  # Will be set after /start command
    },
    "discord": {
        "enabled": False,
        "webhook_url": "YOUR_WEBHOOK_URL"
    }
}

# Wallet Settings
TRACKED_WALLETS = [
    "0xd3e8e26b1b2a520eba7c9f3db9410a20443e8dc7",
    "0xdb3ec7b16fd60fb4fdb58a438bd8af57d8d3a91c",
    "0x314d295677f81d037fd61bea21e81f9ea7aa2c64",
    "0x5a38f942b5a593652ec1eb844cae8865cdf99412",
    "0x607d2381afecbd80c4ad5cce8059205c2a297966",
] 