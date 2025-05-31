from typing import List, Dict, Optional, Tuple
from datetime import datetime
from moralis_api import MoralisAPI
from storage import Storage, WalletTransaction

class ActivityAnalyzer:
    def __init__(self, moralis_api: MoralisAPI, storage: Storage):
        self.moralis_api = moralis_api
        self.storage = storage
        
    async def analyze_wallet(self, wallet_address: str) -> List[WalletTransaction]:
        """
        Analyze current wallet state and detect token purchases or sales.
        
        Args:
            wallet_address: Wallet address to analyze
            
        Returns:
            List[WalletTransaction]: List of detected transactions
        """
        # Get current token balances
        current_balances = await self.moralis_api.get_token_balances(wallet_address)
        detected_transactions = []
        
        # Process each current balance
        for balance in current_balances:
            # Get previous state of this token
            prev_state = self.storage.get_token_state(
                wallet_address=wallet_address,
                token_id=balance['id'],
                chain=balance['chain']
            )
            
            transaction = await self._detect_transaction(wallet_address, balance, prev_state)
            if transaction:
                detected_transactions.append(transaction)
                self.storage.record_transaction(transaction)
            
            # Update token state in storage
            self.storage.update_token_state(
                wallet_address=wallet_address,
                token_id=balance['id'],
                symbol=balance['symbol'],
                chain=balance['chain'],
                amount=balance['amount'],
                price_usd=balance['price']
            )
        
        return detected_transactions
    
    async def _detect_transaction(
        self, 
        wallet_address: str, 
        current_balance: Dict, 
        prev_state: Optional[Dict]
    ) -> Optional[WalletTransaction]:
        """
        Detect a transaction by comparing current and previous token states.
        """
        if not prev_state:
            # New token appeared - this is a purchase
            if current_balance['amount'] > 0:
                return WalletTransaction(
                    wallet_address=wallet_address,
                    token_id=current_balance['id'],
                    symbol=current_balance['symbol'],
                    chain=current_balance['chain'],
                    amount_change=current_balance['amount'],
                    price_usd=current_balance['price'],
                    total_value_usd=current_balance['amount'] * current_balance['price'],
                    transaction_type="buy",
                    timestamp=int(datetime.now().timestamp())
                )
            return None
            
        prev_amount = prev_state['amount']
        amount_change = current_balance['amount'] - prev_amount
        
        # Define thresholds for significant changes
        SIGNIFICANT_CHANGE_THRESHOLD = 0.001  # 0.1% of previous amount
        significant_change = abs(amount_change) > (prev_amount * SIGNIFICANT_CHANGE_THRESHOLD)
        
        if not significant_change:
            return None
            
        transaction_type = "buy" if amount_change > 0 else "sell"
        
        # For sales, use absolute value of change
        amount_change_abs = abs(amount_change)
        total_value = amount_change_abs * current_balance['price']
        
        return WalletTransaction(
            wallet_address=wallet_address,
            token_id=current_balance['id'],
            symbol=current_balance['symbol'],
            chain=current_balance['chain'],
            amount_change=amount_change_abs,
            price_usd=current_balance['price'],
            total_value_usd=total_value,
            transaction_type=transaction_type,
            timestamp=int(datetime.now().timestamp())
        )

    async def calculate_pnl(self, transaction: WalletTransaction) -> Optional[float]:
        """
        Calculate profit/loss for a sell transaction.
        """
        if transaction.transaction_type != "sell":
            return None
            
        # Get recent buy transactions for this token
        recent_transactions = self.storage.get_recent_transactions(transaction.wallet_address)
        buy_transactions = [
            t for t in recent_transactions 
            if t.token_id == transaction.token_id 
            and t.chain == transaction.chain
            and t.transaction_type == "buy"
        ]
        
        if not buy_transactions:
            return None
            
        # Use last purchase price to calculate PnL
        last_buy = buy_transactions[0]
        pnl = (transaction.price_usd - last_buy.price_usd) * transaction.amount_change
        return pnl

# Example usage
if __name__ == "__main__":
    import asyncio
    from config import MORALIS_API_KEY
    
    async def test_analyzer():
        moralis = MoralisAPI(MORALIS_API_KEY)
        storage = Storage()
        analyzer = ActivityAnalyzer(moralis, storage)
        
        # Test wallet address
        test_wallet = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        
        print(f"Analyzing wallet {test_wallet}...")
        transactions = await analyzer.analyze_wallet(test_wallet)
        
        for tx in transactions:
            print(f"\nDetected {tx.transaction_type} transaction:")
            print(f"Token: {tx.symbol} ({tx.chain})")
            print(f"Amount: {tx.amount_change:.4f}")
            print(f"Price: ${tx.price_usd:.2f}")
            print(f"Total value: ${tx.total_value_usd:.2f}")
            
            if tx.transaction_type == "sell":
                pnl = await analyzer.calculate_pnl(tx)
                if pnl is not None:
                    print(f"PnL: ${pnl:.2f}")
    
    asyncio.run(test_analyzer()) 