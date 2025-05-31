import logging
import time
from typing import List, Optional
import sys
from datetime import datetime
import requests
import asyncio

from moralis_api import MoralisAPI
from storage import Storage, WalletTransaction
from activity_analyzer import ActivityAnalyzer
import config

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WalletMonitorBot:
    def __init__(self):
        self.moralis_api = MoralisAPI(config.MORALIS_API_KEY)
        self.storage = Storage(config.DB_PATH)
        self.analyzer = ActivityAnalyzer(self.moralis_api, self.storage)
        
    def send_telegram_message(self, message: str) -> bool:
        """
        Send message to the bot itself in Telegram
        """
        if not config.NOTIFICATION_CHANNELS['telegram']['enabled']:
            return False
            
        bot_token = config.NOTIFICATION_CHANNELS['telegram']['bot_token']
        bot_username = config.NOTIFICATION_CHANNELS['telegram']['bot_username']
        
        try:
            # First get bot information
            info_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(info_url)
            response.raise_for_status()
            bot_info = response.json()
            
            if not bot_info.get('ok'):
                logger.error("Failed to get bot information")
                return False
                
            # Bot ID will be used as chat_id
            bot_id = bot_info['result']['id']
            
            # Send message
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            response = requests.post(url, json={
                'chat_id': bot_id,  # Send message to the bot itself
                'text': message,
                'parse_mode': 'HTML'
            })
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {str(e)}")
            return False
        
    def send_notification(self, message: str):
        """
        Send notifications through configured channels
        """
        if not config.ENABLE_NOTIFICATIONS:
            return
            
        logger.info(f"Notification: {message}")
        
        # Send to Telegram
        if config.NOTIFICATION_CHANNELS['telegram']['enabled']:
            self.send_telegram_message(message)
            
        # TODO: Add other notification channels if needed
        
    async def process_transactions(self, transactions: List[WalletTransaction], wallet_address: str):
        """
        Process detected transactions
        """
        for tx in transactions:
            if tx.total_value_usd < config.MIN_TRANSACTION_VALUE_USD:
                continue
                
            # Calculate PnL for sales
            pnl: Optional[float] = None
            if tx.transaction_type == "sell":
                pnl = await self.analyzer.calculate_pnl(tx)
                
            # Format message
            message = (
                f"🔔 New {tx.transaction_type.upper()} Transaction Detected!\n"
                f"Wallet: {wallet_address[:6]}...{wallet_address[-4:]}\n"
                f"Token: {tx.symbol} ({tx.chain})\n"
                f"Amount: {tx.amount_change:.4f}\n"
                f"Price: ${tx.price_usd:.2f}\n"
                f"Total Value: ${tx.total_value_usd:.2f}"
            )
            
            if pnl is not None:
                message += f"\nPnL: ${pnl:.2f}"
                
            self.send_notification(message)
            
    async def monitor_wallet(self, wallet_address: str) -> bool:
        """
        Monitor a single wallet
        """
        try:
            transactions = await self.analyzer.analyze_wallet(wallet_address)
            if transactions:
                await self.process_transactions(transactions, wallet_address)
            return True
            
        except Exception as e:
            logger.error(f"Error monitoring wallet {wallet_address}: {str(e)}")
            return False
            
    async def run(self):
        """
        Main bot loop
        """
        logger.info("Starting Wallet Monitor Bot...")
        
        # Send test message on startup
        test_message = "🔄 Bot started and ready to work!\n\nTracked wallets:\n"
        for wallet in config.TRACKED_WALLETS:
            test_message += f"• {wallet[:6]}...{wallet[-4:]}\n"
        
        if self.send_telegram_message(test_message):
            logger.info("Test message successfully sent to Telegram")
        else:
            logger.error("Failed to send test message to Telegram")
            return
        
        if not config.TRACKED_WALLETS:
            logger.warning("No wallets configured for tracking. Please add wallets to config.py")
            return
            
        retry_count = 0
        
        while True:
            try:
                for wallet in config.TRACKED_WALLETS:
                    logger.debug(f"Checking wallet: {wallet}")
                    success = await self.monitor_wallet(wallet)
                    
                    if not success:
                        retry_count += 1
                        if retry_count >= config.MAX_RETRIES:
                            logger.error("Max retries reached. Stopping bot.")
                            return
                    else:
                        retry_count = 0
                        
                logger.debug(f"Sleeping for {config.MONITORING_INTERVAL} seconds...")
                await asyncio.sleep(config.MONITORING_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                retry_count += 1
                if retry_count >= config.MAX_RETRIES:
                    logger.error("Max retries reached. Stopping bot.")
                    break
                    
                logger.info(f"Retrying in {config.RETRY_DELAY} seconds...")
                await asyncio.sleep(config.RETRY_DELAY)

if __name__ == "__main__":
    bot = WalletMonitorBot()
    asyncio.run(bot.run()) 