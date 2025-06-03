# CryptoBot

A Telegram bot for monitoring wallets and tracking cryptocurrency transactions in real-time.

## Features

- 🔍 Real-time wallet monitoring
- 💰 Token balance tracking
- 📊 Price tracking for tokens
- 📈 PnL (Profit and Loss) calculation
- 🔔 Transaction notifications
- 💼 Multi-wallet support
- ⚡ Fast and efficient API integration with Moralis

## Commands

- `/start` - Start the bot and enable notifications
- `/help` - Show available commands
- `/status` - Check bot status
- `/wallets` - List tracked wallets
- `/addwallet <address>` - Add a wallet to track
- `/removewallet <address>` - Remove a tracked wallet
- `/clearwallets` - Remove all tracked wallets
- `/setchain <chain>` - Set the blockchain to monitor
- `/notifications <on/off>` - Toggle notifications
- `/settings` - View current settings
- `/lasttx <limit>` - View last transactions
- `/walletinfo <address>` - Get detailed wallet information
- `/pnl <address>` - Calculate profit/loss
- `/toptokens <address> <sort_by>` - View top tokens by value/amount
- `/buys <address> <limit>` - View buy transactions
- `/sells <address> <limit>` - View sell transactions
- `/gas <chain>` - Check current gas prices

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file with the following variables:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MORALIS_API_KEY=your_moralis_api_key
```
4. Run the bot:
```bash
python main.py
```

## Requirements

- Python 3.8+
- aiohttp
- python-dotenv
- SQLite3

## Environment Variables

- `TELEGRAM_BOT_TOKEN` - Your Telegram Bot Token from @BotFather
- `MORALIS_API_KEY` - Your Moralis API Key

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
