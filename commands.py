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

    async def handle_help(self) -> str:
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

    async def handle_status(self) -> str:
        """Handle /status command."""
        wallets = await self.storage.get_tracked_wallets()
        settings = await self.settings.get_settings()
        
        status_parts = [
            "🤖 Bot Status:",
            f"▫️ State: Running",
            f"▫️ Tracked wallets: {len(wallets)}",
            f"▫️ Current network: {settings['chain']}",
            f"▫️ Notifications: {'Enabled' if settings['notifications_enabled'] else 'Disabled'}"
        ]
        
        return "\n".join(status_parts)

    async def handle_wallets(self) -> str:
        """Handle /wallets command."""
        wallets = await self.storage.get_tracked_wallets()
        
        if not wallets:
            return "📝 No wallets are currently being tracked"
        
        wallet_list = ["📝 Tracked wallets:\n"]
        for i, wallet in enumerate(wallets, 1):
            wallet_list.append(f"{i}. {wallet[:6]}...{wallet[-4:]}")
        
        return "\n".join(wallet_list)

    async def handle_add_wallet(self, address: str) -> str:
        """Handle /addwallet command."""
        if not address:
            return "❌ Error: Please specify wallet address"
            
        # Basic address validation
        if not address.startswith('0x') or len(address) != 42:
            return "❌ Error: Invalid wallet address format"
        
        if await self.storage.add_wallet(address):
            return f"✅ Wallet {address[:6]}...{address[-4:]} successfully added for tracking"
        else:
            return f"❌ Wallet {address[:6]}...{address[-4:]} is already being tracked"

    async def handle_remove_wallet(self, address: str) -> str:
        """Handle /removewallet command."""
        if not address:
            return "❌ Error: Please specify wallet address"
        
        if await self.storage.remove_wallet(address):
            return f"✅ Wallet {address[:6]}...{address[-4:]} removed from tracking"
        else:
            return f"❌ Wallet {address[:6]}...{address[-4:]} not found in tracked list"

    async def handle_clear_wallets(self) -> str:
        """Handle /clearwallets command."""
        wallets = await self.storage.get_tracked_wallets()
        if not wallets:
            return "📝 No wallets to clear"
            
        for wallet in wallets:
            await self.storage.remove_wallet(wallet)
        
        return "✅ All wallets have been removed from tracking"

    async def handle_set_chain(self, chain: str) -> str:
        """Handle /setchain command."""
        if not chain:
            supported_chains = self.settings.get_supported_chains()
            return f"❌ Please specify network. Supported networks: {', '.join(supported_chains)}"
        
        chain = chain.upper()
        if chain not in self.settings.get_supported_chains():
            return f"❌ Unsupported network. Available networks: {', '.join(self.settings.get_supported_chains())}"
        
        if await self.settings.set_chain(chain):
            return f"✅ Network set to: {chain}"
        else:
            return "❌ Error setting network"

    async def handle_notifications(self, state: str) -> str:
        """Handle /notifications command."""
        if not state or state.lower() not in ['on', 'off']:
            return "❌ Please specify state (on/off)"
        
        enabled = state.lower() == 'on'
        if await self.settings.set_notifications(enabled):
            return f"✅ Notifications {'enabled' if enabled else 'disabled'}"
        else:
            return "❌ Error changing notification settings"

    async def handle_settings(self) -> str:
        """Handle /settings command."""
        settings = await self.settings.get_settings()
        
        settings_parts = [
            "⚙️ Current settings:",
            f"▫️ Network: {settings['chain']}",
            f"▫️ Notifications: {'Enabled' if settings['notifications_enabled'] else 'Disabled'}",
            f"▫️ Last updated: {datetime.fromtimestamp(settings['last_updated']).strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        return "\n".join(settings_parts)

    async def handle_last_transactions(self, limit: int = 5) -> str:
        """Handle /lasttx command."""
        transactions = await self.analyzer.get_last_transactions(limit)
        
        if not transactions:
            return "❌ No transactions found"
        
        result = ["📝 Latest transactions:"]
        for tx in transactions:
            action = "🟢 Purchase" if tx.transaction_type == "buy" else "🔴 Sale"
            result.append(
                f"▫️ {action}: {tx.amount_change:.4f} {tx.symbol} "
                f"(${tx.total_value_usd:.2f}) - "
                f"{datetime.fromtimestamp(tx.timestamp).strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        return "\n".join(result)

    async def handle_wallet_info(self, address: str = None) -> str:
        """Handle /walletinfo command."""
        print(f"\nHandling wallet info command for address: {address}")
        
        try:
            # If no address provided, use the first tracked wallet
            if not address:
                wallets = await self.storage.get_tracked_wallets()
                if not wallets:
                    return "❌ No wallets are being tracked. Add a wallet first using /addwallet command."
                address = wallets[0]
                print(f"No address provided, using first tracked wallet: {address}")

            # Validate address format
            if not self._is_valid_address(address):
                return f"❌ Invalid wallet address format: {address}"

            print("Getting wallet info from analyzer...")
            wallet_info = await self.analyzer.get_wallet_info(address)
            
            if not wallet_info:
                print("No wallet info returned from analyzer")
                return f"❌ Could not fetch information for wallet {address}. Please try again later."

            print(f"Received wallet info: {wallet_info}")
            
            # Format the response
            lines = [
                f"💼 Wallet information for {address[:6]}...{address[-4:]}:",
                f"▫️ Total value: ${wallet_info.total_value_usd:.2f}",
                "📊 Assets:"
            ]

            # Add token information
            for token in wallet_info.tokens:
                if token.total_value_usd > 0:  # Only show tokens with value
                    token_line = (
                        f"  • {token.symbol}: {token.amount:.4f} "
                        f"(${token.total_value_usd:.2f})"
                    )
                    lines.append(token_line)

            # If no tokens with value were found
            if len(lines) == 3:
                lines.append("  No assets found with value")

            response = "\n".join(lines)
            print(f"Formatted response: {response}")
            return response

        except Exception as e:
            print(f"Error in handle_wallet_info: {str(e)}", exc_info=True)
            return f"❌ Error processing wallet info: {str(e)}"

    def _is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format."""
        if not address:
            return False
        
        # Remove '0x' prefix if present
        if address.startswith('0x'):
            address = address[2:]
            
        # Check if it's a 40-character hex string
        return len(address) == 40 and all(c in '0123456789abcdefABCDEF' for c in address)

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
            chain = self.settings.get_settings()['chain']
        
        gas_info = await self.analyzer.get_gas_fees(chain)
        if not gas_info:
            return f"❌ Failed to get gas fees information for network {chain}"
        
        return (
            f"⛽ Gas fees for {chain}:\n"
            f"▫️ Low: {gas_info.low:.1f} Gwei\n"
            f"▫️ Medium: {gas_info.medium:.1f} Gwei\n"
            f"▫️ High: {gas_info.high:.1f} Gwei"
        ) 