from typing import List, Tuple, Optional
from storage import Storage
from settings import SettingsManager
from analyzer import AnalyzerExtended
from datetime import datetime
from moralis_api import MoralisAPI

class CommandHandler:
    def __init__(self, storage: Storage, settings: SettingsManager, moralis_api: MoralisAPI):
        self.storage = storage
        self.settings = settings
        self.analyzer = AnalyzerExtended(moralis_api, storage)

    def handle_help(self) -> str:
        """Handle /help command."""
        commands = [
            ("/help", "List of all available commands"),
            ("/status", "Show bot status (running / tracking wallets / errors)"),
            ("/wallets", "List of all tracked wallets"),
            ("/addwallet <address>", "Add a wallet to track"),
            ("/removewallet <address>", "Remove a wallet from tracking"),
            ("/clearwallets", "Clear the entire list of tracked wallets"),
            ("/setchain <network>", "Select network (ETH, BSC, ARB etc.)"),
            ("/notifications <on/off>", "Enable/disable notifications"),
            ("/settings", "Show current settings"),
            ("/lasttx [count]", "Latest transactions for all wallets"),
            ("/walletinfo <address>", "Balance, assets and PnL for wallet"),
            ("/pnl <address>", "Total profit/loss for wallet"),
            ("/toptokens <address> [value/amount]", "Top 5 tokens by volume or value"),
            ("/buys <address> [count]", "List of recent purchases"),
            ("/sells <address> [count]", "List of recent sales"),
            ("/gas [network]", "Current gas fees (ETH/BSC)")
        ]
        
        return "📋 Available commands:\n\n" + "\n".join(
            f"{cmd} - {desc}" for cmd, desc in commands
        )

    def handle_status(self) -> str:
        """Handle /status command."""
        wallets = self.storage.get_tracked_wallets()
        settings = self.settings.get_settings()
        
        status_parts = [
            "🤖 Bot Status:",
            f"▫️ State: Running",
            f"▫️ Tracked wallets: {len(wallets)}",
            f"▫️ Current network: {settings.chain}",
            f"▫️ Notifications: {'Enabled' if settings.notifications_enabled else 'Disabled'}"
        ]
        
        return "\n".join(status_parts)

    def handle_wallets(self) -> str:
        """Handle /wallets command."""
        wallets = self.storage.get_tracked_wallets()
        
        if not wallets:
            return "📝 List of tracked wallets is empty"
        
        return "📝 Tracked wallets:\n\n" + "\n".join(
            f"▫️ {wallet}" for wallet in wallets
        )

    def handle_add_wallet(self, address: str) -> str:
        """Handle /addwallet command."""
        if not address:
            return "❌ Error: Please specify wallet address"
        
        if self.storage.add_wallet(address):
            return f"✅ Wallet {address} successfully added for tracking"
        else:
            return f"❌ Wallet {address} is already being tracked"

    def handle_remove_wallet(self, address: str) -> str:
        """Handle /removewallet command."""
        if not address:
            return "❌ Error: Please specify wallet address"
        
        if self.storage.remove_wallet(address):
            return f"✅ Wallet {address} removed from tracking"
        else:
            return f"❌ Wallet {address} not found in tracked list"

    def handle_clear_wallets(self) -> str:
        """Handle /clearwallets command."""
        wallets = self.storage.get_tracked_wallets()
        for wallet in wallets:
            self.storage.remove_wallet(wallet)
        
        return "✅ List of tracked wallets cleared"

    def handle_set_chain(self, chain: str) -> str:
        """Handle /setchain command."""
        if not chain:
            supported_chains = self.settings.get_supported_chains()
            return f"❌ Please specify network. Supported networks: {', '.join(supported_chains)}"
        
        chain = chain.upper()
        if chain not in self.settings.get_supported_chains():
            return f"❌ Unsupported network. Available networks: {', '.join(self.settings.get_supported_chains())}"
        
        if self.settings.set_chain(chain):
            return f"✅ Network set to: {chain}"
        else:
            return "❌ Error setting network"

    def handle_notifications(self, state: str) -> str:
        """Handle /notifications command."""
        if not state or state.lower() not in ['on', 'off']:
            return "❌ Please specify state (on/off)"
        
        enabled = state.lower() == 'on'
        if self.settings.set_notifications(enabled):
            return f"✅ Notifications {'enabled' if enabled else 'disabled'}"
        else:
            return "❌ Error changing notification settings"

    def handle_settings(self) -> str:
        """Handle /settings command."""
        settings = self.settings.get_settings()
        
        settings_parts = [
            "⚙️ Current settings:",
            f"▫️ Network: {settings.chain}",
            f"▫️ Notifications: {'Enabled' if settings.notifications_enabled else 'Disabled'}",
            f"▫️ Last updated: {datetime.fromtimestamp(settings.last_updated).strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        return "\n".join(settings_parts)

    async def handle_last_transactions(self, limit: int = 5) -> str:
        """Handle /lasttx command."""
        transactions = await self.analyzer.get_last_transactions(limit)
        
        if not transactions:
            return "❌ No transactions found"
        
        result = ["📝 Latest transactions:"]
        for tx in transactions:
            action = "Purchase" if tx.transaction_type == "buy" else "Sale"
            result.append(
                f"▫️ {action}: {tx.amount_change:.4f} {tx.symbol} "
                f"(${tx.total_value_usd:.2f}) - "
                f"{datetime.fromtimestamp(tx.timestamp).strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        return "\n".join(result)

    async def handle_wallet_info(self, wallet_address: str) -> str:
        """Handle /walletinfo command."""
        if not wallet_address:
            return "❌ Please specify wallet address"
        
        wallet_info = await self.analyzer.get_wallet_info(wallet_address)
        if not wallet_info:
            return "❌ Failed to get wallet information"
        
        result = [
            f"💼 Wallet information for {wallet_address[:6]}...{wallet_address[-4:]}:",
            f"▫️ Total value: ${wallet_info.total_value_usd:.2f}",
            f"▫️ Total P&L: ${wallet_info.pnl_total_usd:.2f}",
            "\n📊 Assets:"
        ]
        
        for token in wallet_info.tokens:
            result.append(
                f"▫️ {token.symbol}: {token.amount:.4f} "
                f"(${token.total_value_usd:.2f})"
            )
        
        return "\n".join(result)

    async def handle_pnl(self, wallet_address: str) -> str:
        """Handle /pnl command."""
        if not wallet_address:
            return "❌ Please specify wallet address"
        
        pnl = await self.analyzer.calculate_total_pnl(wallet_address)
        return (
            f"💰 P&L for wallet {wallet_address[:6]}...{wallet_address[-4:]}:\n"
            f"{'📈' if pnl >= 0 else '📉'} ${pnl:.2f}"
        )

    async def handle_top_tokens(self, wallet_address: str, sort_by: str = 'value') -> str:
        """Handle /toptokens command."""
        if not wallet_address:
            return "❌ Please specify wallet address"
        
        tokens = await self.analyzer.get_top_tokens(wallet_address, sort_by=sort_by)
        if not tokens:
            return "❌ No tokens found"
        
        result = [f"🏆 Top tokens for {wallet_address[:6]}...{wallet_address[-4:]}:"]
        for i, token in enumerate(tokens, 1):
            result.append(
                f"{i}. {token.symbol}: {token.amount:.4f} "
                f"(${token.total_value_usd:.2f})"
            )
        
        return "\n".join(result)

    async def handle_buys(self, wallet_address: str, limit: int = 5) -> str:
        """Handle /buys command."""
        if not wallet_address:
            return "❌ Please specify wallet address"
        
        buys = await self.analyzer.get_recent_buys(wallet_address, limit)
        if not buys:
            return "❌ No purchases found"
        
        result = [f"🟢 Recent purchases for {wallet_address[:6]}...{wallet_address[-4:]}:"]
        for buy in buys:
            result.append(
                f"▫️ {buy.amount_change:.4f} {buy.symbol} "
                f"at ${buy.price_usd:.2f} (${buy.total_value_usd:.2f}) - "
                f"{datetime.fromtimestamp(buy.timestamp).strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        return "\n".join(result)

    async def handle_sells(self, wallet_address: str, limit: int = 5) -> str:
        """Handle /sells command."""
        if not wallet_address:
            return "❌ Please specify wallet address"
        
        sells = await self.analyzer.get_recent_sells(wallet_address, limit)
        if not sells:
            return "❌ No sales found"
        
        result = [f"🔴 Recent sales for {wallet_address[:6]}...{wallet_address[-4:]}:"]
        for sell in sells:
            result.append(
                f"▫️ {abs(sell.amount_change):.4f} {sell.symbol} "
                f"at ${sell.price_usd:.2f} (${sell.total_value_usd:.2f}) - "
                f"{datetime.fromtimestamp(sell.timestamp).strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        return "\n".join(result)

    async def handle_gas(self, chain: str = None) -> str:
        """Handle /gas command."""
        if not chain:
            chain = self.settings.get_settings().chain
        
        gas_info = await self.analyzer.get_gas_fees(chain)
        if not gas_info:
            return f"❌ Failed to get gas fees information for network {chain}"
        
        return (
            f"⛽ Gas fees for {chain}:\n"
            f"▫️ Low: {gas_info.low:.1f} Gwei\n"
            f"▫️ Medium: {gas_info.medium:.1f} Gwei\n"
            f"▫️ High: {gas_info.high:.1f} Gwei"
        ) 