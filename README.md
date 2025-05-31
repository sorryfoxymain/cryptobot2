<<<<<<< HEAD
# Crypto Wallet Monitor Bot

A powerful Telegram bot for monitoring cryptocurrency wallets across multiple blockchains. The bot tracks wallet activities, detects transactions, and provides real-time notifications about token movements.

At the moment we have just a working bot with commands, a bot with working functions I will add in 1-2 weeks, when everything will be finalized and tested. Now you can use my code as a good basis for your project.

## Key Features

### Multi-Chain Support
- Ethereum (ETH)
- Binance Smart Chain (BSC)
- Polygon (MATIC)
- Arbitrum (ARB)
- Avalanche (AVAX)

### Wallet Monitoring
- Real-time transaction tracking
- Token balance monitoring
- Portfolio value updates
- Multiple wallet support
- Custom notification thresholds

### Transaction Analysis
- Transaction type detection (buys/sells)
- Price tracking for tokens
- Total value calculation
- Profit/Loss (P&L) analysis
- Historical transaction data

### Gas Monitoring
- Real-time gas prices
- Network-specific gas tracking
- Gas price alerts (low/medium/high)

### Notifications
- Real-time transaction alerts
- Price movement notifications
- Gas price alerts
- Portfolio value updates
- P&L reports

## Bot Commands

### Basic Commands
- `/help` - Display all available commands
- `/start` - Initialize the bot
- `/status` - Show current bot status
- `/settings` - Display current settings

### Wallet Management
- `/addwallet <address>` - Add a new wallet to track
- `/removewallet <address>` - Stop tracking a wallet
- `/wallets` - List all tracked wallets
- `/clearwallets` - Remove all tracked wallets

### Analysis Commands
- `/lasttx [count]` - Show recent transactions
- `/walletinfo <address>` - Display wallet details and balancesо
- `/pnl <address>` - Calculate profit/loss for wallet
- `/toptokens <address> [value/amount]` - List top tokens by value or amount
- `/buys <address> [count]` - Show recent purchases
- `/sells <address> [count]` - Show recent sales
- `/gas [network]` - Display current gas prices

### Settings Commands
- `/setchain <network>` - Change active blockchain network
- `/notifications <on/off>` - Toggle notifications

## Technical Details

### Architecture
The bot is built using modern Python features and follows best practices:
- Asynchronous operations using `async/await`
- Type hints for better code reliability
- Clean architecture with separation of concerns
- Efficient database management
- Error handling and retry mechanisms

### Components
- `activity_analyzer.py` - Core transaction analysis logic
- `moralis_api.py` - Blockchain data integration
- `storage.py` - Database management
- `commands.py` - Telegram command handlers
- `notifier.py` - Notification system
- `settings.py` - Configuration management
- `main.py` - Bot initialization and main loop

### Dependencies
- Python 3.8+
- `python-telegram-bot` - Telegram API integration
- `aiohttp` - Async HTTP client
- `python-dotenv` - Environment configuration
- `Pillow` - Image processing for charts
- `sqlite3` - Local database storage

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-wallet-monitor.git
cd crypto-wallet-monitor
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with required credentials:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
MORALIS_API_KEY=your_moralis_api_key
```

## Configuration

### Environment Variables
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Chat ID for notifications
- `MORALIS_API_KEY` - API key from Moralis

### Bot Settings (config.py)
- `POLLING_INTERVAL` - Wallet check frequency
- `MONITORING_INTERVAL` - Time between updates
- `MIN_TRANSACTION_VALUE_USD` - Minimum transaction value for notifications
- `SIGNIFICANT_CHANGE_THRESHOLD` - Threshold for balance change alerts

## Running the Bot

1. Start the bot:
```bash
python main.py
```

2. Initialize in Telegram:
- Start chat with your bot
- Send `/start` command
- Follow setup instructions

## Security Considerations

### API Keys
- Store API keys in `.env` file
- Never commit sensitive data
- Use environment variables
- Regularly rotate API keys

### Data Protection
- Local SQLite database
- Encrypted storage recommended
- Regular backups suggested
- Access control implementation

### Best Practices
- Regular dependency updates
- Security patch monitoring
- Rate limiting implementation
- Error logging and monitoring

## Troubleshooting

### Common Issues
1. API Connection Problems
   - Check API keys
   - Verify network connection
   - Review rate limits

2. Database Errors
   - Check file permissions
   - Verify database integrity
   - Clear corrupted data

3. Notification Issues
   - Confirm Telegram token
   - Check chat ID
   - Verify bot permissions

### Debug Mode
Enable debug logging in `config.py`:
```python
LOG_LEVEL = 'DEBUG'
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests:
1. Check existing issues
2. Create detailed bug report
3. Include error logs
4. Provide reproduction steps 
=======
# crypto-wallet-monitor
A powerful Telegram bot for monitoring cryptocurrency wallets across multiple blockchains. The bot tracks wallet activities, detects transactions, and provides real-time notifications about token movements.
>>>>>>> af00635dc20566bbd5c46a125d0a9ec5998b18a8
