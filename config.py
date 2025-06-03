import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import json

# Load environment variables from .env file
load_dotenv()

@dataclass
class NotificationConfig:
    enabled: bool
    bot_token: str
    chat_id: Optional[str] = None

@dataclass
class Config:
    # Logging settings
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level: str = 'INFO'
    log_file: str = 'bot.log'

    # Database settings
    db_path: str = "wallet_monitor.db"

    # API settings
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    moralis_api_key: str = os.getenv('MORALIS_API_KEY', '')

    # Monitoring settings
    polling_interval: int = 60  # seconds
    significant_change_threshold: float = 0.05  # 5%
    monitoring_interval: int = 300  # seconds (5 minutes)
    max_retries: int = 3
    retry_delay: int = 60  # seconds

    # Analysis Settings
    min_transaction_value_usd: float = 100.0  # Minimum USD value for significant transactions
    min_token_value_usd: float = 10.0  # Minimum USD value for token tracking

    # Notification Settings
    notifications_enabled: bool = True
    notification_config: NotificationConfig = None

    # Wallet tracking
    tracked_wallets: List[str] = None

    def __post_init__(self):
        """Validate and initialize config after loading."""
        # Initialize logger
        logging.basicConfig(
            format=self.log_format,
            level=getattr(logging, self.log_level.upper()),
            filename=self.log_file
        )
        self.logger = logging.getLogger('config')

        # Validate API keys
        if not self.telegram_bot_token:
            self.logger.error("Telegram bot token not found in environment variables")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        if not self.moralis_api_key:
            self.logger.error("Moralis API key not found in environment variables")
            raise ValueError("MORALIS_API_KEY environment variable is required")

        # Initialize notification config
        self.notification_config = NotificationConfig(
            enabled=self.notifications_enabled,
            bot_token=self.telegram_bot_token
        )

        # Initialize tracked wallets list
        if self.tracked_wallets is None:
            self.tracked_wallets = []

        self.logger.info("Configuration initialized successfully")

    def save_chat_id(self, chat_id: str):
        """Save Telegram chat ID to config."""
        if self.notification_config:
            self.notification_config.chat_id = chat_id
            self.logger.info(f"Updated Telegram chat ID: {chat_id}")

    def add_tracked_wallet(self, wallet: str) -> bool:
        """Add a wallet to tracking list."""
        wallet = wallet.lower()
        if wallet not in self.tracked_wallets:
            self.tracked_wallets.append(wallet)
            self.logger.info(f"Added wallet to tracking: {wallet}")
            return True
        return False

    def remove_tracked_wallet(self, wallet: str) -> bool:
        """Remove a wallet from tracking list."""
        wallet = wallet.lower()
        if wallet in self.tracked_wallets:
            self.tracked_wallets.remove(wallet)
            self.logger.info(f"Removed wallet from tracking: {wallet}")
            return True
        return False

    def clear_tracked_wallets(self):
        """Clear all tracked wallets."""
        self.tracked_wallets = []
        self.logger.info("Cleared all tracked wallets")

    def to_dict(self) -> Dict:
        """Convert config to dictionary for storage/display."""
        return {
            'telegram_bot_token': '***hidden***',
            'moralis_api_key': '***hidden***',
            'polling_interval': self.polling_interval,
            'significant_change_threshold': self.significant_change_threshold,
            'monitoring_interval': self.monitoring_interval,
            'min_transaction_value_usd': self.min_transaction_value_usd,
            'notifications_enabled': self.notifications_enabled,
            'tracked_wallets': [f"{w[:6]}...{w[-4:]}" for w in self.tracked_wallets]
        }

    def __str__(self) -> str:
        """String representation of config (safe for logging)."""
        return json.dumps(self.to_dict(), indent=2)

# Create global config instance
config = Config() 