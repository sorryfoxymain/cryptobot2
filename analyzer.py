from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from storage import Storage, WalletTransaction
from moralis_api import MoralisAPI

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

    async def get_last_transactions(self, limit: int = 5) -> List[WalletTransaction]:
        """Get latest transactions for all wallets."""
        wallets = self.storage.get_tracked_wallets()
        all_transactions = []
        
        for wallet in wallets:
            transactions = self.storage.get_recent_transactions(wallet, limit)
            all_transactions.extend(transactions)
        
        # Sort by time (newest first)
        return sorted(all_transactions, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_wallet_info(self, wallet_address: str) -> Optional[WalletBalance]:
        """Get complete wallet information."""
        try:
            # Get current balances
            balances = await self.moralis_api.get_token_balances(wallet_address)
            
            tokens = []
            total_value = 0
            
            for balance in balances:
                token = TokenInfo(
                    token_id=balance['id'],
                    symbol=balance['symbol'],
                    amount=float(balance['amount']),
                    price_usd=float(balance['price']),
                    total_value_usd=float(balance['amount']) * float(balance['price']),
                    chain=balance['chain']
                )
                tokens.append(token)
                total_value += token.total_value_usd
            
            # Calculate total PnL
            pnl = await self.calculate_total_pnl(wallet_address)
            
            return WalletBalance(
                total_value_usd=total_value,
                tokens=tokens,
                pnl_total_usd=pnl,
                last_updated=int(datetime.now().timestamp())
            )
        except Exception as e:
            print(f"Error getting wallet info: {str(e)}")
            return None

    async def calculate_total_pnl(self, wallet_address: str) -> float:
        """Calculate total PnL for all wallet transactions."""
        transactions = self.storage.get_recent_transactions(wallet_address, limit=1000)
        total_pnl = 0.0
        
        # Dictionary to track token purchases
        token_buys: Dict[str, List[Tuple[float, float]]] = {}
        
        for tx in sorted(transactions, key=lambda x: x.timestamp):
            if tx.transaction_type == "buy":
                if tx.token_id not in token_buys:
                    token_buys[tx.token_id] = []
                token_buys[tx.token_id].append((tx.amount_change, tx.price_usd))
            elif tx.transaction_type == "sell":
                if tx.token_id in token_buys and token_buys[tx.token_id]:
                    # FIFO for PnL calculation
                    buy_amount, buy_price = token_buys[tx.token_id].pop(0)
                    pnl = (tx.price_usd - buy_price) * min(abs(tx.amount_change), buy_amount)
                    total_pnl += pnl
        
        return total_pnl

    async def get_top_tokens(self, wallet_address: str, limit: int = 5, sort_by: str = 'value') -> List[TokenInfo]:
        """Get top tokens by volume or value."""
        wallet_info = await self.get_wallet_info(wallet_address)
        if not wallet_info:
            return []
        
        if sort_by == 'value':
            sorted_tokens = sorted(wallet_info.tokens, key=lambda x: x.total_value_usd, reverse=True)
        else:  # sort by amount
            sorted_tokens = sorted(wallet_info.tokens, key=lambda x: x.amount, reverse=True)
        
        return sorted_tokens[:limit]

    async def get_recent_buys(self, wallet_address: str, limit: int = 5) -> List[WalletTransaction]:
        """Get recent purchases."""
        transactions = self.storage.get_recent_transactions(wallet_address, limit=100)
        buys = [tx for tx in transactions if tx.transaction_type == "buy"]
        return sorted(buys, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_recent_sells(self, wallet_address: str, limit: int = 5) -> List[WalletTransaction]:
        """Get recent sales."""
        transactions = self.storage.get_recent_transactions(wallet_address, limit=100)
        sells = [tx for tx in transactions if tx.transaction_type == "sell"]
        return sorted(sells, key=lambda x: x.timestamp, reverse=True)[:limit]

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