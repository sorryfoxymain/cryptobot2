import logging
import requests
from typing import Optional
import time
import config

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        
    def send_message(self, chat_id: int, text: str) -> bool:
        """Send message to specified chat"""
        try:
            url = f"{self.api_url}/sendMessage"
            response = requests.post(url, json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            })
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
            
    def get_updates(self) -> list:
        """Get updates (new messages) from Telegram"""
        try:
            url = f"{self.api_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 30
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            updates = response.json()
            
            if updates.get('ok') and updates.get('result'):
                if updates['result']:
                    self.last_update_id = updates['result'][-1]['update_id']
                return updates['result']
            return []
            
        except Exception as e:
            logger.error(f"Error getting updates: {str(e)}")
            return []
            
    def handle_updates(self):
        """Process incoming messages"""
        updates = self.get_updates()
        
        for update in updates:
            if 'message' not in update:
                continue
                
            message = update['message']
            chat_id = message['chat']['id']
            
            if 'text' not in message:
                continue
                
            text = message['text']
            
            # Handle /start command
            if text == '/start':
                welcome_message = (
                    "👋 Hi! I'm a bot for tracking cryptocurrency transactions.\n\n"
                    "I will send notifications about transactions in tracked wallets.\n\n"
                    "Tracked wallets:\n"
                )
                
                for wallet in config.TRACKED_WALLETS:
                    welcome_message += f"• {wallet[:6]}...{wallet[-4:]}\n"
                    
                self.send_message(chat_id, welcome_message)
                
                # Save chat_id for future notifications
                config.NOTIFICATION_CHANNELS['telegram']['chat_id'] = chat_id
                
    def run(self):
        """Start bot in message receiving mode"""
        logger.info("Telegram bot started and waiting for messages...")
        
        while True:
            try:
                self.handle_updates()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Bot error: {str(e)}")
                time.sleep(5)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start bot
    bot = TelegramBot(config.NOTIFICATION_CHANNELS['telegram']['bot_token'])
    bot.run() 