import sqlite3
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BotSettings:
    chain: str
    notifications_enabled: bool
    last_updated: int

class SettingsManager:
    def __init__(self, db_path: str = "wallet_monitor.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize settings table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    chain TEXT NOT NULL DEFAULT 'ETH',
                    notifications_enabled BOOLEAN NOT NULL DEFAULT 1,
                    last_updated INTEGER NOT NULL
                )
            """)
            
            # Insert default settings if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO bot_settings (id, chain, notifications_enabled, last_updated)
                VALUES (1, 'ETH', 1, ?)
            """, (int(datetime.now().timestamp()),))
            
            conn.commit()

    def get_settings(self) -> BotSettings:
        """Get current bot settings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chain, notifications_enabled, last_updated FROM bot_settings WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return BotSettings(
                    chain=row[0],
                    notifications_enabled=bool(row[1]),
                    last_updated=row[2]
                )
            return BotSettings("ETH", True, int(datetime.now().timestamp()))

    def set_chain(self, chain: str) -> bool:
        """Set the blockchain network to monitor."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bot_settings 
                SET chain = ?, last_updated = ?
                WHERE id = 1
            """, (chain.upper(), int(datetime.now().timestamp())))
            return cursor.rowcount > 0

    def set_notifications(self, enabled: bool) -> bool:
        """Enable or disable notifications."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bot_settings 
                SET notifications_enabled = ?, last_updated = ?
                WHERE id = 1
            """, (enabled, int(datetime.now().timestamp())))
            return cursor.rowcount > 0

    def get_supported_chains(self) -> List[str]:
        """Get list of supported blockchain networks."""
        return ["ETH", "BSC", "ARB", "MATIC", "AVAX"] 