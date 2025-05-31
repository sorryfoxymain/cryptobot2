import os
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv
from custom_telegram import CustomBot

# Load environment variables
load_dotenv()

# Enable logging with more detailed output
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def start_command(bot: CustomBot, chat_id: int):
    """Send a message when the command /start is issued."""
    logger.debug(f"Executing start command for chat_id: {chat_id}")
    await bot.send_message(
        chat_id=chat_id,
        text='👋 Hi! I am your Crypto Wallet Monitor Bot.\n\n'
        'I can help you track your cryptocurrency wallets '
        'and notify you about important transactions.\n\n'
        'Use /help to see available commands.'
    )

async def help_command(bot: CustomBot, chat_id: int):
    """Send a message when the command /help is issued."""
    logger.debug(f"Executing help command for chat_id: {chat_id}")
    help_text = (
        "Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/addwallet <address> - Add a wallet to monitor\n"
        "/removewallet <address> - Remove a wallet from monitoring\n"
        "/wallets - List monitored wallets\n"
        "/balance <address> - Get wallet balance\n"
        "/transactions <address> - Get recent transactions"
    )
    await bot.send_message(chat_id=chat_id, text=help_text)

async def balance_command(bot: CustomBot, chat_id: int, address: str = None):
    """Handle the balance command."""
    logger.debug(f"Executing balance command for chat_id: {chat_id}, address: {address}")
    if not address:
        await bot.send_message(
            chat_id=chat_id,
            text="Please provide a wallet address. Usage: /balance <address>"
        )
        return
    
    # Temporary response for testing
    await bot.send_message(
        chat_id=chat_id,
        text=f"Getting balance for address: {address}\nThis feature will be implemented soon."
    )

async def wallets_command(bot: CustomBot, chat_id: int):
    """Handle the wallets command."""
    logger.debug(f"Executing wallets command for chat_id: {chat_id}")
    # Temporary response for testing
    await bot.send_message(
        chat_id=chat_id,
        text="List of monitored wallets will be shown here.\nThis feature will be implemented soon."
    )

async def add_wallet_command(bot: CustomBot, chat_id: int, address: str = None):
    """Handle the addwallet command."""
    logger.debug(f"Executing addwallet command for chat_id: {chat_id}, address: {address}")
    if not address:
        await bot.send_message(
            chat_id=chat_id,
            text="Please provide a wallet address. Usage: /addwallet <address>"
        )
        return
    
    # Temporary response for testing
    await bot.send_message(
        chat_id=chat_id,
        text=f"Adding wallet: {address}\nThis feature will be implemented soon."
    )

async def remove_wallet_command(bot: CustomBot, chat_id: int, address: str = None):
    """Handle the removewallet command."""
    logger.debug(f"Executing removewallet command for chat_id: {chat_id}, address: {address}")
    if not address:
        await bot.send_message(
            chat_id=chat_id,
            text="Please provide a wallet address. Usage: /removewallet <address>"
        )
        return
    
    # Temporary response for testing
    await bot.send_message(
        chat_id=chat_id,
        text=f"Removing wallet: {address}\nThis feature will be implemented soon."
    )

async def transactions_command(bot: CustomBot, chat_id: int, address: str = None):
    """Handle the transactions command."""
    logger.debug(f"Executing transactions command for chat_id: {chat_id}, address: {address}")
    if not address:
        await bot.send_message(
            chat_id=chat_id,
            text="Please provide a wallet address. Usage: /transactions <address>"
        )
        return
    
    # Temporary response for testing
    await bot.send_message(
        chat_id=chat_id,
        text=f"Getting transactions for address: {address}\nThis feature will be implemented soon."
    )

async def message_handler(bot: CustomBot, chat_id: int, text: str):
    """Handle incoming messages."""
    logger.info(f"Received message: '{text}' from chat_id: {chat_id}")
    
    if not text:
        logger.warning(f"Received empty message from chat_id: {chat_id}")
        return

    try:
        # Split message into command and arguments
        parts = text.strip().split()
        command = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        arg = args[0] if args else None

        # Command handling
        if command == '/start':
            await start_command(bot, chat_id)
        elif command == '/help':
            await help_command(bot, chat_id)
        elif command == '/balance':
            await balance_command(bot, chat_id, arg)
        elif command == '/wallets':
            await wallets_command(bot, chat_id)
        elif command == '/addwallet':
            await add_wallet_command(bot, chat_id, arg)
        elif command == '/removewallet':
            await remove_wallet_command(bot, chat_id, arg)
        elif command == '/transactions':
            await transactions_command(bot, chat_id, arg)
        else:
            logger.warning(f"Unknown command: {command}")
            await bot.send_message(
                chat_id=chat_id,
                text="I don't understand that command. Use /help to see available commands."
            )
            
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}", exc_info=True)
        await bot.send_message(
            chat_id=chat_id,
            text="Sorry, there was an error processing your command. Please try again."
        )

async def main():
    """Start the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No token found in environment variables!")
        return

    logger.info(f"Starting bot with token: {token[:5]}...")
    bot = CustomBot(token)
    
    # Test the bot token
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{bot.base_url}/getMe") as response:
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
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{bot.base_url}/getUpdates",
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
                                await message_handler(
                                    bot,
                                    message['chat']['id'],
                                    message['text']
                                )
                    else:
                        logger.error(f"Update not OK: {updates}")
        
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}", exc_info=True)
            await asyncio.sleep(5)

if __name__ == '__main__':
    logger.info("Bot starting...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {str(e)}", exc_info=True) 