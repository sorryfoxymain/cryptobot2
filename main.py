import os
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv
from custom_telegram import CustomBot
from moralis_api import MoralisAPI
from storage import Storage
from settings import SettingsManager
from commands import CommandHandler

# Load environment variables
load_dotenv()

# Enable logging with minimal output
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler('bot.log'),
    ]
)

logger = logging.getLogger(__name__)

class WalletMonitorBot:
    def __init__(self):
        self.moralis_api = MoralisAPI(os.getenv('MORALIS_API_KEY'))
        self.monitoring_enabled = True
        self.notification_chat_ids = set()
        self._initialized = False

    @classmethod
    async def create(cls) -> 'WalletMonitorBot':
        """Create and initialize a new WalletMonitorBot instance."""
        instance = cls()
        await instance.initialize()
        return instance

    async def initialize(self):
        """Initialize bot components."""
        if not self._initialized:
            self.storage = await Storage.create("wallet_monitor.db")
            self.settings = await SettingsManager.create()
            self.bot = CustomBot(os.getenv('TELEGRAM_BOT_TOKEN'))
            self.command_handler = CommandHandler(self.storage, self.settings, self.moralis_api)
            self._initialized = True

    async def process_transactions(self, transactions, wallet_address: str):
        """Process detected transactions"""
        for tx in transactions:
            if tx.total_value_usd < 100:  # Минимальная сумма для уведомлений
                continue
                
            # Calculate PnL for sales
            pnl = None
            if tx.transaction_type == "sell":
                pnl = await self.command_handler.analyzer.calculate_pnl(tx)
                
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
                
            # Send notification to all subscribed chats
            for chat_id in self.notification_chat_ids:
                await self.bot.send_message(chat_id, message)

    async def monitor_wallet(self, wallet_address: str) -> bool:
        """Monitor a single wallet"""
        try:
            transactions = await self.command_handler.analyzer.analyze_wallet(wallet_address)
            if transactions:
                await self.process_transactions(transactions, wallet_address)
            return True
            
        except Exception as e:
            logger.error(f"Error monitoring wallet {wallet_address}: {str(e)}")
            return False

    async def monitor_wallets(self):
        """Monitor all wallets in background"""
        logger.info("Starting wallet monitoring...")
        
        retry_count = 0
        max_retries = 3
        monitoring_interval = 60  # 1 minute
        
        while self.monitoring_enabled:
            try:
                wallets = self.storage.get_tracked_wallets()
                
                if not wallets:
                    logger.debug("No wallets to monitor")
                    await asyncio.sleep(monitoring_interval)
                    continue
                
                for wallet in wallets:
                    logger.debug(f"Checking wallet: {wallet}")
                    success = await self.monitor_wallet(wallet)
                    
                    if not success:
                        retry_count += 1
                        if retry_count >= max_retries:
                            logger.error("Max retries reached for wallet monitoring")
                            retry_count = 0
                    else:
                        retry_count = 0
                        
                await asyncio.sleep(monitoring_interval)
                
            except Exception as e:
                logger.error(f"Unexpected error in wallet monitoring: {str(e)}")
                await asyncio.sleep(30)  # Wait 30 seconds before retry

    async def message_handler(self, chat_id: int, text: str):
        """Handle incoming messages."""
        print(f"\nReceived message: '{text}' from chat_id: {chat_id}")
        
        if not text:
            print("Received empty message")
            return

        try:
            # Split message into command and arguments
            parts = text.strip().split()
            command = parts[0].lower() if parts else ""
            args = parts[1:] if len(parts) > 1 else []
            arg = args[0] if args else None

            print(f"Command: {command}")
            print(f"Arguments: {args}")
            
            # Command handling
            response = None
            
            if command == '/start':
                self.notification_chat_ids.add(chat_id)
                response = '👋 Hi! I am your Crypto Wallet Monitor Bot.\n\nI can help you track your cryptocurrency wallets and notify you about important transactions.\n\nUse /help to see available commands.'
            elif command == '/help':
                response = await self.command_handler.handle_help()
            elif command == '/status':
                response = await self.command_handler.handle_status()
            elif command == '/wallets':
                response = await self.command_handler.handle_wallets()
            elif command == '/addwallet':
                response = await self.command_handler.handle_add_wallet(arg)
            elif command == '/removewallet':
                response = await self.command_handler.handle_remove_wallet(arg)
            elif command == '/clearwallets':
                response = await self.command_handler.handle_clear_wallets()
            elif command == '/setchain':
                response = await self.command_handler.handle_set_chain(arg)
            elif command == '/notifications':
                response = await self.command_handler.handle_notifications(arg)
            elif command == '/settings':
                response = await self.command_handler.handle_settings()
            elif command == '/lasttx':
                limit = int(arg) if arg and arg.isdigit() else 5
                response = await self.command_handler.handle_last_transactions(limit)
            elif command == '/walletinfo':
                print(f"Processing /walletinfo command for address: {arg}")
                response = await self.command_handler.handle_wallet_info(arg)
                print(f"Wallet info response: {response}")
            elif command == '/pnl':
                response = await self.command_handler.handle_pnl(arg)
            elif command == '/toptokens':
                sort_by = args[1] if len(args) > 1 else 'value'
                response = await self.command_handler.handle_top_tokens(arg, sort_by)
            elif command == '/buys':
                limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 5
                response = await self.command_handler.handle_buys(arg, limit)
            elif command == '/sells':
                limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 5
                response = await self.command_handler.handle_sells(arg, limit)
            elif command == '/gas':
                response = await self.command_handler.handle_gas(arg)
            else:
                response = "I don't understand that command. Use /help to see available commands."

            if response:
                print(f"Sending response: {response[:100]}...")
                await self.bot.send_message(chat_id=chat_id, text=response)
                
        except Exception as e:
            print(f"Error handling message: {str(e)}", exc_info=True)
            await self.bot.send_message(
                chat_id=chat_id,
                text="Sorry, there was an error processing your command. Please try again."
            )

    async def run(self):
        """Run bot with concurrent wallet monitoring and command handling"""
        if not self._initialized:
            await self.initialize()

        logger.info("Starting Wallet Monitor Bot...")
        
        # Create task for wallet monitoring
        monitoring_task = asyncio.create_task(self.monitor_wallets())
        
        # Test the bot token
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.bot.base_url}/getMe") as response:
                    if response.status == 200:
                        me = await response.json()
                        if me.get('ok'):
                            logger.info(f"Bot authorized as: {me['result']['username']}")
                        else:
                            logger.error(f"Bot authorization failed: {me}")
                            return
                    else:
                        logger.error(f"Failed to authorize bot: {response.status}")
                        return
        except Exception as e:
            logger.error(f"Error testing bot token: {str(e)}")
            return

        logger.info("Starting message polling...")
        offset = 0
        
        try:
            while True:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.bot.base_url}/getUpdates",
                            params={
                                'offset': offset,
                                'timeout': 30,
                                'allowed_updates': ['message']
                            }
                        ) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                logger.error(f"Error from Telegram API: {response.status} - {error_text}")
                                await asyncio.sleep(5)
                                continue

                            updates = await response.json()
                            logger.debug(f"Received updates: {updates}")
                            
                            if updates.get('ok'):
                                for update in updates.get('result', []):
                                    offset = update['update_id'] + 1
                                    
                                    if 'message' in update and 'text' in update['message']:
                                        message = update['message']
                                        await self.message_handler(
                                            message['chat']['id'],
                                            message['text']
                                        )
                            else:
                                logger.error(f"Update not OK: {updates}")
                
                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}", exc_info=True)
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {str(e)}")
        finally:
            # Stop wallet monitoring
            self.monitoring_enabled = False
            monitoring_task.cancel()

if __name__ == "__main__":
    logger.info("Bot starting...")
    try:
        async def main():
            bot = await WalletMonitorBot.create()
            await bot.run()
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {str(e)}", exc_info=True) 