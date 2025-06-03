import aiosqlite
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from contextlib import asynccontextmanager

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
        self._initialized = False

    @classmethod
    async def create(cls, db_path: str = "wallet_monitor.db") -> 'Storage':
        """Create and initialize a new Storage instance."""
        instance = cls(db_path)
        await instance.initialize()
        return instance

    async def initialize(self):
        """Initialize the database if not already initialized."""
        if not self._initialized:
            await self._init_db()
            self._initialized = True

    async def _init_db(self):
        """Initialize database tables with optimized indexes."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    address TEXT PRIMARY KEY,
                    added_at INTEGER NOT NULL,
                    last_checked INTEGER
                )
            """)
            
            # Create token states table with optimized indexes
            await conn.execute("""
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
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_token_states_wallet ON token_states(wallet_address)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_token_states_token ON token_states(token_id)")
            
            # Create transactions table with optimized indexes
            await conn.execute("""
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
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_wallet ON transactions(wallet_address)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_token ON transactions(token_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(timestamp)")
            
            await conn.commit()

    @asynccontextmanager
    async def _get_connection(self):
        """Get database connection with context management."""
        async with aiosqlite.connect(self.db_path) as conn:
            yield conn

    async def add_wallet(self, address: str) -> bool:
        """Add a new wallet address for monitoring."""
        try:
            async with self._get_connection() as conn:
                await conn.execute(
                    "INSERT INTO wallets (address, added_at) VALUES (?, ?)",
                    (address.lower(), int(datetime.now().timestamp()))
                )
                await conn.commit()
                return True
        except aiosqlite.IntegrityError:
            return False
        except Exception as e:
            print(f"Error adding wallet: {str(e)}")
            return False

    async def remove_wallet(self, address: str) -> bool:
        """Remove a wallet address from monitoring."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("DELETE FROM wallets WHERE address = ?", (address.lower(),))
                await conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing wallet: {str(e)}")
            return False

    async def get_tracked_wallets(self) -> List[str]:
        """Get all tracked wallet addresses."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("SELECT address FROM wallets")
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print(f"Error getting tracked wallets: {str(e)}")
            return []

    async def update_token_state(self, wallet_address: str, token_id: str, symbol: str, 
                               chain: str, amount: float, price_usd: float):
        """Update or insert current token state for a wallet."""
        try:
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT OR REPLACE INTO token_states 
                    (wallet_address, token_id, symbol, chain, amount, price_usd, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    wallet_address.lower(), token_id, symbol, chain, 
                    amount, price_usd, int(datetime.now().timestamp())
                ))
                await conn.commit()
        except Exception as e:
            print(f"Error updating token state: {str(e)}")

    async def get_token_state(self, wallet_address: str, token_id: str, chain: str) -> Optional[Dict]:
        """Get previous token state for a wallet."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT symbol, amount, price_usd, last_updated 
                    FROM token_states 
                    WHERE wallet_address = ? AND token_id = ? AND chain = ?
                """, (wallet_address.lower(), token_id, chain))
                
                row = await cursor.fetchone()
                if row:
                    return {
                        'symbol': row[0],
                        'amount': row[1],
                        'price_usd': row[2],
                        'last_updated': row[3]
                    }
                return None
        except Exception as e:
            print(f"Error getting token state: {str(e)}")
            return None

    async def add_transaction(self, transaction: WalletTransaction):
        """Add a new transaction to history."""
        try:
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT INTO transactions 
                    (wallet_address, token_id, symbol, chain, amount_change, 
                     price_usd, total_value_usd, transaction_type, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.wallet_address.lower(), transaction.token_id,
                    transaction.symbol, transaction.chain, transaction.amount_change,
                    transaction.price_usd, transaction.total_value_usd,
                    transaction.transaction_type, transaction.timestamp
                ))
                await conn.commit()
        except Exception as e:
            print(f"Error adding transaction: {str(e)}")

    async def get_recent_transactions(
        self, 
        wallet_address: str, 
        token_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 100
    ) -> List[WalletTransaction]:
        """Get recent transactions for a wallet with optional filtering."""
        try:
            query = """
                SELECT wallet_address, token_id, symbol, chain, amount_change,
                       price_usd, total_value_usd, transaction_type, timestamp
                FROM transactions 
                WHERE wallet_address = ?
            """
            params = [wallet_address.lower()]
            
            if token_id:
                query += " AND token_id = ?"
                params.append(token_id)
            
            if transaction_type:
                query += " AND transaction_type = ?"
                params.append(transaction_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with self._get_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                
                return [
                    WalletTransaction(
                        wallet_address=row[0],
                        token_id=row[1],
                        symbol=row[2],
                        chain=row[3],
                        amount_change=row[4],
                        price_usd=row[5],
                        total_value_usd=row[6],
                        transaction_type=row[7],
                        timestamp=row[8]
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting recent transactions: {str(e)}")
            return []

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
    storage.add_transaction(transaction)
    
    # Print tracked wallets
    print("Tracked wallets:", storage.get_tracked_wallets()) 