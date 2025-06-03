from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from storage import Storage, WalletTransaction
from moralis_api import MoralisAPI
import asyncio
from functools import lru_cache
import time

@dataclass
class TokenInfo:
    token_id: str
    symbol: str
    amount: float
    price_usd: float
    total_value_usd: float
    chain: str

@dataclass
class WalletBalance:
    total_value_usd: float
    tokens: List[TokenInfo]
    pnl_total_usd: float
    last_updated: int

@dataclass
class GasInfo:
    chain: str
    low: float
    medium: float
    high: float
    timestamp: int

class AnalyzerExtended:
    def __init__(self, moralis_api: MoralisAPI, storage: Storage):
        self.moralis_api = moralis_api
        self.storage = storage
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def _cache_get(self, key: str):
        """Get value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return value
            del self._cache[key]
        return None

    def _cache_set(self, key: str, value):
        """Set value in cache with current timestamp."""
        self._cache[key] = (value, time.time())

    async def get_last_transactions(self, limit: int = 5) -> List[WalletTransaction]:
        """Get latest transactions for all wallets."""
        cache_key = f"last_transactions_{limit}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        wallets = await self.storage.get_tracked_wallets()
        all_transactions = []
        
        # Get transactions for each wallet concurrently
        async def get_wallet_transactions(wallet):
            return await self.storage.get_recent_transactions(wallet, limit)
        
        tasks = [get_wallet_transactions(wallet) for wallet in wallets]
        wallet_transactions = await asyncio.gather(*tasks)
        
        for transactions in wallet_transactions:
            all_transactions.extend(transactions)
        
        # Sort by time (newest first) and limit
        result = sorted(all_transactions, key=lambda x: x.timestamp, reverse=True)[:limit]
        self._cache_set(cache_key, result)
        return result

    async def get_wallet_info(self, wallet_address: str) -> Optional[WalletBalance]:
        """Get complete wallet information."""
        print(f"\nGetting wallet info for: {wallet_address}")
        
        cache_key = f"wallet_info_{wallet_address}"
        cached = self._cache_get(cache_key)
        if cached:
            print("Using cached data")
            return cached

        try:
            # Get all token balances (including native token)
            print("Requesting token balances...")
            token_balances = await self.moralis_api.get_token_balances(wallet_address)
            print(f"Received {len(token_balances)} token balances")
            
            tokens = []
            total_value = 0

            # Process tokens in parallel
            async def process_token(balance):
                try:
                    amount = float(balance['amount'])
                    price_usd = float(balance['price'])
                    total_value_usd = amount * price_usd
                    
                    token = TokenInfo(
                        token_id=balance['id'],
                        symbol=balance['symbol'],
                        amount=amount,
                        price_usd=price_usd,
                        total_value_usd=total_value_usd,
                        chain=balance['chain']
                    )
                    print(f"Processed token: {token.symbol} - Amount: {token.amount}, Value: ${token.total_value_usd}")
                    return token
                except Exception as e:
                    print(f"Error processing token balance: {balance} - Error: {str(e)}")
                    return None
            
            # Process all tokens (including native)
            print("Processing tokens...")
            tasks = [process_token(balance) for balance in token_balances]
            processed_tokens = await asyncio.gather(*tasks)
            
            # Filter out failed tokens
            tokens = [token for token in processed_tokens if token is not None]
            print(f"Successfully processed {len(tokens)} tokens")
            
            # Calculate total value
            total_value = sum(token.total_value_usd for token in tokens)
            print(f"Total value: ${total_value}")
            
            # Sort tokens by value
            tokens.sort(key=lambda x: x.total_value_usd, reverse=True)
            
            result = WalletBalance(
                total_value_usd=total_value,
                tokens=tokens,
                pnl_total_usd=0,  # We don't need PnL for simple balance display
                last_updated=int(datetime.now().timestamp())
            )
            
            self._cache_set(cache_key, result)
            return result
        except Exception as e:
            print(f"Error getting wallet info: {str(e)}")
            return None

    async def get_top_tokens(self, wallet_address: str, limit: int = 5, sort_by: str = 'value') -> List[TokenInfo]:
        """Get top tokens by volume or value."""
        cache_key = f"top_tokens_{wallet_address}_{limit}_{sort_by}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        wallet_info = await self.get_wallet_info(wallet_address)
        if not wallet_info:
            return []
        
        if sort_by == 'value':
            sorted_tokens = sorted(wallet_info.tokens, key=lambda x: x.total_value_usd, reverse=True)
        else:  # sort by amount
            sorted_tokens = sorted(wallet_info.tokens, key=lambda x: x.amount, reverse=True)
        
        result = sorted_tokens[:limit]
        self._cache_set(cache_key, result)
        return result

    async def get_recent_buys(self, wallet_address: str, limit: int = 5) -> List[WalletTransaction]:
        """Get recent purchases."""
        cache_key = f"recent_buys_{wallet_address}_{limit}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        transactions = await self.storage.get_recent_transactions(wallet_address, limit=100)
        buys = [tx for tx in transactions if tx.transaction_type == "buy"]
        result = sorted(buys, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        self._cache_set(cache_key, result)
        return result

    async def get_recent_sells(self, wallet_address: str, limit: int = 5) -> List[WalletTransaction]:
        """Get recent sales."""
        cache_key = f"recent_sells_{wallet_address}_{limit}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        transactions = await self.storage.get_recent_transactions(wallet_address, limit=100)
        sells = [tx for tx in transactions if tx.transaction_type == "sell"]
        result = sorted(sells, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        self._cache_set(cache_key, result)
        return result

    async def calculate_total_pnl(self, wallet_address: str) -> float:
        """Calculate total profit/loss for a wallet."""
        transactions = await self.storage.get_recent_transactions(wallet_address)
        total_pnl = 0.0
        
        for tx in transactions:
            if tx.transaction_type == "sell":
                pnl = await self.calculate_pnl(tx)
                total_pnl += pnl
                
        return total_pnl

    async def calculate_pnl(self, sell_tx: WalletTransaction) -> float:
        """Calculate profit/loss for a single sale transaction."""
        # Get previous buy transactions for this token
        buy_txs = await self.storage.get_recent_transactions(
            sell_tx.wallet_address,
            token_id=sell_tx.token_id,
            transaction_type="buy"
        )
        
        if not buy_txs:
            return 0.0
            
        # Calculate average buy price
        total_amount = sum(tx.amount_change for tx in buy_txs)
        total_value = sum(tx.total_value_usd for tx in buy_txs)
        avg_buy_price = total_value / total_amount if total_amount > 0 else 0
        
        # Calculate PnL
        sell_amount = abs(sell_tx.amount_change)
        return (sell_tx.price_usd - avg_buy_price) * sell_amount

    @lru_cache(maxsize=10)
    async def get_gas_fees(self, chain: str) -> Optional[GasInfo]:
        """Get current gas fees for the specified network."""
        try:
            gas_data = await self.moralis_api.get_gas_price(chain)
            return GasInfo(
                chain=chain.upper(),
                low=gas_data['safe_low'],
                medium=gas_data['standard'],
                high=gas_data['fast'],
                timestamp=int(datetime.now().timestamp())
            )
        except Exception as e:
            print(f"Error getting gas fees: {str(e)}")
            return None 