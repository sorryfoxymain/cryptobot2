import aiosqlite
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class BotSettings:
    chain: str
    notifications_enabled: bool
    last_updated: int

class SettingsManager:
    def __init__(self, db_path: str = "wallet_monitor.db"):
        self.db_path = db_path
        self._initialized = False

    @classmethod
    async def create(cls, db_path: str = "wallet_monitor.db") -> 'SettingsManager':
        """Create and initialize a new SettingsManager instance."""
        instance = cls(db_path)
        await instance.initialize()
        return instance

    async def initialize(self):
        """Initialize the database if not already initialized."""
        if not self._initialized:
            await self._init_db()
            self._initialized = True

    async def _init_db(self):
        """Initialize settings table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    chain TEXT NOT NULL DEFAULT 'ETH',
                    notifications_enabled INTEGER NOT NULL DEFAULT 1,
                    last_updated INTEGER NOT NULL
                )
            """)
            
            # Insert default settings if not exists
            await conn.execute("""
                INSERT OR IGNORE INTO bot_settings (id, chain, notifications_enabled, last_updated)
                VALUES (1, 'ETH', 1, ?)
            """, (int(datetime.now().timestamp()),))
            
            await conn.commit()

    async def get_settings(self):
        """Get current bot settings."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                SELECT chain, notifications_enabled, last_updated
                FROM bot_settings
                WHERE id = 1
            """)
            row = await cursor.fetchone()
            if row:
                return {
                    'chain': row[0],
                    'notifications_enabled': bool(row[1]),
                    'last_updated': row[2]
                }
            return None

    async def set_chain(self, chain: str) -> bool:
        """Set the blockchain network to monitor."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                UPDATE bot_settings 
                SET chain = ?, last_updated = ?
                WHERE id = 1
            """, (chain.upper(), int(datetime.now().timestamp())))
            await conn.commit()
            return cursor.rowcount > 0

    async def set_notifications(self, enabled: bool) -> bool:
        """Enable or disable notifications."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                UPDATE bot_settings 
                SET notifications_enabled = ?, last_updated = ?
                WHERE id = 1
            """, (enabled, int(datetime.now().timestamp())))
            await conn.commit()
            return cursor.rowcount > 0

    def get_supported_chains(self) -> List[str]:
        """Get list of supported blockchain networks."""
        return ["ETH", "BSC", "ARB", "MATIC", "AVAX"] 