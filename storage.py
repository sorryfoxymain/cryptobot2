import sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class WalletTransaction:
    wallet_address: str
    token_id: str
    symbol: str
    chain: str
    amount_change: float
    price_usd: float
    total_value_usd: float
    transaction_type: str  # 'buy' or 'sell'
    timestamp: int

class Storage:
    def __init__(self, db_path: str = "wallet_monitor.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create wallets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    address TEXT PRIMARY KEY,
                    added_at INTEGER NOT NULL,
                    last_checked INTEGER
                )
            """)
            
            # Create token states table for tracking previous balances
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_states (
                    wallet_address TEXT,
                    token_id TEXT,
                    symbol TEXT,
                    chain TEXT,
                    amount REAL,
                    price_usd REAL,
                    last_updated INTEGER,
                    PRIMARY KEY (wallet_address, token_id, chain)
                )
            """)
            
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_address TEXT,
                    token_id TEXT,
                    symbol TEXT,
                    chain TEXT,
                    amount_change REAL,
                    price_usd REAL,
                    total_value_usd REAL,
                    transaction_type TEXT,
                    timestamp INTEGER,
                    FOREIGN KEY (wallet_address) REFERENCES wallets(address)
                )
            """)
            
            conn.commit()

    def add_wallet(self, address: str) -> bool:
        """
        Add a new wallet address for monitoring.
        
        Args:
            address: Wallet address to monitor
            
        Returns:
            bool: True if successfully added, False if already exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO wallets (address, added_at) VALUES (?, ?)",
                    (address, int(datetime.now().timestamp()))
                )
                return True
        except sqlite3.IntegrityError:
            return False

    def remove_wallet(self, address: str) -> bool:
        """
        Remove a wallet address from monitoring.
        
        Args:
            address: Wallet address to remove
            
        Returns:
            bool: True if successfully removed, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM wallets WHERE address = ?", (address,))
            return cursor.rowcount > 0

    def get_tracked_wallets(self) -> List[str]:
        """Get all tracked wallet addresses."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT address FROM wallets")
            return [row[0] for row in cursor.fetchall()]

    def update_token_state(self, wallet_address: str, token_id: str, symbol: str, 
                          chain: str, amount: float, price_usd: float):
        """
        Update or insert current token state for a wallet.
        
        Args:
            wallet_address: Wallet address
            token_id: Token identifier
            symbol: Token symbol
            chain: Blockchain network
            amount: Token amount
            price_usd: Token price in USD
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO token_states 
                (wallet_address, token_id, symbol, chain, amount, price_usd, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (wallet_address, token_id, symbol, chain, amount, price_usd, 
                 int(datetime.now().timestamp())))

    def get_token_state(self, wallet_address: str, token_id: str, chain: str) -> Optional[Dict]:
        """
        Get previous token state for a wallet.
        
        Args:
            wallet_address: Wallet address
            token_id: Token identifier
            chain: Blockchain network
            
        Returns:
            Optional[Dict]: Token state if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, amount, price_usd, last_updated 
                FROM token_states 
                WHERE wallet_address = ? AND token_id = ? AND chain = ?
            """, (wallet_address, token_id, chain))
            
            row = cursor.fetchone()
            if row:
                return {
                    'symbol': row[0],
                    'amount': row[1],
                    'price_usd': row[2],
                    'last_updated': row[3]
                }
            return None

    def record_transaction(self, transaction: WalletTransaction):
        """
        Record a new transaction (buy/sell) in the database.
        
        Args:
            transaction: Transaction details
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions 
                (wallet_address, token_id, symbol, chain, amount_change, 
                 price_usd, total_value_usd, transaction_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.wallet_address,
                transaction.token_id,
                transaction.symbol,
                transaction.chain,
                transaction.amount_change,
                transaction.price_usd,
                transaction.total_value_usd,
                transaction.transaction_type,
                transaction.timestamp
            ))

    def get_recent_transactions(self, wallet_address: str, limit: int = 10) -> List[WalletTransaction]:
        """
        Get recent transactions for a wallet.
        
        Args:
            wallet_address: Wallet address
            limit: Maximum number of transactions to return
            
        Returns:
            List[WalletTransaction]: List of recent transactions
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE wallet_address = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (wallet_address, limit))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append(WalletTransaction(
                    wallet_address=row[1],
                    token_id=row[2],
                    symbol=row[3],
                    chain=row[4],
                    amount_change=row[5],
                    price_usd=row[6],
                    total_value_usd=row[7],
                    transaction_type=row[8],
                    timestamp=row[9]
                ))
            return transactions

# Example usage
if __name__ == "__main__":
    storage = Storage()
    
    # Test adding a wallet
    test_wallet = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    storage.add_wallet(test_wallet)
    
    # Test updating token state
    storage.update_token_state(
        wallet_address=test_wallet,
        token_id="eth",
        symbol="ETH",
        chain="eth",
        amount=1.5,
        price_usd=2000.0
    )
    
    # Test recording a transaction
    transaction = WalletTransaction(
        wallet_address=test_wallet,
        token_id="eth",
        symbol="ETH",
        chain="eth",
        amount_change=1.5,
        price_usd=2000.0,
        total_value_usd=3000.0,
        transaction_type="buy",
        timestamp=int(datetime.now().timestamp())
    )
    storage.record_transaction(transaction)
    
    # Print tracked wallets
    print("Tracked wallets:", storage.get_tracked_wallets()) 