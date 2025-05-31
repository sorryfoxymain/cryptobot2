from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from storage import WalletTransaction

class TelegramNotifier:
    def __init__(self, bot_token: str, default_chat_id: Optional[str] = None):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            default_chat_id: Default chat ID for sending messages
        """
        self.bot = Bot(token=bot_token)
        self.default_chat_id = default_chat_id

    async def send_transaction_notification(
        self, 
        transaction: WalletTransaction, 
        pnl: Optional[float] = None,
        chat_id: Optional[str] = None
    ):
        """
        Send notification about detected transaction.
        
        Args:
            transaction: Transaction details
            pnl: Optional profit/loss value for sell transactions
            chat_id: Optional specific chat ID for sending (if not provided, default chat is used)
        """
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            raise ValueError("Chat ID not provided and not set as default")

        # Create message
        action = "🟢 Bought" if transaction.transaction_type == "buy" else "🔴 Sold"
        
        message = (
            f"{action} {transaction.symbol}\n\n"
            f"Network: {transaction.chain}\n"
            f"Amount: {transaction.amount_change:.4f}\n"
            f"Price: ${transaction.price_usd:.2f}\n"
            f"Total value: ${transaction.total_value_usd:.2f}\n"
            f"Wallet: {transaction.wallet_address[:6]}...{transaction.wallet_address[-4:]}"
        )
        
        if pnl is not None and transaction.transaction_type == "sell":
            profit_emoji = "📈" if pnl > 0 else "📉"
            message += f"\nP&L: {profit_emoji} ${pnl:.2f}"

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode='HTML'
            )
        except TelegramError as e:
            print(f"Failed to send Telegram notification: {str(e)}")

    async def send_wallet_list(self, wallets: list[str], chat_id: Optional[str] = None):
        """Send list of tracked wallets."""
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            raise ValueError("Chat ID not provided and not set as default")

        if not wallets:
            message = "No wallets are currently being tracked."
        else:
            message = "📋 Tracked wallets:\n\n"
            for i, wallet in enumerate(wallets, 1):
                message += f"{i}. {wallet[:6]}...{wallet[-4:]}\n"

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode='HTML'
            )
        except TelegramError as e:
            print(f"Failed to send Telegram notification: {str(e)}")

    async def send_error_notification(
        self, 
        error_message: str, 
        chat_id: Optional[str] = None
    ):
        """Send error notification."""
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            raise ValueError("Chat ID not provided and not set as default")

        message = f"⚠️ Error: {error_message}"

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode='HTML'
            )
        except TelegramError as e:
            print(f"Failed to send Telegram notification: {str(e)}")

# Example usage
if __name__ == "__main__":
    import os
    from datetime import datetime
    
    # Usually this is in config.py
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    async def test_notifications():
        notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID)
        
        # Test transaction notification
        test_transaction = WalletTransaction(
            wallet_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            token_id="eth",
            symbol="ETH",
            chain="eth",
            amount_change=1.5,
            price_usd=2000.0,
            total_value_usd=3000.0,
            transaction_type="buy",
            timestamp=int(datetime.now().timestamp())
        )
        
        await notifier.send_transaction_notification(test_transaction)
        
        # Test wallet list
        test_wallets = [
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "0x1234567890123456789012345678901234567890"
        ]
        await notifier.send_wallet_list(test_wallets)
    
    if BOT_TOKEN and CHAT_ID:
        asyncio.run(test_notifications())
    else:
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables") 